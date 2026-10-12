"""Estrutura (RF-02) e semântica (RF-09, RF-10, RF-11) da definição."""

from __future__ import annotations

import pytest

from sintetica.schema.checks import MAX_FIELDS, check_spec, pattern_error
from sintetica.schema.spec import SchemaIssue, SchemaSpecModel, dump_spec, parse_spec

from .conftest import VALID_FIXTURES, load_fixture, spec_of


@pytest.mark.parametrize("name", VALID_FIXTURES)
def test_valid_fixtures_have_no_issues(name: str) -> None:
    assert check_spec(spec_of(load_fixture(name))) == []


def test_structure_errors_are_all_reported_with_path() -> None:
    issues = parse_spec(
        {"format": "xml", "fields": [{"name": "a", "type": "texto"}, {"type": "int", "x": 1}]}
    )
    assert isinstance(issues, list)
    paths = {i.path for i in issues}
    assert {"format", "fields[0].type", "fields[1].x"} <= paths
    assert all(isinstance(i, SchemaIssue) and i.message for i in issues)
    assert str(issues[0]).startswith(issues[0].path + ": ")


def test_empty_fields_and_non_object_root() -> None:
    assert isinstance(parse_spec({"format": "json", "fields": []}), list)
    root = parse_spec([1, 2])
    assert isinstance(root, list) and root[0].path == "(raiz)"


def test_defaults_are_applied() -> None:
    spec = spec_of({"format": "json", "fields": [{"name": "a", "type": "text"}]})
    assert spec.kind == "records" and spec.model_name == "Record"
    assert spec.fields[0].required is True and spec.fields[0].description == ""
    assert dump_spec(spec)["fields"] == [
        {"name": "a", "type": "text", "required": True, "description": "", "constraints": {}}
    ]


def test_contradictions_fixture() -> None:
    messages = [str(i) for i in check_spec(spec_of(load_fixture("contradictions")))]
    joined = "\n".join(messages)
    assert "idade: mínimo (90) maior que máximo (18)" in joined
    assert "codigo: tamanho mínimo (5) maior que tamanho máximo (2)" in joined
    assert "codigo: padrão inválido" in joined
    assert "uf: o tipo enum exige ao menos 1 valor em choices" in joined
    assert "ativo: a restrição ge não se aplica ao tipo bool" in joined


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ({"name": "x", "type": "list"}, "o tipo list exige items"),
        ({"name": "x", "type": "object"}, "o tipo object exige ao menos 1 campo"),
        ({"name": "x", "type": "text", "items": {"type": "int"}}, "items só se aplica"),
        ({"name": "x", "type": "text", "fields": [{"name": "y", "type": "int"}]}, "fields só"),
        ({"name": "x", "type": "enum", "constraints": {"choices": ["a", "a"]}}, "repetidos"),
        ({"name": "x", "type": "enum", "constraints": {"choices": [""]}}, "valor vazio"),
        (
            {"name": "x", "type": "int", "constraints": {"ge": 1.5}},
            "ge: deve ser um número inteiro",
        ),
        (
            {"name": "x", "type": "int", "constraints": {"le": True}},
            "le: deve ser um número inteiro",
        ),
        ({"name": "x", "type": "decimal", "constraints": {"ge": "abc"}}, "ge: deve ser um número"),
        ({"name": "x", "type": "decimal", "constraints": {"ge": False}}, "ge: deve ser um número"),
        ({"name": "x", "type": "date", "constraints": {"ge": 2020}}, "ge: deve ser texto"),
        ({"name": "x", "type": "date", "constraints": {"ge": "31/12/2020"}}, "ge: Invalid"),
        (
            {
                "name": "x",
                "type": "datetime",
                "constraints": {"ge": "2030-01-01", "le": "2020-01-01"},
            },
            "mínimo (2030-01-01) maior que máximo (2020-01-01)",
        ),
        (
            {"name": "x", "type": "decimal", "constraints": {"casas_decimais": 11}},
            "casas_decimais deve estar entre 0 e 10",
        ),
        ({"name": "", "type": "int"}, "o nome do campo é obrigatório"),
    ],
)
def test_semantic_rules(field: dict[str, object], expected: str) -> None:
    issues = check_spec(spec_of({"format": "json", "fields": [field]}))
    assert any(expected.lower() in str(i).lower() for i in issues), issues


def test_mixed_date_and_datetime_bounds_are_reported() -> None:
    field = {"name": "x", "type": "datetime", "constraints": {"ge": "2020-01-01T00:00:00+00:00"}}
    field["constraints"]["le"] = "2030-01-01T00:00:00"  # type: ignore[index]
    issues = check_spec(spec_of({"format": "json", "fields": [field]}))
    assert any("mesmo tipo de data" in str(i) for i in issues)


def test_item_constraints_are_checked_with_item_path() -> None:
    field = {
        "name": "notas",
        "type": "list",
        "items": {"type": "int", "constraints": {"ge": 5, "le": 1}},
    }
    issues = check_spec(spec_of({"format": "json", "fields": [field]}))
    assert [i.path for i in issues] == ["notas[]"]


def test_field_limit_counts_nested_fields() -> None:
    nested = {
        "name": "obj",
        "type": "object",
        "fields": [{"name": f"n{i}", "type": "int"} for i in range(50)],
    }
    flat = [{"name": f"c{i}", "type": "int"} for i in range(50)]
    issues = check_spec(spec_of({"format": "json", "fields": [*flat, nested]}))
    assert any(f"101 campos; o limite é {MAX_FIELDS}" in str(i) for i in issues)
    ok = check_spec(spec_of({"format": "json", "fields": flat}))
    assert ok == []


def test_conversation_rejects_csv() -> None:
    spec = SchemaSpecModel.model_validate(
        {"format": "csv", "kind": "conversation", "fields": [{"name": "r", "type": "text"}]}
    )
    assert any("conversa" in str(i) for i in check_spec(spec))


def test_pattern_supported_by_python_but_not_by_validator() -> None:
    error = pattern_error(r"(?<=a)b")
    assert error is not None and "não suportado pelo validador" in error
    assert pattern_error(r"^[a-z]+$") is None
    assert pattern_error("(abc") is not None
