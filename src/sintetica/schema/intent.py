"""Leitura tolerante de `intent.json` e definição padrão de estrutura indefinida (D-17, D-18)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from sintetica.schema.spec import DatasetFormat, FieldSpecModel, SchemaSpecModel

INTENT_FILE = "intent.json"
_FORMATS = ("csv", "json", "jsonl")


class IntentError(Exception):
    """`intent.json` ausente ou sem os campos mínimos."""


@dataclass(frozen=True, slots=True)
class Intent:
    slug: str
    mode: Literal["guiado", "expresso"]
    format: DatasetFormat
    structure_defined: bool


def load_intent(dataset_dir: Path) -> Intent:
    path = dataset_dir / INTENT_FILE
    if not path.exists():
        raise IntentError(f"sem {INTENT_FILE} em {dataset_dir}; rode /sintetica-start")
    try:
        data = json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        raise IntentError(f"{INTENT_FILE} inválido ({exc.msg}); rode /sintetica-start") from exc
    if not isinstance(data, dict):
        raise IntentError(f"{INTENT_FILE} deve conter um objeto JSON; rode /sintetica-start")
    fmt = data.get("format")
    if fmt not in _FORMATS:
        raise IntentError(f"{INTENT_FILE} sem formato válido; rode /sintetica-start")
    structure = data.get("structure")
    status = structure.get("status") if isinstance(structure, dict) else None
    return Intent(
        slug=str(data.get("slug", dataset_dir.name)),
        mode="expresso" if data.get("mode") == "expresso" else "guiado",
        format=cast(DatasetFormat, fmt),
        structure_defined=status != "indefinido",
    )


def default_spec(fmt: DatasetFormat) -> SchemaSpecModel:
    """Contrato mínimo para estrutura indefinida (RN-07)."""
    field = FieldSpecModel(name="descricao", type="text", description="a definir")
    return SchemaSpecModel(format=fmt, fields=[field])
