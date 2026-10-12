"""Ponta a ponta pela CLI, com o protocolo real do harness (`sintetica submit`).

Cenários Gherkin do requirements.md e onde cada um é coberto:
- Lote recusado sem amostra da versão atual: test_sample_of_other_version_is_refused
- Provedor escolhido pelo volume total: test_provider_is_chosen_by_total_volume
- Custo acima do teto exige autorização:
  test_engine::test_cost_above_ceiling_requires_authorization
- Lote autorizado respeita o valor: test_engine::test_authorized_lot_never_spends_more
- Lote completo em JSON: test_harness_lot_end_to_end
- Lote em CSV: test_csv_lot_with_harness
- Inválidos, duplicados e PII num bloco: test_harness_lot_end_to_end
- Rodadas extras esgotadas: test_engine::test_extra_rounds_and_incomplete_status
- Retomada sem perda: test_engine::test_provider_failure_keeps_blocks_and_resume_finishes
- Falha do provedor no meio do lote:
  test_engine::test_provider_failure_keeps_blocks_and_resume_finishes
- Teto de custo atingido no meio: test_engine::test_budget_stop_mid_lot
- Lote acima de 100 sem prender o chat:
  test_background::test_background_lot_returns_fast_and_finishes
- Processo encerrado durante o lote: test_background::test_killed_process_is_detected_and_resumed
- Segundo lote recusado: test_engine::test_second_lot_is_refused_while_running,
  test_background::test_killed_process_is_detected_and_resumed
- Expresso começa direto: test_expresso_lot_with_harness
- Lote de teste com o harness: test_harness_lot_end_to_end
- Bloco adaptativo para registros longos: test_engine::test_adaptive_block_for_long_records
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sintetica.batch.service import _default_provider

from .conftest import CPF, CSV_DRAFT, all_text, cli, dataset, prepare, run_state, submit


def _requests(project: Path) -> list[Path]:
    return sorted((dataset(project) / "requests").glob("*.json"))


def test_harness_lot_end_to_end(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    prepare(project, volume=5)
    capsys.readouterr()
    assert cli(project, "generate", "pedidos") == 0
    out = capsys.readouterr().out
    assert "1 pedido ao agente do harness" in out
    assert "uv run sintetica submit pedidos" in out
    assert "--- INSTRUÇÕES DO PEDIDO ---" in out
    assert "--- JSON SCHEMA DOS REGISTROS ---" in out
    state = run_state(project)
    assert state.status == "aguardando_agente" and state.provider == "harness"
    first_id = state.pending_request_id
    request = json.loads(_requests(project)[0].read_text("utf-8"))
    assert request["n_records"] == 5
    assert "rodada 1 de 4" in request["instructions"]
    assert "1 objeto JSON por linha" in request["instructions"]
    lines = [
        {"cliente": "Ana", "valor": 10},  # igual a uma semente: aceito, a amostra fica fora do lote
        {"cliente": "Bia", "valor": 99},  # inválido
        {"cliente": f"Caio {CPF}", "valor": 7},
        {"cliente": "Duda", "valor": 8},
        {"cliente": "Duda", "valor": 8},  # duplicado
    ]
    assert submit(project, monkeypatch, first_id, lines) == 0
    assert cli(project, "generate", "pedidos") == 0
    state = run_state(project)
    assert state.status == "aguardando_agente" and state.round == 2
    assert state.pending_request_id != first_id
    assert state.accepted == 3 and state.missing == 2
    assert not (dataset(project) / "requests" / f"{first_id}.response.jsonl").exists()
    second = json.loads(
        (dataset(project) / "requests" / f"{state.pending_request_id}.json").read_text("utf-8")
    )
    assert second["n_records"] == 2 and "rodada 2 de 4" in second["instructions"]
    assert (
        submit(
            project,
            monkeypatch,
            state.pending_request_id,
            [{"cliente": "Eva", "valor": 9}, {"cliente": "Fia", "valor": 11}],
        )
        == 0
    )
    capsys.readouterr()
    assert cli(project, "generate", "pedidos") == 0
    out = capsys.readouterr().out
    assert "Lote concluido: 5 de 5" in out
    assert "Avaliação do dataset pedidos: APROVADO" in out
    records = json.loads((dataset(project) / "output" / "dataset.json").read_text("utf-8"))
    assert len(records) == 5
    assert CPF not in all_text(project)
    assert list((dataset(project) / "requests").glob("*.response.jsonl")) == []
    assert cli(project, "status", "pedidos") == 0
    assert "concluido" in capsys.readouterr().out


def test_waiting_agent_without_response_keeps_state(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prepare(project, volume=5)
    assert cli(project, "generate", "pedidos") == 0
    first = run_state(project).pending_request_id
    capsys.readouterr()
    assert cli(project, "generate", "pedidos") == 0
    out = capsys.readouterr().out
    assert run_state(project).pending_request_id == first
    assert "uv run sintetica submit pedidos" in out
    assert "--block-size ignorado" not in out
    assert cli(project, "status", "pedidos") == 0
    assert "Aguardando o agente" in capsys.readouterr().out


def test_csv_lot_with_harness(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(project, volume=2, draft=CSV_DRAFT)
    assert cli(project, "generate", "pedidos", "--block-size", "5") == 0
    rid = run_state(project).pending_request_id
    rows = [
        {"nome": 'Ana, "A"', "tags": ["x", "y"], "saldo": 1.5},
        {"nome": "Bia", "tags": [], "saldo": 2},
    ]
    assert submit(project, monkeypatch, rid, rows) == 0
    assert cli(project, "generate", "pedidos") == 0
    raw = (dataset(project) / "output" / "dataset.csv").read_bytes()
    assert raw == b'nome,tags,saldo\r\n"Ana, ""A""",x|y,1.50\r\nBia,,2.00\r\n'


def test_expresso_lot_with_harness(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prepare(project, volume=2, mode="expresso")
    assert cli(project, "generate", "pedidos") == 0
    rid = run_state(project).pending_request_id
    lines = [{"cliente": "Eva", "valor": 9}, {"cliente": "Fia", "valor": 11}]
    assert submit(project, monkeypatch, rid, lines) == 0
    assert cli(project, "generate", "pedidos") == 0
    assert run_state(project).status == "concluido"


def test_sample_of_other_version_is_refused(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = prepare(project, volume=5)
    meta = path / "seeds" / "sample.meta.json"
    data = json.loads(meta.read_text("utf-8"))
    data["schema_version"] = "versao-antiga"
    meta.write_text(json.dumps(data), "utf-8")
    capsys.readouterr()
    assert cli(project, "generate", "pedidos") == 14
    assert "sintetica sample run pedidos" in capsys.readouterr().err


def test_cli_codes_for_arguments(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli(project, "generate", "pedidos") == 2
    assert cli(project, "status", "pedidos") == 2
    with pytest.raises(SystemExit) as exc:
        cli(project, "generate", "pedidos", "--authorize-usd", "abc")
    assert exc.value.code == 2
    prepare(project, volume=5)
    assert cli(project, "generate", "pedidos", "--block-size", "0") == 2
    assert cli(project, "status", "pedidos") == 16
    assert cli(project, "generate", "pedidos", "--resume") == 16
    capsys.readouterr()


def test_authorize_usd_accepts_comma(project: Path) -> None:
    from sintetica.cli import _usd

    assert str(_usd("6,50")) == "6.50"


def test_provider_is_chosen_by_total_volume(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = prepare(project, volume=5)
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:9")  # Ollama desligado
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")
    _, big = _default_provider(1000, path, project, None, None)
    assert big.provider == "external"
    assert "harness pulado: 1000 > 100" in big.reason
    _, small = _default_provider(50, path, project, None, None)
    assert small.provider == "harness"


def test_harness_large_batch_in_foreground_chunks(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:9")  # sem Ollama
    prepare(project, volume=120)
    capsys.readouterr()
    # 120 > 100, mas como o provedor é o harness, não vai para background!
    assert cli(project, "generate", "pedidos") == 0
    out = capsys.readouterr().out
    assert "--- INSTRUÇÕES DO PEDIDO ---" in out
    assert "--- JSON SCHEMA DOS REGISTROS ---" in out
    state = run_state(project)
    assert state.status == "aguardando_agente" and state.provider == "harness"
    assert state.mode == "foreground"
    assert state.volume_requested == 120
    assert state.round == 1
    rid1 = state.pending_request_id
    assert rid1 is not None
    req1 = json.loads((dataset(project) / "requests" / f"{rid1}.json").read_text("utf-8"))
    assert req1["n_records"] == 100

    # Submete os primeiros 100 registros
    block1 = [{"cliente": f"Cliente_{i}", "valor": 10} for i in range(100)]
    assert submit(project, monkeypatch, rid1, block1) == 0

    capsys.readouterr()
    assert cli(project, "generate", "pedidos") == 0
    out2 = capsys.readouterr().out
    assert "--- INSTRUÇÕES DO PEDIDO ---" in out2
    state2 = run_state(project)
    assert state2.status == "aguardando_agente"
    assert state2.accepted == 100
    assert state2.missing == 20
    assert state2.round == 2
    rid2 = state2.pending_request_id
    assert rid2 is not None and rid2 != rid1
    req2 = json.loads((dataset(project) / "requests" / f"{rid2}.json").read_text("utf-8"))
    assert req2["n_records"] == 20

    # Submete os 20 registros restantes
    block2 = [{"cliente": f"Cliente_Final_{i}", "valor": 20} for i in range(20)]
    assert submit(project, monkeypatch, rid2, block2) == 0

    capsys.readouterr()
    assert cli(project, "generate", "pedidos") == 0
    out3 = capsys.readouterr().out
    assert "Lote concluido: 120 de 120" in out3
    state3 = run_state(project)
    assert state3.status == "concluido"
    assert state3.accepted == 120
    assert state3.missing == 0
