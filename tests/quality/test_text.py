"""Texto livre, normalização e 3-gramas de palavras (D-06, Q47)."""

from __future__ import annotations

from sintetica.quality.text import free_text, has_free_text, normalize, shingles
from sintetica.schema.spec import SchemaSpecModel, parse_spec


def _spec(data: dict[str, object]) -> SchemaSpecModel:
    spec = parse_spec(data)
    assert isinstance(spec, SchemaSpecModel), spec
    return spec


NESTED = _spec(
    {
        "format": "json",
        "fields": [
            {"name": "titulo", "type": "text"},
            {"name": "status", "type": "enum", "constraints": {"choices": ["a", "b"]}},
            {"name": "dia", "type": "date"},
            {"name": "n", "type": "int"},
            {"name": "tags", "type": "list", "items": {"type": "text"}},
            {
                "name": "end",
                "type": "object",
                "fields": [{"name": "rua", "type": "text"}, {"name": "num", "type": "int"}],
            },
            {
                "name": "itens",
                "type": "list",
                "items": {"type": "object", "fields": [{"name": "obs", "type": "text"}]},
            },
        ],
    }
)


def test_free_text_follows_contract_order_and_skips_fixed_fields() -> None:
    record = {
        "titulo": "Pedido",
        "status": "a",
        "dia": "2026-10-12",
        "n": 3,
        "tags": ["urgente", "novo"],
        "end": {"rua": "Rua Um", "num": 9},
        "itens": [{"obs": "frágil"}, {"obs": None}],
    }
    assert free_text(record, NESTED) == "Pedido urgente novo Rua Um frágil"
    assert has_free_text(NESTED)


def test_contract_without_text() -> None:
    spec = _spec({"format": "json", "fields": [{"name": "n", "type": "int"}]})
    assert not has_free_text(spec)
    assert free_text({"n": 1}, spec) == ""


def test_conversation_uses_messages_and_label_text() -> None:
    spec = _spec(
        {
            "format": "jsonl",
            "kind": "conversation",
            "fields": [
                {"name": "sentimento", "type": "enum", "constraints": {"choices": ["p", "n"]}},
                {"name": "nota", "type": "text", "required": False},
            ],
        }
    )
    record = {
        "messages": [{"role": "user", "content": "Oi"}, {"role": "assistant", "content": "Olá!"}],
        "labels": {"sentimento": "p", "nota": "curta"},
    }
    assert has_free_text(spec)
    assert free_text(record, spec) == "Oi Olá! curta"


def test_normalize_and_shingles() -> None:
    assert normalize("  Olá,   MUNDO!! É—bom.  ") == "olá mundo é bom"
    assert shingles("a b c d") == frozenset({"a b c", "b c d"})
    assert shingles("Só dois!") == frozenset({"só dois"})
    assert shingles("...") == frozenset()
    assert shingles("O cliente, pediu.") == shingles("o CLIENTE pediu")
