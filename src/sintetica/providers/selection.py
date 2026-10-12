"""Escolha do provedor pela `provider_priority` (RN-01, RF-03, RF-12, D-08 a D-10)."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import httpx

from sintetica.providers.domain import (
    EXTERNAL,
    EXTERNAL_BACKENDS,
    HARNESS,
    OLLAMA,
    ProviderChoice,
)
from sintetica.providers.errors import ProviderUnavailable
from sintetica.providers.external.backends import BACKENDS, ollama_host
from sintetica.providers.harness.store import MAX_HARNESS_RECORDS

OLLAMA_PROBE_TIMEOUT_S = 2.0
EXTERNAL_BACKEND_ENV = "SINTETICA_EXTERNAL_BACKEND"


@dataclass(frozen=True, slots=True)
class Availability:
    harness: bool
    external_backend: str | None
    ollama: Callable[[], bool]  # sondado só quando a prioridade chega ao Ollama (R-09)
    ollama_host: str


def checked_sources(host: str) -> tuple[str, ...]:
    keys = tuple(str(BACKENDS[b].key_env_var) for b in EXTERNAL_BACKENDS)
    return (*keys, f"OLLAMA_HOST ({host})")


def select_provider(
    priority: Sequence[str], n_records: int, availability: Availability
) -> ProviderChoice:
    skipped: list[str] = []
    harness_oversized = False
    for provider in priority:
        if provider == HARNESS:
            if not availability.harness:
                skipped.append("harness indisponível: execução fora do agente do harness")
            elif n_records > MAX_HARNESS_RECORDS:
                harness_oversized = True
                skipped.append(f"harness pulado: {n_records} > {MAX_HARNESS_RECORDS} registros")
            else:
                return _choice(HARNESS, None, f"harness atende {n_records} registros", skipped)
        elif provider == OLLAMA:
            if availability.ollama():
                return _choice(
                    OLLAMA, OLLAMA, f"ollama disponível em {availability.ollama_host}", skipped
                )
            skipped.append(f"ollama indisponível em {availability.ollama_host}")
        elif provider == EXTERNAL:
            backend = availability.external_backend
            if backend is not None:
                env_var = BACKENDS[backend].key_env_var
                return _choice(EXTERNAL, backend, f"external/{backend} com {env_var}", skipped)
            skipped.append("external indisponível: nenhuma chave de API definida")
    if harness_oversized and availability.harness:
        return _choice(
            HARNESS,
            None,
            f"harness atende {n_records} registros em blocos de até {MAX_HARNESS_RECORDS}",
            skipped,
        )
    raise ProviderUnavailable(checked_sources(availability.ollama_host))


def _choice(provider: str, backend: str | None, why: str, skipped: list[str]) -> ProviderChoice:
    reason = "; ".join([*skipped, f"escolhido {why}"])
    return ProviderChoice(provider, backend, reason, tuple(skipped))


def external_backend_from_env() -> str | None:
    """`SINTETICA_EXTERNAL_BACKEND` com chave, ou o 1º backend com chave na ordem fixa (D-10)."""
    forced = os.environ.get(EXTERNAL_BACKEND_ENV, "").strip().lower()
    candidates = (forced,) if forced in EXTERNAL_BACKENDS else EXTERNAL_BACKENDS
    for backend in candidates:
        env_var = BACKENDS[backend].key_env_var
        if env_var and os.environ.get(env_var, "").strip():
            return backend
    return None


def probe_ollama(host: str, transport: httpx.BaseTransport | None = None) -> bool:
    try:
        with httpx.Client(transport=transport, timeout=OLLAMA_PROBE_TIMEOUT_S) as client:
            return client.get(f"{host}/api/tags").status_code == 200
    except httpx.HTTPError:
        return False


def probe_availability(
    harness_available: bool, transport: httpx.BaseTransport | None = None
) -> Availability:
    host = ollama_host()
    return Availability(
        harness=harness_available,
        external_backend=external_backend_from_env(),
        ollama=lambda: probe_ollama(host, transport),
        ollama_host=host,
    )
