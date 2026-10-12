"""Modelo de `datasets/<slug>/intent.json` (data-delta.md#1, D-02, D-03, D-10)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from sintetica.command import cli_command
from sintetica.fsutil import write_atomic

INTENT_FILE = "intent.json"
TEXT_ITEMS = ("objective", "structure", "rules")
ALL_ITEMS = (*TEXT_ITEMS, "format", "volume")
LABELS = {
    "objective": "objetivo",
    "structure": "estrutura",
    "rules": "regras",
    "format": "formato",
    "volume": "volume",
}
FORMATS = ("csv", "json", "jsonl")
DEFAULT_FORMAT: Literal["jsonl"] = "jsonl"  # Q38
DEFAULT_VOLUME = 10  # Q38
MIN_VOLUME = 1
MAX_VOLUME = 10_000

ItemStatus = Literal["pendente", "definido", "indefinido"]
Mode = Literal["guiado", "expresso"]
Source = Literal["usuario", "padrao"]


class IntentError(Exception):
    """Dataset ou `intent.json` ausente ou ilegível."""


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ItemStatus = "pendente"
    text: str | None = None


class IntentModel(BaseModel):
    # extra="allow": preserva chaves gravadas por outras features (ex.: finished_at).
    model_config = ConfigDict(extra="allow")

    slug: str
    mode: Mode = "guiado"
    started_at: str
    objective: Item = Field(default_factory=Item)
    structure: Item = Field(default_factory=Item)
    rules: Item = Field(default_factory=Item)
    format: Literal["csv", "json", "jsonl"] | None = None
    format_source: Source | None = None
    volume: int | None = Field(default=None, ge=MIN_VOLUME, le=MAX_VOLUME)
    volume_source: Source | None = None
    volume_rejections: int = Field(default=0, ge=0)
    pii_masked: bool = False
    confirmed_at: str | None = None

    def item(self, name: str) -> Item:
        value = getattr(self, name)
        assert isinstance(value, Item)
        return value


def intent_path(dataset_dir: Path) -> Path:
    return dataset_dir / INTENT_FILE


def load_intent_model(dataset_dir: Path) -> IntentModel:
    path = intent_path(dataset_dir)
    if not path.exists():
        raise IntentError(f"sem {INTENT_FILE} em {dataset_dir}; inicie com: {cli_command()} start")
    try:
        return IntentModel.model_validate(json.loads(path.read_text("utf-8")))
    except (ValueError, ValidationError) as exc:
        raise IntentError(f"{INTENT_FILE} ilegível em {dataset_dir}: {exc}") from exc


def save_intent(dataset_dir: Path, intent: IntentModel) -> None:
    text = json.dumps(intent.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
    write_atomic(intent_path(dataset_dir), text)
