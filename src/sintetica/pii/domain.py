"""Tipos de domínio do pii-guard. Nenhum tipo guarda o valor original de um achado (RN-04)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum


class PiiType(str, Enum):
    """Tipos de PII cobertos. Os 7 primeiros são fixos (Q9); CUSTOM vem da política do projeto."""

    CPF = "cpf"
    CNPJ = "cnpj"
    EMAIL = "email"
    PHONE = "phone"
    CARD = "card"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    CUSTOM = "custom"


FIXED_TYPES: tuple[PiiType, ...] = (
    PiiType.CPF,
    PiiType.CNPJ,
    PiiType.EMAIL,
    PiiType.PHONE,
    PiiType.CARD,
    PiiType.IPV4,
    PiiType.IPV6,
)


@dataclass(frozen=True, slots=True)
class PiiFinding:
    """Um achado de PII. `start` é inclusivo e `end` é exclusivo."""

    type: PiiType
    start: int
    end: int
    field: str | None
    preview: str


@dataclass(frozen=True, slots=True)
class MaskResult:
    """Texto mascarado, achados substituídos por tipo e substitutos que falharam."""

    text: str
    counts: Mapping[PiiType, int]
    fallbacks: int


@dataclass(frozen=True, slots=True)
class Coverage:
    """Escopo e limites da detecção, para o relatório do quality-evaluator (Q9)."""

    types: tuple[PiiType, ...]
    custom_patterns: int
    limits: tuple[str, ...]


class PolicyError(Exception):
    """Política de PII inválida. `index` aponta o padrão com problema, ou -1 se for o arquivo."""

    def __init__(self, index: int, message: str) -> None:
        super().__init__(message)
        self.index = index


def make_preview(value: str) -> str:
    """Prévia segura: 2 primeiros caracteres seguidos de `***` (RF-10)."""
    return value[:2] + "***"
