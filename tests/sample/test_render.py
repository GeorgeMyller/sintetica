"""Exibição da amostra (D-10)."""

from __future__ import annotations

from pathlib import Path

from sintetica.sample.render import render_records
from sintetica.schema import load_record_model

from .conftest import CSV_DRAFT, prepare


def test_csv_table_escapes_separators(project: Path) -> None:
    model = load_record_model(prepare(project, draft=CSV_DRAFT))
    lines = ['{"nome":"Ana | Bia","tags":["a","b"],"saldo":1.5}']
    table = render_records(lines, model, "csv")
    assert table[0] == "| nome | tags | saldo |"
    assert table[1] == "|---|---|---|"
    assert table[2] == "| Ana \\| Bia | a\\|b | 1.50 |"


def test_json_blocks_keep_exact_decimals(project: Path) -> None:
    model = load_record_model(prepare(project))
    out = render_records(['{"cliente":"Ana","valor":19.90}'], model, "json")
    assert out[:2] == ["Registro 1:", "```json"]
    assert '  "valor": 19.90' in out and out[-1] == "```"


def test_empty_sample(project: Path) -> None:
    model = load_record_model(prepare(project))
    assert render_records([], model, "json") == ["(nenhum registro aceito)"]
