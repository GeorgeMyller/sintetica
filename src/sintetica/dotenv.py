"""Carregamento de variáveis de ambiente de arquivos `.env`."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: Path | None = None) -> dict[str, str]:
    """Lê arquivo `.env` e injeta em `os.environ` (não sobrescreve variáveis existentes)."""
    env_path = path or (Path.cwd() / ".env")
    if not env_path.is_file():
        return {}
    loaded: dict[str, str] = {}
    try:
        content = env_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            val = val[1:-1]
        if key not in os.environ:
            os.environ[key] = val
        loaded[key] = val
    return loaded
