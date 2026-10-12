"""Leitura de `pii_custom_patterns` de `.sintetica/policy.json` (D-11, data-delta.md#3)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from sintetica.pii.domain import PolicyError

MAX_PATTERN_LENGTH = 200


def load_custom_patterns(path: Path) -> tuple[str, ...]:
    """Arquivo ou chave ausente: tupla vazia. Qualquer problema de conteúdo: `PolicyError`."""
    if not path.exists():
        return ()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PolicyError(-1, f"policy.json inválido: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise PolicyError(-1, "policy.json deve conter um objeto JSON")
    patterns = data.get("pii_custom_patterns", [])
    if not isinstance(patterns, list):
        raise PolicyError(-1, "pii_custom_patterns deve ser uma lista")
    for index, pattern in enumerate(patterns):
        if not isinstance(pattern, str) or not pattern:
            raise PolicyError(index, f"padrão {index}: deve ser texto não vazio")
        if len(pattern) > MAX_PATTERN_LENGTH:
            raise PolicyError(index, f"padrão {index}: excede {MAX_PATTERN_LENGTH} caracteres")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise PolicyError(index, f"padrão {index}: regex inválida ({exc})") from exc
    return tuple(patterns)
