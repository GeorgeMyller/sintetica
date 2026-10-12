"""Gerador determinístico (RF-03 a RF-06, RN-02)."""

from __future__ import annotations

import datetime
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from sintetica.schema.codegen import VERSION_PREFIX, generate_code, py_str
from sintetica.schema.loader import export_json_schema, header_version
from sintetica.schema.version import canonical_json, schema_version

from .conftest import VALID_FIXTURES, attr, build_model, load_fixture, spec_of

VALID_ALL_TYPES: dict[str, Any] = {
    "nome": "Ana",
    "idade": 30,
    "saldo": "10.5",
    "ativo": True,
    "nascimento": "1990-05-01",
    "criado_em": "2026-10-12T08:00:00",
    "uf": "SP",
    "tags": ["a", "b"],
    "endereco": {"cidade": "Recife"},
}

VALID_CONSTRAINTS: dict[str, Any] = {
    "codigo": "ABC",
    "idade": 18,
    "preco": "19.9",
    "data": "2020-01-01",
    "momento": "2001-01-01T00:00:00",
    "status": "novo",
    "itens": [1, 2],
}


@pytest.mark.parametrize("name", VALID_FIXTURES)
def test_generation_is_deterministic(name: str) -> None:
    spec = spec_of(load_fixture(name))
    version = schema_version(spec)
    assert generate_code(spec, version) == generate_code(spec_of(load_fixture(name)), version)


def test_header_carries_version(tmp_path: Path) -> None:
    spec = spec_of(load_fixture("all_types"))
    version = schema_version(spec)
    path = tmp_path / "schema.py"
    path.write_text(generate_code(spec, version), "utf-8")
    assert header_version(path) == version
    assert path.read_text("utf-8").splitlines()[1] == VERSION_PREFIX + version
    assert header_version(tmp_path / "nao-existe.py") is None


def test_version_ignores_formatting_and_key_order() -> None:
    data = load_fixture("constraints")
    reordered = json.loads(json.dumps(data, sort_keys=True, indent=7))
    assert schema_version(spec_of(data)) == schema_version(spec_of(reordered))
    changed = json.loads(json.dumps(data))
    changed["fields"][1]["constraints"]["le"] = 80
    assert schema_version(spec_of(changed)) != schema_version(spec_of(data))
    assert canonical_json(spec_of(data)).startswith('{"fields":')


def test_all_nine_types_accept_a_valid_record(tmp_path: Path) -> None:
    record = build_model(spec_of(load_fixture("all_types")), tmp_path)
    obj = record.model_validate(VALID_ALL_TYPES)
    assert attr(obj, "saldo") == Decimal("10.5")
    assert attr(obj, "nascimento") == datetime.date(1990, 5, 1)
    assert isinstance(attr(obj, "endereco"), BaseModel)
    assert attr(attr(obj, "endereco"), "cep") is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("idade", "trinta"),
        ("ativo", "talvez"),
        ("nascimento", "ontem"),
        ("uf", "BA"),
        ("tags", "a"),
        ("endereco", {"cidade": "Recife", "extra": 1}),
        ("extra", 1),
    ],
)
def test_types_reject_wrong_values(tmp_path: Path, field: str, value: object) -> None:
    record = build_model(spec_of(load_fixture("all_types")), tmp_path)
    with pytest.raises(ValidationError):
        record.model_validate({**VALID_ALL_TYPES, field: value})


def test_required_field_missing_is_rejected(tmp_path: Path) -> None:
    record = build_model(spec_of(load_fixture("all_types")), tmp_path)
    data = dict(VALID_ALL_TYPES)
    del data["nome"]
    with pytest.raises(ValidationError):
        record.model_validate(data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("codigo", "AB"),  # tamanho mínimo
        ("codigo", "ABCDEF"),  # tamanho máximo
        ("codigo", "abc"),  # padrão
        ("idade", 17),  # mínimo
        ("idade", 91),  # máximo
        ("preco", "19.999"),  # casas decimais
        ("preco", "0"),  # mínimo decimal
        ("data", "1999-12-31"),  # mínimo de data
        ("data", "2031-01-01"),  # máximo de data
        ("momento", "1999-01-01T00:00:00"),
        ("status", "cancelado"),  # valores permitidos
        ("itens", []),  # tamanho mínimo da lista
        ("itens", [1, 2, 3, 4]),  # tamanho máximo da lista
        ("itens", [-1]),  # restrição do item
    ],
)
def test_each_constraint_rejects_violation(tmp_path: Path, field: str, value: object) -> None:
    record = build_model(spec_of(load_fixture("constraints")), tmp_path)
    record.model_validate(VALID_CONSTRAINTS)
    with pytest.raises(ValidationError):
        record.model_validate({**VALID_CONSTRAINTS, field: value})


def test_optional_field_with_constraints_accepts_none(tmp_path: Path) -> None:
    record = build_model(spec_of(load_fixture("conversation")), tmp_path)
    base = {"messages": [{"role": "user", "content": "oi"}], "labels": {"sentimento": "neutro"}}
    assert attr(attr(record.model_validate(base), "labels"), "confianca") is None


def test_conversation_model(tmp_path: Path) -> None:
    record = build_model(spec_of(load_fixture("conversation")), tmp_path)
    ok = {
        "messages": [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "olá"}],
        "labels": {"sentimento": "positivo", "confianca": "0.9"},
    }
    record.model_validate(ok)
    for bad in (
        {**ok, "messages": [{"role": "bot", "content": "oi"}]},
        {**ok, "messages": []},
        {**ok, "messages": [{"role": "user", "content": ""}]},
        {"messages": ok["messages"]},
        {**ok, "labels": {"sentimento": "bravo"}},
    ):
        with pytest.raises(ValidationError):
            record.model_validate(bad)


def test_hostile_text_is_data_not_code(tmp_path: Path) -> None:
    spec = spec_of(load_fixture("hostile_text"))
    code = generate_code(spec, schema_version(spec))
    assert "\nimport os" not in code
    assert "\nos.system" not in code
    record = build_model(spec, tmp_path)
    schema = export_json_schema(record)
    expected = load_fixture("hostile_text")["fields"][0]["description"]
    assert schema["properties"]["campo"]["description"] == expected
    record.model_validate({"campo": "\"ab'c", "escolha": "\nimport os", "longo": "x"})
    assert not (tmp_path / "invadido").exists()


@pytest.mark.parametrize(
    "text",
    [
        "simples",
        'com "aspas"',
        "com 'apóstrofo'",
        "as \"duas\" 'aspas'",
        "barra \\ e\ttab\r",
        "\x07\u2028\U0001f600",
    ],
)
def test_py_str_round_trips(text: str) -> None:
    literal = py_str(text)
    assert eval(literal) == text  # literal produzido pelo gerador


def test_name_collisions_get_unique_class_names(tmp_path: Path) -> None:
    data = {
        "format": "json",
        "fields": [
            {"name": "record", "type": "object", "fields": [{"name": "a", "type": "int"}]},
            {"name": "decimal", "type": "object", "fields": [{"name": "b", "type": "int"}]},
            {
                "name": "x",
                "type": "list",
                "items": {"type": "object", "fields": [{"name": "c", "type": "int"}]},
            },
            {
                "name": "y",
                "type": "list",
                "items": {"type": "enum", "constraints": {"choices": ["p"]}},
            },
        ],
    }
    spec = spec_of(data)
    code = generate_code(spec, schema_version(spec))
    assert "class Record2(BaseModel):" in code and "class Decimal2(BaseModel):" in code
    assert "class XItem(BaseModel):" in code and "YItemChoices = Literal[" in code
    record = build_model(spec, tmp_path)
    record.model_validate({"record": {"a": 1}, "decimal": {"b": 2}, "x": [{"c": 3}], "y": ["p"]})
