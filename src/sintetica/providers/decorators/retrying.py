"""Retry de falhas temporárias: 3 chamadas no total, esperas de 1 s e 2 s (RF-09, D-19)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence

from sintetica.providers.domain import CostEstimate, GenerationRequest, GenerationResult
from sintetica.providers.errors import ProviderExhausted, TransientProviderError
from sintetica.providers.ports import LLMProvider

MAX_ATTEMPTS = 3
DELAYS_S: tuple[float, ...] = (1.0, 2.0)


class RetryingProvider:
    def __init__(
        self,
        inner: LLMProvider,
        *,
        attempts: int = MAX_ATTEMPTS,
        delays_s: Sequence[float] = DELAYS_S,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._inner = inner
        self._attempts = attempts
        self._delays = tuple(delays_s)
        self._sleep = sleep

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def is_local(self) -> bool:
        return self._inner.is_local

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        last: TransientProviderError | None = None
        for attempt in range(self._attempts):
            try:
                return await self._inner.generate(request)
            except TransientProviderError as exc:
                last = exc
                if attempt < self._attempts - 1:
                    await self._sleep(self._delays[min(attempt, len(self._delays) - 1)])
        raise ProviderExhausted(
            f"{self.name}: {ProviderExhausted.reason} após {self._attempts} tentativas ({last})"
        )

    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate:
        return self._inner.estimate_cost(n_records, avg_tokens)
