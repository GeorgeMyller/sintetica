"""Orquestração de `sintetica eval` e da avaliação ao fim do lote (interfaces/eval-cli.md)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from sintetica.batch.lock import is_locked
from sintetica.batch.state import (
    RunState,
    RunStateError,
    dataset_path,
    load_run_state,
    lock_path,
)
from sintetica.command import cli_command
from sintetica.intent import IntentError, IntentModel, load_intent_model
from sintetica.pii import PiiGuard, PolicyError
from sintetica.pii.domain import PiiFinding
from sintetica.providers.policy import POLICY_RELATIVE_PATH
from sintetica.quality.metrics import (
    collect,
    duration_min,
    pct,
    time_target_met,
    verdict,
)
from sintetica.quality.reader import DatasetReadError, read_items
from sintetica.quality.report import (
    PiiCoverage,
    PiiFindingOut,
    ProblemIndices,
    Report,
    headline,
    metric_lines,
    write_report,
)
from sintetica.quality.text import has_free_text
from sintetica.sample.service import CommandResult
from sintetica.schema import GeneratedCodeError, SchemaNotFoundError, load_record_model
from sintetica.schema.loader import read_spec
from sintetica.schema.spec import SchemaSpecModel
from sintetica.schema.version import schema_version

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_MASKING = 9
EXIT_WRITE = 10
EXIT_CONTRACT = 11
EXIT_BUSY = 16
EXIT_REJECTED = 17
EXIT_NO_DATASET = 18

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _Fail(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class _Ctx:
    slug: str
    dataset: Path
    intent: IntentModel
    spec: SchemaSpecModel
    model: type[BaseModel]
    version: str
    run: RunState | None
    warnings: list[str]


def _context(project: Path, slug: str, check_lock: bool) -> _Ctx:
    """Pré-condições na ordem de D-02."""
    dataset = project / "datasets" / slug
    if not dataset.is_dir():
        raise _Fail(EXIT_USAGE, f"dataset inexistente: datasets/{slug}; inicie com sintetica start")
    try:
        intent = load_intent_model(dataset)
    except IntentError as exc:
        raise _Fail(EXIT_USAGE, str(exc)) from exc
    rebuild = f"rode: {cli_command()} schema build {slug}"
    try:
        spec = read_spec(dataset)
        model = load_record_model(dataset)
    except SchemaNotFoundError as exc:
        raise _Fail(EXIT_CONTRACT, f"sem contrato; {rebuild}") from exc
    except (GeneratedCodeError, OSError, ValueError) as exc:
        raise _Fail(EXIT_CONTRACT, f"contrato ilegível; {rebuild}") from exc
    if check_lock and is_locked(lock_path(dataset)):
        raise _Fail(
            EXIT_BUSY,
            f"o lote ainda está em andamento; acompanhe com: {cli_command()} status {slug}",
        )
    warnings: list[str] = []
    try:
        run = load_run_state(dataset)
    except RunStateError:
        run = None
        warnings.append("run.json ilegível: o status do lote não foi considerado")
    return _Ctx(slug, dataset, intent, spec, model, schema_version(spec), run, warnings)


def _leaks(ctx: _Ctx, project: Path) -> tuple[PiiGuard, Callable[[str, str], list[PiiFinding]]]:
    try:
        guard = PiiGuard.for_dataset(ctx.dataset, project / POLICY_RELATIVE_PATH)
    except PolicyError as exc:
        raise _Fail(
            EXIT_MASKING, f"detecção de PII indisponível: {exc}; nenhum relatório foi gravado"
        ) from exc

    def leaks(text: str, path: str) -> list[PiiFinding]:
        try:
            return guard.leaks(text, field=path)
        except OSError as exc:
            raise _Fail(EXIT_MASKING, f"detecção de PII indisponível: {exc.strerror}") from exc

    return guard, leaks


def _volume(ctx: _Ctx) -> int:
    """`volume_requested` de `run.json`; sem ele, o volume da intenção (D-04)."""
    if ctx.run is not None:
        if ctx.intent.volume is not None and ctx.intent.volume != ctx.run.volume_requested:
            ctx.warnings.append(
                f"a intenção pede {ctx.intent.volume} registros; o lote pediu "
                f"{ctx.run.volume_requested} (usado na conformidade)"
            )
        return ctx.run.volume_requested
    if ctx.intent.volume is None:
        raise _Fail(
            EXIT_USAGE, f"volume indefinido na intenção; rode sintetica intent set {ctx.slug}"
        )
    return ctx.intent.volume


def _evaluate(project: Path, slug: str, check_lock: bool, clock: Clock) -> Report:
    ctx = _context(project, slug, check_lock)
    path = dataset_path(ctx.dataset, ctx.spec.format)
    if not path.exists():
        raise _Fail(
            EXIT_NO_DATASET,
            f"dataset final ausente: {path}; gere com {cli_command()} generate {slug} "
            "(ou --resume, se o lote parou)",
        )
    guard, leaks = _leaks(ctx, project)
    volume = _volume(ctx)
    if ctx.run is not None:
        if ctx.run.status != "concluido":
            ctx.warnings.append(f"o lote terminou com status {ctx.run.status}")
        if ctx.run.schema_version != ctx.version:
            ctx.warnings.append(
                "o contrato mudou depois do lote; a avaliação usou o contrato atual"
            )
    else:
        ctx.warnings.append("sem run.json: o status do lote é desconhecido")
    if not guard.allowlist_available:
        ctx.warnings.append(
            "allowlist de valores falsos ausente: todo achado de PII conta como vazamento"
        )
    try:
        stats = collect(read_items(path, ctx.spec.format, ctx.model, ctx.spec), ctx.spec, leaks)
    except DatasetReadError as exc:
        raise _Fail(
            EXIT_NO_DATASET, f"dataset final ilegível: {exc}; gere de novo com --new"
        ) from exc
    except OSError as exc:
        raise _Fail(EXIT_NO_DATASET, f"dataset final ilegível: {exc.strerror}") from exc
    conformity = pct(min(stats.valid, volume), volume)
    structural = pct(stats.records_read - len(stats.duplicates), stats.records_read)
    applicable = has_free_text(ctx.spec)
    semantic = (
        pct(stats.with_text - len(stats.near_duplicates), stats.with_text) if applicable else None
    )
    result, failed = verdict(conformity, structural, semantic, len(stats.pii))
    finished = clock()
    duration = duration_min(ctx.intent.started_at, finished)
    coverage = guard.coverage()
    return Report(
        slug=slug,
        verdict=result,
        failed_metrics=failed,
        volume_requested=volume,
        records_read=stats.records_read,
        valid_records=stats.valid,
        conformity_pct=conformity,
        structural_uniqueness_pct=structural,
        semantic_uniqueness_pct=semantic,
        semantic_applicable=applicable,
        pii_leaks=len(stats.pii),
        pii_findings=[
            PiiFindingOut(index=h.index, field=h.field, type=h.type, preview=h.preview)
            for h in stats.pii
        ],
        pii_coverage=PiiCoverage(
            types=list(coverage.types),
            custom_patterns=coverage.custom_patterns,
            limits=list(coverage.limits),
        ),
        duration_min=duration,
        time_target_met=time_target_met(volume, duration),
        run_status=ctx.run.status if ctx.run is not None else None,
        schema_version=ctx.version,
        warnings=ctx.warnings,
        problem_indices=ProblemIndices(
            invalid=stats.invalid,
            duplicates=stats.duplicates,
            near_duplicates=stats.near_duplicates,
            pii=sorted({h.index for h in stats.pii}),
        ),
        finished_at=finished.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _lines(report: Report, md_path: Path) -> list[str]:
    return [
        headline(report),
        *[f"  {line}" for line in metric_lines(report)],
        *[f"Aviso: {w}" for w in report.warnings],
        f"Relatório: {md_path.resolve()}",
    ]


def _run(project: Path, slug: str, check_lock: bool, clock: Clock) -> tuple[int, list[str]]:
    report = _evaluate(project, slug, check_lock, clock)
    try:
        _, md_path = write_report(project / "datasets" / slug, report)
    except OSError as exc:
        raise _Fail(EXIT_WRITE, f"não foi possível gravar o relatório: {exc.strerror}") from exc
    code = EXIT_OK if report.verdict == "APROVADO" else EXIT_REJECTED
    return code, _lines(report, md_path)


def evaluate(project: Path, slug: str, *, clock: Clock | None = None) -> CommandResult:
    """`sintetica eval <slug>`: 0 em APROVADO, 17 em REPROVADO (Q48)."""
    try:
        code, lines = _run(project, slug, True, clock or _utc_now)
    except _Fail as fail:
        return CommandResult(fail.code, err=[str(fail)])
    return CommandResult(code, out=lines)


def evaluate_after_lot(project: Path, slug: str, *, clock: Clock | None = None) -> list[str]:
    """Avaliação no fim do lote, dentro da trava dele (Q49). Erro vira aviso, nunca exceção."""
    try:
        _, lines = _run(project, slug, False, clock or _utc_now)
    except _Fail as fail:
        return [f"Aviso: avaliação não concluída: {fail}; rode: {cli_command()} eval {slug}"]
    return lines
