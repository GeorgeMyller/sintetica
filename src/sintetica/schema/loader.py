"""Carregamento e validação do `schema.py` gerado (D-13, D-14, RN-08)."""

from __future__ import annotations

import importlib.util
import itertools
import json
import re
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from sintetica.schema.codegen import VERSION_PREFIX, generate_code
from sintetica.schema.spec import SchemaSpecModel
from sintetica.schema.version import schema_version

SCHEMA_JSON = "schema.json"
SCHEMA_PY = "schema.py"
RECORD_SCHEMA_JSON = "record.schema.json"

_VERSION_RE = re.compile(rf"^{re.escape(VERSION_PREFIX)}([0-9a-f]{{64}})$", re.MULTILINE)
_counter = itertools.count()


class GeneratedCodeError(Exception):
    """O código gerado não importa, não define `Record` ou não exporta JSON Schema."""


class SchemaNotFoundError(Exception):
    """O dataset não tem `schema.json`."""


def header_version(code_path: Path) -> str | None:
    """Versão gravada no cabeçalho do `schema.py`, ou None se ausente."""
    if not code_path.exists():
        return None
    match = _VERSION_RE.search(code_path.read_text("utf-8")[:512])
    return match.group(1) if match else None


def import_record(code_path: Path, version: str) -> type[BaseModel]:
    """Importa o arquivo com nome de módulo único e devolve a classe `Record`."""
    name = f"sintetica_dataset_{version[:16]}_{next(_counter)}"
    try:
        spec = importlib.util.spec_from_file_location(name, code_path)
        if spec is None or spec.loader is None:
            raise GeneratedCodeError(f"não foi possível carregar {code_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        # Sem __pycache__ dentro da pasta do dataset.
        previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
        try:
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous
    except GeneratedCodeError:
        raise
    except Exception as exc:
        sys.modules.pop(name, None)
        raise GeneratedCodeError(f"o código gerado não importa: {exc}") from exc
    record = getattr(module, "Record", None)
    if not (isinstance(record, type) and issubclass(record, BaseModel)):
        raise GeneratedCodeError("o código gerado não define a classe Record")
    return record


def export_json_schema(record: type[BaseModel]) -> dict[str, Any]:
    try:
        return record.model_json_schema()
    except Exception as exc:
        raise GeneratedCodeError(f"o Record não exporta JSON Schema: {exc}") from exc


def read_spec(dataset_dir: Path) -> SchemaSpecModel:
    path = dataset_dir / SCHEMA_JSON
    if not path.exists():
        raise SchemaNotFoundError(f"sem {SCHEMA_JSON} em {dataset_dir}")
    return SchemaSpecModel.model_validate(json.loads(path.read_text("utf-8")))


def load_record_model(dataset_dir: Path) -> type[BaseModel]:
    """`Record` do dataset. Gera de novo o `schema.py` se a versão não bater com `schema.json`."""
    spec = read_spec(dataset_dir)
    version = schema_version(spec)
    code_path = dataset_dir / SCHEMA_PY
    if header_version(code_path) != version:
        code_path.write_text(generate_code(spec, version), "utf-8")
    return import_record(code_path, version)
