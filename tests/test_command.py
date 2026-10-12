"""Prefixo dos comandos citados nas mensagens (feature 008, RF-16, D-13)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sintetica.batch.service import status_lines
from sintetica.batch.state import RunState
from sintetica.command import cli_command
from sintetica.providers.harness.provider import HarnessAgentProvider


def _stopped_lot() -> RunState:
    return RunState(
        slug="pedidos",
        status="em_andamento",
        volume_requested=10,
        format="json",
        block_size=10,
        avg_tokens=10,
        provider="ollama",
        provider_reason="teste",
        schema_version="v",
    )


def test_default_is_uv_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SINTETICA_CMD", raising=False)
    assert cli_command() == "uv run sintetica"
    monkeypatch.setenv("SINTETICA_CMD", "   ")
    assert cli_command() == "uv run sintetica"


def test_messages_follow_the_launcher(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SINTETICA_CMD", raising=False)
    lines = status_lines(tmp_path, _stopped_lot(), alive=False)
    assert "Para retomar: uv run sintetica generate pedidos --resume" in lines
    monkeypatch.setenv("SINTETICA_CMD", ".sintetica/bin/sintetica")
    lines = status_lines(tmp_path, _stopped_lot(), alive=False)
    assert "Para retomar: .sintetica/bin/sintetica generate pedidos --resume" in lines
    submit = HarnessAgentProvider(tmp_path / "pedidos").submit_command("abc")
    assert submit == ".sintetica/bin/sintetica submit pedidos abc"
