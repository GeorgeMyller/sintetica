"""Serialização para JSON, JSONL e CSV (RF-19, RN-09, Q37)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import BaseModel

from sintetica.schema.csvflat import flatten_for_csv
from sintetica.schema.formats import (
    csv_columns,
    to_csv_row,
    to_json_obj,
    to_json_text,
    to_jsonl_line,
)

from .conftest import build_model, load_fixture, spec_of


@pytest.fixture
def money(tmp_path: Path) -> type[BaseModel]:
    spec = spec_of(
        {
            "format": "json",
            "fields": [
                {"name": "preco", "type": "decimal", "constraints": {"casas_decimais": 2}},
                {"name": "taxa", "type": "decimal", "required": False},
                {"name": "pago", "type": "bool"},
                {"name": "dia", "type": "date"},
                {
                    "name": "itens",
                    "type": "list",
                    "items": {"type": "decimal", "constraints": {"casas_decimais": 1}},
                },
                {
                    "name": "end",
                    "type": "object",
                    "fields": [
                        {"name": "valor", "type": "decimal", "constraints": {"casas_decimais": 3}}
                    ],
                },
            ],
        }
    )
    return build_model(spec, tmp_path)


def _record(money: type[BaseModel]) -> BaseModel:
    return money.model_validate(
        {
            "preco": "19.9",
            "pago": False,
            "dia": "2026-10-12",
            "itens": [1, "2.5"],
            "end": {"valor": 1},
        }
    )


def test_json_obj_and_text_emit_exact_numbers(money: type[BaseModel]) -> None:
    record = _record(money)
    obj = to_json_obj(record)
    assert obj["preco"] == Decimal("19.90") and str(obj["preco"]) == "19.90"
    assert obj["taxa"] is None and obj["dia"] == "2026-10-12"
    assert obj["end"] == {"valor": Decimal("1.000")}
    line = to_jsonl_line(record)
    assert '"preco":19.90' in line
    assert '"itens":[1.0,2.5]' in line
    assert '"end":{"valor":1.000}' in line
    assert json.loads(line)["preco"] == 19.9


def test_json_text_does_not_touch_user_strings() -> None:
    text = to_json_text({"nota": '"@dec0000:1"', "valor": Decimal("-1.50")})
    assert json.loads(text)["nota"] == '"@dec0000:1"'
    assert text.endswith('"valor":-1.50}')
    with pytest.raises(TypeError):
        to_json_text({"x": object()})


def test_csv_row_formats_decimals_lists_and_booleans(money: type[BaseModel]) -> None:
    row = to_csv_row(_record(money))
    assert row["preco"] == "19.90"
    assert row["taxa"] == ""
    assert row["pago"] == "false"
    assert row["dia"] == "2026-10-12"
    assert row["itens"] == "1.0|2.5"


def test_csv_columns_follow_definition_order(tmp_path: Path) -> None:
    flat = flatten_for_csv(spec_of(load_fixture("csv_nested")))
    assert not isinstance(flat, list)
    record = build_model(flat[0], tmp_path)
    assert csv_columns(record) == ["nome", "tags", "notas", "endereco_cidade", "endereco_geo_lat"]
    row = to_csv_row(
        record.model_validate({"nome": "Ana", "tags": ["a", "b"], "notas": ["7.5", 8]})
    )
    assert row == {
        "nome": "Ana",
        "tags": "a|b",
        "notas": "7.5|8.0",
        "endereco_cidade": "",
        "endereco_geo_lat": "",
    }
    assert (
        to_csv_row(record.model_validate({"nome": "B", "tags": [], "endereco_cidade": "x"}))["tags"]
        == ""
    )


def test_zero_decimal_places_on_list_items(tmp_path: Path) -> None:
    spec = spec_of(
        {
            "format": "json",
            "fields": [
                {
                    "name": "v",
                    "type": "list",
                    "items": {"type": "decimal", "constraints": {"casas_decimais": 0}},
                }
            ],
        }
    )
    record = build_model(spec, tmp_path)
    assert to_jsonl_line(record.model_validate({"v": ["3"]})) == '{"v":[3]}'


def test_json_text_indent_keeps_exact_decimals_and_default_is_unchanged() -> None:
    obj = {"valor": Decimal("19.90"), "nome": "Ana"}
    assert to_json_text(obj) == '{"valor":19.90,"nome":"Ana"}'
    assert to_json_text(obj, indent=None) == to_json_text(obj)
    assert to_json_text(obj, indent=2) == '{\n  "valor": 19.90,\n  "nome": "Ana"\n}'
