"""Cenários Gherkin de ponta a ponta com o protocolo real do harness (interfaces/sample-cli.md)."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from sintetica.providers.domain import GenerationRequest, GenerationResult, ProviderChoice
from sintetica.providers.errors import ProviderUnavailable
from sintetica.providers.ports import LLMProvider
from sintetica.sample import load_sample_state, service

from .conftest import CSV_DRAFT, agent_reply, all_text, cli, dataset, pending_id, prepare

CPF = "529.982.247-25"
OK: list[dict[str, object]] = [
    {"cliente": "Ana", "valor": "19.9"},
    {"cliente": "Bia", "valor": 7},
    {"cliente": "Caio", "valor": 12},
]


def _state(project: Path, slug: str = "pedidos"):  # type: ignore[no-untyped-def]
    state = load_sample_state(dataset(project, slug))
    assert state is not None
    return state


def test_contract_must_be_approved(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    prepare(project, approve=False)
    assert cli(project, "sample", "run", "pedidos") == 11
    assert "sintetica schema approve pedidos" in capsys.readouterr().err


def test_missing_dataset_contract_and_bad_n(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli(project, "sample", "run", "nada") == 2
    assert cli(project, "start", "sem-contrato") == 0
    assert cli(project, "sample", "run", "sem-contrato") == 11
    assert "schema build" in capsys.readouterr().err
    prepare(project)
    assert cli(project, "sample", "run", "pedidos", "--n", "6") == 2
    assert cli(project, "sample", "run", "pedidos", "--n", "2") == 2
    assert "entre 3 e 5" in capsys.readouterr().err


def test_first_run_writes_request_and_waits_for_agent(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = prepare(project)
    assert cli(project, "sample", "run", "pedidos") == 0
    out = capsys.readouterr().out
    rid = pending_id(project)
    assert f"uv run sintetica submit pedidos {rid}" in out and "estado aguardando_agente" in out
    request = json.loads((path / "requests" / f"{rid}.json").read_text("utf-8"))
    assert request["n_records"] == 3
    assert request["schema_json"] == json.loads((path / "record.schema.json").read_text("utf-8"))
    assert "Objetivo: testar pedidos" in request["instructions"]
    # chamar de novo sem resposta continua esperando o mesmo pedido
    assert cli(project, "sample", "run", "pedidos") == 0
    assert pending_id(project) == rid and _state(project).attempt == 1


def test_valid_sample_shown_as_json(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project)
    cli(project, "sample", "run", "pedidos")
    assert agent_reply(project, monkeypatch, OK) == 0
    capsys.readouterr()
    assert cli(project, "sample", "run", "pedidos") == 0
    out = capsys.readouterr().out
    assert out.count("```json") == 3 and '"valor": 19.90' in out
    assert "Provedor: harness" in out and "estado em_revisao" in out
    assert "sample approve pedidos" in out and "sample adjust pedidos" in out


def test_csv_sample_shown_as_table(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project, draft=CSV_DRAFT)
    cli(project, "sample", "run", "pedidos")
    rows = [{"nome": n, "tags": ["x"], "saldo": 1} for n in ("Ana", "Bia", "Caio")]
    agent_reply(project, monkeypatch, rows)
    capsys.readouterr()
    cli(project, "sample", "run", "pedidos")
    out = capsys.readouterr().out
    assert "| nome | tags | saldo |" in out and "| Caio | x | 1.00 |" in out


def test_invalid_and_duplicate_are_requested_again(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project)
    cli(project, "sample", "run", "pedidos")
    first = pending_id(project)
    reply = [OK[0], {"cliente": "Bia", "valor": 99}, OK[0], OK[2]]
    agent_reply(project, monkeypatch, reply[:3])
    capsys.readouterr()
    cli(project, "sample", "run", "pedidos")
    out = capsys.readouterr().out
    assert "Tentativa 1: 1 aceito(s), 2 descartado(s)." in out
    assert "registro 3: duplicado" in out
    second = pending_id(project)
    assert second != first
    assert (
        json.loads((dataset(project) / "requests" / f"{second}.json").read_text())["n_records"] == 2
    )
    assert not (dataset(project) / "requests" / f"{first}.response.jsonl").exists()


def test_non_json_reply_is_refused_without_spending_attempt(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project)
    cli(project, "sample", "run", "pedidos")
    assert agent_reply(project, monkeypatch, ["isto não é json"]) == 5
    cli(project, "sample", "run", "pedidos")
    state = _state(project)
    assert state.status == "aguardando_agente" and state.attempt == 1


def test_three_failed_attempts_guided_then_partial_approval(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project)
    cli(project, "sample", "run", "pedidos")
    agent_reply(project, monkeypatch, [OK[0], OK[1], {"cliente": "x", "valor": 0}])
    cli(project, "sample", "run", "pedidos")
    for _ in range(2):
        agent_reply(project, monkeypatch, [{"cliente": "x", "valor": 999}])
        capsys.readouterr()
        cli(project, "sample", "run", "pedidos")
    out = capsys.readouterr().out
    assert "Após 3 tentativas, a amostra tem 2 de 3" in out and "voltar ao contrato" in out
    assert _state(project).status == "em_revisao"
    assert cli(project, "sample", "approve", "pedidos") == 0
    assert "amostra parcial aprovada (2 de 3" in capsys.readouterr().out
    meta = json.loads((dataset(project) / "seeds" / "sample.meta.json").read_text("utf-8"))
    assert meta["partial"] is True and meta["n_records"] == 2


def test_express_partial_stops_and_needs_decision(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project, mode="expresso")
    cli(project, "sample", "run", "pedidos")
    agent_reply(project, monkeypatch, [OK[0]])
    for _ in range(2):
        cli(project, "sample", "run", "pedidos")
        agent_reply(project, monkeypatch, [{"cliente": "x", "valor": 999}])
    capsys.readouterr()
    cli(project, "sample", "run", "pedidos")
    out = capsys.readouterr().out
    assert "a automação parou" in out
    assert _state(project).status == "interrompida"
    assert not (dataset(project) / "seeds" / "sample.jsonl").exists()
    assert cli(project, "sample", "approve", "pedidos") == 0  # decisão humana


def test_express_complete_is_approved_in_same_call(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project, mode="expresso")
    cli(project, "sample", "run", "pedidos")
    agent_reply(project, monkeypatch, OK)
    capsys.readouterr()
    cli(project, "sample", "run", "pedidos")
    assert "Amostra aprovada" in capsys.readouterr().out
    lines = (dataset(project) / "seeds" / "sample.jsonl").read_text("utf-8").splitlines()
    assert len(lines) == 3 and _state(project).status == "aprovada"


def test_pii_is_masked_on_screen_and_disk(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project)
    cli(project, "sample", "run", "pedidos")
    agent_reply(project, monkeypatch, [{"cliente": f"Ana {CPF}", "valor": 10}, OK[1], OK[2]])
    capsys.readouterr()
    cli(project, "sample", "run", "pedidos")
    cli(project, "sample", "approve", "pedidos")
    captured = capsys.readouterr()
    assert CPF not in captured.out + captured.err
    assert CPF not in all_text(project)


def test_adjust_discards_sample_and_suggests_contract_on_4th_round(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project)
    cli(project, "sample", "run", "pedidos")
    agent_reply(project, monkeypatch, OK)
    cli(project, "sample", "run", "pedidos")
    for round_number in range(1, 5):
        capsys.readouterr()
        assert (
            cli(project, "sample", "adjust", "pedidos", f"nomes mais variados {round_number}") == 0
        )
        out = capsys.readouterr().out
        state = _state(project)
        assert state.round == round_number and state.accepted == []
        rid = pending_id(project)
        req = json.loads((dataset(project) / "requests" / f"{rid}.json").read_text("utf-8"))
        assert f"nomes mais variados {round_number}" in req["instructions"]
        assert ("Considere voltar ao contrato" in out) is (round_number >= 4)


def test_approval_writes_seed_files(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = prepare(project)
    cli(project, "sample", "run", "pedidos")
    agent_reply(project, monkeypatch, OK)
    cli(project, "sample", "run", "pedidos")
    capsys.readouterr()
    assert cli(project, "sample", "approve", "pedidos") == 0
    out = capsys.readouterr().out
    assert "Próximo passo: uv run sintetica generate pedidos" in out
    meta = json.loads((path / "seeds" / "sample.meta.json").read_text("utf-8"))
    version = json.loads((path / "schema.state.json").read_text("utf-8"))["schema_version"]
    assert meta == {
        "schema_version": version,
        "approved_at": meta["approved_at"],
        "provider": "harness",
        "n_requested": 3,
        "n_records": 3,
        "partial": False,
        "rounds": 0,
    }
    seeds = (path / "seeds" / "sample.jsonl").read_text("utf-8").splitlines()
    assert seeds[0] == '{"cliente":"Ana","valor":19.90}'
    assert cli(project, "sample", "run", "pedidos") == 0  # já aprovada: só mostra
    assert cli(project, "sample", "approve", "pedidos") == 13
    assert cli(project, "sample", "adjust", "pedidos", "x") == 13


def test_contract_change_invalidates_sample(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = prepare(project)
    cli(project, "sample", "run", "pedidos")
    agent_reply(project, monkeypatch, OK)
    cli(project, "sample", "run", "pedidos")
    draft = json.loads((path / "schema.draft.json").read_text("utf-8"))
    draft["fields"][0]["description"] = "nome do cliente"
    (path / "schema.draft.json").write_text(json.dumps(draft), "utf-8")
    cli(project, "schema", "build", "pedidos")
    cli(project, "schema", "approve", "pedidos")
    assert cli(project, "sample", "approve", "pedidos") == 11
    capsys.readouterr()
    assert cli(project, "sample", "run", "pedidos") == 0
    assert "amostra anterior foi descartada" in capsys.readouterr().out
    assert _state(project).accepted == []


def test_not_approvable_states_and_usage(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    prepare(project)
    assert cli(project, "sample", "show", "pedidos") == 13
    assert cli(project, "sample", "approve", "pedidos") == 13
    assert cli(project, "sample", "adjust", "pedidos", "x") == 13
    assert cli(project, "sample", "adjust", "pedidos", "   ") == 2
    cli(project, "sample", "run", "pedidos")
    assert cli(project, "sample", "approve", "pedidos") == 13  # aguardando o agente
    assert cli(project, "sample", "show", "pedidos") == 0
    agent_reply(project, monkeypatch, [{"cliente": "x", "valor": 999}])
    for _ in range(2):
        cli(project, "sample", "run", "pedidos")
        agent_reply(project, monkeypatch, [{"cliente": "x", "valor": 999}])
    cli(project, "sample", "run", "pedidos")
    capsys.readouterr()
    assert cli(project, "sample", "approve", "pedidos") == 13
    assert "não tem registros válidos" in capsys.readouterr().err
    assert cli(project, "sample", "run", "pedidos", "--n", "5") == 0
    assert "--n 5 ignorado" in capsys.readouterr().out


class _ListProvider:
    """Provedor externo simulado: devolve os registros na hora, sem passar pelo agente."""

    def __init__(self, batches: list[list[dict[str, object]]]) -> None:
        self._batches = batches
        self.requests: list[GenerationRequest] = []

    @property
    def name(self) -> str:
        return "external"

    @property
    def is_local(self) -> bool:
        return False

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        return GenerationResult(tuple(self._batches.pop(0)), 1, 1, Decimal(0), "external")

    def estimate_cost(self, n_records: int, avg_tokens: int):  # type: ignore[no-untyped-def]
        raise NotImplementedError


def test_external_provider_runs_all_attempts_in_one_call(project: Path) -> None:
    prepare(project)
    provider = _ListProvider([[OK[0], {"cliente": "x", "valor": 0}], [OK[1]], [OK[2]]])

    def factory(k: int, ds: Path, pj: Path) -> tuple[LLMProvider, ProviderChoice]:
        return provider, ProviderChoice("external", "openai", "1º disponível")

    result = service.run(project, "pedidos", provider_factory=factory)
    assert result.code == 0
    assert [r.n_records for r in provider.requests] == [3, 2, 1]
    state = _state(project)
    assert state.status == "em_revisao" and len(state.accepted) == 3
    assert state.provider == "external"


def test_provider_failure_keeps_state(project: Path) -> None:
    prepare(project)

    def factory(k: int, ds: Path, pj: Path) -> tuple[LLMProvider, ProviderChoice]:
        raise ProviderUnavailable(["OPENAI_API_KEY"])

    result = service.run(project, "pedidos", provider_factory=factory)
    assert result.code == 12
    assert "falha ao escolher o provedor" in result.err[0] and "OPENAI_API_KEY" in result.err[0]
    assert load_sample_state(dataset(project)) is None


def test_provider_error_during_generation(project: Path) -> None:
    prepare(project)

    class _Broken(_ListProvider):
        async def generate(self, request: GenerationRequest) -> GenerationResult:
            raise ProviderUnavailable(["OLLAMA_HOST"])

    def factory(k: int, ds: Path, pj: Path) -> tuple[LLMProvider, ProviderChoice]:
        return _Broken([]), ProviderChoice("ollama", "ollama", "local")

    result = service.run(project, "pedidos", provider_factory=factory)
    assert result.code == 12 and result.err[0].startswith("falha do provedor ollama")


def test_masking_unavailable_writes_nothing(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(project)
    cli(project, "sample", "run", "pedidos")
    agent_reply(project, monkeypatch, OK)
    before = (dataset(project) / "sample.state.json").read_text("utf-8")
    (project / ".sintetica").mkdir()
    (project / ".sintetica" / "policy.json").write_text(
        json.dumps({"pii_custom_patterns": ["(aberto"]}), "utf-8"
    )
    assert cli(project, "sample", "run", "pedidos") == 9
    assert (dataset(project) / "sample.state.json").read_text("utf-8") == before


def test_write_failure(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(project)

    def broken(*_: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(service, "save_sample_state", broken)
    assert cli(project, "sample", "run", "pedidos") == 10
