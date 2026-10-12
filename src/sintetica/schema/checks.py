"""Validação semântica da definição (D-05): regras entre atributos que o meta-modelo não cobre."""

from __future__ import annotations

import datetime
import re
from decimal import Decimal, InvalidOperation
from typing import Annotated

from pydantic import Field, TypeAdapter

from sintetica.schema.spec import Bound, FieldSpecModel, SchemaIssue, SchemaSpecModel
from sintetica.schema.walk import count_fields, walk

MAX_FIELDS = 100
MAX_DECIMAL_PLACES = 10

ALLOWED: dict[str, frozenset[str]] = {
    "text": frozenset({"min_length", "max_length", "pattern"}),
    "int": frozenset({"ge", "le"}),
    "decimal": frozenset({"ge", "le", "casas_decimais"}),
    "bool": frozenset(),
    "date": frozenset({"ge", "le"}),
    "datetime": frozenset({"ge", "le"}),
    "enum": frozenset({"choices"}),
    "list": frozenset({"min_length", "max_length"}),
    "object": frozenset(),
}

BoundValue = int | Decimal | datetime.date | datetime.datetime


def parse_bound(field_type: str, value: Bound) -> BoundValue:
    """Converte `ge`/`le` para o tipo do campo. Levanta ValueError se não for compatível."""
    if field_type == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("deve ser um número inteiro")
        return value
    if field_type == "decimal":
        if isinstance(value, bool):
            raise ValueError("deve ser um número")
        try:
            return Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError("deve ser um número") from exc
    if not isinstance(value, str):
        raise ValueError("deve ser texto no formato ISO 8601")
    if field_type == "date":
        return datetime.date.fromisoformat(value)
    return datetime.datetime.fromisoformat(value)


def pattern_error(pattern: str) -> str | None:
    """Erro do padrão no `re` do Python ou no motor de regex do Pydantic; None se válido."""
    try:
        re.compile(pattern)
    except re.error as exc:
        return f"padrão inválido: {exc}"
    try:
        TypeAdapter(Annotated[str, Field(pattern=pattern)])
    except Exception as exc:
        first = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
        return f"padrão não suportado pelo validador: {first}"
    return None


def _check_field(path: str, field: FieldSpecModel, is_item: bool) -> list[SchemaIssue]:
    issues: list[SchemaIssue] = []
    c = field.constraints
    if not is_item and not field.name.strip():
        issues.append(SchemaIssue(path or "(campo sem nome)", "o nome do campo é obrigatório"))
    for name in c.set_names():
        if name not in ALLOWED[field.type]:
            issues.append(
                SchemaIssue(path, f"a restrição {name} não se aplica ao tipo {field.type}")
            )
    if field.items is not None and field.type != "list":
        issues.append(SchemaIssue(path, "items só se aplica ao tipo list"))
    if field.fields is not None and field.type != "object":
        issues.append(SchemaIssue(path, "fields só se aplica ao tipo object"))
    if field.type == "list" and field.items is None:
        issues.append(SchemaIssue(path, "o tipo list exige items"))
    if field.type == "object" and not field.fields:
        issues.append(SchemaIssue(path, "o tipo object exige ao menos 1 campo em fields"))
    if field.type == "enum":
        choices = c.choices or []
        if not choices:
            issues.append(SchemaIssue(path, "o tipo enum exige ao menos 1 valor em choices"))
        if any(not ch for ch in choices):
            issues.append(SchemaIssue(path, "choices não aceita valor vazio"))
        if len(set(choices)) != len(choices):
            issues.append(SchemaIssue(path, "choices tem valores repetidos"))
    issues.extend(_check_bounds(path, field))
    if c.min_length is not None and c.max_length is not None and c.min_length > c.max_length:
        issues.append(
            SchemaIssue(
                path,
                f"tamanho mínimo ({c.min_length}) maior que tamanho máximo ({c.max_length})",
            )
        )
    if c.pattern is not None and field.type == "text":
        error = pattern_error(c.pattern)
        if error is not None:
            issues.append(SchemaIssue(path, error))
    if c.casas_decimais is not None and not 0 <= c.casas_decimais <= MAX_DECIMAL_PLACES:
        issues.append(
            SchemaIssue(path, f"casas_decimais deve estar entre 0 e {MAX_DECIMAL_PLACES}")
        )
    return issues


def _check_bounds(path: str, field: FieldSpecModel) -> list[SchemaIssue]:
    c = field.constraints
    if field.type not in ("int", "decimal", "date", "datetime"):
        return []
    parsed: dict[str, BoundValue] = {}
    issues: list[SchemaIssue] = []
    for name in ("ge", "le"):
        value = getattr(c, name)
        if value is None:
            continue
        try:
            parsed[name] = parse_bound(field.type, value)
        except ValueError as exc:
            issues.append(SchemaIssue(path, f"{name}: {exc}"))
    if "ge" in parsed and "le" in parsed:
        ge, le = parsed["ge"], parsed["le"]
        try:
            contradiction = ge > le  # type: ignore[operator]
        except TypeError:
            issues.append(SchemaIssue(path, "ge e le precisam ter o mesmo tipo de data"))
            return issues
        if contradiction:
            issues.append(SchemaIssue(path, f"mínimo ({c.ge}) maior que máximo ({c.le})"))
    return issues


def check_spec(spec: SchemaSpecModel) -> list[SchemaIssue]:
    """Todos os problemas semânticos da definição; lista vazia se válida."""
    issues: list[SchemaIssue] = []
    total = count_fields(spec.fields)
    if total > MAX_FIELDS:
        issues.append(
            SchemaIssue(
                "fields",
                f"{total} campos; o limite é {MAX_FIELDS}. Divida o dataset em mais de um.",
            )
        )
    if spec.kind == "conversation" and spec.format == "csv":
        issues.append(SchemaIssue("kind", "o contrato de conversa exige formato JSON ou JSONL"))
    for path, field, is_item in walk(spec.fields):
        issues.extend(_check_field(path, field, is_item))
    return issues
