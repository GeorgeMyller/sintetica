"""Limite de pedidos simultâneos por provedor, 8 por padrão (RF-11)."""

from __future__ import annotations

import asyncio

from sintetica.providers.domain import CostEstimate, GenerationRequest, GenerationResult
from sintetica.providers.ports import LLMProvider

DEFAULT_CONCURRENCY = 8


class ConcurrencyLimitedProvider:
    def __init__(self, inner: LLMProvider, limit: int = DEFAULT_CONCURRENCY) -> None:
        if limit < 1:
            raise ValueError("a concorrência deve ser maior ou igual a 1")
        self._inner = inner
        self._semaphore = asyncio.Semaphore(limit)

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def is_local(self) -> bool:
        return self._inner.is_local

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        async with self._semaphore:
            return await self._inner.generate(request)

    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate:
        return self._inner.estimate_cost(n_records, avg_tokens)
