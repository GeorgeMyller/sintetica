"""Transformação da definição para CSV (RN-04, D-08, Q35)."""

from __future__ import annotations

from collections.abc import Sequence

from sintetica.schema.spec import FieldSpecModel, SchemaIssue, SchemaSpecModel

LIST_SEPARATOR = "|"
SIMPLE_ITEM_TYPES = frozenset({"text", "int", "decimal", "bool", "date", "datetime", "enum"})


def _flatten(
    fields: Sequence[FieldSpecModel],
    prefix: str,
    parent_required: bool,
    warnings: list[str],
    issues: list[SchemaIssue],
) -> list[FieldSpecModel]:
    out: list[FieldSpecModel] = []
    for field in fields:
        path = f"{prefix}.{field.name}" if prefix else field.name
        column = path.replace(".", "_")
        required = field.required and parent_required
        if field.type == "object":
            warnings.append(f"objeto '{path}' achatado em colunas com o prefixo '{column}_'")
            out.extend(_flatten(field.fields or [], path, required, warnings, issues))
            continue
        if field.type == "list":
            item = field.items
            if item is None or item.type not in SIMPLE_ITEM_TYPES:
                issues.append(
                    SchemaIssue(
                        path,
                        "lista de objetos ou de listas não cabe em CSV; "
                        "use o formato JSON ou JSONL",
                    )
                )
                continue
            choices = item.constraints.choices or []
            if any(LIST_SEPARATOR in ch for ch in choices):
                issues.append(
                    SchemaIssue(f"{path}[]", "valores de lista em CSV não podem conter '|'")
                )
                continue
            warnings.append(
                f"lista '{path}' vira 1 coluna com os itens separados por '{LIST_SEPARATOR}'"
            )
        out.append(field.model_copy(update={"name": column, "required": required}))
    return out


def flatten_for_csv(
    spec: SchemaSpecModel,
) -> tuple[SchemaSpecModel, list[str]] | list[SchemaIssue]:
    """Definição plana para CSV e avisos, ou os problemas que impedem o CSV."""
    warnings: list[str] = []
    issues: list[SchemaIssue] = []
    fields = _flatten(spec.fields, "", True, warnings, issues)
    if issues:
        return issues
    return spec.model_copy(update={"fields": fields}), warnings
