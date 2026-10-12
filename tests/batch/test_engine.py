"""Motor e `generate`: rodadas, status finais, custo, retomada, lote existente (D-03 a D-18)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from sintetica.batch import service
from sintetica.batch.lock import DatasetLock
from sintetica.batch.state import lock_path
from sintetica.pii import PiiGuard
from sintetica.providers.decorators.budget import BudgetedProvider
from sintetica.providers.domain import GenerationRequest, GenerationResult, ProviderChoice
from sintetica.providers.ports import LLMProvider
from sintetica.sample.service import CommandResult

from .conftest import (
    CPF,
    Factory,
    FakeProvider,
    counter_responder,
    dataset,
    make_records,
    prepare,
    run_state,
)


def _output(project: Path, name: str = "dataset.json") -> Path:
    return dataset(project) / "output" / name


def _dataset_records(project: Path) -> list[dict[str, object]]:
    data: list[dict[str, object]] = json.loads(_output(project).read_text("utf-8"))
    return data


def _gen(project: Path, factory: Factory, **kwargs: object) -> CommandResult:
    return service.generate(project, "pedidos", provider_factory=factory, **kwargs)  # type: ignore[arg-type]


def test_complete_json_lot(project: Path) -> None:
    prepare(project, volume=50)
    fake = FakeProvider(counter_responder())
    factory = Factory(fake)
    result = _gen(project, factory)
    assert result.code == 0, result.err
    records = _dataset_records(project)
    assert len(records) == 50 and len({json.dumps(r) for r in records}) == 50
    state = run_state(project)
    assert state.status == "concluido" and state.accepted == 50 and state.round == 1
    assert len(fake.requests) == 5 and {r.n_records for r in fake.requests} == {10}
    assert result.out[-1].startswith("Relatório: ")  # Q49: avaliação ao fim do lote
    # RN-02: o provedor é escolhido pelo volume total, nunca pelo bloco.
    assert {n for n, _, _ in factory.calls} == {50}
    # D-11: cada bloco leva o seu número e as sementes da amostra.
    assert "Bloco 3 de 5, rodada 1 de 4." in fake.requests[2].instructions
    assert len(fake.requests[0].seeds) == 2


def test_extra_rounds_and_incomplete_status(project: Path) -> None:
    prepare(project, volume=20)

    def one_invalid(request: GenerationRequest, n: int) -> GenerationResult:
        records = [*make_records(n * 100, request.n_records - 1), {"cliente": "X", "valor": 99}]
        return GenerationResult(tuple(records), 1, 1, Decimal("0"), "fake")

    fake = FakeProvider(one_invalid)
    result = _gen(project, Factory(fake), block_size_override=2)
    assert result.code == 0
    state = run_state(project)
    assert state.status == "incompleto" and state.round == 4
    assert state.accepted == 18 and state.discarded_invalid == len(fake.requests)
    assert len(_dataset_records(project)) == 18
    assert any("Atenção: menos de 95%" in line for line in result.out)


def test_ninety_five_percent_is_complete(project: Path) -> None:
    prepare(project, volume=20)

    def one_invalid(request: GenerationRequest, n: int) -> GenerationResult:
        records = [*make_records(n * 100, request.n_records - 1), {"cliente": "X", "valor": 99}]
        return GenerationResult(tuple(records), 1, 1, Decimal("0"), "fake")

    assert _gen(project, Factory(FakeProvider(one_invalid))).code == 0
    state = run_state(project)
    assert state.accepted == 19 and state.status == "concluido"


def test_block_with_invalid_duplicate_and_cpf(project: Path) -> None:
    prepare(project, volume=4)
    bad: list[dict[str, object]] = [
        {"cliente": "Bia", "valor": 99},
        {"cliente": "Ana", "valor": 10},
        {"cliente": "Ana", "valor": 10},
        {"cliente": f"Caio {CPF}", "valor": 7},
    ]

    def respond(request: GenerationRequest, n: int) -> GenerationResult:
        records = bad if n == 1 else make_records(n * 10, request.n_records)
        return GenerationResult(tuple(records), 1, 1, Decimal("0"), "fake")

    assert _gen(project, Factory(FakeProvider(respond))).code == 0
    state = run_state(project)
    assert (state.discarded_invalid, state.discarded_duplicate) == (1, 1)
    assert state.accepted == 4 and state.round == 2
    for path in project.rglob("*"):
        if path.is_file():
            assert CPF not in path.read_text("utf-8", errors="ignore"), path


def test_provider_failure_keeps_blocks_and_resume_finishes(project: Path) -> None:
    prepare(project, volume=50)
    failing = FakeProvider(counter_responder(fail_at=3))
    result = _gen(project, Factory(failing))
    assert result.code == 12
    state = run_state(project)
    assert state.status == "falha_provedor" and state.accepted == 20
    assert "5xx" in (state.stop_cause or "")
    assert any("--resume" in line for line in result.out)
    assert len(_dataset_records(project)) == 20
    # Sem --resume, o lote interrompido não recomeça sozinho.
    blocked = _gen(project, Factory(FakeProvider(counter_responder())))
    assert blocked.code == 16 and "--resume" in blocked.err[0]
    healthy = FakeProvider(counter_responder(start=1000))
    resumed = _gen(project, Factory(healthy), resume=True)
    assert resumed.code == 0
    assert len(healthy.requests) == 3  # só os 3 blocos que faltavam
    records = _dataset_records(project)
    assert len(records) == 50 and len({json.dumps(r) for r in records}) == 50


def test_resume_after_crash_mid_block(project: Path) -> None:
    prepare(project, volume=30)
    assert _gen(project, Factory(FakeProvider(counter_responder(fail_at=2)))).code == 12
    partial = dataset(project) / "output" / "records.partial.jsonl"
    with partial.open("ab") as f:  # queda no meio da escrita do bloco seguinte
        f.write(b'{"cliente":"Meio')
    healthy = FakeProvider(counter_responder(start=1000))
    assert _gen(project, Factory(healthy), resume=True).code == 0
    assert sum(r.n_records for r in healthy.requests) == 20
    assert len(_dataset_records(project)) == 30


def test_budget_stop_mid_lot(project: Path) -> None:
    prepare(project, volume=50)
    result = _gen(project, Factory(FakeProvider(counter_responder(budget_at=3))))
    assert result.code == 0
    state = run_state(project)
    assert state.status == "interrompido_custo" and state.accepted == 20
    assert len(_dataset_records(project)) == 20
    assert any("--authorize-usd" in line for line in result.out)


def test_cost_above_ceiling_requires_authorization(project: Path) -> None:
    prepare(project, volume=50)
    fake = FakeProvider(
        counter_responder(), estimate_usd=Decimal("6.00"), requires_authorization=True
    )
    result = _gen(project, Factory(fake))
    assert result.code == 15
    assert fake.requests == []
    assert "US$ 6,00" in result.err[0]
    assert "uv run sintetica generate pedidos --authorize-usd 6.00" in result.err[0]
    assert not (dataset(project) / "output" / "run.json").exists()


def test_unknown_price_requires_authorization(project: Path) -> None:
    prepare(project, volume=50)
    fake = FakeProvider(counter_responder(), requires_authorization=True, price_known=False)
    result = _gen(project, Factory(fake))
    assert result.code == 15 and "preço desconhecido" in result.err[0]


class _BudgetFactory:
    """`BudgetedProvider` real em volta do provedor simulado, como no `build_provider`."""

    def __init__(self, inner: FakeProvider) -> None:
        self.inner = inner
        self.authorized: list[Decimal | None] = []

    def __call__(
        self,
        n: int,
        dataset_dir: Path,
        project_dir: Path,
        authorized: Decimal | None,
        per_request: Decimal | None,
    ) -> tuple[LLMProvider, ProviderChoice]:
        self.authorized.append(authorized)
        provider = BudgetedProvider(self.inner, authorized or Decimal("5.00"), per_request)
        return provider, ProviderChoice("external", "openai", "external/openai simulado")


def test_authorized_lot_never_spends_more(project: Path) -> None:
    prepare(project, volume=100)
    fake = FakeProvider(
        counter_responder(cost=Decimal("1.00")),
        estimate_usd=Decimal("6.00"),
        requires_authorization=True,
    )
    factory = _BudgetFactory(fake)
    result = service.generate(
        project, "pedidos", authorize_usd=Decimal("6.00"), provider_factory=factory
    )
    assert result.code == 0, result.err
    state = run_state(project)
    assert state.cost_usd <= Decimal("6.00") and state.authorized_usd == Decimal("6.00")
    assert state.status == "interrompido_custo"
    assert factory.authorized[-1] == Decimal("6.00")
    # Retomar sem novo valor: nada sai, o teto já foi usado.
    before = len(fake.requests)
    again = service.generate(project, "pedidos", resume=True, provider_factory=factory)
    assert again.code == 0 and len(fake.requests) == before
    assert run_state(project).status == "interrompido_custo"
    # Com novo teto total, o restante passado ao provedor desconta o já gasto.
    more = service.generate(
        project,
        "pedidos",
        resume=True,
        authorize_usd=Decimal("20"),
        provider_factory=factory,
    )
    assert more.code == 0
    assert factory.authorized[-1] == Decimal("20") - state.cost_usd
    assert run_state(project).status == "concluido"


def test_authorization_below_estimate_warns(project: Path) -> None:
    prepare(project, volume=10)
    fake = FakeProvider(
        counter_responder(), estimate_usd=Decimal("6.00"), requires_authorization=True
    )
    factory = Factory(fake)
    result = _gen(project, factory, authorize_usd=Decimal("1"))
    assert result.code == 0 and "Aviso: valor autorizado abaixo" in result.out[0]
    assert factory.calls[-1] == (10, Decimal("1"), Decimal("6.00"))


def test_adaptive_block_for_long_records(project: Path) -> None:
    long_seed = json.dumps({"cliente": "x" * 3973, "valor": 10.0}, separators=(",", ":"))
    prepare(project, volume=12, seeds=[long_seed])
    fake = FakeProvider(counter_responder())
    assert _gen(project, Factory(fake)).code == 0
    assert [r.n_records for r in fake.requests] == [4, 4, 4]
    assert run_state(project).block_size == 4


def test_second_lot_is_refused_while_running(project: Path) -> None:
    prepare(project, volume=20)
    assert _gen(project, Factory(FakeProvider(counter_responder(fail_at=2)))).code == 12
    lock = DatasetLock(lock_path(dataset(project)))
    assert lock.acquire()
    try:
        result = _gen(project, Factory(FakeProvider(counter_responder())), resume=True)
    finally:
        lock.release()
    assert result.code == 16 and "em andamento" in result.err[0]
    assert result.out and "Lote do dataset pedidos: falha_provedor" in result.out[0]


def test_existing_lot_rules(project: Path) -> None:
    prepare(project, volume=10)
    assert _gen(project, Factory(FakeProvider(counter_responder())), resume=True).code == 16
    assert _gen(project, Factory(FakeProvider(counter_responder()))).code == 0
    done = _gen(project, Factory(FakeProvider(counter_responder())))
    assert done.code == 16 and "--new" in done.err[0]
    assert _gen(project, Factory(FakeProvider(counter_responder())), resume=True).code == 16
    fresh = FakeProvider(counter_responder())
    assert _gen(project, Factory(fresh), new=True).code == 0
    assert len(fresh.requests) == 1
    both = _gen(project, Factory(fresh), new=True, resume=True)
    assert both.code == 2


def test_contract_change_after_lot(project: Path) -> None:
    prepare(project, volume=10)
    assert _gen(project, Factory(FakeProvider(counter_responder(fail_at=1)))).code == 12
    state_file = dataset(project) / "output" / "run.json"
    data = json.loads(state_file.read_text("utf-8"))
    data["schema_version"] = "outra"
    state_file.write_text(json.dumps(data), "utf-8")
    result = _gen(project, Factory(FakeProvider(counter_responder())), resume=True)
    assert result.code == 16 and "contrato mudou" in result.err[0]


def test_preconditions(project: Path) -> None:
    factory = Factory(FakeProvider(counter_responder()))
    assert _gen(project, factory).code == 2  # sem dataset
    prepare(project, volume=10, sample=False)
    no_sample = _gen(project, factory)
    assert no_sample.code == 14 and "sintetica sample run" in no_sample.err[0]
    from .conftest import write_sample

    write_sample(dataset(project), ['{"cliente":"Ana","valor":10.00}'], version="antiga")
    old = _gen(project, factory)
    assert old.code == 14 and "outra versão" in old.err[0]
    (dataset(project) / "schema.state.json").unlink()
    assert _gen(project, factory).code == 11
    assert factory.calls == []


def test_invalid_arguments(project: Path) -> None:
    prepare(project, volume=10)
    factory = Factory(FakeProvider(counter_responder()))
    assert _gen(project, factory, block_size_override=0).code == 2
    assert _gen(project, factory, authorize_usd=Decimal("-1")).code == 2
    (dataset(project) / "output").mkdir()
    (dataset(project) / "output" / "run.json").write_text("{", "utf-8")
    assert _gen(project, factory).code == 2
    assert _gen(project, factory, new=True).code == 0


def test_masking_unavailable_before_any_request(project: Path) -> None:
    prepare(project, volume=10)
    (project / ".sintetica").mkdir()
    (project / ".sintetica" / "policy.json").write_text(
        json.dumps({"pii_custom_patterns": ["(aberto"]}), "utf-8"
    )
    fake = FakeProvider(counter_responder())
    assert _gen(project, Factory(fake)).code == 9
    assert fake.requests == []


def test_masking_failure_mid_lot_keeps_previous_blocks(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project, volume=30)
    real = PiiGuard.for_dataset
    calls = {"n": 0}

    def flaky(*args: object, **kwargs: object) -> object:
        guard = real(*args, **kwargs)  # type: ignore[arg-type]
        original = guard.mask

        def mask(text: str, field: str | None = None) -> object:
            calls["n"] += 1
            if calls["n"] > 10:
                raise OSError(5, "Input/output error")
            return original(text, field=field)

        monkeypatch.setattr(guard, "mask", mask)
        return guard

    monkeypatch.setattr(PiiGuard, "for_dataset", flaky)
    result = _gen(project, Factory(FakeProvider(counter_responder())))
    assert result.code == 9 and "--resume" in result.err[0]
    state = run_state(project)
    assert state.accepted == 10 and state.status == "em_andamento"


def test_write_failure_returns_10(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(project, volume=10)

    def broken(*_: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr("sintetica.batch.engine.append_block", broken)
    result = _gen(project, Factory(FakeProvider(counter_responder())))
    assert result.code == 10 and "último bloco íntegro" in result.err[0]


def test_provider_choice_failure_returns_12(project: Path) -> None:
    prepare(project, volume=10)

    def no_provider(*_: object) -> tuple[LLMProvider, ProviderChoice]:
        from sintetica.providers.errors import ProviderUnavailable

        raise ProviderUnavailable(["ollama"])

    result = service.generate(project, "pedidos", provider_factory=no_provider)
    assert result.code == 12 and "escolher o provedor" in result.err[0]


def test_expresso_starts_without_questions(project: Path) -> None:
    prepare(project, volume=10, mode="expresso")
    result = _gen(project, Factory(FakeProvider(counter_responder())))
    assert result.code == 0 and run_state(project).status == "concluido"


def test_progress_callback_streams_lines(project: Path) -> None:
    prepare(project, volume=20)
    lines: list[str] = []
    result = _gen(project, Factory(FakeProvider(counter_responder())), progress=lines.append)
    assert lines[0].startswith("Lote do dataset pedidos: 20 registros em JSON")
    assert lines[2].startswith("Bloco 1/2 (rodada 1), 10 válidos")
    assert result.out[0].startswith("Lote concluido")


def test_resume_discards_records_already_saved(project: Path) -> None:
    """O índice reconstruído do arquivo parcial barra a repetição dos blocos gravados."""
    prepare(project, volume=30)
    assert _gen(project, Factory(FakeProvider(counter_responder(fail_at=2)))).code == 12
    repeating = FakeProvider(counter_responder())  # recomeça do registro 0
    assert _gen(project, Factory(repeating), resume=True).code == 0
    state = run_state(project)
    assert state.discarded_duplicate == 10 and state.accepted == 30
    records = _dataset_records(project)
    assert len({json.dumps(r) for r in records}) == 30
