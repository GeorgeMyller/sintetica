"""Contrato com o schema-builder (feature 003): intenção da entrevista aceita sem ajuste."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sintetica.schema.intent import load_intent as schema_load_intent

from .conftest import dataset, run


def _interview(project: Path, slug: str, *answers: str, mode: str = "guiado") -> Path:
    assert run(project, "start", slug, "--mode", mode) == 0
    assert run(project, "intent", "set", slug, *answers) == 0
    if mode == "guiado":
        assert run(project, "intent", "confirm", slug) == 0
    return dataset(project, slug)


def test_schema_reader_accepts_interview_intent(project: Path) -> None:
    path = _interview(
        project,
        "pedidos",
        "--objective",
        "o",
        "--structure",
        "s",
        "--rules",
        "r",
        "--format",
        "CSV",
        "--volume",
        "50",
    )
    intent = schema_load_intent(path)
    assert (intent.slug, intent.mode, intent.format, intent.structure_defined) == (
        "pedidos",
        "guiado",
        "csv",
        True,
    )


def test_schema_build_with_draft(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _interview(
        project,
        "pedidos",
        "--objective",
        "o",
        "--structure",
        "cliente e valor",
        "--unknown",
        "rules",
        "--format",
        "json",
        "--volume",
        "50",
        mode="expresso",
    )
    draft = {"format": "json", "fields": [{"name": "cliente", "type": "text"}]}
    (path / "schema.draft.json").write_text(json.dumps(draft), "utf-8")
    assert run(project, "schema", "build", "pedidos") == 0
    assert "status aprovado" in capsys.readouterr().out  # Expresso aprova o contrato


def test_schema_build_with_undefined_structure(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _interview(
        project,
        "rapido",
        "--unknown",
        "objective",
        "--unknown",
        "structure",
        "--unknown",
        "rules",
        "--unknown",
        "format",
        "--unknown",
        "volume",
    )
    assert run(project, "schema", "build", "rapido") == 0
    out = capsys.readouterr().out
    assert "estrutura indefinida" in out and "| descricao |" in out
