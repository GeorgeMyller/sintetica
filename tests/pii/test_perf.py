"""Desempenho (RNF): scan em 10.000 registros de 1 KB em ≤ 30 s. Rode com `pytest -m perf`."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from sintetica.pii import PiiGuard

RECORDS = 10_000
RECORD_SIZE = 1024
TIME_LIMIT_S = 30.0

_PII = "CPF 529.982.247-25, ana@exemplo.com, (11) 91234-5678, 4111 1111 1111 1111, 192.168.0.1 "


def _record(i: int) -> str:
    base = f"registro {i}: " + _PII
    filler = "texto sintético comum sem dados pessoais " * 30
    return (base + filler)[:RECORD_SIZE]


@pytest.mark.perf
def test_scan_10k_records_of_1kb(tmp_path: Path) -> None:
    guard = PiiGuard.for_dataset(tmp_path, tmp_path / "policy.json")
    records = [_record(i) for i in range(RECORDS)]
    started = time.perf_counter()
    total = sum(len(guard.scan(r)) for r in records)
    elapsed = time.perf_counter() - started
    assert total == RECORDS * 5
    assert elapsed <= TIME_LIMIT_S, f"{elapsed:.1f} s"
