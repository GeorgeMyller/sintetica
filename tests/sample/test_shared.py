"""Mudanças da feature 006 na amostra: funções públicas, `intent_lines` e próximo passo."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from sintetica.cli import main
from sintetica.intent import load_intent_model
from sintetica.sample.request import build_instructions, intent_lines
from sintetica.sample.review import first_error, mask_value

from .conftest import cli, dataset, pending_id, prepare


class _M(BaseModel):
    valor: int


def test_first_error_hides_the_value() -> None:
    with pytest.raises(ValidationError) as exc:
        _M.model_validate({"valor": "segredo"})
    message = first_error(exc.value)
    assert message.startswith("valor:") and "segredo" not in message


def test_mask_value_passes_the_field_path() -> None:
    seen: list[str] = []

    def masker(text: str, path: str) -> str:
        seen.append(path)
        return text.upper()

    value = {"nome": "ana", "end": {"cidade": "rio"}, "tags": ["a"], "n": 1}
    assert mask_value(value, "", masker) == {
        "nome": "ANA",
        "end": {"cidade": "RIO"},
        "tags": ["A"],
        "n": 1,
    }
    assert seen == ["nome", "end.cidade", "tags[]"]


def test_intent_lines_keeps_build_instructions_output(project: Path) -> None:
    intent = load_intent_model(prepare(project))
    assert intent_lines(intent) == ["Objetivo: testar pedidos", "Estrutura: cliente e valor"]
    text = build_instructions(intent, 3, 1, None, False)
    assert text.splitlines()[1:3] == intent_lines(intent)


def test_approval_points_to_generate(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    prepare(project)
    cli(project, "sample", "run", "pedidos")
    lines = [{"cliente": n, "valor": 10} for n in ("Ana", "Bia", "Caio")]
    text = "".join(json.dumps(line) + "\n" for line in lines)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(text.encode("utf-8"))))
    rid = pending_id(project)
    assert main(["submit", "pedidos", rid, "--project-dir", str(project)]) == 0
    assert cli(project, "sample", "run", "pedidos") == 0
    capsys.readouterr()
    assert cli(project, "sample", "approve", "pedidos") == 0
    assert "Próximo passo: uv run sintetica generate pedidos" in capsys.readouterr().out
    assert (dataset(project) / "seeds" / "sample.jsonl").exists()
