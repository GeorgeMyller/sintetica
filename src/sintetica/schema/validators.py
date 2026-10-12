"""Validadores usados pelo código gerado (`schema.py`)."""

from __future__ import annotations


def no_pipe(value: str) -> str:
    """Itens de lista em CSV não podem conter `|`, o separador da célula (RN-04)."""
    if "|" in value:
        raise ValueError("o caractere | não é permitido em itens de lista CSV")
    return value
