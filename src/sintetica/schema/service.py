"""Orquestração de `sintetica schema build | show | approve` (interfaces/schema-cli.md)."""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from sintetica.command import cli_command
from sintetica.schema.checks import check_spec
from sintetica.schema.codegen import generate_code
from sintetica.schema.csvflat import flatten_for_csv
from sintetica.schema.intent import IntentError, default_spec, load_intent
from sintetica.schema.loader import (
    RECORD_SCHEMA_JSON,
    SCHEMA_JSON,
    SCHEMA_PY,
    GeneratedCodeError,
    export_json_schema,
    header_version,
    import_record,
)
from sintetica.schema.names import normalize_names
from sintetica.schema.render import diff_specs, render_table
from sintetica.schema.spec import SchemaIssue, SchemaSpecModel, parse_spec
from sintetica.schema.state import (
    MAX_ROUNDS,
    approved,
    load_state,
    next_state,
    save_state,
    write_atomic,
)
from sintetica.schema.version import pretty_json, schema_version

DRAFT_JSON = "schema.draft.json"
ERRORS_LOG = "errors.log"

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INVALID_SPEC = 6
EXIT_INVALID_CODE = 7


@dataclass
class CommandResult:
    code: int
    out: list[str] = field(default_factory=list)
    err: list[str] = field(default_factory=list)


def _dataset(project_dir: Path, slug: str) -> Path | None:
    path = project_dir / "datasets" / slug
    return path if path.is_dir() else None


def _missing_dataset(slug: str) -> CommandResult:
    return CommandResult(
        EXIT_USAGE, err=[f"dataset inexistente: datasets/{slug}; rode /sintetica-start"]
    )


def _invalid(issues: list[SchemaIssue]) -> CommandResult:
    lines = [f"definição inválida ({len(issues)} problema(s)):"]
    lines.extend(f"  {issue}" for issue in issues)
    return CommandResult(EXIT_INVALID_SPEC, err=lines)


def _log_error(dataset: Path, version: str, exc: BaseException) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    with (dataset / ERRORS_LOG).open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] schema_version {version}\n{exc}\n{trace}\n")


def _read_existing(dataset: Path) -> SchemaSpecModel | None:
    path = dataset / SCHEMA_JSON
    if not path.exists():
        return None
    try:
        return SchemaSpecModel.model_validate(json.loads(path.read_text("utf-8")))
    except (ValueError, ValidationError):
        return None


def _prepare(dataset: Path) -> tuple[SchemaSpecModel, list[str], bool] | CommandResult:
    """Definição final (normalizada e, em CSV, plana), avisos e modo Expresso."""
    try:
        intent = load_intent(dataset)
    except IntentError as exc:
        return CommandResult(EXIT_USAGE, err=[str(exc)])
    warnings: list[str] = []
    draft = dataset / DRAFT_JSON
    if draft.exists():
        try:
            data = json.loads(draft.read_text("utf-8"))
        except json.JSONDecodeError as exc:
            return _invalid([SchemaIssue(DRAFT_JSON, f"JSON inválido: {exc.msg}")])
        parsed = parse_spec(data)
        if isinstance(parsed, list):
            return _invalid(parsed)
        spec = parsed
    elif not intent.structure_defined:
        spec = default_spec(intent.format)
        warnings.append("estrutura indefinida: contrato com 1 campo 'descricao' a definir")
    else:
        return CommandResult(
            EXIT_USAGE, err=[f"sem {DRAFT_JSON}: o agente precisa gravar o rascunho do contrato"]
        )
    if spec.format != intent.format:
        return _invalid(
            [SchemaIssue("format", f"'{spec.format}' difere da intenção ('{intent.format}')")]
        )
    issues = check_spec(spec)
    if issues:
        return _invalid(issues)
    spec, renamed = normalize_names(spec)
    warnings.extend(renamed)
    if spec.format == "csv":
        flat = flatten_for_csv(spec)
        if isinstance(flat, list):
            return _invalid(flat)
        spec, csv_warnings = flat
        spec, renamed = normalize_names(spec)
        warnings.extend(csv_warnings + renamed)
    return spec, warnings, intent.mode == "expresso"


def build(project_dir: Path, slug: str) -> CommandResult:
    dataset = _dataset(project_dir, slug)
    if dataset is None:
        return _missing_dataset(slug)
    prepared = _prepare(dataset)
    if isinstance(prepared, CommandResult):
        return prepared
    spec, warnings, express = prepared
    version = schema_version(spec)

    staged = dataset / ".schema.staged.py"
    try:
        staged.write_text(generate_code(spec, version), "utf-8")
        json_schema = export_json_schema(import_record(staged, version))
    except GeneratedCodeError as exc:
        staged.unlink(missing_ok=True)
        _log_error(dataset, version, exc)
        return CommandResult(
            EXIT_INVALID_CODE,
            err=[f"o código gerado falhou na validação; detalhes em {dataset / ERRORS_LOG}"],
        )

    previous = _read_existing(dataset)
    write_atomic(dataset / SCHEMA_JSON, pretty_json(spec))
    staged.replace(dataset / SCHEMA_PY)
    write_atomic(
        dataset / RECORD_SCHEMA_JSON, json.dumps(json_schema, ensure_ascii=False, indent=2) + "\n"
    )
    state = next_state(load_state(dataset), version, express=express, warnings=warnings)
    save_state(dataset, state)

    out = [
        f"Contrato do dataset {slug}: versão {version[:12]}, "
        f"{len(spec.fields)} campo(s), status {state.status}"
    ]
    if warnings:
        out.append("Avisos:")
        out.extend(f"  - {w}" for w in warnings)
    out.append(render_table(spec))
    if previous is not None:
        diff = diff_specs(previous, spec)
        out.append(
            f"Diferenças em relação à versão {schema_version(previous)[:12]}: "
            f"+{len(diff.added)} -{len(diff.removed)} ~{len(diff.changed)}"
        )
        out.extend(f"  + {p}" for p in diff.added)
        out.extend(f"  - {p}" for p in diff.removed)
        out.extend(f"  ~ {c}" for c in diff.changed)
    if state.status == "em_revisao":
        if state.rounds:
            out.append(f"Rodada de ajuste {state.rounds} de {MAX_ROUNDS}.")
        if state.rounds_exhausted:
            out.append(
                f"{MAX_ROUNDS} rodadas sem aprovação. "
                "Considere reiniciar a entrevista com /sintetica-start."
            )
        out.append(f"Para aprovar: {cli_command()} schema approve {slug}")
    return CommandResult(EXIT_OK, out=out)


def show(project_dir: Path, slug: str) -> CommandResult:
    dataset = _dataset(project_dir, slug)
    if dataset is None:
        return _missing_dataset(slug)
    spec = _read_existing(dataset)
    if spec is None:
        return CommandResult(EXIT_USAGE, err=[f"sem {SCHEMA_JSON}: rode sintetica schema build"])
    state = load_state(dataset)
    status = state.status if state else "em_revisao"
    out = [f"Contrato do dataset {slug}: versão {schema_version(spec)[:12]}, status {status}"]
    out.append(render_table(spec))
    return CommandResult(EXIT_OK, out=out)


def approve(project_dir: Path, slug: str) -> CommandResult:
    dataset = _dataset(project_dir, slug)
    if dataset is None:
        return _missing_dataset(slug)
    spec = _read_existing(dataset)
    if spec is None:
        return CommandResult(EXIT_USAGE, err=[f"sem {SCHEMA_JSON}: rode sintetica schema build"])
    version = schema_version(spec)
    if header_version(dataset / SCHEMA_PY) != version:
        return CommandResult(
            EXIT_INVALID_CODE,
            err=[
                f"{SCHEMA_PY} desatualizado em relação a {SCHEMA_JSON}; rode sintetica schema build"
            ],
        )
    state = load_state(dataset) or next_state(None, version, express=False, warnings=[])
    state = approved(state)
    save_state(dataset, state)
    return CommandResult(EXIT_OK, out=[f"Contrato {version[:12]} aprovado em {state.approved_at}."])
