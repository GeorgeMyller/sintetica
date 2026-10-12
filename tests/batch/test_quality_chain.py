"""Avaliação ao fim do lote (feature 007, Q49): primeiro plano, background e `status`."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from sintetica.batch import service
from sintetica.batch.lock import is_locked
from sintetica.batch.state import lock_path

from .conftest import Factory, FakeProvider, OllamaServer, counter_responder, dataset, prepare


def test_foreground_lot_ends_with_evaluation(project: Path) -> None:
    prepare(project, volume=20)
    result = service.generate(
        project, "pedidos", provider_factory=Factory(FakeProvider(counter_responder()))
    )
    assert result.code == 0
    assert "Avaliação do dataset pedidos: APROVADO" in result.out
    assert not any("Próximo passo" in line for line in result.out)
    report = json.loads((dataset(project) / "report.json").read_text("utf-8"))
    assert report["verdict"] == "APROVADO" and report["run_status"] == "concluido"
    shown = service.status(project, "pedidos")
    assert shown.out[-1].startswith("Avaliação: APROVADO (")


def test_lot_code_does_not_follow_the_verdict(project: Path) -> None:
    prepare(project, volume=30)
    failing = FakeProvider(counter_responder(fail_at=2))
    result = service.generate(project, "pedidos", provider_factory=Factory(failing))
    assert result.code == 12  # falha_provedor, não 17
    assert any("REPROVADO (falharam: conformidade)" in line for line in result.out)
    report = json.loads((dataset(project) / "report.json").read_text("utf-8"))
    assert report["run_status"] == "falha_provedor"


def test_evaluation_error_is_a_warning(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(project, volume=10)

    def broken(*_: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("sintetica.quality.service.write_report", broken)
    result = service.generate(
        project, "pedidos", provider_factory=Factory(FakeProvider(counter_responder()))
    )
    assert result.code == 0
    assert result.out[-1].startswith("Aviso: avaliação não concluída")
    assert "uv run sintetica eval pedidos" in result.out[-1]
    assert not (dataset(project) / "report.json").exists()
    assert not any(line.startswith("Avaliação:") for line in service.status(project, "pedidos").out)


def test_status_with_unreadable_report(project: Path) -> None:
    prepare(project, volume=10)
    assert (
        service.generate(
            project, "pedidos", provider_factory=Factory(FakeProvider(counter_responder()))
        ).code
        == 0
    )
    (dataset(project) / "report.json").write_text("{", "utf-8")
    assert "report.json ilegível" in service.status(project, "pedidos").out[-1]


def test_background_lot_writes_the_report(project: Path, ollama: OllamaServer) -> None:
    prepare(project, volume=150)
    assert service.generate(project, "pedidos").code == 0
    report = dataset(project) / "report.json"
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if report.exists() and not is_locked(lock_path(dataset(project))):
            break
        time.sleep(0.1)
    data = json.loads(report.read_text("utf-8"))
    assert data["records_read"] == 150 and data["verdict"] == "APROVADO"
    log = (dataset(project) / "output" / "worker.log").read_text("utf-8")
    assert "Avaliação do dataset pedidos: APROVADO" in log
