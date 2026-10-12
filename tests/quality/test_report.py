"""Relatório: mesmos números no JSON e no Markdown, escopo da PII, determinismo (D-12)."""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from sintetica.quality import load_report
from sintetica.quality.report import MD_INDEX_LIMIT, render_markdown
from sintetica.quality.service import evaluate

from .conftest import EMAIL, FIXED_NOW, json_records, prepare, write_dataset, write_run


def test_json_and_markdown_have_the_same_numbers(project: Path) -> None:
    path = prepare(project, volume=40)
    records = json_records(30)
    records += [dict(r) for r in records[:5]]
    records.append({"cliente": f"Contato {EMAIL} aqui", "valor": 10})
    write_dataset(path, "json", records)
    write_run(path, volume=40, fmt="json")
    assert evaluate(project, "pedidos", clock=lambda: FIXED_NOW).code == 17
    data = json.loads((path / "report.json").read_text("utf-8"), parse_float=Decimal)
    md = (path / "report.md").read_text("utf-8")
    assert data["conformity_pct"] == Decimal("90.0")
    assert "Conformidade: 90,0%" in md
    assert (
        f"Unicidade estrutural: {str(data['structural_uniqueness_pct']).replace('.', ',')}%" in md
    )
    assert f"Vazamentos de PII: {data['pii_leaks']}" in md
    assert "## Escopo e limites da detecção de PII" in md
    assert "Tipos cobertos: cpf, cnpj, email, phone, card, ipv4, ipv6." in md
    assert md.count("\n- ") >= 6
    assert EMAIL not in md and EMAIL not in (path / "report.json").read_text("utf-8")
    assert '"conformity_pct": 90.0' in (path / "report.json").read_text("utf-8")


def test_markdown_limits_indices(project: Path) -> None:
    path = prepare(project, volume=30)
    write_dataset(path, "json", [{"cliente": "x", "valor": 99}] * 30)
    write_run(path, volume=30, fmt="json")
    evaluate(project, "pedidos", clock=lambda: FIXED_NOW)
    report = load_report(path)
    assert report is not None and len(report.problem_indices.invalid) == 30
    md = render_markdown(report)
    assert f"… ({30} no total)" in md
    assert "Inválidos: " + ", ".join(str(i) for i in range(MD_INDEX_LIMIT)) in md


def test_report_is_deterministic(project: Path) -> None:
    path = prepare(project, volume=20)
    write_dataset(path, "json", json_records(20))
    write_run(path, volume=20, fmt="json")
    evaluate(project, "pedidos", clock=lambda: FIXED_NOW)
    first = json.loads((path / "report.json").read_text("utf-8"))
    evaluate(project, "pedidos", clock=lambda: FIXED_NOW + timedelta(minutes=3))
    second = json.loads((path / "report.json").read_text("utf-8"))
    volatile = {"finished_at", "duration_min", "time_target_met"}
    assert {k: v for k, v in first.items() if k not in volatile} == {
        k: v for k, v in second.items() if k not in volatile
    }
    assert first["finished_at"] != second["finished_at"]
