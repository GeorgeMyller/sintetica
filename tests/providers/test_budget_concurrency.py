"""Concorrência limitada e teto de custo durante a geração (RF-08, RF-11, D-18, R-07)."""

from __future__ import annotations

import asyncio
from decimal import Decimal

import pytest
from support import make_request

from sintetica.providers.decorators.budget import BudgetedProvider
from sintetica.providers.decorators.concurrency import ConcurrencyLimitedProvider
from sintetica.providers.domain import (
    STOP_BUDGET,
    CostEstimate,
    GenerationRequest,
    GenerationResult,
)
from sintetica.providers.ports import LLMProvider


class FakeProvider:
    """Provedor em memória: custo fixo por pedido e medição de pedidos simultâneos."""

    def __init__(self, cost: str = "0.40", delay_s: float = 0.0, fail_first: bool = False) -> None:
        self.cost = Decimal(cost)
        self.delay_s = delay_s
        self.fail_first = fail_first
        self.calls = 0
        self.in_flight = 0
        self.max_in_flight = 0

    @property
    def name(self) -> str:
        return "fake"

    @property
    def is_local(self) -> bool:
        return False

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        self.calls += 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delay_s)
            if self.fail_first and self.calls == 1:
                raise RuntimeError("falha simulada")
            return GenerationResult(({"i": self.calls},), 10, 10, self.cost, self.name)
        finally:
            self.in_flight -= 1

    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate:
        return CostEstimate(self.name, "m", n_records, avg_tokens, Decimal("1"), False)


async def _gather(provider: LLMProvider, n: int) -> list[GenerationResult]:
    return list(await asyncio.gather(*(provider.generate(make_request()) for _ in range(n))))


def test_concurrency_never_exceeds_default_limit() -> None:
    inner = FakeProvider(cost="0", delay_s=0.001)
    asyncio.run(_gather(ConcurrencyLimitedProvider(inner), 100))
    assert inner.calls == 100
    assert inner.max_in_flight == 8


def test_concurrency_is_adjustable_and_validated() -> None:
    inner = FakeProvider(cost="0", delay_s=0.001)
    limited = ConcurrencyLimitedProvider(inner, 3)
    asyncio.run(_gather(limited, 20))
    assert inner.max_in_flight == 3
    assert (limited.name, limited.is_local) == ("fake", False)
    assert limited.estimate_cost(1, 1).usd == 1
    with pytest.raises(ValueError):
        ConcurrencyLimitedProvider(inner, 0)


def test_ceiling_reached_mid_batch() -> None:
    inner = FakeProvider(cost="0.40")
    budget = BudgetedProvider(inner, Decimal("1.00"))

    async def sequence() -> list[GenerationResult]:
        return [await budget.generate(make_request()) for _ in range(4)]

    results = asyncio.run(sequence())
    assert inner.calls == 2
    assert [len(r.records) for r in results[:2]] == [1, 1]
    assert results[2].stop_reason == STOP_BUDGET and results[2].records == ()
    assert results[3].stop_reason == STOP_BUDGET
    assert budget.stopped is True
    assert budget.spent_usd == Decimal("0.80")


def test_concurrent_requests_never_pass_authorized_value() -> None:
    inner = FakeProvider(cost="0.40", delay_s=0.001)
    budget = BudgetedProvider(ConcurrencyLimitedProvider(inner), Decimal("1.00"))
    results = asyncio.run(_gather(budget, 8))
    assert budget.spent_usd <= Decimal("1.00")
    assert sum(1 for r in results if r.stop_reason == STOP_BUDGET) == 8 - inner.calls


def test_per_request_estimate_is_used_before_first_result() -> None:
    inner = FakeProvider(cost="0.40", delay_s=0.001)
    budget = BudgetedProvider(inner, Decimal("1.00"), per_request_estimate=Decimal("0.60"))
    asyncio.run(_gather(budget, 8))
    # Com reserva de US$ 0,60 por pedido, só 1 pedido cabe antes do 1º resultado.
    assert inner.calls == 1


def test_failure_releases_reservation() -> None:
    inner = FakeProvider(cost="0.40", fail_first=True)
    budget = BudgetedProvider(inner, Decimal("1.00"), per_request_estimate=Decimal("0.40"))

    async def run() -> GenerationResult:
        with pytest.raises(RuntimeError):
            await budget.generate(make_request())
        return await budget.generate(make_request())

    assert asyncio.run(run()).stop_reason is None
    assert (budget.name, budget.is_local) == ("fake", False)
    assert budget.estimate_cost(1, 1).provider == "fake"
