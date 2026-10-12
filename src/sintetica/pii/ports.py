"""Portas (Clean Architecture) do pii-guard."""

from __future__ import annotations

from typing import Protocol

from sintetica.pii.domain import PiiFinding, PiiType


class Detector(Protocol):
    """Encontra achados de um único tipo em um texto."""

    @property
    def type(self) -> PiiType: ...

    def find(self, text: str) -> list[PiiFinding]: ...


class SubstituteGenerator(Protocol):
    """Gera um valor falso do mesmo tipo e formato que `original`."""

    def generate(self, pii_type: PiiType, original: str) -> str: ...


class AllowlistStore(Protocol):
    """Registro de impressões dos valores falsos inseridos pelo mascaramento (RF-07)."""

    def add(self, pii_type: PiiType, value: str) -> None: ...

    def contains(self, pii_type: PiiType, value: str) -> bool: ...

    def exists(self) -> bool: ...
