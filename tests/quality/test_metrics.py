"""Métricas: conformidade, unicidades, PII, duração e veredito (D-04 a D-11)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sintetica.quality import load_report
from sintetica.quality.metrics import duration_min, pct, time_target_met, verdict
from sintetica.quality.service import evaluate

from .conftest import (
    EMAIL,
    FIXED_NOW,
    NUMERIC_DRAFT,
    json_records,
    prepare,
    register_fake,
    write_dataset,
    write_run,
)


def _eval(project: Path) -> int:
    return evaluate(project, "pedidos", clock=lambda: FIXED_NOW).code


def test_pct_and_verdict_order() -> None:
    assert pct(96, 100) == Decimal("96.0")
    assert pct(2, 3) == Decimal("66.7")
    assert pct(1, 0) == Decimal("0.0")
    assert verdict(Decimal(94), Decimal(80), Decimal(10), 1) == (
        "REPROVADO",
        ["conformidade", "unicidade_estrutural", "unicidade_semantica", "pii"],
    )
    assert verdict(Decimal(95), Decimal(90), None, 0) == ("APROVADO", [])


def test_duration_and_time_target() -> None:
    end = datetime(2026, 10, 12, 12, 12, 0, tzinfo=timezone.utc)
    assert duration_min("2026-10-12T12:00:00Z", end) == Decimal("12.0")
    assert duration_min("2026-10-12T11:52:36Z", end) == Decimal("19.4")
    assert duration_min("", end) is None and duration_min("ontem", end) is None
    assert time_target_met(50, Decimal("12.0")) is False
    assert time_target_met(50, Decimal("9.9")) is True
    assert time_target_met(150, Decimal("1")) is None
    assert time_target_met(50, None) is None


def test_conformity_uses_run_volume_and_warns(project: Path) -> None:
    path = prepare(project, volume=100)
    write_run(path, volume=50, fmt="json", status="incompleto")
    write_dataset(path, "json", json_records(48))
    assert _eval(project) == 0
    report = load_report(path)
    assert report is not None
    assert report.volume_requested == 50 and report.conformity_pct == Decimal("96.0")
    assert report.run_status == "incompleto"
    assert any("o lote pediu 50" in w for w in report.warnings)
    assert any("status incompleto" in w for w in report.warnings)


def test_conformity_without_run_uses_intent(project: Path) -> None:
    path = prepare(project, volume=100)
    write_dataset(path, "json", [*json_records(94), {"cliente": "x", "valor": 99}])
    assert _eval(project) == 17
    report = load_report(path)
    assert report is not None
    assert report.conformity_pct == Decimal("94.0") and report.failed_metrics == ["conformidade"]
    assert report.problem_indices.invalid == [94]
    assert report.run_status is None and any("sem run.json" in w for w in report.warnings)


def test_structural_uniqueness_with_exact_copies(project: Path) -> None:
    path = prepare(project, volume=100)
    records = json_records(95)
    write_dataset(path, "json", records + records[:5])
    write_run(path, volume=100, fmt="json")
    assert _eval(project) == 0
    report = load_report(path)
    assert report is not None
    assert report.structural_uniqueness_pct == Decimal("95.0")
    assert report.problem_indices.duplicates == [95, 96, 97, 98, 99]
    # As cópias exatas também são quase-duplicadas (texto igual).
    assert report.problem_indices.near_duplicates == [95, 96, 97, 98, 99]


def test_semantic_not_applicable_without_text(project: Path) -> None:
    path = prepare(project, volume=3, draft=NUMERIC_DRAFT)
    write_dataset(path, "jsonl", [{"idade": 1, "ativo": True}, {"idade": 1, "ativo": True}])
    write_run(path, volume=2, fmt="jsonl")
    assert _eval(project) == 17
    report = load_report(path)
    assert report is not None
    assert report.semantic_uniqueness_pct is None and not report.semantic_applicable
    assert report.failed_metrics == ["unicidade_estrutural"]


def test_pii_leak_and_allowlisted_fake(project: Path) -> None:
    path = prepare(project, volume=3)
    fake = register_fake(path, project, f"Contato {EMAIL}")
    assert EMAIL not in fake
    records = [
        {"cliente": f"{fake} pedido um dois", "valor": 10},
        {"cliente": f"Real {EMAIL} três quatro", "valor": 11},
        {"cliente": "sem dado pessoal algum aqui", "valor": 12},
    ]
    write_dataset(path, "json", records)
    write_run(path, volume=3, fmt="json")
    assert _eval(project) == 17
    report = load_report(path)
    assert report is not None
    assert report.pii_leaks == 1 and report.failed_metrics == ["pii"]
    (finding,) = report.pii_findings
    assert (finding.index, finding.field, finding.type) == (1, "cliente", "email")
    assert EMAIL not in finding.preview
    assert not any("allowlist" in w for w in report.warnings)


def test_missing_allowlist_counts_every_finding(project: Path) -> None:
    path = prepare(project, volume=1)
    fake = register_fake(path, project, f"Contato {EMAIL}")
    (path / ".pii_allowlist").unlink()
    write_dataset(path, "json", [{"cliente": f"{fake} pedido", "valor": 10}])
    write_run(path, volume=1, fmt="json")
    assert _eval(project) == 17
    report = load_report(path)
    assert report is not None and report.pii_leaks == 1
    assert any("allowlist" in w for w in report.warnings)


def test_pii_in_invalid_line_is_counted(project: Path) -> None:
    path = prepare(project, volume=1)
    write_dataset(path, "json", [{"cliente": EMAIL, "valor": 99}])
    write_run(path, volume=1, fmt="json")
    assert _eval(project) == 17
    report = load_report(path)
    assert report is not None and report.pii_leaks == 1
    assert report.pii_findings[0].field == "registro"


def test_time_target_and_unmeasured_duration(project: Path) -> None:
    path = prepare(project, volume=2, started_minutes_ago=12)
    write_dataset(path, "json", json_records(2))
    write_run(path, volume=2, fmt="json")
    assert _eval(project) == 0  # a meta de tempo não entra no veredito
    report = load_report(path)
    assert report is not None
    assert report.duration_min == Decimal("12.0") and report.time_target_met is False


def test_duration_not_measured(tmp_path: Path) -> None:
    path = prepare(tmp_path, volume=2, started_minutes_ago=None)
    write_dataset(path, "json", json_records(2))
    write_run(path, volume=2, fmt="json")
    assert evaluate(tmp_path, "pedidos").code == 0
    report = load_report(path)
    assert report is not None and report.duration_min is None
    assert report.time_target_met is None


def test_schema_changed_after_lot_warns(project: Path) -> None:
    path = prepare(project, volume=2)
    write_dataset(path, "json", json_records(2))
    write_run(path, volume=2, fmt="json", schema="versao-antiga")
    assert _eval(project) == 0
    report = load_report(path)
    assert report is not None
    assert any("contrato mudou" in w for w in report.warnings)
