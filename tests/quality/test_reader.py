"""Leitura do dataset final por formato (D-03)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sintetica.batch.output import convert_final
from sintetica.quality.reader import DatasetReadError, read_items
from sintetica.schema import load_record_model
from sintetica.schema.loader import read_spec

from .conftest import CSV_DRAFT, json_records, prepare, write_dataset


def _items(path: Path, fmt: str, dest: Path) -> list[tuple[int, bool, str | None]]:
    model, spec = load_record_model(path), read_spec(path)
    return [(i.index, i.record is not None, i.reason) for i in read_items(dest, fmt, model, spec)]


def test_jsonl_with_corrupted_line(project: Path) -> None:
    path = prepare(project, draft={**JSON_DRAFT_JSONL})
    rows: list[object] = [*json_records(2), '{"cliente": "quebrado"', "", json_records(1, 5)[0]]
    dest = write_dataset(path, "jsonl", rows)
    items = _items(path, "jsonl", dest)
    assert [(i, ok) for i, ok, _ in items] == [(0, True), (1, True), (2, False), (3, True)]
    assert items[2][2] == "linha não é JSON válido"


def test_json_list_and_invalid_items(project: Path) -> None:
    path = prepare(project)
    dest = write_dataset(path, "json", [*json_records(1), {"cliente": "x", "valor": 99}, 7])
    items = _items(path, "json", dest)
    assert [ok for _, ok, _ in items] == [True, False, False]
    assert items[1][2] is not None and "99" not in items[1][2]
    assert items[2][2] == "o registro não é um objeto JSON"
    dest.write_text('{"a": 1}', "utf-8")
    with pytest.raises(DatasetReadError):
        list(read_items(dest, "json", load_record_model(path), read_spec(path)))
    dest.write_text("[", "utf-8")
    with pytest.raises(DatasetReadError):
        list(read_items(dest, "json", load_record_model(path), read_spec(path)))


def test_csv_round_trip_with_lot_output(project: Path) -> None:
    path = prepare(project, draft=CSV_DRAFT)
    partial = project / "p.jsonl"
    partial.write_text(
        '{"nome":"Ana, \\"A\\"","tags":["x","y"],"saldo":1.50}\n'
        '{"nome":"Bia","tags":[],"saldo":2.00}\n',
        "utf-8",
    )
    dest = convert_final(partial, path / "output" / "dataset.csv", "csv", load_record_model(path))
    model, spec = load_record_model(path), read_spec(path)
    canon = [i.canonical for i in read_items(dest, "csv", model, spec)]
    assert canon == partial.read_text("utf-8").splitlines()


def test_csv_extra_and_missing_columns(project: Path) -> None:
    path = prepare(project, draft=CSV_DRAFT)
    dest = write_dataset(
        path,
        "csv",
        [
            ["nome", "tags", "saldo"],
            ["Ana", "a|b", "1.00", "extra"],
            ["Bia", "a"],
            ["Caio", "", ""],
        ],
    )
    items = _items(path, "csv", dest)
    assert items[0] == (0, False, "linha com colunas a mais")
    assert items[1] == (1, False, "linha com colunas a menos")
    assert items[2][1] is False  # saldo obrigatório vazio


JSON_DRAFT_JSONL = {
    "format": "jsonl",
    "fields": [
        {"name": "cliente", "type": "text"},
        {
            "name": "valor",
            "type": "decimal",
            "constraints": {"ge": 5, "le": 50, "casas_decimais": 2},
        },
    ],
}


def test_decimal_is_exact(project: Path) -> None:
    path = prepare(project)
    dest = write_dataset(path, "json", [])
    dest.write_text('[{"cliente": "Ana", "valor": 19.9}]', "utf-8")
    model, spec = load_record_model(path), read_spec(path)
    (item,) = list(read_items(dest, "json", model, spec))
    assert json.loads(item.canonical)["valor"] == 19.9
    assert item.canonical == '{"cliente":"Ana","valor":19.90}'
