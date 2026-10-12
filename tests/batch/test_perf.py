"""Desempenho: 10.000 registros de cerca de 1 KB com memória ≤ 500 MB (RNF de memória, R-07).

Fora da suíte padrão. Rode com: uv run pytest -m perf tests/batch/test_perf.py
"""

from __future__ import annotations

import json
import tracemalloc
from decimal import Decimal
from pathlib import Path

import pytest

from sintetica.batch import service
from sintetica.batch.service import _execute
from sintetica.providers.domain import GenerationRequest, GenerationResult

from .conftest import Factory, FakeProvider, dataset, prepare, run_state

LIMIT_BYTES = 500 * 1024 * 1024


@pytest.mark.perf
def test_ten_thousand_records_within_memory(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(project, volume=100)
    intent_file = dataset(project) / "intent.json"
    intent = json.loads(intent_file.read_text("utf-8"))
    intent["volume"] = 10_000
    intent_file.write_text(json.dumps(intent), "utf-8")
    filler = "x" * 960
    counter = {"next": 0}

    def respond(request: GenerationRequest, n: int) -> GenerationResult:
        start = counter["next"]
        counter["next"] += request.n_records
        records = [
            {"cliente": f"Cliente {i} {filler}", "valor": 5 + (i % 40)}
            for i in range(start, start + request.n_records)
        ]
        return GenerationResult(tuple(records), 1, 1, Decimal("0"), "fake")

    # Primeiro plano no próprio processo, para medir a memória do motor.
    def foreground(ctx: object, state: object, lock: object, spawner: object, out: list[str]):  # type: ignore[no-untyped-def]
        return _execute(ctx, state, Factory(FakeProvider(respond)), None, out)  # type: ignore[arg-type]

    monkeypatch.setattr(service, "_launch_background", foreground)
    tracemalloc.start()
    result = service.generate(project, "pedidos", provider_factory=Factory(FakeProvider(respond)))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert result.code == 0, result.err
    assert peak <= LIMIT_BYTES
    state = run_state(project)
    assert state.accepted == 10_000 and state.status == "concluido"
    seen: set[str] = set()
    with (dataset(project) / "output" / "dataset.json").open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("{"):
                seen.add(line.rstrip(",\n"))
    assert len(seen) == 10_000
