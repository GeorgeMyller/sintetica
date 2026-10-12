"""Revisão por bloco: inválidos, duplicados, mascaramento e revalidação (D-09)."""

from __future__ import annotations

from pathlib import Path

from sintetica.batch.output import append_block, load_partial
from sintetica.batch.review import DedupIndex, review_block
from sintetica.schema import load_record_model

from .conftest import CPF, JSON_DRAFT, prepare

FAKE_CPF = "111.444.777-35"


def _masker(text: str, path: str) -> str:
    return text.replace(CPF, FAKE_CPF)


def test_block_with_invalid_duplicate_and_cpf(project: Path) -> None:
    model = load_record_model(prepare(project))
    index = DedupIndex()
    first = review_block([{"cliente": "Ana", "valor": 10}], model, index, _masker, 5)
    assert first.accepted == ['{"cliente":"Ana","valor":10.00}']
    raw: list[dict[str, object]] = [
        {"cliente": "Bia", "valor": 99},  # acima de 50
        {"cliente": "Ana", "valor": "10.0"},  # duplicado de um já aceito
        {"cliente": f"Caio {CPF}", "valor": 7},
        {"cliente": "Duda", "valor": 8},
        {"cliente": "Duda", "valor": 8},  # duplicado no mesmo bloco
    ]
    result = review_block(raw, model, index, _masker, 5)
    assert result.accepted == [
        f'{{"cliente":"Caio {FAKE_CPF}","valor":7.00}}',
        '{"cliente":"Duda","valor":8.00}',
    ]
    assert (result.invalid, result.duplicate) == (1, 2)
    assert result.reasons and "99" not in result.reasons[0]
    assert len(index) == 3


def test_limit_ignores_surplus_records(project: Path) -> None:
    model = load_record_model(prepare(project))
    raw: list[dict[str, object]] = [{"cliente": f"C{i}", "valor": 9} for i in range(5)]
    result = review_block(raw, model, DedupIndex(), _masker, 2)
    assert len(result.accepted) == 2 and result.invalid == result.duplicate == 0


def test_masked_value_that_breaks_the_rule_is_invalid(project: Path) -> None:
    draft = {
        "format": "json",
        "fields": [{"name": "codigo", "type": "text", "constraints": {"pattern": "^[a-z]+$"}}],
    }
    model = load_record_model(prepare(project, draft=draft, sample=False))
    result = review_block([{"codigo": "abc"}], model, DedupIndex(), lambda t, p: "ABC 1", 1)
    assert result.accepted == [] and result.invalid == 1
    assert "mascaramento" in result.reasons[0]


def test_index_rebuilt_from_partial_file(project: Path) -> None:
    assert JSON_DRAFT["format"] == "json"
    model = load_record_model(prepare(project))
    partial = project / "p.jsonl"
    append_block(partial, ['{"cliente":"Ana","valor":10.00}'])
    index = DedupIndex()
    assert load_partial(partial, index) == 1
    result = review_block([{"cliente": "Ana", "valor": 10}], model, index, _masker, 1)
    assert result.duplicate == 1 and result.accepted == []
