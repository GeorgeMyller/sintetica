"""Orquestração de `sintetica generate` e `sintetica status` (interfaces/generate-cli.md)."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from sintetica.batch.background import start_background
from sintetica.batch.engine import (
    BatchEngine,
    BatchWriteError,
    EngineContext,
    MaskingFailed,
    Progress,
    finish,
    usd,
)
from sintetica.batch.lock import DatasetLock, is_locked
from sintetica.batch.output import convert_final, load_partial
from sintetica.batch.plan import avg_tokens, block_size, split
from sintetica.batch.review import DedupIndex
from sintetica.batch.state import (
    MAX_ROUNDS,
    RUN_FILE,
    RunState,
    RunStateError,
    dataset_path,
    load_run_state,
    lock_path,
    log_path,
    output_dir,
    partial_path,
    save_run_state,
)
from sintetica.command import cli_command
from sintetica.intent import IntentError, IntentModel, load_intent_model
from sintetica.pii import PiiGuard, PolicyError
from sintetica.providers.domain import HARNESS, ProviderChoice
from sintetica.providers.errors import ProviderError
from sintetica.providers.factory import build_provider
from sintetica.providers.harness.store import MAX_HARNESS_RECORDS, RequestStore
from sintetica.providers.policy import POLICY_RELATIVE_PATH, load_provider_policy
from sintetica.providers.ports import LLMProvider
from sintetica.sample.service import CommandResult
from sintetica.sample.state import SEEDS_DIR, SEEDS_JSONL, SEEDS_META, SampleMeta
from sintetica.schema import GeneratedCodeError, SchemaNotFoundError, load_record_model
from sintetica.schema.loader import RECORD_SCHEMA_JSON, read_spec
from sintetica.schema.spec import DatasetFormat
from sintetica.schema.state import load_state as load_schema_state
from sintetica.schema.version import schema_version

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_MASKING = 9
EXIT_WRITE = 10
EXIT_CONTRACT = 11
EXIT_PROVIDER = 12
EXIT_SAMPLE = 14
EXIT_AUTHORIZATION = 15
EXIT_BUSY = 16

BACKGROUND_ABOVE = MAX_HARNESS_RECORDS  # Q28: acima de 100 registros, background
STARTING_GRACE_S = 10  # janela do estado `iniciando` (D-16)

ProviderFactory = Callable[
    [int, Path, Path, Decimal | None, Decimal | None], tuple[LLMProvider, ProviderChoice]
]
Spawner = Callable[[Path, Path, str, DatasetLock], int]


class _Fail(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class _Ctx:
    project: Path
    slug: str
    dataset: Path
    intent: IntentModel
    model: type[BaseModel]
    schema_json: Mapping[str, Any]
    version: str
    fmt: DatasetFormat
    volume: int
    seed_lines: list[str]


def _default_provider(
    n: int, dataset: Path, project: Path, authorized: Decimal | None, per_request: Decimal | None
) -> tuple[LLMProvider, ProviderChoice]:
    return build_provider(
        n,
        dataset_dir=dataset,
        project_dir=project,
        harness_available=True,
        authorized_usd=authorized,
        per_request_estimate=per_request,
    )


def _context(project: Path, slug: str) -> _Ctx:
    """Pré-condições na ordem de D-02: dataset e intenção, contrato, amostra, volume."""
    dataset = project / "datasets" / slug
    if not dataset.is_dir():
        raise _Fail(EXIT_USAGE, f"dataset inexistente: datasets/{slug}; inicie com sintetica start")
    try:
        intent = load_intent_model(dataset)
    except IntentError as exc:
        raise _Fail(EXIT_USAGE, str(exc)) from exc
    try:
        spec = read_spec(dataset)
    except SchemaNotFoundError as exc:
        raise _Fail(
            EXIT_CONTRACT, f"sem contrato; rode: {cli_command()} schema build {slug}"
        ) from exc
    version = schema_version(spec)
    schema_state = load_schema_state(dataset)
    if schema_state is None or schema_state.status != "aprovado":
        raise _Fail(
            EXIT_CONTRACT, f"contrato não aprovado; rode: {cli_command()} schema approve {slug}"
        )
    if schema_state.schema_version != version:
        raise _Fail(
            EXIT_CONTRACT, f"contrato desatualizado; rode: {cli_command()} schema build {slug}"
        )
    try:
        model = load_record_model(dataset)
        schema_json = json.loads((dataset / RECORD_SCHEMA_JSON).read_text("utf-8"))
    except (GeneratedCodeError, OSError, ValueError) as exc:
        raise _Fail(
            EXIT_CONTRACT, f"contrato ilegível; rode: {cli_command()} schema build {slug}"
        ) from exc
    seed_lines = _seed_lines(dataset, slug, version)
    if intent.volume is None:
        raise _Fail(EXIT_USAGE, f"volume indefinido na intenção; rode sintetica intent set {slug}")
    return _Ctx(
        project,
        slug,
        dataset,
        intent,
        model,
        schema_json,
        version,
        spec.format,
        intent.volume,
        seed_lines,
    )


def _seed_lines(dataset: Path, slug: str, version: str) -> list[str]:
    seeds = dataset / SEEDS_DIR
    rerun = f"rode: {cli_command()} sample run {slug}"
    try:
        meta = SampleMeta.model_validate(json.loads((seeds / SEEDS_META).read_text("utf-8")))
        text = (seeds / SEEDS_JSONL).read_text("utf-8")
    except FileNotFoundError as exc:
        raise _Fail(EXIT_SAMPLE, f"sem amostra aprovada; {rerun}") from exc
    except (OSError, ValueError, ValidationError) as exc:
        raise _Fail(EXIT_SAMPLE, f"amostra aprovada ilegível; {rerun}") from exc
    if meta.schema_version != version:
        raise _Fail(EXIT_SAMPLE, f"a amostra aprovada é de outra versão do contrato; {rerun}")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise _Fail(EXIT_SAMPLE, f"a amostra aprovada não tem registros; {rerun}")
    return lines


def _masker(ctx: _Ctx) -> Callable[[str, str], str]:
    try:
        guard = PiiGuard.for_dataset(ctx.dataset, ctx.project / POLICY_RELATIVE_PATH)
    except PolicyError as exc:
        raise _Fail(
            EXIT_MASKING, f"mascaramento de PII indisponível: {exc}; nada foi gravado"
        ) from exc

    def mask(text: str, path: str) -> str:
        try:
            return guard.mask(text, field=path).text
        except OSError as exc:
            raise MaskingFailed(f"mascaramento de PII indisponível: {exc.strerror}") from exc

    return mask


def _save(ctx: _Ctx, state: RunState) -> RunState:
    try:
        return save_run_state(ctx.dataset, state)
    except OSError as exc:
        raise BatchWriteError(f"não foi possível gravar {RUN_FILE}: {exc.strerror}") from exc


def _load(dataset: Path) -> RunState | None:
    try:
        return load_run_state(dataset)
    except RunStateError as exc:
        raise _Fail(EXIT_USAGE, f"{exc}; para recomeçar, use --new") from exc


def _build(
    factory: ProviderFactory, ctx: _Ctx, authorized: Decimal | None, per_request: Decimal | None
) -> tuple[LLMProvider, ProviderChoice]:
    try:
        # RN-02: o volume total decide o provedor, nunca o tamanho do bloco.
        return factory(ctx.volume, ctx.dataset, ctx.project, authorized, per_request)
    except ProviderError as exc:
        raise _Fail(EXIT_PROVIDER, f"falha ao escolher o provedor: {exc}") from exc


def _ceiling(ctx: _Ctx) -> Decimal:
    try:
        return load_provider_policy(ctx.project / POLICY_RELATIVE_PATH).cost_ceiling_usd
    except ProviderError as exc:
        raise _Fail(EXIT_PROVIDER, str(exc)) from exc


def _cents_up(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_CEILING):f}"


def _starting(state: RunState) -> bool:
    """Estado `iniciando` recente: o processo filho ainda pode estar pegando a trava."""
    if state.status != "iniciando":
        return False
    updated = datetime.strptime(state.updated_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - updated).total_seconds() < STARTING_GRACE_S


def _alive(dataset: Path, state: RunState) -> bool:
    return is_locked(lock_path(dataset)) or _starting(state)


# -- linhas de saída ----------------------------------------------------------------------


def status_lines(dataset: Path, state: RunState, alive: bool) -> list[str]:
    who = f", PID {state.pid}" if state.pid is not None else ""
    lines = [
        f"Lote do dataset {state.slug}: {state.status} ({state.mode}{who})",
        f"Registros: {state.accepted} de {state.volume_requested} válidos; descartados: "
        f"{state.discarded_invalid} inválido(s), {state.discarded_duplicate} duplicado(s)",
    ]
    budget = f" de US$ {usd(state.authorized_usd)} autorizados" if state.authorized_usd else ""
    lines.append(f"Custo: US$ {usd(state.cost_usd)}{budget}")
    lines.append(f"Provedor: {state.provider} ({state.provider_reason})")
    lines.append(f"Bloco: {state.block_size} registro(s); rodada {state.round} de {MAX_ROUNDS}")
    if state.stop_cause:
        lines.append(f"Causa: {state.stop_cause}")
    if state.status in ("iniciando", "em_andamento") and not alive:
        lines.append("Processo encerrado antes do fim do lote.")
        lines.append(f"Para retomar: {cli_command()} generate {state.slug} --resume")
    if state.status == "aguardando_agente" and state.pending_command:
        lines.append(f"Aguardando o agente: {state.pending_command} < registros.jsonl")
    lines.append(f"Arquivo parcial: {partial_path(dataset).resolve()}")
    if state.is_final:
        lines.append(f"Dataset: {dataset_path(dataset, state.format).resolve()}")
    if state.mode == "background":
        lines.append(f"Log: {log_path(dataset).resolve()}")
    lines.extend(_evaluation_line(dataset))
    return lines


def _evaluation_line(dataset: Path) -> list[str]:
    from sintetica.quality.report import REPORT_MD, load_report

    try:
        report = load_report(dataset)
    except (OSError, ValueError):
        return [f"Avaliação: report.json ilegível; rode {cli_command()} eval de novo"]
    if report is None:
        return []
    return [f"Avaliação: {report.verdict} ({(dataset / REPORT_MD).resolve()})"]


def _final_lines(ctx: _Ctx, state: RunState, dest: Path) -> list[str]:
    lines = [
        f"Lote {state.status}: {state.accepted} de {state.volume_requested} registros válidos "
        f"({state.discarded_invalid} inválido(s), {state.discarded_duplicate} duplicado(s) "
        f"descartado(s)), custo US$ {usd(state.cost_usd)}"
    ]
    if state.stop_cause:
        lines.append(f"Causa: {state.stop_cause}")
    if state.status == "incompleto":
        lines.append(
            f"Atenção: menos de 95% do volume pedido após {MAX_ROUNDS - 1} rodadas extras."
        )
    lines.append(f"Dataset: {dest.resolve()}")
    resume = f"{cli_command()} generate {ctx.slug} --resume"
    if state.status == "falha_provedor":
        lines.append(f"Para retomar: {resume}")
    elif state.status == "interrompido_custo":
        lines.append(f"Para retomar com novo teto: {resume} --authorize-usd <novo total>")
    return lines


def _pending_lines(ctx: _Ctx, state: RunState) -> list[str]:
    path = RequestStore(ctx.dataset).request_path(state.pending_request_id or "")
    return [
        f"Pedido para o agente (rodada {state.round} de {MAX_ROUNDS}, "
        f"{state.missing} registros): {path.resolve()}",
        "Gere os registros conforme o pedido e envie 1 objeto JSON por linha:",
        f"  {state.pending_command} < registros.jsonl",
        f"Depois rode: {cli_command()} generate {ctx.slug}",
    ]


# -- lote novo, lote existente e execução -------------------------------------------------


def _clear_output(dataset: Path) -> None:
    out = output_dir(dataset)
    if not out.is_dir():
        return
    for path in out.iterdir():
        if path.is_file() and path.name != lock_path(dataset).name:
            path.unlink()


def _resolve_existing(
    ctx: _Ctx,
    state: RunState | None,
    resume: bool,
    authorize_usd: Decimal | None,
    override: int | None,
    out: list[str],
) -> RunState | None:
    """Estado a continuar, ou `None` para um lote novo (D-18)."""
    slug = ctx.slug
    if state is None:
        if resume:
            raise _Fail(
                EXIT_BUSY, f"nenhum lote para retomar; rode: {cli_command()} generate {slug}"
            )
        return None
    if state.schema_version != ctx.version:
        raise _Fail(
            EXIT_BUSY,
            f"o contrato mudou depois do lote; para gerar de novo: "
            f"{cli_command()} generate {slug} --new",
        )
    if state.status == "aguardando_agente":
        return state
    if state.status == "concluido":
        raise _Fail(
            EXIT_BUSY,
            f"lote já concluído em {dataset_path(ctx.dataset, state.format).resolve()}; "
            f"para gerar de novo (substitui output/): {cli_command()} generate {slug} --new",
        )
    if not resume:
        raise _Fail(
            EXIT_BUSY,
            f"existe um lote {state.status}; para continuar: "
            f"{cli_command()} generate {slug} --resume; "
            f"para recomeçar (substitui output/): {cli_command()} generate {slug} --new",
        )
    update: dict[str, Any] = {
        "status": "em_andamento",
        "round": 0,
        "stop_cause": None,
        "finished_at": None,
        "pid": None,
    }
    if authorize_usd is not None:
        update["authorized_usd"] = authorize_usd
    if override is not None:
        update["block_size"] = override
    out.append(f"Retomando o lote do dataset {slug} ({state.status}).")
    return state.model_copy(update=update)


def _prepare_new(
    ctx: _Ctx,
    authorize_usd: Decimal | None,
    override: int | None,
    factory: ProviderFactory,
    out: list[str],
) -> RunState:
    try:
        avg = avg_tokens(ctx.seed_lines)
        size = block_size(avg, override)
    except ValueError as exc:
        raise _Fail(EXIT_USAGE, str(exc)) from exc
    provider, choice = _build(factory, ctx, None, None)
    estimate = provider.estimate_cost(ctx.volume, avg)
    ceiling = _ceiling(ctx)
    command = f"{cli_command()} generate {ctx.slug} --authorize-usd"
    if estimate.requires_authorization and authorize_usd is None:
        if estimate.price_known:
            raise _Fail(
                EXIT_AUTHORIZATION,
                f"custo estimado US$ {usd(estimate.usd)} acima do teto de US$ {usd(ceiling)}. "
                f"Nenhum pedido foi enviado. Para autorizar: {command} "
                f"{_cents_up(estimate.usd)}",
            )
        raise _Fail(
            EXIT_AUTHORIZATION,
            f"preço desconhecido para o modelo {estimate.model}; não é possível estimar o custo. "
            f"Nenhum pedido foi enviado. Para autorizar um teto: {command} <valor>",
        )
    if authorize_usd is not None and estimate.price_known and authorize_usd < estimate.usd:
        out.append(
            f"Aviso: valor autorizado abaixo da estimativa de US$ {usd(estimate.usd)}; "
            "o lote pode parar com interrompido_custo."
        )
    harness = choice.provider == HARNESS
    if harness and override is not None:
        out.append("Aviso: --block-size ignorado; o harness recebe 1 pedido por rodada.")
    out.append(
        f"Lote do dataset {ctx.slug}: {ctx.volume} registros em {ctx.fmt.upper()} "
        f"(provedor {choice.provider}: {choice.reason})"
    )
    plan = "1 pedido ao agente do harness" if harness else f"bloco de {size} registro(s)"
    out.append(f"Estimativa: US$ {usd(estimate.usd)}; {plan}")
    return RunState(
        slug=ctx.slug,
        status="em_andamento",
        volume_requested=ctx.volume,
        format=ctx.fmt,
        block_size=size,
        avg_tokens=avg,
        estimate_usd=estimate.usd if estimate.price_known else None,
        authorized_usd=authorize_usd if authorize_usd is not None else ceiling,
        provider=choice.provider,
        provider_reason=choice.reason,
        schema_version=ctx.version,
    )


def _execute(
    ctx: _Ctx, state: RunState, factory: ProviderFactory, progress: Progress | None, out: list[str]
) -> CommandResult:
    """Roda o motor até o fim (ou até o agente do harness) e gera o arquivo final."""
    emit: Progress = progress or out.append
    if progress is not None:
        for line in out:
            progress(line)
        out.clear()
    masker = _masker(ctx)
    index = DedupIndex()
    try:
        count = load_partial(partial_path(ctx.dataset), index)
    except OSError as exc:
        raise _Fail(EXIT_WRITE, f"não foi possível ler o arquivo parcial: {exc.strerror}") from exc
    state = state.model_copy(update={"accepted": count})
    left = None
    if state.authorized_usd is not None:
        left = max(Decimal("0"), state.authorized_usd - state.cost_usd)
    per_request = None
    if state.estimate_usd:
        per_request = state.estimate_usd / len(split(state.volume_requested, state.block_size))
    provider, choice = _build(factory, ctx, left, per_request)
    state = state.model_copy(update={"provider": choice.provider, "provider_reason": choice.reason})
    # Exemplos para o prompt: `json.loads` comum, como na amostra (o prompt não aceita Decimal).
    seeds = [json.loads(line) for line in ctx.seed_lines]
    engine = BatchEngine(
        EngineContext(
            dataset=ctx.dataset,
            model=ctx.model,
            intent=ctx.intent,
            schema_json=ctx.schema_json,
            seeds=seeds,
            masker=masker,
            index=index,
            save=lambda s: _save(ctx, s),
            progress=emit,
        )
    )
    try:
        if left is not None and left <= 0 and state.cost_usd > 0 and state.missing > 0:
            state = finish(state, "interrompido_custo", "teto de custo atingido")
        elif choice.provider == HARNESS:
            state = engine.run_harness(state, provider, RequestStore(ctx.dataset))
        else:
            state = engine.run_automatic(state, provider)
        if state.status == "aguardando_agente":
            return CommandResult(EXIT_OK, out=[*out, *_pending_lines(ctx, state)])
        dest = dataset_path(ctx.dataset, state.format)
        try:
            convert_final(partial_path(ctx.dataset), dest, state.format, ctx.model)
        except OSError as exc:
            raise BatchWriteError(f"não foi possível gravar {dest}: {exc.strerror}") from exc
        state = _save(ctx, state)
    except MaskingFailed as exc:
        raise _Fail(
            EXIT_MASKING,
            f"{exc}; o bloco não foi gravado. Para retomar: "
            f"{cli_command()} generate {ctx.slug} --resume",
        ) from exc
    except BatchWriteError as exc:
        raise _Fail(EXIT_WRITE, str(exc)) from exc
    code = EXIT_PROVIDER if state.status == "falha_provedor" else EXIT_OK
    # Q49: a avaliação roda no fim do lote, dentro da trava; o veredito não muda o código.
    from sintetica.quality.service import evaluate_after_lot

    evaluation = evaluate_after_lot(ctx.project, ctx.slug)
    return CommandResult(code, out=[*out, *_final_lines(ctx, state, dest), *evaluation])


def generate(
    project: Path,
    slug: str,
    *,
    resume: bool = False,
    new: bool = False,
    authorize_usd: Decimal | None = None,
    block_size_override: int | None = None,
    provider_factory: ProviderFactory | None = None,
    spawner: Spawner | None = None,
    progress: Progress | None = None,
) -> CommandResult:
    factory = provider_factory or _default_provider
    out: list[str] = []
    try:
        if resume and new:
            raise _Fail(EXIT_USAGE, "use --resume ou --new, não os 2")
        if authorize_usd is not None and (not authorize_usd.is_finite() or authorize_usd <= 0):
            raise _Fail(EXIT_USAGE, "--authorize-usd deve ser um valor maior que 0")
        if block_size_override is not None:
            try:
                block_size(1, block_size_override)
            except ValueError as exc:
                raise _Fail(EXIT_USAGE, str(exc)) from exc
        ctx = _context(project, slug)
        lock = DatasetLock(lock_path(ctx.dataset))
        try:
            acquired = lock.acquire()
        except OSError as exc:
            raise _Fail(EXIT_WRITE, f"não foi possível criar a trava: {exc.strerror}") from exc
        try:
            state = None if new else _load(ctx.dataset)
            if not acquired or (state is not None and _starting(state)):
                busy = [] if state is None else status_lines(ctx.dataset, state, True)
                return CommandResult(
                    EXIT_BUSY,
                    out=busy,
                    err=[f"já existe um lote em andamento para o dataset {slug}"],
                )
            if new:
                _clear_output(ctx.dataset)
            state = _resolve_existing(ctx, state, resume, authorize_usd, block_size_override, out)
            if state is None:
                state = _prepare_new(ctx, authorize_usd, block_size_override, factory, out)
            if state.volume_requested > BACKGROUND_ABOVE:
                return _launch_background(ctx, state, lock, spawner or start_background, out)
            return _execute(ctx, state, factory, progress, out)
        finally:
            lock.release()
    except _Fail as fail:
        return CommandResult(fail.code, out=out, err=[str(fail)])
    except (BatchWriteError, OSError) as exc:
        return CommandResult(EXIT_WRITE, out=out, err=[str(exc)])


def _launch_background(
    ctx: _Ctx, state: RunState, lock: DatasetLock, spawner: Spawner, out: list[str]
) -> CommandResult:
    state = _save(
        ctx, state.model_copy(update={"status": "iniciando", "mode": "background", "pid": None})
    )
    try:
        pid = spawner(ctx.project, ctx.dataset, ctx.slug, lock)
    except OSError as exc:
        raise _Fail(EXIT_WRITE, f"não foi possível iniciar o processo: {exc.strerror}") from exc
    out += [
        f"Lote em background: {state.volume_requested} registros (PID {pid}).",
        f"Acompanhe: {cli_command()} status {ctx.slug}",
        f"Log: {log_path(ctx.dataset).resolve()}",
    ]
    return CommandResult(EXIT_OK, out=out)


def run_worker(
    project: Path,
    slug: str,
    *,
    provider_factory: ProviderFactory | None = None,
    progress: Progress | None = None,
) -> CommandResult:
    """Corpo do processo em background: a trava já é deste processo."""
    out: list[str] = []
    try:
        ctx = _context(project, slug)
        state = _load(ctx.dataset)
        if state is None or state.status not in ("iniciando", "em_andamento"):
            raise _Fail(EXIT_BUSY, "nenhum lote em background para executar")
        state = _save(
            ctx,
            state.model_copy(
                update={"status": "em_andamento", "mode": "background", "pid": os.getpid()}
            ),
        )
        return _execute(ctx, state, provider_factory or _default_provider, progress, out)
    except _Fail as fail:
        return CommandResult(fail.code, out=out, err=[str(fail)])
    except (BatchWriteError, OSError) as exc:
        return CommandResult(EXIT_WRITE, out=out, err=[str(exc)])


def status(project: Path, slug: str) -> CommandResult:
    dataset = project / "datasets" / slug
    if not dataset.is_dir():
        return CommandResult(EXIT_USAGE, err=[f"dataset inexistente: datasets/{slug}"])
    try:
        state = _load(dataset)
    except _Fail as fail:
        return CommandResult(fail.code, err=[str(fail)])
    if state is None:
        return CommandResult(
            EXIT_BUSY, err=[f"nenhum lote iniciado; rode: {cli_command()} generate {slug}"]
        )
    return CommandResult(EXIT_OK, out=status_lines(dataset, state, _alive(dataset, state)))
