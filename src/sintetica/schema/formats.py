"""Serialização de registros válidos para JSON, JSONL e CSV (RF-19, RN-09, D-15)."""

from __future__ import annotations

import datetime
import json
import re
import secrets
import types
from decimal import Decimal
from typing import Annotated, Any, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from sintetica.schema.csvflat import LIST_SEPARATOR


def _places_in(metadata: list[Any]) -> int | None:
    for meta in metadata:
        if isinstance(meta, FieldInfo):
            found = _places_in(meta.metadata)
            if found is not None:
                return found
        places = getattr(meta, "decimal_places", None)
        if isinstance(places, int):
            return places
    return None


def _places_in_type(tp: Any) -> int | None:
    """Casas decimais de itens de lista, declaradas no tipo do item (`list[Annotated[...]]`)."""
    origin = get_origin(tp)
    if origin is Annotated:
        args = get_args(tp)
        found = _places_in(list(args[1:]))
        return found if found is not None else _places_in_type(args[0])
    if origin in (list, Union, types.UnionType):
        for arg in get_args(tp):
            found = _places_in_type(arg)
            if found is not None:
                return found
    return None


def _decimal_places(info: FieldInfo) -> int | None:
    found = _places_in(info.metadata)
    return found if found is not None else _places_in_type(info.annotation)


def _fixed(value: Decimal, places: int | None) -> Decimal:
    if places is None:
        return value
    return value.quantize(Decimal(1).scaleb(-places))


def _plain(value: Any, places: int | None) -> Any:
    if isinstance(value, BaseModel):
        return to_json_obj(value)
    if isinstance(value, Decimal):
        return _fixed(value, places)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [_plain(item, places) for item in value]
    return value


def to_json_obj(record: BaseModel) -> dict[str, Any]:
    """Objeto Python do registro: decimais como `Decimal` com as casas definidas, datas em ISO."""
    fields = type(record).model_fields
    return {
        name: _plain(getattr(record, name), _decimal_places(info)) for name, info in fields.items()
    }


def to_json_text(obj: Any, indent: int | None = None) -> str:
    """JSON em que cada `Decimal` vira número exato (`19.90`), não texto.

    Compacto por padrão; com `indent`, formatado para leitura (feature 005, D-11).
    """
    nonce = secrets.token_hex(8)
    marker = re.compile(rf'"@dec{nonce}:(-?[0-9.Ee+-]+)"')

    def default(value: Any) -> Any:
        if isinstance(value, Decimal):
            return f"@dec{nonce}:{value:f}"
        raise TypeError(f"tipo não serializável: {type(value).__name__}")

    separators = (",", ":") if indent is None else (",", ": ")
    text = json.dumps(
        obj, ensure_ascii=False, default=default, separators=separators, indent=indent
    )
    return marker.sub(r"\1", text)


def to_jsonl_line(record: BaseModel) -> str:
    return to_json_text(to_json_obj(record))


def _cell(value: Any, places: int | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        return f"{_fixed(value, places):f}"
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return LIST_SEPARATOR.join(_cell(item, places) for item in value)
    return str(value)


def csv_columns(model: type[BaseModel]) -> list[str]:
    """Colunas do CSV na ordem da definição."""
    return list(model.model_fields)


def to_csv_row(record: BaseModel) -> dict[str, str]:
    """Linha de CSV: decimais com as casas fixas, listas unidas por `|`, booleanos minúsculos."""
    fields = type(record).model_fields
    return {
        name: _cell(getattr(record, name), _decimal_places(info)) for name, info in fields.items()
    }
