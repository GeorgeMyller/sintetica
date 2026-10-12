"""Testes de fumaça com API real (R-02). Geram custo: rode só com `-m live`.

Cada teste é pulado quando a chave do backend não existe ou o Ollama não responde.
"""

from __future__ import annotations

import asyncio
import os
from decimal import Decimal
from pathlib import Path

import pytest
from support import make_request

from sintetica.providers.external.backends import BACKENDS, ollama_host
from sintetica.providers.external.provider import ExternalAPIProvider
from sintetica.providers.pricing import PriceTable
from sintetica.providers.selection import probe_ollama

pytestmark = pytest.mark.live

# O conftest limpa o ambiente; aqui lemos o valor real antes disso, na carga do módulo.
_REAL_ENV = {
    k: v for k, v in os.environ.items() if k.endswith(("_API_KEY", "_MODEL")) or k == "OLLAMA_HOST"
}


@pytest.mark.parametrize("backend", ["openai", "anthropic", "gemini", "ollama"])
def test_live_backend(backend: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in _REAL_ENV.items():
        monkeypatch.setenv(name, value)
    env_var = BACKENDS[backend].key_env_var
    if env_var is not None and not os.environ.get(env_var):
        pytest.skip(f"{env_var} não definida")
    if backend == "ollama" and not probe_ollama(ollama_host()):
        pytest.skip("Ollama não responde")

    provider = ExternalAPIProvider(
        backend, prices=PriceTable.load(tmp_path), ceiling_usd=Decimal("5.00")
    )
    result = asyncio.run(provider.generate(make_request(n_records=3)))

    assert len(result.records) >= 1
    assert result.input_tokens > 0
    assert result.output_tokens > 0
    if backend != "ollama":
        assert result.cost_usd > 0
