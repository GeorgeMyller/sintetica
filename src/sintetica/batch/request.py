"""Pedido de geração do lote (D-11).

O número do bloco e da rodada vão nas instruções: varia o pedido entre blocos (menos repetição)
e dá a cada rodada do harness um id novo, porque pedido idêntico devolve a resposta antiga.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from sintetica.batch.state import MAX_ROUNDS
from sintetica.intent import IntentModel
from sintetica.providers.domain import GenerationRequest
from sintetica.sample.request import intent_lines


def build_instructions(
    intent: IntentModel,
    k: int,
    block: int,
    blocks: int,
    round_: int,
    *,
    harness: bool,
    has_examples: bool,
) -> str:
    lines = [f'Gere exatamente {k} registro(s) sintético(s) para o dataset "{intent.slug}".']
    lines += intent_lines(intent)
    if has_examples:
        lines.append(
            "Os exemplos vêm da amostra aprovada: use-os como referência e não repita nenhum."
        )
    if harness:
        lines.append("Responda com 1 objeto JSON por linha, seguindo o JSON Schema do pedido.")
    lines.append("Varie os valores entre os registros; não repita registros.")
    lines.append("Use dados fictícios; não use dados pessoais reais.")
    lines.append(f"Bloco {block} de {blocks}, rodada {round_} de {MAX_ROUNDS}.")
    return "\n".join(lines)


def build_batch_request(
    intent: IntentModel,
    schema_json: Mapping[str, object],
    seeds: Sequence[Mapping[str, object]],
    k: int,
    block: int,
    blocks: int,
    round_: int,
    *,
    harness: bool = False,
) -> GenerationRequest:
    return GenerationRequest(
        schema_json=schema_json,
        seeds=list(seeds),
        instructions=build_instructions(
            intent, k, block, blocks, round_, harness=harness, has_examples=bool(seeds)
        ),
        n_records=k,
    )
