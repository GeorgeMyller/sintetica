"""`HarnessAgentProvider`: o agente do harness gera; o runtime lê a resposta enviada (D-13)."""

from __future__ import annotations

import math
from pathlib import Path

from sintetica.command import cli_command
from sintetica.providers.domain import HARNESS, CostEstimate, GenerationRequest, GenerationResult
from sintetica.providers.errors import HarnessLimitExceeded, HarnessResponsePending
from sintetica.providers.harness.store import MAX_HARNESS_RECORDS, RequestStore
from sintetica.providers.pricing import ZERO
from sintetica.providers.prompt import build_user_prompt


def estimate_tokens(text: str) -> int:
    """Heurística de 4 caracteres por token (D-15)."""
    return math.ceil(len(text) / 4)


class HarnessAgentProvider:
    def __init__(self, dataset_dir: Path) -> None:
        self._store = RequestStore(dataset_dir)
        self._slug = dataset_dir.name

    @property
    def name(self) -> str:
        return HARNESS

    @property
    def is_local(self) -> bool:
        return True

    def submit_command(self, rid: str) -> str:
        return f"{cli_command()} submit {self._slug} {rid}"

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if request.n_records > MAX_HARNESS_RECORDS:
            raise HarnessLimitExceeded(request.n_records, MAX_HARNESS_RECORDS)
        rid = self._store.save_request(request)
        response = self._store.load_response(rid)
        if response is None:
            raise HarnessResponsePending(rid, self.submit_command(rid))
        text, records = response
        return GenerationResult(
            records,
            estimate_tokens(build_user_prompt(request)),
            estimate_tokens(text),
            ZERO,
            HARNESS,
        )

    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate:
        return CostEstimate(HARNESS, None, n_records, avg_tokens, ZERO, False)
