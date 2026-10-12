from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from sintetica.schema.codegen import generate_code
from sintetica.schema.loader import import_record
from sintetica.schema.spec import SchemaSpecModel, parse_spec
from sintetica.schema.version import schema_version

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "schema"
VALID_FIXTURES = ["all_types", "constraints", "conversation", "csv_nested", "hostile_text"]


def attr(obj: object, name: str) -> Any:
    """Atributo de um Record gerado (tipo dinâmico, desconhecido pelo mypy)."""
    return getattr(obj, name)


def load_fixture(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / f"{name}.json").read_text("utf-8"))
    return data


def spec_of(data: object) -> SchemaSpecModel:
    parsed = parse_spec(data)
    assert isinstance(parsed, SchemaSpecModel), parsed
    return parsed


def build_model(spec: SchemaSpecModel, tmp_path: Path) -> type[BaseModel]:
    version = schema_version(spec)
    path = tmp_path / f"schema_{version[:8]}.py"
    path.write_text(generate_code(spec, version), "utf-8")
    return import_record(path, version)


def make_dataset(
    project: Path,
    slug: str = "demo",
    *,
    fmt: str = "json",
    mode: str = "guiado",
    structure: str = "definido",
    draft: object | None = None,
) -> Path:
    dataset = project / "datasets" / slug
    dataset.mkdir(parents=True, exist_ok=True)
    intent = {"slug": slug, "mode": mode, "format": fmt, "structure": {"status": structure}}
    (dataset / "intent.json").write_text(json.dumps(intent), "utf-8")
    if draft is not None:
        (dataset / "schema.draft.json").write_text(json.dumps(draft), "utf-8")
    return dataset


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return tmp_path
