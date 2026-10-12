"""Mascaramento antes do envio externo, inclusive Ollama (RN-03, RN-04, RF-05, D-05 a D-07)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from support import FAKE_KEY, FakeServer, json_reply, make_request, ok_body, write_json

from sintetica.pii import PiiGuard
from sintetica.pii.allowlist import ALLOWLIST_FILENAME
from sintetica.providers import MaskingUnavailable, build_provider
from sintetica.providers.decorators.masking import MaskingProvider, mask_request
from sintetica.providers.external.provider import ExternalAPIProvider
from sintetica.providers.pricing import PriceTable

EMAIL = "ana@empresa.com"


def _masked_external(project: Path, server: FakeServer, backend: str = "openai") -> MaskingProvider:
    dataset = project / "datasets" / "demo"
    policy = project / ".sintetica" / "policy.json"
    inner = ExternalAPIProvider(
        backend,
        prices=PriceTable.load(project),
        ceiling_usd=Decimal("5.00"),
        transport=server.transport,
    )
    return MaskingProvider(inner, lambda: PiiGuard.for_dataset(dataset, policy, seed=3))


@pytest.mark.parametrize("backend", ["openai", "ollama"])
def test_email_never_reaches_the_server(
    backend: str,
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    server_factory: Callable[..., FakeServer],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    server = server_factory(json_reply(ok_body(backend)))
    provider = _masked_external(project, server, backend)

    asyncio.run(provider.generate(make_request(instructions=f"clientes como {EMAIL}")))

    assert len(server.calls) == 1
    assert EMAIL not in server.bodies()[0]
    allowlist = project / "datasets" / "demo" / ALLOWLIST_FILENAME
    assert allowlist.exists() and EMAIL not in allowlist.read_text("utf-8")


def test_whole_request_is_masked(project: Path) -> None:
    guard = PiiGuard.for_dataset(project / "datasets" / "demo", project / "policy.json", seed=1)
    request = make_request(
        instructions="sem PII",
        seeds=[{"contato": {"emails": [EMAIL]}, "idade": 30}],
        schema={
            "type": "object",
            "description": f"cliente, ex.: {EMAIL}",
            "properties": {
                "email": {"type": "string", "examples": [EMAIL], "enum": [EMAIL]},
                "idade": {"type": "integer", "default": 30},
            },
        },
    )
    masked = mask_request(guard, request)
    dumped = json.dumps([masked.schema_json, list(masked.seeds)])
    assert EMAIL not in dumped
    assert masked.seeds[0]["idade"] == 30
    assert masked.schema_json["type"] == "object"
    assert masked.instructions == "sem PII"
    assert masked.n_records == request.n_records


def test_invalid_pii_policy_blocks_sending(
    project: Path, monkeypatch: pytest.MonkeyPatch, server_factory: Callable[..., FakeServer]
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    write_json(project / ".sintetica" / "policy.json", {"pii_custom_patterns": ["("]})
    server = server_factory(json_reply(ok_body("openai")))
    provider = _masked_external(project, server)

    with pytest.raises(MaskingUnavailable, match="mascaramento indisponível"):
        asyncio.run(provider.generate(make_request(instructions=EMAIL)))
    assert server.calls == []


def test_allowlist_write_failure_blocks_sending(
    project: Path, monkeypatch: pytest.MonkeyPatch, server_factory: Callable[..., FakeServer]
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    blocked = project / "datasets" / "demo" / ALLOWLIST_FILENAME
    blocked.mkdir()  # um diretório no lugar do arquivo impede a gravação
    server = server_factory(json_reply(ok_body("openai")))
    provider = _masked_external(project, server)

    with pytest.raises(MaskingUnavailable, match="allowlist"):
        asyncio.run(provider.generate(make_request(instructions=EMAIL)))
    assert server.calls == []


def test_factory_masks_ollama_but_not_harness(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = project / "datasets" / "demo"
    up = httpx.MockTransport(lambda r: httpx.Response(200, json=ok_body("ollama")))
    provider, choice = build_provider(
        10, dataset_dir=dataset, project_dir=project, probe_transport=up, transport=up
    )
    assert choice.provider == "ollama"
    sent: list[bytes] = []

    def capture(request: httpx.Request) -> httpx.Response:
        sent.append(request.content)
        return httpx.Response(200, json=ok_body("ollama"))

    provider, _ = build_provider(
        10,
        dataset_dir=dataset,
        project_dir=project,
        probe_transport=up,
        transport=httpx.MockTransport(capture),
    )
    asyncio.run(provider.generate(make_request(instructions=EMAIL)))
    assert EMAIL.encode() not in sent[0]

    harness, choice = build_provider(
        10, dataset_dir=dataset, project_dir=project, harness_available=True, probe_transport=up
    )
    assert choice.provider == "harness"
    with pytest.raises(Exception, match="aguardando resposta"):
        asyncio.run(harness.generate(make_request(instructions=EMAIL)))
    request_file = next((dataset / "requests").glob("*.json"))
    assert EMAIL in request_file.read_text("utf-8")  # harness não é externo (D-05)


def test_premask_off_sends_original(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    write_json(project / ".sintetica" / "policy.json", {"pii_premask": False})
    sent: list[bytes] = []

    def capture(request: httpx.Request) -> httpx.Response:
        sent.append(request.content)
        return httpx.Response(200, json=ok_body("openai"))

    provider, _ = build_provider(
        1000,
        dataset_dir=project / "datasets" / "demo",
        project_dir=project,
        probe_transport=httpx.MockTransport(lambda r: httpx.Response(503)),
        transport=httpx.MockTransport(capture),
    )
    asyncio.run(provider.generate(make_request(instructions=EMAIL)))
    assert EMAIL.encode() in sent[0]
