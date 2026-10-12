"""Leitura do dataset final, 1 registro por vez, validado pelo contrato atual (D-03).

JSONL é lido por linha; a lista JSON, de uma vez (o lote grava 1 registro por linha, mas o
arquivo pode ter sido editado); CSV é convertido célula a célula pelo `schema.json`.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from sintetica.sample.review import first_error
from sintetica.schema import to_jsonl_line
from sintetica.schema.csvflat import LIST_SEPARATOR
from sintetica.schema.spec import FieldSpecModel, SchemaSpecModel


class DatasetReadError(Exception):
    """O arquivo inteiro é ilegível (ex.: JSON que não é uma lista)."""


@dataclass(frozen=True, slots=True)
class Item:
    """1 registro lido. `canonical` é o JSON canônico do válido ou o texto bruto do inválido."""

    index: int
    record: BaseModel | None
    canonical: str
    reason: str | None = None


def _validate(index: int, data: Any, raw: str, model: type[BaseModel]) -> Item:
    if not isinstance(data, dict):
        return Item(index, None, raw, "o registro não é um objeto JSON")
    try:
        record = model.model_validate(data)
    except ValidationError as exc:
        return Item(index, None, raw, first_error(exc))
    return Item(index, record, to_jsonl_line(record))


def _jsonl(path: Path, model: type[BaseModel]) -> Iterator[Item]:
    index = 0
    with path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            try:
                data = json.loads(line, parse_float=Decimal)
            except ValueError:
                yield Item(index, None, line, "linha não é JSON válido")
            else:
                yield _validate(index, data, line, model)
            index += 1


def _json(path: Path, model: type[BaseModel]) -> Iterator[Item]:
    try:
        data = json.loads(path.read_text("utf-8"), parse_float=Decimal)
    except ValueError as exc:
        raise DatasetReadError(f"{path.name} não é JSON válido") from exc
    if not isinstance(data, list):
        raise DatasetReadError(f"{path.name} não é uma lista JSON")
    for index, item in enumerate(data):
        raw = json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)
        yield _validate(index, item, raw, model)


def _cell(text: str, field: FieldSpecModel) -> Any:
    if field.type == "list":
        return [] if text == "" else text.split(LIST_SEPARATOR)
    if text == "":
        return None
    return text


def csv_record(row: Mapping[str, str], spec: SchemaSpecModel) -> dict[str, Any]:
    """Linha do CSV de volta a registro, pelo contrato achatado (inverso de `to_csv_row`)."""
    return {f.name: _cell(row[f.name], f) for f in spec.fields if row.get(f.name) is not None}


def _csv(path: Path, model: type[BaseModel], spec: SchemaSpecModel) -> Iterator[Item]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        for index, cells in enumerate(reader):
            raw = json.dumps(cells, ensure_ascii=False)
            if len(cells) > len(header):
                yield Item(index, None, raw, "linha com colunas a mais")
            elif len(cells) < len(header):
                yield Item(index, None, raw, "linha com colunas a menos")
            else:
                yield _validate(
                    index, csv_record(dict(zip(header, cells, strict=True)), spec), raw, model
                )


def read_items(
    path: Path, fmt: str, model: type[BaseModel], spec: SchemaSpecModel
) -> Iterator[Item]:
    if fmt == "csv":
        return _csv(path, model, spec)
    if fmt == "json":
        return _json(path, model)
    return _jsonl(path, model)
