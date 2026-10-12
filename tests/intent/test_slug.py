"""Slug do dataset (RN-02, D-04)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from sintetica.intent.slug import MAX_SLUG, base_slug, create_dataset_dir

NOW = datetime(2026, 10, 12, 8, 30, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Pedidos de Café", "pedidos-de-cafe"),
        ("  Ação__Clientes!! 2026 ", "acao-clientes-2026"),
        ("suporte", "suporte"),
        (None, "dataset-20261012-083000"),
        ("", "dataset-20261012-083000"),
        ("😀 !!", "dataset-20261012-083000"),
    ],
)
def test_base_slug(name: str | None, expected: str) -> None:
    assert base_slug(name, NOW) == expected


def test_long_names_are_cut_without_trailing_hyphen() -> None:
    slug = base_slug("a" * 59 + " bcd", NOW)
    assert len(slug) <= MAX_SLUG and not slug.endswith("-")
    assert slug == "a" * 59


def test_collisions_get_numeric_suffix(tmp_path: Path) -> None:
    slugs = [create_dataset_dir(tmp_path, "Pedidos", NOW)[0] for _ in range(3)]
    assert slugs == ["pedidos", "pedidos-2", "pedidos-3"]
    assert all((tmp_path / s).is_dir() for s in slugs)
