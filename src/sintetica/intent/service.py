"""Orquestração de `sintetica start` e `sintetica intent` (interfaces/intent-cli.md)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from sintetica.command import cli_command
from sintetica.intent.answers import (
    Answers,
    InvalidAnswer,
    Masker,
    MaskingUnavailable,
    PiiGuardMasker,
    apply_answers,
)
from sintetica.intent.model import (
    IntentError,
    IntentModel,
    Mode,
    load_intent_model,
    save_intent,
)
from sintetica.intent.questions import render_questions
from sintetica.intent.slug import create_dataset_dir
from sintetica.intent.summary import is_complete, missing_items, render_summary
from sintetica.pii import PiiGuard

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INVALID_ANSWER = 8
EXIT_MASKING = 9
EXIT_WRITE = 10

POLICY_PATH = Path(".sintetica") / "policy.json"
SEEDS_DIR = "seeds"


@dataclass
class CommandResult:
    code: int
    out: list[str] = field(default_factory=list)
    err: list[str] = field(default_factory=list)


def _utc(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def start(
    project_dir: Path, name: str | None, mode: Mode = "guiado", now: datetime | None = None
) -> CommandResult:
    """Cria a pasta e a intenção inicial antes de qualquer pergunta (RN-01, Q20)."""
    moment = now or datetime.now(timezone.utc)
    datasets = project_dir / "datasets"
    try:
        datasets.mkdir(parents=True, exist_ok=True)
        slug, dataset = create_dataset_dir(datasets, name, moment.astimezone(timezone.utc))
        (dataset / SEEDS_DIR).mkdir()
        intent = IntentModel(slug=slug, mode=mode, started_at=_utc(moment))
        save_intent(dataset, intent)
    except OSError as exc:
        where = exc.filename or datasets
        return CommandResult(EXIT_WRITE, err=[f"não foi possível criar {where}: {exc.strerror}"])
    return CommandResult(
        EXIT_OK,
        out=[
            f"Dataset criado: {slug} (modo {mode})",
            f"Pasta: {dataset.resolve()}",
            f"Início da medição: {intent.started_at}",
            f"Próximo: {cli_command()} intent questions --mode {mode}",
        ],
    )


def questions(mode: Mode = "guiado") -> CommandResult:
    return CommandResult(EXIT_OK, out=render_questions(mode))


def _load(project_dir: Path, slug: str) -> tuple[Path, IntentModel] | CommandResult:
    dataset = project_dir / "datasets" / slug
    if not dataset.is_dir():
        return CommandResult(
            EXIT_USAGE,
            err=[f"dataset inexistente: datasets/{slug}; inicie com: {cli_command()} start"],
        )
    try:
        return dataset, load_intent_model(dataset)
    except IntentError as exc:
        return CommandResult(EXIT_USAGE, err=[str(exc)])


def _save(dataset: Path, intent: IntentModel) -> CommandResult | None:
    try:
        save_intent(dataset, intent)
    except OSError as exc:
        return CommandResult(
            EXIT_WRITE, err=[f"não foi possível gravar {dataset / 'intent.json'}: {exc.strerror}"]
        )
    return None


def set_answers(
    project_dir: Path,
    slug: str,
    answers: Answers,
    masker_factory: Callable[[Path, Path], Masker] | None = None,
) -> CommandResult:
    if answers.empty:
        return CommandResult(EXIT_USAGE, err=["informe ao menos 1 item ou --unknown <item>"])
    conflicts = answers.conflicts()
    if conflicts:
        return CommandResult(
            EXIT_USAGE, err=[f"item informado e marcado como --unknown: {', '.join(conflicts)}"]
        )
    loaded = _load(project_dir, slug)
    if isinstance(loaded, CommandResult):
        return loaded
    dataset, intent = loaded

    def factory() -> Masker:
        policy = project_dir / POLICY_PATH
        if masker_factory is not None:
            return masker_factory(dataset, policy)
        return PiiGuardMasker(PiiGuard.for_dataset(dataset, policy))

    try:
        updated, warnings = apply_answers(intent, answers, factory)
    except InvalidAnswer as exc:
        failed = _save(dataset, exc.intent) if exc.intent != intent else None
        if failed is not None:
            return failed
        return CommandResult(EXIT_INVALID_ANSWER, err=exc.messages)
    except MaskingUnavailable as exc:
        return CommandResult(EXIT_MASKING, err=[f"{exc}; nada foi gravado"])
    failed = _save(dataset, updated)
    if failed is not None:
        return failed
    out = [f"Aviso: {w}" for w in warnings]
    out.extend(render_summary(updated, dataset))
    return CommandResult(EXIT_OK, out=out)


def show(project_dir: Path, slug: str) -> CommandResult:
    loaded = _load(project_dir, slug)
    if isinstance(loaded, CommandResult):
        return loaded
    dataset, intent = loaded
    return CommandResult(EXIT_OK, out=render_summary(intent, dataset))


def confirm(project_dir: Path, slug: str, now: datetime | None = None) -> CommandResult:
    loaded = _load(project_dir, slug)
    if isinstance(loaded, CommandResult):
        return loaded
    dataset, intent = loaded
    if not is_complete(intent):
        return CommandResult(
            EXIT_INVALID_ANSWER,
            err=[f"intenção incompleta; faltam: {', '.join(missing_items(intent))}"],
        )
    updated = intent.model_copy(update={"confirmed_at": _utc(now or datetime.now(timezone.utc))})
    failed = _save(dataset, updated)
    if failed is not None:
        return failed
    return CommandResult(EXIT_OK, out=render_summary(updated, dataset))
