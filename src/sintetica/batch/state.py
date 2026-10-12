"""Estado do lote em `datasets/<slug>/output/run.json` (data-delta.md#1)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from sintetica.fsutil import write_atomic

OUTPUT_DIR = "output"
RUN_FILE = "run.json"
PARTIAL_FILE = "records.partial.jsonl"
LOCK_FILE = "run.lock"
LOG_FILE = "worker.log"
DATASET_STEM = "dataset"

MAX_ROUNDS = 4  # 1ª rodada + 3 rodadas extras (RN-07)
MAX_BLOCK_OVERRIDE = 100
CONFORMITY = Decimal("0.95")  # RN-10

RunStatus = Literal[
    "iniciando",
    "em_andamento",
    "aguardando_agente",
    "concluido",
    "incompleto",
    "interrompido_custo",
    "falha_provedor",
]
FINAL_STATUSES: frozenset[str] = frozenset(
    {"concluido", "incompleto", "interrompido_custo", "falha_provedor"}
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RunStateError(Exception):
    """`run.json` ilegível."""


class RunState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    status: RunStatus
    mode: Literal["foreground", "background"] = "foreground"
    pid: int | None = None
    volume_requested: int = Field(ge=1)
    format: Literal["csv", "json", "jsonl"]
    accepted: int = Field(default=0, ge=0)
    discarded_invalid: int = Field(default=0, ge=0)
    discarded_duplicate: int = Field(default=0, ge=0)
    round: int = Field(default=0, ge=0)
    block_size: int = Field(ge=1, le=MAX_BLOCK_OVERRIDE)
    avg_tokens: int = Field(ge=1)
    estimate_usd: Decimal | None = None
    authorized_usd: Decimal | None = None
    cost_usd: Decimal = Decimal("0")
    provider: str
    provider_reason: str
    schema_version: str
    pending_request_id: str | None = None
    pending_command: str | None = None
    stop_cause: str | None = None
    started_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    finished_at: str | None = None

    @property
    def missing(self) -> int:
        return max(0, self.volume_requested - self.accepted)

    @property
    def discarded(self) -> int:
        return self.discarded_invalid + self.discarded_duplicate

    @property
    def is_final(self) -> bool:
        return self.status in FINAL_STATUSES


def output_dir(dataset_dir: Path) -> Path:
    return dataset_dir / OUTPUT_DIR


def run_path(dataset_dir: Path) -> Path:
    return output_dir(dataset_dir) / RUN_FILE


def partial_path(dataset_dir: Path) -> Path:
    return output_dir(dataset_dir) / PARTIAL_FILE


def lock_path(dataset_dir: Path) -> Path:
    return output_dir(dataset_dir) / LOCK_FILE


def log_path(dataset_dir: Path) -> Path:
    return output_dir(dataset_dir) / LOG_FILE


def dataset_path(dataset_dir: Path, fmt: str) -> Path:
    return output_dir(dataset_dir) / f"{DATASET_STEM}.{fmt}"


def load_run_state(dataset_dir: Path) -> RunState | None:
    path = run_path(dataset_dir)
    if not path.exists():
        return None
    try:
        return RunState.model_validate(json.loads(path.read_text("utf-8")))
    except (ValueError, ValidationError) as exc:
        raise RunStateError(f"{RUN_FILE} ilegível em {path.parent}") from exc


def save_run_state(dataset_dir: Path, state: RunState) -> RunState:
    """Grava de forma atômica e devolve o estado com `updated_at` novo."""
    state = state.model_copy(update={"updated_at": utc_now()})
    text = json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n"
    write_atomic(run_path(dataset_dir), text)
    return state
