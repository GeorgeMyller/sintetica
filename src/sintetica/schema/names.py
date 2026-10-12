"""Normalização de nomes de campo (RN-03, D-06)."""

from __future__ import annotations

import keyword
import re
import unicodedata
from collections.abc import Sequence

from pydantic import BaseModel

from sintetica.schema.spec import FieldSpecModel, SchemaSpecModel

# Nomes que, como atributo de classe, sombreariam nomes usados nas anotações do código gerado.
_GENERATED_CODE_NAMES = frozenset(
    {"datetime", "str", "int", "bool", "list", "float", "no_pipe", "annotated", "literal"}
)
_RESERVED = (
    frozenset(keyword.kwlist)
    | frozenset(keyword.softkwlist)
    | frozenset(dir(BaseModel))
    | _GENERATED_CODE_NAMES
)


def normalize_name(raw: str) -> str:
    """snake_case ASCII; sufixo `_` para nomes reservados. Não resolve repetidos."""
    ascii_text = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")
    if not name:
        name = "campo"
    if name[0].isdigit():
        name = f"campo_{name}"
    if name in _RESERVED or name.startswith("model_"):
        name = f"{name}_"
    return name


def _normalize_level(
    fields: Sequence[FieldSpecModel], prefix: str, warnings: list[str]
) -> list[FieldSpecModel]:
    used: set[str] = set()
    out: list[FieldSpecModel] = []
    for field in fields:
        base = normalize_name(field.name)
        name, n = base, 2
        while name in used:
            name, n = f"{base}_{n}", n + 1
        used.add(name)
        if name != field.name:
            where = f"{prefix}.{field.name}" if prefix else field.name
            warnings.append(f"campo '{where}' renomeado para '{name}'")
        path = f"{prefix}.{name}" if prefix else name
        update: dict[str, object] = {"name": name}
        if field.fields is not None:
            update["fields"] = _normalize_level(field.fields, path, warnings)
        if field.items is not None:
            update["items"] = _normalize_item(field.items, f"{path}[]", warnings)
        out.append(field.model_copy(update=update))
    return out


def _normalize_item(item: FieldSpecModel, path: str, warnings: list[str]) -> FieldSpecModel:
    update: dict[str, object] = {"name": normalize_name(item.name) if item.name else "item"}
    if item.fields is not None:
        update["fields"] = _normalize_level(item.fields, path, warnings)
    if item.items is not None:
        update["items"] = _normalize_item(item.items, f"{path}[]", warnings)
    return item.model_copy(update=update)


def normalize_names(spec: SchemaSpecModel) -> tuple[SchemaSpecModel, list[str]]:
    """Normaliza todos os nomes; devolve a definição nova e os avisos de renomeação."""
    warnings: list[str] = []
    fields = _normalize_level(spec.fields, "", warnings)
    return spec.model_copy(update={"fields": fields}), warnings
