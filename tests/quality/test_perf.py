"""Desempenho: 10.000 registros de cerca de 1 KB avaliados em ≤ 120 s (RNF-04, R-01, R-02).

Fora da suíte padrão. Rode com: uv run pytest -m perf tests/quality/test_perf.py
"""

from __future__ import annotations

import random
import time
from pathlib import Path

import pytest

from sintetica.quality import load_report
from sintetica.quality.service import evaluate

from .conftest import WORDS, prepare, write_dataset, write_run

LIMIT_S = 120


@pytest.mark.perf
def test_ten_thousand_records_within_time(project: Path) -> None:
    path = prepare(project, volume=10)
    rng = random.Random(7)
    vocab = [f"{w}{i}" for w in WORDS for i in range(40)]
    template = rng.sample(vocab, 60)  # trecho comum: textos parecidos, pior caso do prefixo
    records: list[dict[str, object]] = []
    for i in range(10_000):
        words = template[:40] + rng.sample(vocab, 120)
        if i % 50 == 0 and i:
            words = str(records[i - 1]["cliente"]).split()  # cópias para achar pares
        records.append({"cliente": " ".join(words), "valor": 5 + i % 40})
    write_dataset(path, "json", records)
    write_run(path, volume=10_000, fmt="json")
    start = time.monotonic()
    result = evaluate(project, "pedidos")
    elapsed = time.monotonic() - start
    assert result.code in (0, 17)
    assert elapsed <= LIMIT_S, elapsed
    report = load_report(path)
    assert report is not None and report.records_read == 10_000
    assert len(report.problem_indices.near_duplicates) >= 199
    print(f"avaliação de 10.000 registros: {elapsed:.1f} s")
