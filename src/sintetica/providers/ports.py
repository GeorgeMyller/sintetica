"""Porta única de geração (RF-01)."""

from __future__ import annotations

from typing import Protocol

from sintetica.providers.domain import CostEstimate, GenerationRequest, GenerationResult


class LLMProvider(Protocol):
    @property
    def name(self) -> str:
        """`harness`, `openai`, `anthropic`, `gemini` ou `ollama`."""
        ...

    @property
    def is_local(self) -> bool:
        """Verdadeiro para harness e Ollama."""
        ...

    async def generate(self, request: GenerationRequest) -> GenerationResult: ...

    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate: ...
