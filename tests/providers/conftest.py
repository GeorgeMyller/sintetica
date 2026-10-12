"""Fixtures do llm-provider: ambiente limpo, servidor simulado, sleep falso e projeto."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from support import ENV_VARS, FakeServer, FakeSleep, Reply


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    yield


@pytest.fixture
def server_factory() -> Callable[..., FakeServer]:
    def make(*replies: Reply) -> FakeServer:
        return FakeServer(list(replies))

    return make


@pytest.fixture
def fake_sleep() -> FakeSleep:
    return FakeSleep()


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Projeto com `datasets/demo/` criado, como faz o intent-interview."""
    (tmp_path / "datasets" / "demo").mkdir(parents=True)
    return tmp_path
