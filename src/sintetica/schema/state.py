"""Estado da revisão do contrato em `schema.state.json` (RF-16, RF-17, D-16)."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

STATE_FILE = "schema.state.json"
MAX_ROUNDS = 5

Status = Literal["em_revisao", "aprovado"]


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class SchemaState:
    status: Status
    rounds: int
    schema_version: str
    approved_at: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def rounds_exhausted(self) -> bool:
        return self.status == "em_revisao" and self.rounds >= MAX_ROUNDS


def load_state(dataset_dir: Path) -> SchemaState | None:
    path = dataset_dir / STATE_FILE
    if not path.exists():
        return None
    data = json.loads(path.read_text("utf-8"))
    return SchemaState(
        status="aprovado" if data.get("status") == "aprovado" else "em_revisao",
        rounds=int(data.get("rounds", 0)),
        schema_version=str(data.get("schema_version", "")),
        approved_at=data.get("approved_at"),
        warnings=[str(w) for w in data.get("warnings", [])],
    )


def save_state(dataset_dir: Path, state: SchemaState) -> None:
    text = json.dumps(asdict(state), ensure_ascii=False, indent=2) + "\n"
    write_atomic(dataset_dir / STATE_FILE, text)


def next_state(
    previous: SchemaState | None, version: str, *, express: bool, warnings: list[str]
) -> SchemaState:
    """Estado após um `build`. Versão nova sobre contrato existente conta 1 rodada de ajuste."""
    if previous is not None and previous.schema_version == version:
        return SchemaState(
            previous.status, previous.rounds, version, previous.approved_at, warnings
        )
    rounds = 0 if previous is None else previous.rounds + 1
    if express:
        return SchemaState("aprovado", rounds, version, _now(), warnings)
    return SchemaState("em_revisao", rounds, version, None, warnings)


def approved(state: SchemaState) -> SchemaState:
    return SchemaState("aprovado", state.rounds, state.schema_version, _now(), state.warnings)
