"""Projeto com intenção e contrato aprovados e um dataset final gravado como o lote faria."""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from sintetica.batch.state import RunState, save_run_state
from sintetica.cli import main
from sintetica.pii import PiiGuard

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

NUMERIC_DRAFT: dict[str, Any] = {
    "format": "jsonl",
    "fields": [
        {"name": "idade", "type": "int"},
        {"name": "ativo", "type": "bool"},
    ],
}

CONVERSATION_DRAFT: dict[str, Any] = {
    "format": "jsonl",
    "kind": "conversation",
    "fields": [
        {
            "name": "sentimento",
            "type": "enum",
            "constraints": {"choices": ["positivo", "negativo", "neutro"]},
        },
        {"name": "nota", "type": "text", "required": False},
    ],
}

EMAIL = "ana.souza@empresa.com.br"
FIXED_NOW = datetime(2026, 10, 12, 12, 0, 0, tzinfo=timezone.utc)

WORDS = [
    "pedido",
    "entrega",
    "cliente",
    "atraso",
    "produto",
    "cupom",
    "troca",
    "loja",
    "frete",
    "prazo",
    "nota",
    "caixa",
    "suporte",
    "cartão",
    "boleto",
    "estoque",
    "pagamento",
    "devolução",
    "garantia",
    "vendedor",
]


def cli(project: Path, *args: str) -> int:
    return main([*args, "--project-dir", str(project)])


def dataset(project: Path, slug: str = "pedidos") -> Path:
    return project / "datasets" / slug


def distinct_text(i: int, words: int = 6) -> str:
    """Texto livre sem 3-gramas em comum com o de outro índice."""
    return " ".join(f"{WORDS[(i * 7 + k) % len(WORDS)]}{i}x{k}" for k in range(words))


def prepare(
    project: Path,
    *,
    volume: int = 10,
    draft: dict[str, Any] | None = None,
    started_minutes_ago: float | None = 5,
) -> Path:
    """Intenção confirmada e contrato aprovado; `started_at` ajustado em relação a FIXED_NOW."""
    spec = draft or JSON_DRAFT
    assert cli(project, "start", "pedidos", "--mode", "guiado") == 0
    answers = ["--objective", "testar avaliação", "--structure", "campos do contrato"]
    answers += ["--unknown", "rules", "--format", spec["format"], "--volume", str(volume)]
    assert cli(project, "intent", "set", "pedidos", *answers) == 0
    assert cli(project, "intent", "confirm", "pedidos") == 0
    path = dataset(project)
    (path / "schema.draft.json").write_text(json.dumps(spec), "utf-8")
    assert cli(project, "schema", "build", "pedidos") == 0
    assert cli(project, "schema", "approve", "pedidos") == 0
    intent_file = path / "intent.json"
    intent = json.loads(intent_file.read_text("utf-8"))
    if started_minutes_ago is None:
        intent["started_at"] = ""
    else:
        start = FIXED_NOW - timedelta(minutes=started_minutes_ago)
        intent["started_at"] = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    intent_file.write_text(json.dumps(intent), "utf-8")
    return path


def version(path: Path) -> str:
    data: dict[str, Any] = json.loads((path / "schema.state.json").read_text("utf-8"))
    return str(data["schema_version"])


def write_run(
    path: Path, *, volume: int, fmt: str, status: str = "concluido", schema: str | None = None
) -> None:
    state = RunState(
        slug="pedidos",
        status=status,
        volume_requested=volume,
        format=fmt,
        accepted=volume,
        block_size=10,
        avg_tokens=10,
        provider="ollama",
        provider_reason="teste",
        schema_version=schema or version(path),
    )
    save_run_state(path, state)


def write_dataset(path: Path, fmt: str, records: Sequence[Any]) -> Path:
    """Grava `output/dataset.<ext>`. Itens `str` entram como linha bruta (JSONL)."""
    out = path / "output"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"dataset.{fmt}"
    if fmt == "jsonl":
        lines = [r if isinstance(r, str) else json.dumps(r, ensure_ascii=False) for r in records]
        dest.write_text("".join(f"{line}\n" for line in lines), "utf-8")
    elif fmt == "json":
        dest.write_text(json.dumps(list(records), ensure_ascii=False), "utf-8")
    else:
        with dest.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, lineterminator="\r\n")
            for row in records:
                writer.writerow(row)
    return dest


def json_records(count: int, start: int = 0) -> list[dict[str, Any]]:
    return [{"cliente": distinct_text(i), "valor": 5 + i % 40} for i in range(start, start + count)]


def register_fake(path: Path, project: Path, text: str) -> str:
    """Mascara `text` com o PiiGuard do dataset; o valor falso entra na allowlist."""
    guard = PiiGuard.for_dataset(path, project / ".sintetica" / "policy.json")
    return guard.mask(text, field="cliente").text


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return tmp_path
