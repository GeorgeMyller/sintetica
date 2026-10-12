"""Pedido da amostra (D-03) e ids distintos entre tentativas (R-01)."""

from __future__ import annotations

import json
from pathlib import Path

from sintetica.intent import load_intent_model
from sintetica.providers.harness.store import request_id
from sintetica.sample.request import build_request

from .conftest import prepare


def test_instructions_carry_intent_adjustment_and_attempt(project: Path) -> None:
    path = prepare(project)
    intent = load_intent_model(path)
    schema = json.loads((path / "record.schema.json").read_text("utf-8"))
    req = build_request(intent, schema, [], 3, 1, "nomes mais variados")
    assert req.n_records == 3 and req.seeds == [] and req.schema_json == schema
    assert "Objetivo: testar pedidos" in req.instructions
    assert "Estrutura: cliente e valor" in req.instructions
    assert "Regras:" not in req.instructions  # regras indefinidas não entram
    assert "Ajuste pedido pelo usuário: nomes mais variados" in req.instructions
    assert "Tentativa 1 de 3." in req.instructions
    assert "não repita" not in req.instructions


def test_accepted_records_become_seeds(project: Path) -> None:
    path = prepare(project)
    intent = load_intent_model(path)
    req = build_request(intent, {}, ['{"cliente":"Ana","valor":19.90}'], 2, 2, None)
    assert req.seeds == [{"cliente": "Ana", "valor": 19.9}]
    assert "não repita nenhum" in req.instructions


def test_attempts_with_same_missing_count_get_distinct_ids(project: Path) -> None:
    path = prepare(project)
    intent = load_intent_model(path)
    first = build_request(intent, {}, [], 3, 1, None)
    second = build_request(intent, {}, [], 3, 2, None)
    assert request_id(first) != request_id(second)
    assert request_id(first) == request_id(build_request(intent, {}, [], 3, 1, None))
