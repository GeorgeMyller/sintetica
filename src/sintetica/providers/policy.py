"""Leitura das chaves do llm-provider em `.sintetica/policy.json` (D-23).

Padrões de `cli-installer` RF-06: `pii_premask: true`, `cost_ceiling_usd: 5.00`,
`provider_priority: ["harness", "ollama", "external"]`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from sintetica.providers.domain import EXTERNAL, HARNESS, OLLAMA
from sintetica.providers.errors import ProviderPolicyError

POLICY_RELATIVE_PATH = Path(".sintetica") / "policy.json"
DEFAULT_CEILING = Decimal("5.00")
DEFAULT_PRIORITY: tuple[str, ...] = (HARNESS, OLLAMA, EXTERNAL)
_KNOWN_PROVIDERS = frozenset(DEFAULT_PRIORITY)
PROVIDER_ENV = "SINTETICA_PROVIDER"


@dataclass(frozen=True, slots=True)
class ProviderPolicy:
    pii_premask: bool = True
    cost_ceiling_usd: Decimal = DEFAULT_CEILING
    provider_priority: tuple[str, ...] = DEFAULT_PRIORITY


def load_provider_policy(path: Path) -> ProviderPolicy:
    """Arquivo ausente: padrões. Conteúdo inválido: `ProviderPolicyError`."""
    forced = os.environ.get(PROVIDER_ENV, "").strip().lower()
    forced_priority = (
        (forced, *(p for p in DEFAULT_PRIORITY if p != forced))
        if forced in _KNOWN_PROVIDERS
        else DEFAULT_PRIORITY
    )
    if not path.exists():
        return ProviderPolicy(provider_priority=forced_priority)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProviderPolicyError(f"policy.json inválido: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ProviderPolicyError("policy.json deve conter um objeto JSON")

    premask = data.get("pii_premask", True)
    if not isinstance(premask, bool):
        raise ProviderPolicyError("pii_premask deve ser true ou false")

    ceiling_raw = data.get("cost_ceiling_usd", DEFAULT_CEILING)
    if isinstance(ceiling_raw, bool) or not isinstance(ceiling_raw, (int, float, str, Decimal)):
        raise ProviderPolicyError("cost_ceiling_usd deve ser um número")
    try:
        ceiling = Decimal(str(ceiling_raw))
    except ArithmeticError as exc:
        raise ProviderPolicyError("cost_ceiling_usd deve ser um número") from exc
    if not ceiling.is_finite() or ceiling < 0:
        raise ProviderPolicyError("cost_ceiling_usd deve ser um número maior ou igual a 0")

    priority = data.get("provider_priority", list(DEFAULT_PRIORITY))
    if not isinstance(priority, list) or not priority:
        raise ProviderPolicyError("provider_priority deve ser uma lista não vazia")
    for item in priority:
        if item not in _KNOWN_PROVIDERS:
            raise ProviderPolicyError(
                f"provider_priority: valor desconhecido {item!r}; use harness, ollama ou external"
            )
    if forced in _KNOWN_PROVIDERS:
        priority = [forced, *(p for p in priority if p != forced)]
    return ProviderPolicy(premask, ceiling, tuple(priority))
