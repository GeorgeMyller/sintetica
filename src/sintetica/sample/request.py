"""Pedido de geração da amostra (D-03).

Cada tentativa leva o seu número nas instruções: o `HarnessAgentProvider` devolve a resposta
antiga para um pedido idêntico, e o laço de tentativas nunca avançaria (R-01).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from sintetica.intent import IntentModel
from sintetica.providers.domain import GenerationRequest
from sintetica.sample.state import MAX_ATTEMPTS

_LABELS = (("objective", "Objetivo"), ("structure", "Estrutura"), ("rules", "Regras"))


def intent_lines(intent: IntentModel) -> list[str]:
    """Objetivo, estrutura e regras definidos na intenção, 1 por linha (comum ao lote)."""
    lines: list[str] = []
    for name, label in _LABELS:
        item = intent.item(name)
        if item.status == "definido" and item.text:
            lines.append(f"{label}: {item.text}")
    return lines


def build_instructions(
    intent: IntentModel, k: int, attempt: int, adjustment: str | None, has_examples: bool
) -> str:
    lines = [f'Gere exatamente {k} registro(s) sintético(s) para o dataset "{intent.slug}".']
    lines += intent_lines(intent)
    if adjustment:
        lines.append(f"Ajuste pedido pelo usuário: {adjustment}")
    if has_examples:
        lines.append("Os exemplos já foram aceitos: use-os como referência e não repita nenhum.")
    lines.append("Responda com 1 objeto JSON por linha, seguindo o JSON Schema do pedido.")
    lines.append("Use dados fictícios; não use dados pessoais reais.")
    lines.append(f"Tentativa {attempt} de {MAX_ATTEMPTS}.")
    return "\n".join(lines)


def build_request(
    intent: IntentModel,
    schema_json: Mapping[str, object],
    accepted: Sequence[str],
    k: int,
    attempt: int,
    adjustment: str | None,
) -> GenerationRequest:
    seeds = [json.loads(line) for line in accepted]
    return GenerationRequest(
        schema_json=schema_json,
        seeds=seeds,
        instructions=build_instructions(intent, k, attempt, adjustment, bool(seeds)),
        n_records=k,
    )
