"""Versão do contrato: SHA-256 do JSON canônico da definição (RN-05, D-12)."""

from __future__ import annotations

import hashlib
import json

from sintetica.schema.spec import SchemaSpecModel, dump_spec


def canonical_json(spec: SchemaSpecModel) -> str:
    return json.dumps(dump_spec(spec), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def pretty_json(spec: SchemaSpecModel) -> str:
    """Forma gravada em `schema.json`: legível e com a mesma versão da forma canônica."""
    return json.dumps(dump_spec(spec), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def schema_version(spec: SchemaSpecModel) -> str:
    return hashlib.sha256(canonical_json(spec).encode("utf-8")).hexdigest()
