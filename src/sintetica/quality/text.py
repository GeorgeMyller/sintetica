"""Texto livre do registro, normalização e 3-gramas de palavras (D-06, Q47).

Texto livre são os campos `text` do contrato, inclusive em listas e objetos; numa conversa,
também o conteúdo das mensagens. `enum`, números e datas ficam fora.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Mapping
from typing import Any

from sintetica.schema.spec import FieldSpecModel, SchemaSpecModel

SHINGLE_WORDS = 3


def _has_text(fields: Iterable[FieldSpecModel]) -> bool:
    for field in fields:
        if field.type == "text":
            return True
        if field.type == "list" and field.items is not None and _has_text([field.items]):
            return True
        if field.type == "object" and _has_text(field.fields or []):
            return True
    return False


def has_free_text(spec: SchemaSpecModel) -> bool:
    return spec.kind == "conversation" or _has_text(spec.fields)


def _walk(value: Any, field: FieldSpecModel, out: list[str]) -> None:
    if value is None:
        return
    if field.type == "text" and isinstance(value, str):
        out.append(value)
    elif field.type == "list" and field.items is not None and isinstance(value, list):
        for item in value:
            _walk(item, field.items, out)
    elif field.type == "object" and isinstance(value, Mapping):
        for sub in field.fields or []:
            _walk(value.get(sub.name), sub, out)


def free_text(record: Mapping[str, Any], spec: SchemaSpecModel) -> str:
    """Textos livres do registro unidos por espaço, na ordem do contrato."""
    out: list[str] = []
    if spec.kind == "conversation":
        for message in record.get("messages") or []:
            if isinstance(message, Mapping) and isinstance(message.get("content"), str):
                out.append(message["content"])
        labels = record.get("labels")
        if isinstance(labels, Mapping):
            for field in spec.fields:
                _walk(labels.get(field.name), field, out)
        return " ".join(out)
    for field in spec.fields:
        _walk(record.get(field.name), field, out)
    return " ".join(out)


def normalize(text: str) -> str:
    """Minúsculas, pontuação Unicode trocada por espaço, espaços únicos."""
    chars = (" " if unicodedata.category(c).startswith("P") else c for c in text.lower())
    return " ".join("".join(chars).split())


def shingles(text: str) -> frozenset[str]:
    """3-gramas de palavras do texto normalizado; menos de 3 palavras vira 1 trecho."""
    words = normalize(text).split()
    if not words:
        return frozenset()
    if len(words) < SHINGLE_WORDS:
        return frozenset({" ".join(words)})
    return frozenset(
        " ".join(words[i : i + SHINGLE_WORDS]) for i in range(len(words) - SHINGLE_WORDS + 1)
    )
