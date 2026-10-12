"""Estado da amostra e metadados da semente (data-delta.md#1 e #2)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from sintetica.fsutil import write_atomic

STATE_FILE = "sample.state.json"
SEEDS_DIR = "seeds"
SEEDS_JSONL = "sample.jsonl"
SEEDS_META = "sample.meta.json"

MIN_N = 3
MAX_N = 5
DEFAULT_N = 3  # Q41
MAX_ATTEMPTS = 3

Status = Literal["aguardando_agente", "em_revisao", "aprovada", "interrompida"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SampleState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Status
    n: int = Field(ge=MIN_N, le=MAX_N)
    schema_version: str
    round: int = 0
    attempt: int = Field(default=0, ge=0, le=MAX_ATTEMPTS)
    adjustment: str | None = None
    pending_request_id: str | None = None
    pending_command: str | None = None
    # Registros aceitos já mascarados, 1 linha JSONL exata por registro (to_jsonl_line).
    accepted: list[str] = Field(default_factory=list)
    rejected: list[str] = Field(default_factory=list)  # motivos, nunca valores
    provider: str | None = None
    provider_reason: str | None = None
    updated_at: str = Field(default_factory=utc_now)

    @property
    def missing(self) -> int:
        return max(self.n - len(self.accepted), 0)


class SampleMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    approved_at: str
    provider: str
    n_requested: int
    n_records: int
    partial: bool
    rounds: int


def state_path(dataset_dir: Path) -> Path:
    return dataset_dir / STATE_FILE


def load_sample_state(dataset_dir: Path) -> SampleState | None:
    path = state_path(dataset_dir)
    if not path.exists():
        return None
    return SampleState.model_validate(json.loads(path.read_text("utf-8")))


def save_sample_state(dataset_dir: Path, state: SampleState) -> None:
    state = state.model_copy(update={"updated_at": utc_now()})
    text = json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
    write_atomic(state_path(dataset_dir), text)


def write_seeds(dataset_dir: Path, lines: list[str], meta: SampleMeta) -> tuple[Path, Path]:
    seeds = dataset_dir / SEEDS_DIR
    jsonl, meta_path = seeds / SEEDS_JSONL, seeds / SEEDS_META
    write_atomic(jsonl, "".join(f"{line}\n" for line in lines))
    write_atomic(meta_path, json.dumps(meta.model_dump(), ensure_ascii=False, indent=2) + "\n")
    return jsonl, meta_path
