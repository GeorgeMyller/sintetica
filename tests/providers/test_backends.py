"""Os 4 backends contra interfaces/*.md: requisição, leitura, tokens, custo e erros."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest
from support import FAKE_KEY, RECORDS, FakeServer, json_reply, make_request, ok_body

from sintetica.providers import CredentialError, MalformedResponse
from sintetica.providers.errors import ProviderError, TransientProviderError
from sintetica.providers.external.backends import BACKENDS
from sintetica.providers.external.provider import ExternalAPIProvider
from sintetica.providers.pricing import PriceTable
from sintetica.providers.prompt import parse_records

KEYS = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}


def _provider(tmp_path: Path, backend: str, server: FakeServer) -> ExternalAPIProvider:
    return ExternalAPIProvider(
        backend,
        prices=PriceTable.load(tmp_path),
        ceiling_usd=Decimal("5.00"),
        transport=server.transport,
    )


@pytest.fixture(autouse=True)
def all_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in KEYS.values():
        monkeypatch.setenv(var, FAKE_KEY)


def _run(
    tmp_path: Path, backend: str, server_factory: Callable[..., FakeServer], body: Any
) -> tuple[FakeServer, Any]:
    server = server_factory(json_reply(body))
    result = asyncio.run(_provider(tmp_path, backend, server).generate(make_request()))
    return server, result


@pytest.mark.parametrize("backend", ["openai", "anthropic", "gemini", "ollama"])
def test_backend_returns_common_result(
    tmp_path: Path, backend: str, server_factory: Callable[..., FakeServer]
) -> None:
    server, result = _run(tmp_path, backend, server_factory, ok_body(backend))
    assert result.records == tuple(RECORDS)
    assert (result.input_tokens, result.output_tokens) == (100, 400)
    assert result.provider == backend
    assert len(server.calls) == 1
    sent = json.loads(server.bodies()[0])
    assert "Gere exatamente 2 registros." in json.dumps(sent, ensure_ascii=False)


def test_openai_request_shape_and_cost(
    tmp_path: Path, server_factory: Callable[..., FakeServer]
) -> None:
    server, result = _run(tmp_path, "openai", server_factory, ok_body("openai"))
    call = server.calls[0]
    assert str(call.url) == "https://api.openai.com/v1/chat/completions"
    assert call.headers["Authorization"] == f"Bearer {FAKE_KEY}"
    body = json.loads(call.content)
    assert body["model"] == "gpt-4o-mini"
    assert body["response_format"] == {"type": "json_object"}
    assert result.cost_usd == 100 * Decimal("0.00000015") + 400 * Decimal("0.0000006")


def test_anthropic_request_shape(tmp_path: Path, server_factory: Callable[..., FakeServer]) -> None:
    server, _ = _run(tmp_path, "anthropic", server_factory, ok_body("anthropic"))
    call = server.calls[0]
    assert str(call.url) == "https://api.anthropic.com/v1/messages"
    assert call.headers["x-api-key"] == FAKE_KEY
    assert call.headers["anthropic-version"] == "2023-06-01"
    body = json.loads(call.content)
    assert body["model"] == "claude-haiku-5-5"
    assert body["max_tokens"] == 8192
    assert body["messages"][0]["role"] == "user"


def test_gemini_key_goes_in_header_not_url(
    tmp_path: Path, server_factory: Callable[..., FakeServer]
) -> None:
    server, _ = _run(tmp_path, "gemini", server_factory, ok_body("gemini"))
    call = server.calls[0]
    assert str(call.url) == (
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    )
    assert FAKE_KEY not in str(call.url)
    assert call.headers["x-goog-api-key"] == FAKE_KEY
    assert json.loads(call.content)["generationConfig"]["responseMimeType"] == "application/json"


def test_ollama_uses_host_without_auth_and_costs_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, server_factory: Callable[..., FakeServer]
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "meuhost:11434/")
    server, result = _run(tmp_path, "ollama", server_factory, ok_body("ollama"))
    call = server.calls[0]
    assert str(call.url) == "http://meuhost:11434/api/chat"
    assert "authorization" not in call.headers
    body = json.loads(call.content)
    assert (body["model"], body["stream"], body["format"]) == ("llama3.2", False, "json")
    assert result.cost_usd == 0


def test_model_env_override_is_sent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, server_factory: Callable[..., FakeServer]
) -> None:
    monkeypatch.setenv("SINTETICA_OPENAI_MODEL", "x")
    server, result = _run(tmp_path, "openai", server_factory, ok_body("openai"))
    assert json.loads(server.calls[0].content)["model"] == "x"
    assert result.cost_usd == 0  # modelo sem preço: custo real registrado como 0


def test_anthropic_truncated_response_is_malformed(
    tmp_path: Path, server_factory: Callable[..., FakeServer]
) -> None:
    body = ok_body("anthropic") | {"stop_reason": "max_tokens"}
    with pytest.raises(MalformedResponse, match="max_tokens"):
        _run(tmp_path, "anthropic", server_factory, body)


@pytest.mark.parametrize("backend", ["openai", "anthropic", "gemini", "ollama"])
def test_unexpected_payload_is_malformed(
    tmp_path: Path, backend: str, server_factory: Callable[..., FakeServer]
) -> None:
    with pytest.raises(MalformedResponse):
        _run(tmp_path, backend, server_factory, {"inesperado": True})


@pytest.mark.parametrize(
    "body",
    [
        {"choices": [{"message": {"content": None}}]},
        {"choices": [{"message": {"content": '{"records": [1, 2]}'}}]},
        {"choices": [{"message": {"content": '{"outra": []}'}}]},
    ],
)
def test_openai_bad_content_is_malformed(
    tmp_path: Path, server_factory: Callable[..., FakeServer], body: dict[str, Any]
) -> None:
    with pytest.raises(MalformedResponse):
        _run(tmp_path, "openai", server_factory, body)


def test_ollama_non_text_content_is_malformed(
    tmp_path: Path, server_factory: Callable[..., FakeServer]
) -> None:
    with pytest.raises(MalformedResponse):
        _run(tmp_path, "ollama", server_factory, {"message": {"content": 5}})


@pytest.mark.parametrize("backend", ["openai", "anthropic", "gemini"])
def test_model_not_found_points_to_env_var(
    tmp_path: Path, backend: str, server_factory: Callable[..., FakeServer]
) -> None:
    server = server_factory(httpx.Response(404))
    with pytest.raises(ProviderError, match=f"SINTETICA_{backend.upper()}_MODEL") as info:
        asyncio.run(_provider(tmp_path, backend, server).generate(make_request()))
    assert not isinstance(info.value, TransientProviderError)


def test_ollama_model_not_found_suggests_pull(
    tmp_path: Path, server_factory: Callable[..., FakeServer]
) -> None:
    server = server_factory(httpx.Response(404))
    with pytest.raises(ProviderError, match=r"ollama pull llama3\.2"):
        asyncio.run(_provider(tmp_path, "ollama", server).generate(make_request()))


def test_gemini_400_with_invalid_key_is_credential_error(
    tmp_path: Path, server_factory: Callable[..., FakeServer]
) -> None:
    server = server_factory(httpx.Response(400, text="API key not valid. Please pass a valid key."))
    with pytest.raises(CredentialError, match="GEMINI_API_KEY"):
        asyncio.run(_provider(tmp_path, "gemini", server).generate(make_request()))


def test_ollama_server_errors_are_temporary(
    tmp_path: Path, server_factory: Callable[..., FakeServer]
) -> None:
    server = server_factory(httpx.Response(500))
    with pytest.raises(TransientProviderError):
        asyncio.run(_provider(tmp_path, "ollama", server).generate(make_request()))


def test_backend_registry_and_identity(tmp_path: Path) -> None:
    assert set(BACKENDS) == {"openai", "anthropic", "gemini", "ollama"}
    server = FakeServer([httpx.Response(200)])
    provider = _provider(tmp_path, "gemini", server)
    assert (provider.name, provider.model, provider.is_local) == (
        "gemini",
        "gemini-1.5-flash",
        False,
    )


def test_parse_records_rejects_non_json() -> None:
    with pytest.raises(MalformedResponse):
        parse_records("não é json")
    assert parse_records('{"records": []}') == ()
