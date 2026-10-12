"""Teto de custo durante a geração (RF-08, D-18).

Antes de cada pedido, reserva o custo previsto sob `asyncio.Lock`. Se acumulado + reservado +
previsto passar do valor autorizado, o pedido não sai e o resultado vem vazio com o motivo
`teto de custo`. Sem estimativa por pedido, o 1º pedido sai sozinho para medir o custo real.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sintetica.providers.domain import (
    STOP_BUDGET,
    CostEstimate,
    GenerationRequest,
    GenerationResult,
)
from sintetica.providers.ports import LLMProvider
from sintetica.providers.pricing import ZERO


class BudgetedProvider:
    def __init__(
        self,
        inner: LLMProvider,
        authorized_usd: Decimal,
        per_request_estimate: Decimal | None = None,
    ) -> None:
        self._inner = inner
        self._authorized = authorized_usd
        self._estimate = per_request_estimate
        self._lock = asyncio.Lock()
        self._probe = asyncio.Lock()
        self._spent = ZERO
        self._reserved = ZERO
        self._observed = 0
        self._stopped = False

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def is_local(self) -> bool:
        return self._inner.is_local

    @property
    def spent_usd(self) -> Decimal:
        return self._spent

    @property
    def stopped(self) -> bool:
        return self._stopped

    def _forecast(self) -> Decimal:
        if self._observed:
            return self._spent / self._observed
        return self._estimate if self._estimate is not None else ZERO

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        if self._observed == 0 and self._estimate is None:
            async with self._probe:
                if self._observed == 0:
                    return await self._send(request)
        return await self._send(request)

    async def _send(self, request: GenerationRequest) -> GenerationResult:
        async with self._lock:
            forecast = self._forecast()
            if self._stopped or self._spent + self._reserved + forecast > self._authorized:
                self._stopped = True
                return GenerationResult((), 0, 0, ZERO, self.name, STOP_BUDGET)
            self._reserved += forecast
        try:
            result = await self._inner.generate(request)
        finally:
            async with self._lock:
                self._reserved -= forecast
        async with self._lock:
            self._spent += result.cost_usd
            self._observed += 1
        return result

    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate:
        return self._inner.estimate_cost(n_records, avg_tokens)
