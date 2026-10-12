"""Revisão dos registros recebidos: validar, descartar duplicados, mascarar e revalidar."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ValidationError

from sintetica.schema import to_json_obj, to_jsonl_line

Masker = Callable[[str, str], str]  # (texto, caminho do campo) -> texto mascarado


@dataclass
class ReviewResult:
    accepted: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)


def first_error(exc: ValidationError) -> str:
    """1º erro de validação com o caminho do campo, sem o valor recebido."""
    err = exc.errors(include_input=False)[0]
    where = ".".join(str(part) for part in err["loc"]) or "registro"
    return f"{where}: {err['msg']}"


def mask_value(value: Any, path: str, masker: Masker) -> Any:
    """Mascara cada texto do valor, com o caminho do campo (`end.cidade`, `tags[]`)."""
    if isinstance(value, str):
        return masker(value, path)
    if isinstance(value, dict):
        return {k: mask_value(v, f"{path}.{k}" if path else k, masker) for k, v in value.items()}
    if isinstance(value, list):
        return [mask_value(v, f"{path}[]", masker) for v in value]
    return value


def parse_line(line: str) -> dict[str, Any]:
    """Linha JSONL guardada no estado, com decimais exatos."""
    data: dict[str, Any] = json.loads(line, parse_float=Decimal)
    return data


def review_records(
    raw: Sequence[Mapping[str, object]],
    model: type[BaseModel],
    existing: Sequence[str],
    masker: Masker,
    limit: int,
) -> ReviewResult:
    """Aceita até `limit` registros novos. Motivos de descarte nunca trazem o valor recebido."""
    result = ReviewResult()
    seen_raw: set[str] = set()
    seen_masked = set(existing)
    for index, item in enumerate(raw, start=1):
        if len(result.accepted) >= limit:
            result.rejected.append(f"registro {index}: excede os {limit} pedidos")
            continue
        try:
            record = model.model_validate(item)
        except ValidationError as exc:
            result.rejected.append(f"registro {index}: {first_error(exc)}")
            continue
        raw_line = to_jsonl_line(record)
        if raw_line in seen_raw or raw_line in seen_masked:
            result.rejected.append(f"registro {index}: duplicado")
            continue
        seen_raw.add(raw_line)
        masked_obj = mask_value(to_json_obj(record), "", masker)
        try:
            masked = model.model_validate(masked_obj)
        except ValidationError as exc:
            result.rejected.append(
                f"registro {index}: o valor falso do mascaramento quebrou a regra "
                f"({first_error(exc)})"
            )
            continue
        line = to_jsonl_line(masked)
        if line in seen_masked:
            result.rejected.append(f"registro {index}: duplicado")
            continue
        seen_masked.add(line)
        result.accepted.append(line)
    return result
