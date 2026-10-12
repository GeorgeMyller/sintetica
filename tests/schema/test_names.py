"""Normalização de nomes (RN-03, RF-08)."""

from __future__ import annotations

import pytest

from sintetica.schema.names import normalize_name, normalize_names

from .conftest import spec_of


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Nome Completo", "nome_completo"),
        ("Ação", "acao"),
        ("  --Preço (R$)-- ", "preco_r"),
        ("class", "class_"),
        ("match", "match_"),
        ("model_config", "model_config_"),
        ("model_x", "model_x_"),
        ("schema", "schema_"),
        ("datetime", "datetime_"),
        ("int", "int_"),
        ("2fa", "campo_2fa"),
        ("___", "campo"),
        ("😀", "campo"),
        ("idade", "idade"),
    ],
)
def test_normalize_name(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected


def test_duplicates_get_numeric_suffix_and_warnings() -> None:
    spec = spec_of(
        {
            "format": "json",
            "fields": [
                {"name": "Nome Completo", "type": "text"},
                {"name": "class", "type": "text"},
                {"name": "Idade", "type": "int"},
                {"name": "idade", "type": "int"},
                {"name": "IDADE", "type": "int"},
            ],
        }
    )
    normalized, warnings = normalize_names(spec)
    assert [f.name for f in normalized.fields] == [
        "nome_completo",
        "class_",
        "idade",
        "idade_2",
        "idade_3",
    ]
    assert "campo 'Nome Completo' renomeado para 'nome_completo'" in warnings
    assert len(warnings) == 5


def test_nested_objects_and_items_are_normalized_per_level() -> None:
    spec = spec_of(
        {
            "format": "json",
            "fields": [
                {
                    "name": "Endereço",
                    "type": "object",
                    "fields": [
                        {"name": "Cidade", "type": "text"},
                        {"name": "cidade", "type": "text"},
                    ],
                },
                {
                    "name": "itens",
                    "type": "list",
                    "items": {"type": "object", "fields": [{"name": "SKU", "type": "text"}]},
                },
                {
                    "name": "matriz",
                    "type": "list",
                    "items": {"name": "Linha", "type": "list", "items": {"type": "int"}},
                },
            ],
        }
    )
    normalized, warnings = normalize_names(spec)
    endereco = normalized.fields[0]
    assert endereco.name == "endereco"
    assert [f.name for f in endereco.fields or []] == ["cidade", "cidade_2"]
    item = normalized.fields[1].items
    assert item is not None and item.name == "item"
    assert [f.name for f in item.fields or []] == ["sku"]
    inner = normalized.fields[2].items
    assert inner is not None and inner.name == "linha" and inner.items is not None
    assert inner.items.name == "item"
    assert "campo 'endereco.Cidade' renomeado para 'cidade'" in warnings
    assert "campo 'itens[].SKU' renomeado para 'sku'" in warnings


def test_normalization_is_idempotent() -> None:
    spec = spec_of({"format": "json", "fields": [{"name": "Nome", "type": "text"}]})
    once, _ = normalize_names(spec)
    twice, warnings = normalize_names(once)
    assert once == twice and warnings == []
