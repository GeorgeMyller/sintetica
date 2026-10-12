"""Motor do lote: rodadas, blocos concorrentes, revisão e gravação por bloco.

Provedor automático (D-08): uma fila de blocos atendida por N trabalhadores; uma falha do
provedor, o teto de custo ou uma falha de mascaramento ou de escrita param a fila. Blocos já
em voo terminam e são gravados. Harness (D-04): 1 pedido com todos os faltantes por rodada,
no protocolo em 2 passos da Q29.
"""

from __future__ import annotations

import asyncio
import math
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from sintetica.batch.output import append_block
from sintetica.batch.plan import split
from sintetica.batch.request import build_batch_request
from sintetica.batch.review import DedupIndex, review_block
from sintetica.batch.state import (
    CONFORMITY,
    MAX_ROUNDS,
    RunState,
    RunStatus,
    partial_path,
    utc_now,
)
from sintetica.intent import IntentModel
from sintetica.providers.decorators.concurrency import DEFAULT_CONCURRENCY
from sintetica.providers.domain import STOP_BUDGET
from sintetica.providers.errors import HarnessResponsePending, ProviderError
from sintetica.providers.harness.store import RequestStore
from sintetica.providers.ports import LLMProvider
from sintetica.sample.review import Masker

Progress = Callable[[str], None]


class MaskingFailed(Exception):
    """Mascaramento indisponível no meio do lote: o bloco não é gravado (RN-08)."""


class BatchWriteError(Exception):
    """Falha ao gravar o arquivo parcial, o estado ou ao apagar a resposta bruta."""


def usd(value: Decimal) -> str:
    """Valor em dólar com 2 casas e vírgula decimal (`0,42`)."""
    return f"{value.quantize(Decimal('0.01')):f}".replace(".", ",")


def conforming(state: RunState) -> bool:
    return state.accepted >= math.ceil(state.volume_requested * CONFORMITY)


def finish(state: RunState, status: RunStatus | None = None, cause: str | None = None) -> RunState:
    """Status final pela RN-10: `concluido` com ≥ 95% do volume, `incompleto` abaixo disso."""
    if status is None:
        status = "concluido" if conforming(state) else "incompleto"
    return state.model_copy(
        update={
            "status": status,
            "stop_cause": cause,
            "pending_request_id": None,
            "pending_command": None,
            "finished_at": utc_now(),
        }
    )


@dataclass
class EngineContext:
    dataset: Path
    model: type[BaseModel]
    intent: IntentModel
    schema_json: Mapping[str, Any]
    seeds: Sequence[Mapping[str, object]]
    masker: Masker
    index: DedupIndex
    save: Callable[[RunState], RunState]
    progress: Progress
    concurrency: int = DEFAULT_CONCURRENCY


class BatchEngine:
    def __init__(self, ctx: EngineContext) -> None:
        self._ctx = ctx

    def _absorb(self, state: RunState, records: Sequence[Mapping[str, object]], k: int) -> RunState:
        ctx = self._ctx
        review = review_block(records, ctx.model, ctx.index, ctx.masker, k)
        try:
            append_block(partial_path(ctx.dataset), review.accepted)
        except OSError as exc:
            raise BatchWriteError(
                f"não foi possível gravar {partial_path(ctx.dataset)}: {exc.strerror}; "
                "o arquivo parcial ficou no último bloco íntegro"
            ) from exc
        return state.model_copy(
            update={
                "accepted": state.accepted + len(review.accepted),
                "discarded_invalid": state.discarded_invalid + review.invalid,
                "discarded_duplicate": state.discarded_duplicate + review.duplicate,
            }
        )

    def _line(self, state: RunState, done: int, total: int) -> str:
        return (
            f"Bloco {done}/{total} (rodada {state.round}), {state.accepted} válidos, "
            f"{state.discarded} descartados, US$ {usd(state.cost_usd)}"
        )

    # -- provedor automático ----------------------------------------------------------------

    def run_automatic(self, state: RunState, provider: LLMProvider) -> RunState:
        return asyncio.run(self._automatic(state, provider))

    async def _automatic(self, state: RunState, provider: LLMProvider) -> RunState:
        stop: tuple[RunStatus, str] | None = None
        while state.missing > 0 and state.round < MAX_ROUNDS and stop is None:
            state = self._ctx.save(
                state.model_copy(update={"round": state.round + 1, "status": "em_andamento"})
            )
            state, stop = await self._round(state, provider)
        if stop is not None:
            return finish(state, *stop)
        return finish(state)

    async def _round(
        self, state: RunState, provider: LLMProvider
    ) -> tuple[RunState, tuple[RunStatus, str] | None]:
        """1 rodada: os faltantes em blocos, atendidos por N trabalhadores."""
        ctx = self._ctx
        sizes = split(state.missing, state.block_size)
        queue = deque(enumerate(sizes, start=1))
        total, done = len(sizes), 0
        halt = asyncio.Event()
        stop: tuple[RunStatus, str] | None = None
        fatal: Exception | None = None

        async def worker() -> None:
            nonlocal state, stop, fatal, done
            while queue and not halt.is_set():
                block, k = queue.popleft()
                request = build_batch_request(
                    ctx.intent, ctx.schema_json, ctx.seeds, k, block, total, state.round
                )
                try:
                    result = await provider.generate(request)
                except ProviderError as exc:
                    if stop is None:
                        stop = ("falha_provedor", f"falha do provedor {provider.name}: {exc}")
                    halt.set()
                    return
                if fatal is not None:
                    return
                state = state.model_copy(update={"cost_usd": state.cost_usd + result.cost_usd})
                if result.stop_reason == STOP_BUDGET:
                    if stop is None:
                        stop = ("interrompido_custo", "teto de custo atingido")
                    halt.set()
                    return
                try:
                    state = ctx.save(self._absorb(state, result.records, k))
                except (MaskingFailed, BatchWriteError) as exc:
                    fatal = exc
                    halt.set()
                    return
                done += 1
                ctx.progress(self._line(state, done, total))

        await asyncio.gather(*(worker() for _ in range(min(ctx.concurrency, total))))
        if fatal is not None:
            raise fatal
        return state, stop

    # -- harness ----------------------------------------------------------------------------

    def run_harness(self, state: RunState, provider: LLMProvider, store: RequestStore) -> RunState:
        ctx = self._ctx
        if state.pending_request_id is not None:
            rid = state.pending_request_id
            response = store.load_response(rid)
            if response is None:
                return state  # o agente ainda não respondeu
            state = self._absorb(state, response[1], state.missing)
            # A resposta bruta pode ter PII; só a versão mascarada fica no disco (W006).
            try:
                store.response_path(rid).unlink(missing_ok=True)
            except OSError as exc:
                raise BatchWriteError(
                    f"não foi possível apagar a resposta bruta: {exc.strerror}"
                ) from exc
            state = ctx.save(
                state.model_copy(
                    update={
                        "status": "em_andamento",
                        "pending_request_id": None,
                        "pending_command": None,
                    }
                )
            )
            ctx.progress(self._line(state, 1, 1))
        while state.missing > 0 and state.round < MAX_ROUNDS:
            round_ = state.round + 1
            k = state.missing
            request = build_batch_request(
                ctx.intent, ctx.schema_json, ctx.seeds, k, 1, 1, round_, harness=True
            )
            state = state.model_copy(update={"round": round_})
            try:
                result = asyncio.run(provider.generate(request))
            except HarnessResponsePending as pending:
                return ctx.save(
                    state.model_copy(
                        update={
                            "status": "aguardando_agente",
                            "pending_request_id": pending.request_id,
                            "pending_command": pending.command,
                        }
                    )
                )
            except ProviderError as exc:
                return finish(state, "falha_provedor", f"falha do provedor {provider.name}: {exc}")
            state = ctx.save(self._absorb(state, result.records, k))
            ctx.progress(self._line(state, 1, 1))
        return finish(state)
