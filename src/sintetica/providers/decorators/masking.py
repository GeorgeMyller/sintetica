"""Mascaramento do pedido inteiro antes de qualquer backend externo (RN-03, RN-04, D-06, D-07)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import cast

from sintetica.pii import PiiGuard, PolicyError
from sintetica.providers.domain import CostEstimate, GenerationRequest, GenerationResult
from sintetica.providers.errors import MaskingUnavailable
from sintetica.providers.ports import LLMProvider

# Chaves do JSON Schema que carregam texto livre escrito pelo usuário.
SCHEMA_TEXT_KEYS = frozenset({"description", "examples", "default", "enum"})


def _mask_value(guard: PiiGuard, value: object) -> object:
    if isinstance(value, str):
        return guard.mask(value).text
    if isinstance(value, Mapping):
        return {k: _mask_value(guard, v) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask_value(guard, v) for v in value]
    return value


def _mask_schema(guard: PiiGuard, node: object) -> object:
    if isinstance(node, Mapping):
        return {
            k: _mask_value(guard, v) if k in SCHEMA_TEXT_KEYS else _mask_schema(guard, v)
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [_mask_schema(guard, v) for v in node]
    return node


def mask_request(guard: PiiGuard, request: GenerationRequest) -> GenerationRequest:
    # Mapping entra, dict sai: o cast só informa o tipo ao mypy.
    schema = cast(dict[str, object], _mask_schema(guard, request.schema_json))
    seeds = [cast(dict[str, object], _mask_value(guard, s)) for s in request.seeds]
    return GenerationRequest(
        schema_json=schema,
        seeds=seeds,
        instructions=guard.mask(request.instructions).text,
        n_records=request.n_records,
    )


class MaskingProvider:
    """O guard é criado no primeiro pedido: política inválida falha ali, sem envio."""

    def __init__(self, inner: LLMProvider, guard_factory: Callable[[], PiiGuard]) -> None:
        self._inner = inner
        self._factory = guard_factory
        self._guard: PiiGuard | None = None

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def is_local(self) -> bool:
        return self._inner.is_local

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            if self._guard is None:
                self._guard = self._factory()
            masked = mask_request(self._guard, request)
        except PolicyError as exc:
            raise MaskingUnavailable(f"mascaramento indisponível: {exc}") from None
        except OSError as exc:
            raise MaskingUnavailable(
                f"mascaramento indisponível: falha ao gravar a allowlist ({exc.strerror})"
            ) from None
        return await self._inner.generate(masked)

    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate:
        return self._inner.estimate_cost(n_records, avg_tokens)
