"""Arquivo parcial, retomada e conversão final (D-12, D-13, D-19)."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest

from sintetica.batch.output import append_block, convert_final, load_partial
from sintetica.batch.review import DedupIndex
from sintetica.schema import load_record_model

from .conftest import CSV_DRAFT, prepare

LINES = ['{"cliente":"Ana","valor":10.00}', '{"cliente":"Bia, \\"B\\"","valor":20.50}']


def test_append_is_durable_and_skips_empty_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    synced: list[int] = []
    real_fsync = os.fsync

    def counting_fsync(fd: int) -> None:
        synced.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", counting_fsync)
    path = tmp_path / "out" / "p.jsonl"
    append_block(path, [])
    assert not path.exists() and synced == []
    append_block(path, LINES[:1])
    append_block(path, LINES[1:])
    assert path.read_text("utf-8").splitlines() == LINES
    assert len(synced) == 2


def test_write_error_truncates_to_previous_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "p.jsonl"
    append_block(path, LINES[:1])
    calls = {"n": 0}
    real_fsync = os.fsync

    def failing_fsync(fd: int) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError(28, "No space left on device")
        real_fsync(fd)

    monkeypatch.setattr(os, "fsync", failing_fsync)
    with pytest.raises(OSError):
        append_block(path, LINES[1:])
    assert path.read_text("utf-8").splitlines() == LINES[:1]


def test_torn_last_line_is_dropped(tmp_path: Path) -> None:
    path = tmp_path / "p.jsonl"
    path.write_bytes((LINES[0] + "\n" + LINES[1][:10]).encode("utf-8"))
    index = DedupIndex()
    assert load_partial(path, index) == 1
    assert path.read_text("utf-8") == LINES[0] + "\n"
    assert load_partial(tmp_path / "nada.jsonl", DedupIndex()) == 0


def test_convert_json_and_jsonl(project: Path) -> None:
    model = load_record_model(prepare(project))
    src = project / "p.jsonl"
    append_block(src, LINES)
    as_json = convert_final(src, project / "out" / "dataset.json", "json", model)
    text = as_json.read_text("utf-8")
    assert json.loads(text) == [json.loads(line) for line in LINES]
    assert '"valor":20.50' in text  # decimal exato
    as_jsonl = convert_final(src, project / "out" / "dataset.jsonl", "jsonl", model)
    assert as_jsonl.read_text("utf-8").splitlines() == LINES
    empty = convert_final(project / "vazio.jsonl", project / "out" / "e.json", "json", model)
    assert json.loads(empty.read_text("utf-8")) == []
    assert [p.name for p in (project / "out").iterdir() if p.name.startswith(".tmp-")] == []


def test_convert_csv_follows_rfc_4180(project: Path) -> None:
    model = load_record_model(prepare(project, draft=CSV_DRAFT))
    src = project / "p.jsonl"
    append_block(
        src,
        [
            '{"nome":"Ana, \\"A\\"","tags":["x","y"],"saldo":1.5}',
            '{"nome":"Bia","tags":[],"saldo":2}',
        ],
    )
    dest = convert_final(src, project / "dataset.csv", "csv", model)
    raw = dest.read_bytes()
    assert raw.startswith(b"nome,tags,saldo\r\n")
    assert b'"Ana, ""A""",x|y,1.50\r\n' in raw
    with dest.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows == [["nome", "tags", "saldo"], ['Ana, "A"', "x|y", "1.50"], ["Bia", "", "2.00"]]
