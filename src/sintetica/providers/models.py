"""Modelo de cada backend: `SINTETICA_<BACKEND>_MODEL` ou o padrão embutido (RN-08)."""

from __future__ import annotations

import os

from sintetica.providers.pricing import load_defaults


def model_env_var(backend: str) -> str:
    return f"SINTETICA_{backend.upper()}_MODEL"


def resolve_model(backend: str) -> str:
    override = os.environ.get(model_env_var(backend), "").strip()
    if override:
        return override
    models = load_defaults()["models"]
    if not isinstance(models, dict) or backend not in models:
        raise KeyError(f"backend sem modelo padrão: {backend}")
    return str(models[backend])
