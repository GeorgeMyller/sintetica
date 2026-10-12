"""Relatório da avaliação: `report.json` e `report.md` gerados do mesmo objeto (D-12, D-13)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from sintetica.fsutil import write_atomic
from sintetica.schema.formats import to_json_text

REPORT_JSON = "report.json"
REPORT_MD = "report.md"
MD_INDEX_LIMIT = 20

MetricName = Literal["conformidade", "unicidade_estrutural", "unicidade_semantica", "pii"]


class PiiCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    types: list[str]
    custom_patterns: int
    limits: list[str]


class PiiFindingOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int
    field: str
    type: str
    preview: str  # prévia mascarada, nunca o valor completo


class ProblemIndices(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invalid: list[int] = Field(default_factory=list)
    duplicates: list[int] = Field(default_factory=list)
    near_duplicates: list[int] = Field(default_factory=list)
    pii: list[int] = Field(default_factory=list)


class Report(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    verdict: Literal["APROVADO", "REPROVADO"]
    failed_metrics: list[MetricName]
    volume_requested: int
    records_read: int
    valid_records: int
    conformity_pct: Decimal
    structural_uniqueness_pct: Decimal
    semantic_uniqueness_pct: Decimal | None
    semantic_applicable: bool
    pii_leaks: int
    pii_findings: list[PiiFindingOut]
    pii_coverage: PiiCoverage
    duration_min: Decimal | None
    time_target_met: bool | None
    run_status: str | None
    schema_version: str
    warnings: list[str]
    problem_indices: ProblemIndices
    finished_at: str


def report_paths(dataset_dir: Path) -> tuple[Path, Path]:
    return dataset_dir / REPORT_JSON, dataset_dir / REPORT_MD


def load_report(dataset_dir: Path) -> Report | None:
    path = dataset_dir / REPORT_JSON
    if not path.exists():
        return None
    return Report.model_validate(json.loads(path.read_text("utf-8"), parse_float=Decimal))


def num(value: Decimal) -> str:
    """Decimal com vírgula para leitura (`96,0`)."""
    return f"{value:f}".replace(".", ",")


def _ok(flag: bool) -> str:
    return "ok" if flag else "falhou"


def metric_lines(report: Report) -> list[str]:
    """Linhas curtas das métricas, comuns ao chat e ao Markdown (D-14)."""
    failed = set(report.failed_metrics)
    semantic = (
        "não aplicável (contrato sem texto livre)"
        if report.semantic_uniqueness_pct is None
        else f"{num(report.semantic_uniqueness_pct)}% (meta ≥ 90%)"
    )
    if report.duration_min is None:
        duration = "não medida"
    elif report.time_target_met is None:
        duration = f"{num(report.duration_min)} min"
    else:
        state = "atingida" if report.time_target_met else "não atingida"
        duration = f"{num(report.duration_min)} min (meta < 10 min: {state})"
    return [
        f"Conformidade: {num(report.conformity_pct)}% (meta ≥ 95%) "
        f"[{_ok('conformidade' not in failed)}]",
        f"Unicidade estrutural: {num(report.structural_uniqueness_pct)}% (meta ≥ 90%) "
        f"[{_ok('unicidade_estrutural' not in failed)}]",
        f"Unicidade semântica: {semantic} [{_ok('unicidade_semantica' not in failed)}]",
        f"Vazamentos de PII: {report.pii_leaks} (meta 0) [{_ok('pii' not in failed)}]",
        f"Duração: {duration}",
    ]


def headline(report: Report) -> str:
    tail = f" (falharam: {', '.join(report.failed_metrics)})" if report.failed_metrics else ""
    return f"Avaliação do dataset {report.slug}: {report.verdict}{tail}"


def _indices(label: str, values: list[int]) -> str:
    shown = ", ".join(str(v) for v in values[:MD_INDEX_LIMIT])
    more = f" … ({len(values)} no total)" if len(values) > MD_INDEX_LIMIT else ""
    return f"- {label}: {shown or 'nenhum'}{more}"


def render_markdown(report: Report) -> str:
    lines = [
        f"# Relatório de qualidade: {report.slug}",
        "",
        f"**Veredito:** {report.verdict}",
        f"**Emitido em:** {report.finished_at}",
        f"**Contrato:** {report.schema_version}",
        f"**Status do lote:** {report.run_status or 'sem run.json'}",
        f"**Registros:** {report.records_read} lidos, {report.valid_records} válidos, "
        f"{report.volume_requested} pedidos",
        "",
        "## Métricas",
        "",
        *[f"- {line}" for line in metric_lines(report)],
        "",
        "## Avisos",
        "",
        *([f"- {w}" for w in report.warnings] or ["- nenhum"]),
        "",
        "## Registros com problema",
        "",
        "Índices a partir de 0 (posição do registro no dataset).",
        "",
        _indices("Inválidos", report.problem_indices.invalid),
        _indices("Duplicados exatos", report.problem_indices.duplicates),
        _indices("Quase-duplicados", report.problem_indices.near_duplicates),
        _indices("Com PII", report.problem_indices.pii),
        "",
    ]
    if report.pii_findings:
        lines += ["| Índice | Campo | Tipo | Prévia |", "|--------|-------|------|--------|"]
        for f in report.pii_findings[:MD_INDEX_LIMIT]:
            lines.append(f"| {f.index} | `{f.field}` | {f.type} | `{f.preview}` |")
        if len(report.pii_findings) > MD_INDEX_LIMIT:
            lines.append(f"\n{len(report.pii_findings)} achados no total; lista completa no JSON.")
        lines.append("")
    cov = report.pii_coverage
    lines += [
        "## Escopo e limites da detecção de PII",
        "",
        f"Tipos cobertos: {', '.join(cov.types)}.",
        f"Padrões extras da política: {cov.custom_patterns}.",
        "A métrica conta só o que esses detectores encontram (Q9). Limites conhecidos:",
        "",
        *[f"- {limit}" for limit in cov.limits],
        "",
    ]
    return "\n".join(lines)


def write_report(dataset_dir: Path, report: Report) -> tuple[Path, Path]:
    json_path, md_path = report_paths(dataset_dir)
    write_atomic(json_path, to_json_text(report.model_dump(), indent=2) + "\n")
    write_atomic(md_path, render_markdown(report))
    return json_path, md_path
