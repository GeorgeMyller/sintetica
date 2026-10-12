"""Transformação para CSV (RN-04, RF-07, Q35)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from sintetica.schema.csvflat import flatten_for_csv
from sintetica.schema.spec import SchemaSpecModel

from .conftest import attr, build_model, load_fixture, spec_of


def _flat(data: object) -> tuple[SchemaSpecModel, list[str]]:
    result = flatten_for_csv(spec_of(data))
    assert not isinstance(result, list), result
    return result


def test_objects_are_flattened_with_prefix_and_optional_propagates() -> None:
    spec, warnings = _flat(load_fixture("csv_nested"))
    names = {f.name: f for f in spec.fields}
    assert list(names) == ["nome", "tags", "notas", "endereco_cidade", "endereco_geo_lat"]
    assert names["nome"].required is True
    assert names["endereco_cidade"].required is False  # objeto pai opcional
    assert names["endereco_geo_lat"].required is False
    assert "objeto 'endereco' achatado em colunas com o prefixo 'endereco_'" in warnings
    assert "objeto 'endereco.geo' achatado em colunas com o prefixo 'endereco_geo_'" in warnings
    assert "lista 'tags' vira 1 coluna com os itens separados por '|'" in warnings


def test_list_of_objects_is_rejected_with_json_guidance() -> None:
    result = flatten_for_csv(spec_of(load_fixture("csv_list_objects")))
    assert isinstance(result, list)
    assert result[0].path == "itens"
    assert "use o formato JSON ou JSONL" in result[0].message


def test_list_of_lists_is_rejected() -> None:
    data = {
        "format": "csv",
        "fields": [
            {"name": "m", "type": "list", "items": {"type": "list", "items": {"type": "int"}}}
        ],
    }
    result = flatten_for_csv(spec_of(data))
    assert isinstance(result, list) and result[0].path == "m"


def test_enum_items_with_separator_are_rejected() -> None:
    data = {
        "format": "csv",
        "fields": [
            {
                "name": "m",
                "type": "list",
                "items": {"type": "enum", "constraints": {"choices": ["a|b"]}},
            }
        ],
    }
    result = flatten_for_csv(spec_of(data))
    assert isinstance(result, list) and result[0].path == "m[]"


def test_csv_text_items_reject_separator(tmp_path: Path) -> None:
    spec, _ = _flat(load_fixture("csv_nested"))
    record = build_model(spec, tmp_path)
    ok = record.model_validate({"nome": "Ana", "tags": ["a", "b"]})
    assert attr(ok, "tags") == ["a", "b"]
    with pytest.raises(ValidationError, match=r"\|"):
        record.model_validate({"nome": "Ana", "tags": ["a|b"]})
