"""Plano de blocos: tamanho médio da amostra e bloco adaptativo (D-05, Q46)."""

from __future__ import annotations

import math
from collections.abc import Sequence

from sintetica.batch.state import MAX_BLOCK_OVERRIDE
from sintetica.providers.harness.provider import estimate_tokens

TOKEN_TARGET = 4000  # saída estimada por pedido
MAX_BLOCK = 10


def avg_tokens(lines: Sequence[str]) -> int:
    """Tokens médios por registro da amostra (4 caracteres por token), no mínimo 1."""
    if not lines:
        raise ValueError("a amostra não tem registros")
    total = sum(estimate_tokens(line) for line in lines)
    return max(1, math.ceil(total / len(lines)))


def block_size(avg: int, override: int | None = None) -> int:
    """Até 10 registros, reduzido para a saída ficar perto de 4.000 tokens; `override` vence."""
    if override is not None:
        if not 1 <= override <= MAX_BLOCK_OVERRIDE:
            raise ValueError(f"--block-size deve estar entre 1 e {MAX_BLOCK_OVERRIDE}")
        return override
    return min(MAX_BLOCK, max(1, TOKEN_TARGET // max(1, avg)))


def split(missing: int, size: int) -> list[int]:
    """Registros por bloco para pedir `missing` registros em blocos de até `size`."""
    full, rest = divmod(missing, size)
    return [size] * full + ([rest] if rest else [])
