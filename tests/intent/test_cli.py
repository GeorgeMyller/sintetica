"""`sintetica start` e `sintetica intent` contra interfaces/intent-cli.md e os cenários Gherkin."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from sintetica.cli import main
from sintetica.intent import load_intent_model

from .conftest import all_text, dataset, run

PII_EMAIL = "ana@empresa.com"


def _start(project: Path, *args: str) -> int:
    return run(project, "start", *args)


def _set(project: Path, slug: str, *args: str) -> int:
    return run(project, "intent", "set", slug, *args)


def test_start_creates_folder_before_any_question(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = datetime.now(timezone.utc).replace(microsecond=0)
    assert _start(project, "Pedidos de Café") == 0
    out = capsys.readouterr().out
    path = dataset(project, "pedidos-de-cafe")
    assert (path / "seeds").is_dir()
    assert f"Pasta: {path.resolve()}" in out
    intent = load_intent_model(path)
    assert intent.mode == "guiado" and intent.slug == "pedidos-de-cafe"
    started = datetime.strptime(intent.started_at, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    assert started >= before
    assert intent.objective.status == "pendente"


def test_start_without_name_and_with_existing_slug(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _start(project, "pedidos") == 0
    assert _start(project, "pedidos", "--mode", "expresso") == 0
    assert load_intent_model(dataset(project, "pedidos-2")).mode == "expresso"
    assert _start(project) == 0
    out = capsys.readouterr().out
    assert re.search(r"Dataset criado: dataset-\d{8}-\d{6} \(modo guiado\)", out)


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignora permissões de escrita")
def test_start_write_failure(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project.chmod(0o500)
    try:
        assert _start(project, "x") == 10
    finally:
        project.chmod(0o700)
    err = capsys.readouterr().err
    assert "não foi possível criar" in err and str(project) in err


def test_questions_guided_and_express(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["intent", "questions"]) == 0
    guided = capsys.readouterr().out
    assert "1 pergunta por vez" in guided and guided.count("ex.:") == 15
    assert main(["intent", "questions", "--mode", "expresso"]) == 0
    express = capsys.readouterr().out
    assert "única mensagem" in express and "5. Quantos registros" in express
    assert "não sei" in express


def test_guided_interview_flow(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _start(project, "pedidos")
    assert _set(project, "pedidos", "--objective", "testar a tela de pedidos") == 0
    assert _set(project, "pedidos", "--structure", "cliente, bebida, valor") == 0
    assert _set(project, "pedidos", "--rules", "valor entre 5 e 50") == 0
    assert _set(project, "pedidos", "--format", "JSON", "--volume", "50") == 0
    out = capsys.readouterr().out
    assert "Confirme a intenção: uv run sintetica intent confirm pedidos" in out
    assert "schema build" not in out
    assert run(project, "intent", "confirm", "pedidos") == 0
    assert "Próximo passo: uv run sintetica schema build pedidos" in capsys.readouterr().out
    assert run(project, "intent", "show", "pedidos") == 0
    assert "schema build pedidos" in capsys.readouterr().out


def test_express_single_call(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _start(project, "suporte", "--mode", "expresso")
    code = _set(
        project,
        "suporte",
        "--objective",
        "classificar sentimento",
        "--structure",
        "conversa com rótulo",
        "--unknown",
        "rules",
        "--format",
        "jsonl",
        "--volume",
        "2000",
    )
    assert code == 0
    assert "Próximo passo: uv run sintetica schema build suporte" in capsys.readouterr().out


def test_express_critical_needs_one_confirmation(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _start(project, "rapido", "--mode", "expresso")
    args = ["--unknown", "objective", "--unknown", "structure", "--rules", "nenhuma"]
    assert _set(project, "rapido", *args, "--format", "csv", "--volume", "20") == 0
    out = capsys.readouterr().out
    assert "1 campo genérico" in out and "intent confirm rapido" in out
    assert run(project, "intent", "confirm", "rapido") == 0
    assert "schema build rapido" in capsys.readouterr().out


def test_unknown_defaults_and_unknown_marker(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _start(project, "d")
    assert (
        _set(project, "d", "--unknown", "format", "--unknown", "volume", "--unknown", "rules") == 0
    )
    out = capsys.readouterr().out
    assert "formato:   jsonl (padrão)" in out and "volume:    10 (padrão)" in out
    intent = load_intent_model(dataset(project, "d"))
    assert intent.rules.status == "indefinido"
    assert (intent.format_source, intent.volume_source) == ("padrao", "padrao")


def test_invalid_format_and_volume(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _start(project, "d")
    assert _set(project, "d", "--format", "Parquet") == 8
    assert "CSV, JSON ou JSONL" in capsys.readouterr().err
    assert _set(project, "d", "--volume", "50.000") == 8
    assert _set(project, "d", "--volume", "0") == 8
    assert "1 a 10.000" in capsys.readouterr().err
    assert _set(project, "d", "--volume", "-5") == 0
    assert "pela 3ª vez" in capsys.readouterr().out
    assert load_intent_model(dataset(project, "d")).volume == 10


def test_pii_is_masked_everywhere(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _start(project, "d")
    assert _set(project, "d", "--objective", f"pedidos, contato {PII_EMAIL}") == 0
    captured = capsys.readouterr()
    assert "e-mail (1)" in captured.out
    assert PII_EMAIL not in captured.out + captured.err
    assert PII_EMAIL not in all_text(project)
    intent = load_intent_model(dataset(project, "d"))
    assert intent.pii_masked and intent.objective.text is not None
    assert "@" in intent.objective.text


def test_policy_failure_blocks_writing(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _start(project, "d")
    path = dataset(project, "d") / "intent.json"
    before = path.read_text("utf-8")
    (project / ".sintetica").mkdir()
    (project / ".sintetica" / "policy.json").write_text(
        json.dumps({"pii_custom_patterns": ["(aberto"]}), "utf-8"
    )
    assert _set(project, "d", "--objective", "algo") == 9
    err = capsys.readouterr().err
    assert "mascaramento de PII indisponível" in err and "nada foi gravado" in err
    assert path.read_text("utf-8") == before


def test_missing_dataset_and_usage_errors(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _set(project, "nada", "--objective", "x") == 2
    assert "sintetica start" in capsys.readouterr().err
    assert run(project, "intent", "show", "nada") == 2
    assert run(project, "intent", "confirm", "nada") == 2
    (project / "datasets" / "vazio").mkdir(parents=True)
    assert _set(project, "vazio", "--objective", "x") == 2
    _start(project, "d")
    assert _set(project, "d") == 2
    assert _set(project, "d", "--format", "csv", "--unknown", "format") == 2
    capsys.readouterr()
    assert run(project, "intent", "confirm", "d") == 8
    assert "faltam: objetivo" in capsys.readouterr().err


def test_corrupted_intent(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _start(project, "d")
    (dataset(project, "d") / "intent.json").write_text("{ruim", "utf-8")
    assert run(project, "intent", "show", "d") == 2
    assert "ilegível" in capsys.readouterr().err


def test_extra_keys_are_preserved(project: Path) -> None:
    _start(project, "d")
    path = dataset(project, "d") / "intent.json"
    data = json.loads(path.read_text("utf-8"))
    data["finished_at"] = "2026-10-12T10:00:00Z"
    path.write_text(json.dumps(data), "utf-8")
    assert _set(project, "d", "--format", "csv") == 0
    assert json.loads(path.read_text("utf-8"))["finished_at"] == "2026-10-12T10:00:00Z"


def test_text_with_quotes_and_newlines_survives(project: Path) -> None:
    _start(project, "d")
    text = "cliente \"VIP\", bebida 'gelada'\nvalor em R$ $HOME"
    assert _set(project, "d", "--structure", text) == 0
    assert load_intent_model(dataset(project, "d")).structure.text == text
