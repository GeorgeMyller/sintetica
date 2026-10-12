"""Percurso da definição com caminhos legíveis em notação de ponto."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from sintetica.schema.spec import FieldSpecModel


def walk(
    fields: Sequence[FieldSpecModel], prefix: str = ""
) -> Iterator[tuple[str, FieldSpecModel, bool]]:
    """Gera (caminho, campo, é_item_de_lista) em pré-ordem. Itens aparecem como `nome[]`."""
    for field in fields:
        path = f"{prefix}.{field.name}" if prefix else field.name
        yield path, field, False
        yield from _children(path, field)


def _children(path: str, field: FieldSpecModel) -> Iterator[tuple[str, FieldSpecModel, bool]]:
    if field.items is not None:
        item_path = f"{path}[]"
        yield item_path, field.items, True
        yield from _children(item_path, field.items)
    if field.fields is not None:
        yield from walk(field.fields, path)


def count_fields(fields: Sequence[FieldSpecModel]) -> int:
    """Conta campos declarados, inclusive aninhados em objetos; itens de lista não contam."""
    return sum(1 for _, _, is_item in walk(fields) if not is_item)
