"""Projeto com intenção e contrato aprovados, e um agente simulado pelo `sintetica submit` real."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from sintetica.cli import main
from sintetica.sample import load_sample_state

JSON_DRAFT: dict[str, Any] = {
    "format": "json",
    "fields": [
        {"name": "cliente", "type": "text"},
        {
            "name": "valor",
            "type": "decimal",
            "constraints": {"ge": 5, "le": 50, "casas_decimais": 2},
        },
    ],
}

CSV_DRAFT: dict[str, Any] = {
    "format": "csv",
    "fields": [
        {"name": "nome", "type": "text"},
        {"name": "tags", "type": "list", "items": {"type": "text"}},
        {"name": "saldo", "type": "decimal", "constraints": {"casas_decimais": 2}},
    ],
}


def cli(project: Path, *args: str) -> int:
    return main([*args, "--project-dir", str(project)])


def dataset(project: Path, slug: str = "pedidos") -> Path:
    return project / "datasets" / slug


def prepare(
    project: Path,
    slug: str = "pedidos",
    *,
    draft: dict[str, Any] | None = None,
    mode: str = "guiado",
    approve: bool = True,
) -> Path:
    """Entrevista concluída e contrato gerado (e aprovado, salvo `approve=False`)."""
    spec = draft or JSON_DRAFT
    assert cli(project, "start", slug, "--mode", mode) == 0
    answers = ["--objective", "testar pedidos", "--structure", "cliente e valor"]
    answers += ["--unknown", "rules", "--format", spec["format"], "--volume", "20"]
    assert cli(project, "intent", "set", slug, *answers) == 0
    if mode == "guiado":
        assert cli(project, "intent", "confirm", slug) == 0
    path = dataset(project, slug)
    (path / "schema.draft.json").write_text(json.dumps(spec), "utf-8")
    assert cli(project, "schema", "build", slug) == 0
    if approve and mode == "guiado":
        assert cli(project, "schema", "approve", slug) == 0
    return path


def pending_id(project: Path, slug: str = "pedidos") -> str:
    state = load_sample_state(dataset(project, slug))
    assert state is not None and state.pending_request_id is not None
    return state.pending_request_id


def agent_reply(
    project: Path,
    monkeypatch: pytest.MonkeyPatch,
    lines: list[Any],
    slug: str = "pedidos",
) -> int:
    """Faz o papel do agente: envia JSONL pelo `sintetica submit` para o pedido pendente."""
    text = "".join((ln if isinstance(ln, str) else json.dumps(ln)) + "\n" for ln in lines)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(text.encode("utf-8"))))
    return main(["submit", slug, pending_id(project, slug), "--project-dir", str(project)])


def all_text(project: Path) -> str:
    return "\n".join(
        p.read_text("utf-8", errors="ignore") for p in project.rglob("*") if p.is_file()
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return tmp_path
