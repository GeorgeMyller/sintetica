"""Orquestração de `sintetica sample run | adjust | approve | show` (interfaces/sample-cli.md)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from sintetica.command import cli_command
from sintetica.intent import IntentError, IntentModel, load_intent_model
from sintetica.pii import PiiGuard, PolicyError
from sintetica.providers.domain import ProviderChoice
from sintetica.providers.errors import HarnessResponsePending, ProviderError
from sintetica.providers.factory import build_provider
from sintetica.providers.harness.store import RequestStore
from sintetica.providers.ports import LLMProvider
from sintetica.sample.render import render_records
from sintetica.sample.request import build_request
from sintetica.sample.review import parse_line, review_records
from sintetica.sample.state import (
    DEFAULT_N,
    MAX_ATTEMPTS,
    MAX_N,
    MIN_N,
    SampleMeta,
    SampleState,
    load_sample_state,
    save_sample_state,
    utc_now,
    write_seeds,
)
from sintetica.schema import GeneratedCodeError, SchemaNotFoundError, load_record_model
from sintetica.schema.loader import RECORD_SCHEMA_JSON, read_spec
from sintetica.schema.state import load_state as load_schema_state
from sintetica.schema.version import schema_version

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_MASKING = 9
EXIT_WRITE = 10
EXIT_CONTRACT = 11
EXIT_PROVIDER = 12
EXIT_NOT_APPROVABLE = 13

ADJUST_SUGGEST_FROM = 4
POLICY_PATH = Path(".sintetica") / "policy.json"

ProviderFactory = Callable[[int, Path, Path], tuple[LLMProvider, ProviderChoice]]


@dataclass
class CommandResult:
    code: int
    out: list[str] = field(default_factory=list)
    err: list[str] = field(default_factory=list)


class _Fail(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class _Ctx:
    project: Path
    slug: str
    dataset: Path
    intent: IntentModel
    model: type[BaseModel]
    schema_json: Mapping[str, Any]
    version: str
    fmt: str


def _default_provider(k: int, dataset: Path, project: Path) -> tuple[LLMProvider, ProviderChoice]:
    return build_provider(k, dataset_dir=dataset, project_dir=project, harness_available=True)


def _context(project: Path, slug: str) -> _Ctx:
    dataset = project / "datasets" / slug
    if not dataset.is_dir():
        raise _Fail(EXIT_USAGE, f"dataset inexistente: datasets/{slug}; inicie com sintetica start")
    try:
        intent = load_intent_model(dataset)
    except IntentError as exc:
        raise _Fail(EXIT_USAGE, str(exc)) from exc
    try:
        spec = read_spec(dataset)
    except SchemaNotFoundError as exc:
        raise _Fail(
            EXIT_CONTRACT, f"sem contrato; rode: {cli_command()} schema build {slug}"
        ) from exc
    version = schema_version(spec)
    schema_state = load_schema_state(dataset)
    if schema_state is None or schema_state.status != "aprovado":
        raise _Fail(
            EXIT_CONTRACT, f"contrato não aprovado; rode: {cli_command()} schema approve {slug}"
        )
    if schema_state.schema_version != version:
        raise _Fail(
            EXIT_CONTRACT, f"contrato desatualizado; rode: {cli_command()} schema build {slug}"
        )
    try:
        model = load_record_model(dataset)
        schema_json = json.loads((dataset / RECORD_SCHEMA_JSON).read_text("utf-8"))
    except (GeneratedCodeError, OSError, ValueError) as exc:
        raise _Fail(
            EXIT_CONTRACT, f"contrato ilegível; rode: {cli_command()} schema build {slug}"
        ) from exc
    return _Ctx(project, slug, dataset, intent, model, schema_json, version, spec.format)


def _masker(ctx: _Ctx) -> Callable[[str, str], str]:
    try:
        guard = PiiGuard.for_dataset(ctx.dataset, ctx.project / POLICY_PATH)
    except PolicyError as exc:
        raise _Fail(
            EXIT_MASKING, f"mascaramento de PII indisponível: {exc}; nada foi gravado"
        ) from exc

    def mask(text: str, path: str) -> str:
        try:
            return guard.mask(text, field=path).text
        except OSError as exc:
            raise _Fail(EXIT_MASKING, f"mascaramento de PII indisponível: {exc}") from exc

    return mask


def _save(ctx: _Ctx, state: SampleState) -> None:
    try:
        save_sample_state(ctx.dataset, state)
    except OSError as exc:
        raise _Fail(
            EXIT_WRITE, f"não foi possível gravar o estado da amostra: {exc.strerror}"
        ) from exc


# -- laço de tentativas ------------------------------------------------------------------


def _absorb(
    ctx: _Ctx, state: SampleState, records: Any, out: list[str], masker: Callable[[str, str], str]
) -> SampleState:
    result = review_records(records, ctx.model, state.accepted, masker, state.missing)
    out.append(
        f"Tentativa {state.attempt}: {len(result.accepted)} aceito(s), "
        f"{len(result.rejected)} descartado(s)."
    )
    out.extend(f"  - {reason}" for reason in result.rejected)
    return state.model_copy(
        update={
            "accepted": state.accepted + result.accepted,
            "rejected": state.rejected + result.rejected,
            "pending_request_id": None,
            "pending_command": None,
        }
    )


def _advance(
    ctx: _Ctx, state: SampleState, out: list[str], provider_factory: ProviderFactory
) -> SampleState:
    masker: Callable[[str, str], str] | None = None
    if state.pending_request_id is not None:
        store, rid = RequestStore(ctx.dataset), state.pending_request_id
        response = store.load_response(rid)
        if response is None:
            return state  # o agente ainda não respondeu
        masker = _masker(ctx)
        state = _absorb(ctx, state, response[1], out, masker)
        # A resposta bruta do agente pode ter PII; só a versão mascarada fica no disco (RN-05).
        # Cada tentativa tem pedido próprio, então a resposta nunca é lida de novo.
        try:
            store.response_path(rid).unlink(missing_ok=True)
        except OSError as exc:
            raise _Fail(
                EXIT_WRITE, f"não foi possível apagar a resposta bruta: {exc.strerror}"
            ) from exc
    while state.missing > 0 and state.attempt < MAX_ATTEMPTS:
        attempt = state.attempt + 1
        k = state.missing
        request = build_request(
            ctx.intent, ctx.schema_json, state.accepted, k, attempt, state.adjustment
        )
        try:
            provider, choice = provider_factory(k, ctx.dataset, ctx.project)
        except ProviderError as exc:  # ex.: nenhum provedor disponível na escolha
            raise _Fail(EXIT_PROVIDER, f"falha ao escolher o provedor: {exc}") from exc
        state = state.model_copy(
            update={
                "attempt": attempt,
                "provider": choice.provider,
                "provider_reason": choice.reason,
            }
        )
        try:
            result = asyncio.run(provider.generate(request))
        except HarnessResponsePending as pending:
            return state.model_copy(
                update={
                    "status": "aguardando_agente",
                    "pending_request_id": pending.request_id,
                    "pending_command": pending.command,
                }
            )
        except ProviderError as exc:
            raise _Fail(EXIT_PROVIDER, f"falha do provedor {choice.provider}: {exc}") from exc
        masker = masker or _masker(ctx)
        state = _absorb(ctx, state, result.records, out, masker)
    return state.model_copy(update={"status": "em_revisao"})


def _finish(ctx: _Ctx, state: SampleState, out: list[str]) -> SampleState:
    """Estado final da rodada: Expresso aprova com N válidos e para na parcial (Q43)."""
    if state.status != "em_revisao":
        return state
    if ctx.intent.mode == "expresso":
        if state.missing == 0:
            return _approve(ctx, state, out)
        out.append(
            f"Amostra parcial ({len(state.accepted)} de {state.n}) no modo Expresso: "
            "a automação parou. Decida: aprovar, ajustar ou voltar ao contrato."
        )
        return state.model_copy(update={"status": "interrompida"})
    if state.missing > 0:
        out.append(
            f"Após {MAX_ATTEMPTS} tentativas, a amostra tem {len(state.accepted)} de {state.n} "
            "registros válidos. Considere voltar ao contrato."
        )
    return state


def _approve(ctx: _Ctx, state: SampleState, out: list[str]) -> SampleState:
    for line in state.accepted:  # revalida com o contrato atual antes de gravar a semente
        ctx.model.model_validate(parse_line(line))
    lines = list(state.accepted)
    partial = len(lines) < state.n
    meta = SampleMeta(
        schema_version=ctx.version,
        approved_at=utc_now(),
        provider=state.provider or "harness",
        n_requested=state.n,
        n_records=len(lines),
        partial=partial,
        rounds=state.round,
    )
    try:
        jsonl, meta_path = write_seeds(ctx.dataset, lines, meta)
    except OSError as exc:
        raise _Fail(EXIT_WRITE, f"não foi possível gravar a semente: {exc.strerror}") from exc
    if partial:
        out.append(f"Atenção: amostra parcial aprovada ({len(lines)} de {state.n} registros).")
    out.append(f"Amostra aprovada: {jsonl.resolve()}")
    out.append(f"Metadados: {meta_path.resolve()}")
    out.append(f"Próximo passo: {cli_command()} generate {ctx.slug}")
    return state.model_copy(update={"status": "aprovada"})


def _report(ctx: _Ctx, state: SampleState, out: list[str]) -> list[str]:
    head = [
        f"Amostra do dataset {ctx.slug}: {len(state.accepted)} de {state.n} registro(s) válido(s), "
        f"estado {state.status}"
    ]
    if state.provider:
        head.append(f"Provedor: {state.provider} ({state.provider_reason})")
    if state.status == "aguardando_agente":
        path = RequestStore(ctx.dataset).request_path(state.pending_request_id or "")
        return [
            *head,
            *out,
            f"Pedido para o agente (tentativa {state.attempt} de {MAX_ATTEMPTS}): {path.resolve()}",
            "Gere os registros conforme o pedido e envie 1 objeto JSON por linha:",
            f"  {state.pending_command} < registros.jsonl",
            f"Depois rode: {cli_command()} sample run {ctx.slug}",
        ]
    lines = [*head, *out, *render_records(state.accepted, ctx.model, ctx.fmt)]
    if state.status in ("em_revisao", "interrompida"):
        lines += [
            "Opções:",
            f"  aprovar:   {cli_command()} sample approve {ctx.slug}",
            f"  ajustar:   {cli_command()} sample adjust {ctx.slug} '<pedido>'",
            "  voltar ao contrato: edite schema.draft.json e rode "
            f"{cli_command()} schema build {ctx.slug}",
        ]
    return lines


def _run_round(
    ctx: _Ctx, state: SampleState, out: list[str], factory: ProviderFactory
) -> CommandResult:
    if state.status == "aguardando_agente":
        state = _advance(ctx, state, out, factory)
    state = _finish(ctx, state, out)
    _save(ctx, state)
    return CommandResult(EXIT_OK, out=_report(ctx, state, out))


def run(
    project: Path,
    slug: str,
    n: int | None = None,
    provider_factory: ProviderFactory | None = None,
) -> CommandResult:
    factory = provider_factory or _default_provider
    out: list[str] = []
    try:
        ctx = _context(project, slug)
        state = load_sample_state(ctx.dataset)
        if state is not None and state.schema_version != ctx.version:
            out.append("Aviso: o contrato mudou; a amostra anterior foi descartada.")
            state = None
        if state is None:
            size = DEFAULT_N if n is None else n
            if not MIN_N <= size <= MAX_N:
                return CommandResult(EXIT_USAGE, err=[f"--n deve estar entre {MIN_N} e {MAX_N}"])
            state = SampleState(status="aguardando_agente", n=size, schema_version=ctx.version)
        elif n is not None and n != state.n:
            out.append(f"Aviso: --n {n} ignorado; a rodada atual pede {state.n} registros.")
        return _run_round(ctx, state, out, factory)
    except _Fail as fail:
        return CommandResult(fail.code, out=out, err=[str(fail)])


def adjust(
    project: Path, slug: str, text: str, provider_factory: ProviderFactory | None = None
) -> CommandResult:
    if not text.strip():
        return CommandResult(EXIT_USAGE, err=["informe o pedido de ajuste"])
    out: list[str] = []
    try:
        ctx = _context(project, slug)
        state = load_sample_state(ctx.dataset)
        if state is None or state.schema_version != ctx.version:
            return CommandResult(
                EXIT_NOT_APPROVABLE,
                err=[f"sem amostra em andamento; rode sintetica sample run {slug}"],
            )
        if state.status == "aprovada":
            return CommandResult(EXIT_NOT_APPROVABLE, err=["a amostra já foi aprovada"])
        masked = _masker(ctx)(text.strip(), "ajuste")
        state = SampleState(
            status="aguardando_agente",
            n=state.n,
            schema_version=ctx.version,
            round=state.round + 1,
            adjustment=masked,
        )
        if state.round >= ADJUST_SUGGEST_FROM:
            out.append(
                f"{state.round} rodadas de ajuste sem aprovação. Considere voltar ao contrato."
            )
        return _run_round(ctx, state, out, provider_factory or _default_provider)
    except _Fail as fail:
        return CommandResult(fail.code, out=out, err=[str(fail)])


def approve(project: Path, slug: str) -> CommandResult:
    out: list[str] = []
    try:
        ctx = _context(project, slug)
        state = load_sample_state(ctx.dataset)
        if state is None:
            return CommandResult(
                EXIT_NOT_APPROVABLE, err=["sem amostra; rode sintetica sample run"]
            )
        if state.schema_version != ctx.version:
            return CommandResult(
                EXIT_CONTRACT, err=["o contrato mudou depois da amostra; rode sintetica sample run"]
            )
        if state.status not in ("em_revisao", "interrompida"):
            return CommandResult(
                EXIT_NOT_APPROVABLE,
                err=[f"a amostra não pode ser aprovada no estado {state.status}"],
            )
        if not state.accepted:
            return CommandResult(EXIT_NOT_APPROVABLE, err=["a amostra não tem registros válidos"])
        state = _approve(ctx, state, out)
        _save(ctx, state)
        return CommandResult(EXIT_OK, out=out)
    except _Fail as fail:
        return CommandResult(fail.code, out=out, err=[str(fail)])


def show(project: Path, slug: str) -> CommandResult:
    try:
        ctx = _context(project, slug)
        state = load_sample_state(ctx.dataset)
        if state is None:
            return CommandResult(
                EXIT_NOT_APPROVABLE, err=["sem amostra; rode sintetica sample run"]
            )
        return CommandResult(EXIT_OK, out=_report(ctx, state, []))
    except _Fail as fail:
        return CommandResult(fail.code, err=[str(fail)])
