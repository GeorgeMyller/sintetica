"""`sintetica schema build | show | approve` contra interfaces/schema-cli.md."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sintetica.cli import main
from sintetica.schema import (
    GeneratedCodeError,
    SchemaNotFoundError,
    load_record_model,
    to_csv_row,
)
from sintetica.schema import service as service_module
from sintetica.schema.loader import header_version
from sintetica.schema.state import MAX_ROUNDS, load_state

from .conftest import attr, load_fixture, make_dataset

CSV_DRAFT = {
    "format": "csv",
    "fields": [
        {"name": "Nome Completo", "type": "text", "constraints": {"min_length": 3}},
        {"name": "idade", "type": "int", "constraints": {"ge": 18, "le": 90}},
        {"name": "saldo", "type": "decimal", "constraints": {"casas_decimais": 2}},
        {"name": "tags", "type": "list", "items": {"type": "text"}},
        {"name": "endereco", "type": "object", "fields": [{"name": "cidade", "type": "text"}]},
    ],
}


def _cli(project: Path, *args: str) -> int:
    return main(["schema", *args, "--project-dir", str(project)])


def test_build_success_writes_artifacts_and_waits_for_approval(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = make_dataset(project, fmt="csv", draft=CSV_DRAFT)
    assert _cli(project, "build", "demo") == 0
    out = capsys.readouterr().out
    for name in ("schema.json", "schema.py", "record.schema.json", "schema.state.json"):
        assert (dataset / name).exists()
    assert not list(dataset.glob(".schema.staged*")) and not (dataset / "__pycache__").exists()
    assert "| endereco_cidade | texto | sim |" in out
    assert "campo 'Nome Completo' renomeado para 'nome_completo'" in out
    assert "objeto 'endereco' achatado" in out and "lista 'tags' vira 1 coluna" in out
    assert "Para aprovar: uv run sintetica schema approve demo" in out
    state = load_state(dataset)
    assert state is not None and state.status == "em_revisao" and state.rounds == 0


def test_express_mode_is_approved_without_question(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = make_dataset(project, mode="expresso", draft=load_fixture("all_types"))
    assert _cli(project, "build", "demo") == 0
    assert "Para aprovar" not in capsys.readouterr().out
    state = load_state(dataset)
    assert state is not None and state.status == "aprovado" and state.approved_at


def test_missing_dataset_or_intent(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _cli(project, "build", "nada") == 2
    assert "/sintetica-start" in capsys.readouterr().err
    (project / "datasets" / "sem-intencao").mkdir(parents=True)
    assert _cli(project, "build", "sem-intencao") == 2
    assert "/sintetica-start" in capsys.readouterr().err


@pytest.mark.parametrize(
    "content", ["{ruim", "[1]", json.dumps({"format": "xml", "structure": {"status": "definido"}})]
)
def test_malformed_intent(project: Path, content: str) -> None:
    dataset = make_dataset(project, draft=load_fixture("all_types"))
    (dataset / "intent.json").write_text(content, "utf-8")
    assert _cli(project, "build", "demo") == 2


def test_missing_draft_with_defined_structure(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    make_dataset(project)
    assert _cli(project, "build", "demo") == 2
    assert "schema.draft.json" in capsys.readouterr().err


def test_undefined_structure_generates_default(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = make_dataset(project, structure="indefinido")
    assert _cli(project, "build", "demo") == 0
    out = capsys.readouterr().out
    assert "estrutura indefinida" in out and "| descricao | texto | sim |  | a definir |" in out
    record = load_record_model(dataset)
    assert attr(record.model_validate({"descricao": "x"}), "descricao") == "x"


@pytest.mark.parametrize(
    ("draft", "expected"),
    [
        ("{ruim", "JSON inválido"),
        ({"format": "json", "fields": "x"}, "fields"),
        (load_fixture("contradictions"), "idade: mínimo (90) maior que máximo (18)"),
        (load_fixture("csv_list_objects"), "use o formato JSON ou JSONL"),
        ({"format": "csv", "fields": [{"name": "a", "type": "text"}]}, "difere da intenção"),
    ],
)
def test_invalid_definition_exit_6_and_nothing_written(
    project: Path, capsys: pytest.CaptureFixture[str], draft: object, expected: str
) -> None:
    fmt = "csv" if draft == load_fixture("csv_list_objects") else "json"
    dataset = make_dataset(project, fmt=fmt)
    text = draft if isinstance(draft, str) else json.dumps(draft)
    (dataset / "schema.draft.json").write_text(text, "utf-8")
    assert _cli(project, "build", "demo") == 6
    assert expected in capsys.readouterr().err
    assert not (dataset / "schema.json").exists()


def test_generator_defect_exit_7_logs_and_keeps_previous(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = make_dataset(project, draft=load_fixture("all_types"))
    assert _cli(project, "build", "demo") == 0
    before = (dataset / "schema.py").read_text("utf-8")
    capsys.readouterr()
    draft = load_fixture("all_types")
    draft["fields"][0]["description"] = "mudou"
    (dataset / "schema.draft.json").write_text(json.dumps(draft), "utf-8")
    monkeypatch.setattr(service_module, "generate_code", lambda spec, version: "x = (\n")
    assert _cli(project, "build", "demo") == 7
    captured = capsys.readouterr()
    assert "errors.log" in captured.err and "| nome |" not in captured.out
    assert "o código gerado não importa" in (dataset / "errors.log").read_text("utf-8")
    assert (dataset / "schema.py").read_text("utf-8") == before


def test_generated_code_without_record_is_rejected(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_dataset(project, draft=load_fixture("all_types"))
    monkeypatch.setattr(service_module, "generate_code", lambda spec, version: "Outra = 1\n")
    assert _cli(project, "build", "demo") == 7


def test_adjustment_shows_diff_and_counts_rounds(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = make_dataset(project, fmt="csv", draft=CSV_DRAFT)
    assert _cli(project, "build", "demo") == 0
    draft = json.loads(json.dumps(CSV_DRAFT))
    for round_number in range(1, MAX_ROUNDS + 1):
        draft["fields"][1]["constraints"]["le"] = 90 - round_number
        if round_number == 2:
            draft["fields"].append({"name": "novo", "type": "bool"})
        if round_number == 3:
            draft["fields"].pop()
        (dataset / "schema.draft.json").write_text(json.dumps(draft), "utf-8")
        capsys.readouterr()
        assert _cli(project, "build", "demo") == 0
        out = capsys.readouterr().out
        assert f"Rodada de ajuste {round_number} de {MAX_ROUNDS}." in out
        assert f"~ idade: le {91 - round_number} → {90 - round_number}" in out
        if round_number == 2:
            assert "+ novo" in out
        if round_number == 3:
            assert "- novo" in out
    assert "Considere reiniciar a entrevista com /sintetica-start." in out


def test_rebuild_without_changes_keeps_state(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = make_dataset(project, draft=load_fixture("all_types"))
    assert _cli(project, "build", "demo") == 0
    assert _cli(project, "approve", "demo") == 0
    assert _cli(project, "build", "demo") == 0
    out = capsys.readouterr().out
    assert "+0 -0 ~0" in out
    state = load_state(dataset)
    assert state is not None and state.status == "aprovado" and state.rounds == 0


def test_show_and_approve(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    dataset = make_dataset(project, draft=load_fixture("conversation"), fmt="jsonl")
    assert _cli(project, "show", "demo") == 2
    assert _cli(project, "approve", "demo") == 2
    assert _cli(project, "build", "demo") == 0
    capsys.readouterr()
    assert _cli(project, "show", "demo") == 0
    out = capsys.readouterr().out
    assert "| messages | lista de mensagens |" in out and "| labels.sentimento | enum |" in out
    assert _cli(project, "approve", "demo") == 0
    assert "aprovado" in capsys.readouterr().out
    state = load_state(dataset)
    assert state is not None and state.status == "aprovado"
    (dataset / "schema.state.json").unlink()
    assert _cli(project, "show", "demo") == 0
    assert "status em_revisao" in capsys.readouterr().out


def test_approve_rejects_stale_code(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    dataset = make_dataset(project, draft=load_fixture("all_types"))
    assert _cli(project, "build", "demo") == 0
    (dataset / "schema.py").write_text("# editado à mão\n", "utf-8")
    assert _cli(project, "approve", "demo") == 7
    assert "desatualizado" in capsys.readouterr().err
    assert _cli(project, "show", "nada") == 2
    assert _cli(project, "approve", "nada") == 2


def test_load_record_model_regenerates_stale_code(project: Path) -> None:
    dataset = make_dataset(project, fmt="csv", draft=CSV_DRAFT)
    assert _cli(project, "build", "demo") == 0
    (dataset / "schema.py").write_text("import os\nos.makedirs('invadido')\n", "utf-8")
    record = load_record_model(dataset)
    assert header_version(dataset / "schema.py") is not None
    assert not (project / "invadido").exists()
    row = to_csv_row(
        record.model_validate(
            {
                "nome_completo": "Ana",
                "idade": 20,
                "saldo": "1.5",
                "tags": ["x"],
                "endereco_cidade": "R",
            }
        )
    )
    assert row["saldo"] == "1.50" and row["tags"] == "x"
    with pytest.raises(SchemaNotFoundError):
        load_record_model(project / "datasets")
    assert issubclass(GeneratedCodeError, Exception)


def test_record_schema_is_accepted_by_harness_request(
    project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = make_dataset(project, draft=load_fixture("constraints"))
    assert _cli(project, "build", "demo") == 0
    code = main(
        [
            "request",
            "demo",
            "--n-records",
            "3",
            "--instructions",
            "pedidos",
            "--schema",
            str(dataset / "record.schema.json"),
            "--project-dir",
            str(project),
        ]
    )
    assert code == 0
    assert "Pedido do harness gravado." in capsys.readouterr().out
