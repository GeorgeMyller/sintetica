"""Normalização por tipo antes do hash da allowlist (D-10, data-delta.md#2)."""

from __future__ import annotations

import ipaddress

from sintetica.pii.checksums import only_digits
from sintetica.pii.domain import PiiType


def normalize(pii_type: PiiType, value: str) -> str:
    if pii_type in (PiiType.CPF, PiiType.CNPJ, PiiType.CARD):
        return only_digits(value)
    if pii_type is PiiType.PHONE:
        digits = only_digits(value)
        if len(digits) in (12, 13) and digits.startswith("55"):
            digits = digits[2:]
        return digits
    if pii_type is PiiType.EMAIL:
        return value.strip().lower()
    if pii_type in (PiiType.IPV4, PiiType.IPV6):
        return str(ipaddress.ip_address(value))
    return value
