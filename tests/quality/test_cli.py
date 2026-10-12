"""Ponta a ponta pela CLI: `sintetica eval` e os códigos de saída (interfaces/eval-cli.md).

Cenários Gherkin do requirements.md e onde cada um é coberto:
- Dataset aprovado: test_approved_dataset
- Conformidade abaixo da meta: test_metrics::test_conformity_without_run_uses_intent,
  test_incomplete_lot_is_rejected
- Cópias exatas: test_metrics::test_structural_uniqueness_with_exact_copies
- Quase-duplicados por pontuação: test_near_duplicates_by_punctuation
- Contrato sem campo de texto: test_metrics::test_semantic_not_applicable_without_text
- PII real no dataset: test_metrics::test_pii_leak_and_allowlisted_fake, test_pii_never_printed
- Allowlist ausente: test_metrics::test_missing_allowlist_counts_every_finding
- Linha corrompida: test_corrupted_line
- Meta de tempo não atingida: test_metrics::test_time_target_and_unmeasured_duration
- Avaliação sem started_at: test_metrics::test_duration_not_measured
- Contrato alterado depois do lote: test_metrics::test_schema_changed_after_lot_warns
- Dataset ausente: test_error_codes
- Mascaramento indisponível: test_error_codes
- Avaliação determinística: test_report::test_report_is_deterministic
- Avaliação ao fim do lote: tests/batch/test_quality_chain.py
- Código de saída para CI: test_incomplete_lot_is_rejected
- Textos curtos e campos fixos: test_short_texts_and_fixed_fields
- Desempenho em lote grande: test_perf::test_ten_thousand_records_within_time
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sintetica.batch.lock import DatasetLock
from sintetica.batch.state import lock_path
from sintetica.quality import load_report

from .conftest import (
    CONVERSATION_DRAFT,
    CSV_DRAFT,
    EMAIL,
    cli,
    json_records,
    prepare,
    write_dataset,
    write_run,
)


def test_approved_dataset(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = prepare(project, volume=50)
    write_dataset(path, "json", json_records(50))
    write_run(path, volume=50, fmt="json")
    capsys.readouterr()
    assert cli(project, "eval", "pedidos") == 0
    out = capsys.readouterr().out
    assert out.startswith("Avaliação do dataset pedidos: APROVADO\n")
    for label in ("Conformidade: 100,0%", "Unicidade estrutural", "Unicidade semântica"):
        assert label in out
    assert "Vazamentos de PII: 0" in out and "Duração:" in out
    assert f"Relatório: {(path / 'report.md').resolve()}" in out
    assert (path / "report.json").exists()


def test_incomplete_lot_is_rejected(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = prepare(project, volume=100)
    write_dataset(path, "json", json_records(94))
    write_run(path, volume=100, fmt="json", status="incompleto")
    capsys.readouterr()
    assert cli(project, "eval", "pedidos") == 17
    out = capsys.readouterr().out
    assert "REPROVADO (falharam: conformidade)" in out
    assert "Conformidade: 94,0%" in out
    assert "Aviso: o lote terminou com status incompleto" in out


def test_near_duplicates_by_punctuation(project: Path) -> None:
    path = prepare(project, volume=2)
    write_dataset(
        path,
        "json",
        [
            {"cliente": "O cliente pediu a troca do produto ontem.", "valor": 10},
            {"cliente": "o CLIENTE, pediu a troca do produto ontem", "valor": 12},
        ],
    )
    write_run(path, volume=2, fmt="json")
    assert cli(project, "eval", "pedidos") == 17
    report = load_report(path)
    assert report is not None
    assert report.problem_indices.near_duplicates == [1]
    assert str(report.semantic_uniqueness_pct) == "50.0"
    assert report.structural_uniqueness_pct == 100


def test_short_texts_and_fixed_fields(project: Path) -> None:
    path = prepare(project, volume=3, draft=CONVERSATION_DRAFT)
    rows = [
        {"messages": [{"role": "user", "content": text}], "labels": {"sentimento": "positivo"}}
        for text in ("Bom dia", "Boa tarde", "Boa noite")
    ]
    write_dataset(path, "jsonl", rows)
    write_run(path, volume=3, fmt="jsonl")
    assert cli(project, "eval", "pedidos") == 0
    report = load_report(path)
    assert report is not None and str(report.semantic_uniqueness_pct) == "100.0"


def test_corrupted_line(project: Path) -> None:
    path = prepare(project, volume=10, draft={**CONVERSATION_DRAFT})
    good = {"messages": [{"role": "user", "content": "Oi"}], "labels": {"sentimento": "neutro"}}
    rows: list[object] = [
        {"messages": [{"role": "user", "content": f"texto {i} único"}], "labels": good["labels"]}
        for i in range(9)
    ]
    rows.insert(4, '{"messages": [')
    write_dataset(path, "jsonl", rows)
    write_run(path, volume=10, fmt="jsonl")
    assert cli(project, "eval", "pedidos") == 17
    report = load_report(path)
    assert report is not None
    assert report.problem_indices.invalid == [4] and report.valid_records == 9


def test_csv_dataset(project: Path) -> None:
    path = prepare(project, volume=2, draft=CSV_DRAFT)
    write_dataset(
        path,
        "csv",
        [["nome", "tags", "saldo"], ["Ana Lima", "a|b", "1.00"], ["Bia Reis", "", "2.50"]],
    )
    write_run(path, volume=2, fmt="csv")
    assert cli(project, "eval", "pedidos") == 0


def test_pii_never_printed(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = prepare(project, volume=1)
    write_dataset(path, "json", [{"cliente": f"Contato {EMAIL}", "valor": 10}])
    write_run(path, volume=1, fmt="json")
    capsys.readouterr()
    assert cli(project, "eval", "pedidos") == 17
    captured = capsys.readouterr()
    for text in (
        captured.out,
        captured.err,
        *(p.read_text("utf-8") for p in path.glob("report.*")),
    ):
        assert EMAIL not in text


def test_error_codes(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli(project, "eval", "pedidos") == 2
    path = prepare(project, volume=2)
    assert cli(project, "eval", "pedidos") == 18
    assert "sintetica generate pedidos" in capsys.readouterr().err
    write_dataset(path, "json", json_records(2))
    lock = DatasetLock(lock_path(path))
    assert lock.acquire()
    try:
        assert cli(project, "eval", "pedidos") == 16
    finally:
        lock.release()
    (project / ".sintetica").mkdir(exist_ok=True)
    policy = project / ".sintetica" / "policy.json"
    policy.write_text(json.dumps({"pii_custom_patterns": ["(aberto"]}), "utf-8")
    assert cli(project, "eval", "pedidos") == 9
    assert not (path / "report.json").exists()
    policy.unlink()
    (path / "output" / "dataset.json").write_text("{}", "utf-8")
    assert cli(project, "eval", "pedidos") == 18
    (path / "output" / "dataset.json").write_text("[]", "utf-8")
    (path / "schema.json").write_text("{", "utf-8")  # contrato ilegível
    assert cli(project, "eval", "pedidos") == 11
    (path / "schema.json").unlink()
    assert cli(project, "eval", "pedidos") == 11


def test_empty_dataset_is_rejected(project: Path) -> None:
    path = prepare(project, volume=5)
    write_dataset(path, "json", [])
    write_run(path, volume=5, fmt="json", status="falha_provedor")
    assert cli(project, "eval", "pedidos") == 17
    report = load_report(path)
    assert report is not None and str(report.conformity_pct) == "0.0"


def test_write_failure(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = prepare(project, volume=2)
    write_dataset(path, "json", json_records(2))

    def broken(*_: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("sintetica.quality.service.write_report", broken)
    assert cli(project, "eval", "pedidos") == 10


def test_unreadable_run_json_is_a_warning(project: Path) -> None:
    path = prepare(project, volume=2)
    write_dataset(path, "json", json_records(2))
    (path / "output" / "run.json").write_text("{", "utf-8")
    assert cli(project, "eval", "pedidos") == 0
    report = load_report(path)
    assert report is not None and any("run.json ilegível" in w for w in report.warnings)
