"""Seleção do provedor e montagem pela fábrica (RN-01, RF-03, RF-12, D-08 a D-10)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from support import FAKE_KEY, write_json

from sintetica.providers import ProviderUnavailable, build_provider
from sintetica.providers.selection import (
    Availability,
    external_backend_from_env,
    probe_availability,
    probe_ollama,
    select_provider,
)

PRIORITY = ("harness", "ollama", "external")
HOST = "http://localhost:11434"


def _avail(
    harness: bool = False, ollama: bool = False, external: str | None = None
) -> tuple[Availability, list[int]]:
    probes: list[int] = []

    def probe() -> bool:
        probes.append(1)
        return ollama

    return Availability(harness, external, probe, HOST), probes


def test_test_batch_uses_harness_without_probing_ollama() -> None:
    availability, probes = _avail(harness=True, external="openai")
    choice = select_provider(PRIORITY, 50, availability)
    assert (choice.provider, choice.backend) == ("harness", None)
    assert probes == []


def test_large_batch_skips_harness_and_offline_ollama() -> None:
    availability, probes = _avail(harness=True, external="openai")
    choice = select_provider(PRIORITY, 1000, availability)
    assert (choice.provider, choice.backend) == ("external", "openai")
    assert "harness pulado: 1000 > 100 registros" in choice.reason
    assert f"ollama indisponível em {HOST}" in choice.reason
    assert len(choice.skipped) == 2
    assert probes == [1]


def test_101_records_skip_harness() -> None:
    availability, _ = _avail(harness=True, external="openai")
    assert select_provider(PRIORITY, 101, availability).provider == "external"


def test_ollama_chosen_when_online() -> None:
    availability, _ = _avail(ollama=True)
    choice = select_provider(PRIORITY, 1000, availability)
    assert (choice.provider, choice.backend) == ("ollama", "ollama")
    assert "harness indisponível" in choice.reason


def test_no_provider_lists_what_was_checked() -> None:
    availability, _ = _avail()
    with pytest.raises(ProviderUnavailable) as info:
        select_provider(PRIORITY, 1000, availability)
    message = str(info.value)
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OLLAMA_HOST"):
        assert name in message


def test_external_backend_order_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    assert external_backend_from_env() is None
    monkeypatch.setenv("GEMINI_API_KEY", FAKE_KEY)
    assert external_backend_from_env() == "gemini"
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    assert external_backend_from_env() == "openai"
    monkeypatch.setenv("SINTETICA_EXTERNAL_BACKEND", "gemini")
    assert external_backend_from_env() == "gemini"
    monkeypatch.setenv("SINTETICA_EXTERNAL_BACKEND", "anthropic")
    assert external_backend_from_env() is None  # forçado, mas sem ANTHROPIC_API_KEY


def test_probe_ollama() -> None:
    up = httpx.MockTransport(lambda r: httpx.Response(200, json={"models": []}))
    down = httpx.MockTransport(lambda r: httpx.Response(500))

    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("recusada", request=request)

    assert probe_ollama(HOST, up) is True
    assert probe_ollama(HOST, down) is False
    assert probe_ollama(HOST, httpx.MockTransport(refuse)) is False


def test_probe_availability_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "outra-maquina:11434")
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200)

    availability = probe_availability(True, httpx.MockTransport(handler))
    assert availability.harness is True
    assert availability.external_backend == "anthropic"
    assert availability.ollama_host == "http://outra-maquina:11434"
    assert availability.ollama() is True
    assert seen == ["http://outra-maquina:11434/api/tags"]


def _offline() -> httpx.MockTransport:
    return httpx.MockTransport(lambda r: httpx.Response(503))


def test_factory_builds_harness(project: Path) -> None:
    provider, choice = build_provider(
        50,
        dataset_dir=project / "datasets" / "demo",
        project_dir=project,
        harness_available=True,
        probe_transport=_offline(),
    )
    assert choice.provider == "harness"
    assert provider.name == "harness" and provider.is_local is True


def test_factory_builds_external(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    provider, choice = build_provider(
        1000,
        dataset_dir=project / "datasets" / "demo",
        project_dir=project,
        harness_available=True,
        probe_transport=_offline(),
    )
    assert (choice.provider, choice.backend) == ("external", "openai")
    assert provider.name == "openai" and provider.is_local is False
    assert provider.estimate_cost(1000, 500).model == "gpt-4o-mini"


def test_factory_respects_policy_priority(project: Path) -> None:
    write_json(project / ".sintetica" / "policy.json", {"provider_priority": ["ollama"]})
    up = httpx.MockTransport(lambda r: httpx.Response(200))
    provider, choice = build_provider(
        10,
        dataset_dir=project / "datasets" / "demo",
        project_dir=project,
        harness_available=True,
        probe_transport=up,
    )
    assert choice.provider == "ollama"
    assert provider.is_local is True


def test_factory_without_any_provider(project: Path) -> None:
    with pytest.raises(ProviderUnavailable):
        build_provider(
            1000,
            dataset_dir=project / "datasets" / "demo",
            project_dir=project,
            probe_transport=_offline(),
        )
