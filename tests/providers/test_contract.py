"""Suíte de contrato da porta `LLMProvider`, aplicada aos 2 adaptadores (RF-01, RF-13)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest
from support import FAKE_KEY, FakeServer, json_reply, make_request, ok_body

from sintetica.providers import CostEstimate, GenerationResult, LLMProvider
from sintetica.providers.external.provider import ExternalAPIProvider
from sintetica.providers.harness.provider import HarnessAgentProvider
from sintetica.providers.harness.store import RequestStore
from sintetica.providers.pricing import PriceTable

Builder = Callable[[Path, pytest.MonkeyPatch, Callable[..., FakeServer]], LLMProvider]


def _external(
    project: Path, mp: pytest.MonkeyPatch, servers: Callable[..., FakeServer]
) -> LLMProvider:
    mp.setenv("OPENAI_API_KEY", FAKE_KEY)
    server = servers(json_reply(ok_body("openai")))
    return ExternalAPIProvider(
        "openai",
        prices=PriceTable.load(project),
        ceiling_usd=Decimal("5.00"),
        transport=server.transport,
    )


def _harness(
    project: Path, mp: pytest.MonkeyPatch, servers: Callable[..., FakeServer]
) -> LLMProvider:
    dataset = project / "datasets" / "demo"
    store = RequestStore(dataset)
    rid = store.save_request(make_request())
    store.submit(rid, b'{"nome": "Ana"}\n{"nome": "Bruno"}\n')
    return HarnessAgentProvider(dataset)


@pytest.mark.parametrize("build", [_external, _harness], ids=["external", "harness"])
def test_port_contract(
    build: Builder,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    server_factory: Callable[..., FakeServer],
) -> None:
    provider = build(project, monkeypatch, server_factory)

    assert isinstance(provider.name, str) and provider.name
    assert isinstance(provider.is_local, bool)

    result = asyncio.run(provider.generate(make_request()))
    assert isinstance(result, GenerationResult)
    assert result.records == ({"nome": "Ana"}, {"nome": "Bruno"})
    assert result.input_tokens > 0
    assert result.output_tokens > 0
    assert isinstance(result.cost_usd, Decimal)
    assert result.provider == provider.name
    assert result.stop_reason is None

    estimate = provider.estimate_cost(10, 50)
    assert isinstance(estimate, CostEstimate)
    assert estimate.provider == provider.name
    assert (estimate.n_records, estimate.avg_tokens) == (10, 50)
