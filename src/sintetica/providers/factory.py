"""`build_provider`: política → seleção → pilha de decoradores (D-04, D-05, D-24)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from decimal import Decimal
from pathlib import Path

import httpx

from sintetica.pii import PiiGuard
from sintetica.providers.decorators.budget import BudgetedProvider
from sintetica.providers.decorators.concurrency import (
    DEFAULT_CONCURRENCY,
    ConcurrencyLimitedProvider,
)
from sintetica.providers.decorators.masking import MaskingProvider
from sintetica.providers.decorators.retrying import RetryingProvider
from sintetica.providers.domain import HARNESS, ProviderChoice
from sintetica.providers.external.provider import ExternalAPIProvider
from sintetica.providers.harness.provider import HarnessAgentProvider
from sintetica.providers.policy import POLICY_RELATIVE_PATH, load_provider_policy
from sintetica.providers.ports import LLMProvider
from sintetica.providers.pricing import PriceTable
from sintetica.providers.selection import probe_availability, select_provider


def build_provider(
    n_records: int,
    *,
    dataset_dir: Path,
    project_dir: Path,
    harness_available: bool = False,
    authorized_usd: Decimal | None = None,
    per_request_estimate: Decimal | None = None,
    concurrency: int = DEFAULT_CONCURRENCY,
    transport: httpx.AsyncBaseTransport | None = None,
    probe_transport: httpx.BaseTransport | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> tuple[LLMProvider, ProviderChoice]:
    """Monta o provedor pronto. `authorized_usd=None` usa o teto da política.

    A autorização acima do teto é do chamador: ele consulta `estimate_cost`, pergunta ao
    usuário e chama de novo com `authorized_usd` (D-24).
    """
    policy_path = project_dir / POLICY_RELATIVE_PATH
    policy = load_provider_policy(policy_path)
    availability = probe_availability(harness_available, probe_transport)
    choice = select_provider(policy.provider_priority, n_records, availability)

    provider: LLMProvider
    if choice.provider == HARNESS:
        provider = HarnessAgentProvider(dataset_dir)
    else:
        backend = choice.backend or choice.provider
        provider = RetryingProvider(
            ExternalAPIProvider(
                backend,
                prices=PriceTable.load(project_dir),
                ceiling_usd=policy.cost_ceiling_usd,
                transport=transport,
            ),
            sleep=sleep,
        )
        if policy.pii_premask:
            # Vale também para o Ollama local (Q30).
            provider = MaskingProvider(
                provider, lambda: PiiGuard.for_dataset(dataset_dir, policy_path)
            )
    provider = ConcurrencyLimitedProvider(provider, concurrency)
    authorized = policy.cost_ceiling_usd if authorized_usd is None else authorized_usd
    return BudgetedProvider(provider, authorized, per_request_estimate), choice
