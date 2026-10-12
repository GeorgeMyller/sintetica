"""Tipos de domínio do llm-provider (data-delta.md#1). Valores monetários em `Decimal` (D-02)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

STOP_BUDGET = "teto de custo"
HARNESS = "harness"
OLLAMA = "ollama"
EXTERNAL = "external"
EXTERNAL_BACKENDS: tuple[str, ...] = ("openai", "anthropic", "gemini")
ALL_BACKENDS: tuple[str, ...] = (*EXTERNAL_BACKENDS, OLLAMA)


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """Pedido de geração. `instructions` e `seeds` podem conter PII até passar pelo mascaramento."""

    schema_json: Mapping[str, object]
    seeds: Sequence[Mapping[str, object]]
    instructions: str
    n_records: int

    def __post_init__(self) -> None:
        if self.n_records < 1:
            raise ValueError("n_records deve ser maior ou igual a 1")


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Registros brutos (ainda não validados pelo schema), tokens e custo real (RF-13)."""

    records: tuple[dict[str, object], ...]
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    provider: str
    stop_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CostEstimate:
    provider: str
    model: str | None
    n_records: int
    avg_tokens: int
    usd: Decimal
    requires_authorization: bool
    price_known: bool = True


@dataclass(frozen=True, slots=True)
class ProviderChoice:
    """Provedor escolhido pela RN-01 e o motivo em texto (RF-03)."""

    provider: str
    backend: str | None
    reason: str
    skipped: tuple[str, ...] = field(default=())


@dataclass(frozen=True, slots=True)
class ModelPrice:
    input_usd_per_token: Decimal
    output_usd_per_token: Decimal
