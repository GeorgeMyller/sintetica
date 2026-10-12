"""Custo, preços, modelos e política (RN-05, RN-08, RF-06, RF-07, D-16, D-17, D-23)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from support import write_json

from sintetica.providers.domain import ModelPrice
from sintetica.providers.errors import ProviderPolicyError
from sintetica.providers.external.provider import ExternalAPIProvider
from sintetica.providers.harness.provider import HarnessAgentProvider
from sintetica.providers.models import model_env_var, resolve_model
from sintetica.providers.policy import DEFAULT_PRIORITY, ProviderPolicy, load_provider_policy
from sintetica.providers.pricing import PriceTable

CENT_THOUSANDTH = Decimal("0.00001")


def _provider(
    prices: PriceTable, model: str = "m", ceiling: str = "5.00", backend: str = "openai"
) -> ExternalAPIProvider:
    return ExternalAPIProvider(backend, prices=prices, ceiling_usd=Decimal(ceiling), model=model)


def _table() -> PriceTable:
    return PriceTable({"m": ModelPrice(CENT_THOUSANDTH, CENT_THOUSANDTH)})


def test_estimate_exactly_at_ceiling_needs_no_authorization() -> None:
    estimate = _provider(_table()).estimate_cost(1000, 500)
    assert estimate.usd == Decimal("5.00")
    assert estimate.requires_authorization is False
    assert estimate.price_known is True
    assert estimate.model == "m"


def test_estimate_above_ceiling_needs_authorization() -> None:
    estimate = _provider(_table()).estimate_cost(1002, 500)
    assert estimate.usd == Decimal("5.01")
    assert estimate.requires_authorization is True


def test_model_without_price_needs_authorization() -> None:
    estimate = _provider(_table(), model="sem-preco").estimate_cost(1, 1)
    assert estimate.requires_authorization is True
    assert estimate.price_known is False


def test_estimate_uses_output_price() -> None:
    table = PriceTable({"m": ModelPrice(Decimal("0.000001"), Decimal("0.00001"))})
    assert table.estimate("m", 1000, 500) == Decimal("5.00")
    assert table.real_cost("m", 100, 400) == Decimal("0.0001") + Decimal("0.004")
    assert table.estimate("x", 1, 1) is None
    assert table.real_cost("x", 1, 1) is None


def test_local_providers_cost_zero(project: Path) -> None:
    ollama = _provider(_table(), backend="ollama")
    assert ollama.estimate_cost(10_000, 500).usd == 0
    assert ollama.estimate_cost(10_000, 500).requires_authorization is False
    harness = HarnessAgentProvider(project / "datasets" / "demo").estimate_cost(50, 500)
    assert harness.usd == 0 and harness.requires_authorization is False and harness.model is None


def test_embedded_defaults_have_q32_q34_models_and_prices(tmp_path: Path) -> None:
    table = PriceTable.load(tmp_path)
    assert resolve_model("openai") == "gpt-4o-mini"
    assert resolve_model("anthropic") == "claude-haiku-5-5"
    assert resolve_model("gemini") == "gemini-1.5-flash"
    assert resolve_model("ollama") == "llama3.2"
    assert table.price("gpt-4o-mini") == ModelPrice(Decimal("0.00000015"), Decimal("0.0000006"))
    assert table.price("claude-haiku-5-5") == ModelPrice(Decimal("0.0000008"), Decimal("0.000004"))
    assert table.price("gemini-1.5-flash") == ModelPrice(
        Decimal("0.000000075"), Decimal("0.0000003")
    )


def test_project_price_overrides_embedded_price(tmp_path: Path) -> None:
    write_json(
        tmp_path / ".sintetica" / "pricing.json",
        {"gpt-4o-mini": {"input_usd_per_token": "0.00001", "output_usd_per_token": "0.00002"}},
    )
    provider = _provider(PriceTable.load(tmp_path), model="gpt-4o-mini")
    assert provider.estimate_cost(100, 500).usd == Decimal("1.00")


@pytest.mark.parametrize(
    "content",
    ["{nao json", '["lista"]', '{"m": 1}', '{"m": {"input_usd_per_token": "x"}}'],
)
def test_invalid_pricing_file(tmp_path: Path, content: str) -> None:
    path = tmp_path / ".sintetica" / "pricing.json"
    path.parent.mkdir()
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ProviderPolicyError):
        PriceTable.load(tmp_path)


def test_model_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SINTETICA_OPENAI_MODEL", "x")
    assert model_env_var("openai") == "SINTETICA_OPENAI_MODEL"
    assert resolve_model("openai") == "x"
    with pytest.raises(KeyError):
        resolve_model("desconhecido")


def test_policy_absent_uses_defaults(tmp_path: Path) -> None:
    policy = load_provider_policy(tmp_path / "policy.json")
    assert policy == ProviderPolicy()
    assert policy.pii_premask is True
    assert policy.cost_ceiling_usd == Decimal("5.00")
    assert policy.provider_priority == DEFAULT_PRIORITY == ("harness", "ollama", "external")


def test_policy_reads_values(tmp_path: Path) -> None:
    path = tmp_path / "policy.json"
    write_json(
        path,
        {
            "pii_premask": False,
            "cost_ceiling_usd": 2.5,
            "provider_priority": ["external"],
            "telemetry": False,
        },
    )
    assert load_provider_policy(path) == ProviderPolicy(False, Decimal("2.5"), ("external",))


@pytest.mark.parametrize(
    "content",
    [
        "{nao json",
        "[]",
        '{"pii_premask": "sim"}',
        '{"cost_ceiling_usd": true}',
        '{"cost_ceiling_usd": [1]}',
        '{"cost_ceiling_usd": "abc"}',
        '{"cost_ceiling_usd": -1}',
        '{"provider_priority": []}',
        '{"provider_priority": "harness"}',
        '{"provider_priority": ["openai"]}',
    ],
)
def test_policy_invalid(tmp_path: Path, content: str) -> None:
    path = tmp_path / "policy.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ProviderPolicyError):
        load_provider_policy(path)
