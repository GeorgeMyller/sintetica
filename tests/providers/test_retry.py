"""Retry, falha rápida de credencial e sigilo da chave (RF-09, RF-10, RN-07, D-19, D-20)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from support import FAKE_KEY, FakeServer, FakeSleep, json_reply, make_request, ok_body

from sintetica.providers import CredentialError, MalformedResponse, ProviderExhausted
from sintetica.providers.decorators.retrying import RetryingProvider
from sintetica.providers.errors import ProviderError, TransientProviderError
from sintetica.providers.external.provider import ExternalAPIProvider
from sintetica.providers.pricing import PriceTable


def _provider(
    tmp_path: Path, server: FakeServer, sleep: FakeSleep, backend: str = "openai"
) -> RetryingProvider:
    inner = ExternalAPIProvider(
        backend,
        prices=PriceTable.load(tmp_path),
        ceiling_usd=Decimal("5.00"),
        transport=server.transport,
    )
    return RetryingProvider(inner, sleep=sleep)


@pytest.fixture(autouse=True)
def openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)


def test_retry_on_temporary_error(
    tmp_path: Path, server_factory: Callable[..., FakeServer], fake_sleep: FakeSleep
) -> None:
    server = server_factory(httpx.Response(503), httpx.Response(503), json_reply(ok_body("openai")))
    result = asyncio.run(_provider(tmp_path, server, fake_sleep).generate(make_request()))
    assert len(server.calls) == 3
    assert fake_sleep.delays == [1.0, 2.0]
    assert len(result.records) == 2


def test_exhausted_attempts(
    tmp_path: Path, server_factory: Callable[..., FakeServer], fake_sleep: FakeSleep
) -> None:
    server = server_factory(httpx.Response(429))
    with pytest.raises(ProviderExhausted, match="falha do provedor"):
        asyncio.run(_provider(tmp_path, server, fake_sleep).generate(make_request()))
    assert len(server.calls) == 3
    assert fake_sleep.delays == [1.0, 2.0]


def test_invalid_key_is_not_retried(
    tmp_path: Path, server_factory: Callable[..., FakeServer], fake_sleep: FakeSleep
) -> None:
    server = server_factory(httpx.Response(401))
    with pytest.raises(CredentialError) as info:
        asyncio.run(_provider(tmp_path, server, fake_sleep).generate(make_request()))
    assert len(server.calls) == 1
    assert "OPENAI_API_KEY" in str(info.value)
    assert FAKE_KEY not in str(info.value)
    assert FAKE_KEY not in repr(info.value)
    assert info.value.env_var == "OPENAI_API_KEY"


def test_forbidden_is_not_retried(
    tmp_path: Path, server_factory: Callable[..., FakeServer], fake_sleep: FakeSleep
) -> None:
    server = server_factory(httpx.Response(403))
    with pytest.raises(CredentialError):
        asyncio.run(_provider(tmp_path, server, fake_sleep).generate(make_request()))
    assert len(server.calls) == 1


def test_malformed_then_valid(
    tmp_path: Path, server_factory: Callable[..., FakeServer], fake_sleep: FakeSleep
) -> None:
    server = server_factory(
        json_reply(ok_body("openai", text="isto não é JSON")), json_reply(ok_body("openai"))
    )
    result = asyncio.run(_provider(tmp_path, server, fake_sleep).generate(make_request()))
    assert len(server.calls) == 2
    assert len(result.records) == 2


@pytest.mark.parametrize(
    "error",
    [httpx.ReadTimeout("lento"), httpx.ConnectError("recusada")],
    ids=["timeout", "conexao"],
)
def test_transport_failures_are_retried_without_leaking_key(
    tmp_path: Path,
    server_factory: Callable[..., FakeServer],
    fake_sleep: FakeSleep,
    error: Exception,
) -> None:
    server = server_factory(error)
    with pytest.raises(ProviderExhausted) as info:
        asyncio.run(_provider(tmp_path, server, fake_sleep).generate(make_request()))
    assert len(server.calls) == 3
    assert FAKE_KEY not in str(info.value)
    assert info.value.__cause__ is None


def test_non_json_body_is_malformed(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda r: httpx.Response(200, content=b"<html>"))
    provider = ExternalAPIProvider(
        "openai",
        prices=PriceTable.load(tmp_path),
        ceiling_usd=Decimal("5"),
        transport=transport,
    )
    with pytest.raises(MalformedResponse):
        asyncio.run(provider.generate(make_request()))


def test_missing_key_fails_before_any_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    server_factory: Callable[..., FakeServer],
    fake_sleep: FakeSleep,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY")
    server = server_factory(json_reply(ok_body("openai")))
    with pytest.raises(CredentialError, match="OPENAI_API_KEY"):
        asyncio.run(_provider(tmp_path, server, fake_sleep).generate(make_request()))
    assert server.calls == []


def test_definitive_error_is_not_retried(
    tmp_path: Path, server_factory: Callable[..., FakeServer], fake_sleep: FakeSleep
) -> None:
    server = server_factory(httpx.Response(400, text="bad request"))
    with pytest.raises(ProviderError) as info:
        asyncio.run(_provider(tmp_path, server, fake_sleep).generate(make_request()))
    assert not isinstance(info.value, TransientProviderError)
    assert len(server.calls) == 1
    assert fake_sleep.delays == []


def test_retry_delegates_identity_and_estimate(
    tmp_path: Path, server_factory: Callable[..., FakeServer], fake_sleep: FakeSleep
) -> None:
    provider = _provider(tmp_path, server_factory(httpx.Response(200)), fake_sleep)
    assert provider.name == "openai" and provider.is_local is False
    assert provider.estimate_cost(10, 10).provider == "openai"
