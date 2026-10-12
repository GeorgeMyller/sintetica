"""Detectores determinísticos, um por tipo (D-04)."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Callable, Sequence

from sintetica.pii.checksums import cnpj_is_valid, cpf_is_valid, luhn_is_valid, only_digits
from sintetica.pii.domain import PiiFinding, PiiType, make_preview

Validator = Callable[[str], bool]


class RegexDetector:
    """Detector baseado em regex, com validação opcional do valor encontrado."""

    def __init__(
        self, pii_type: PiiType, pattern: re.Pattern[str], validator: Validator | None = None
    ) -> None:
        self._type = pii_type
        self._pattern = pattern
        self._validator = validator

    @property
    def type(self) -> PiiType:
        return self._type

    def find(self, text: str) -> list[PiiFinding]:
        found: list[PiiFinding] = []
        for match in self._pattern.finditer(text):
            value = match.group(0)
            if self._validator is not None and not self._validator(value):
                continue
            found.append(
                PiiFinding(self._type, match.start(), match.end(), None, make_preview(value))
            )
        return found


# CPF e CNPJ: aceitam pontuação opcional; não podem fazer parte de uma sequência maior de dígitos.
_CPF_RE = re.compile(r"(?<!\d)(?<!\d[./-])\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)(?![./-]\d)")
_CNPJ_RE = re.compile(r"(?<!\d)(?<!\d[./-])\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)(?![./-]\d)")

# Cartão: 13 a 19 dígitos, com espaço ou hífen opcional entre dígitos.
_CARD_RE = re.compile(r"(?<!\d)(?<!\d[ -])\d(?:[ -]?\d){12,18}(?!\d)(?![ -]\d)")

_EMAIL_RE = re.compile(
    r"(?<![\w.+%-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w-])"
)

# Telefone: só com formatação (DDD entre parênteses, ou DDD seguido de espaço ou hífen)
# ou com prefixo +55. Dígitos corridos sem +55 não contam (RN-06, Q25).
_SUBSCRIBER = r"(?:9\d{4}|[2-5]\d{3})[\s-]?\d{4}"
_PHONE_RE = re.compile(
    r"(?<![\w+])(?:"
    rf"\+55[\s-]?(?:\(\d{{2}}\)|\d{{2}})[\s-]?{_SUBSCRIBER}"
    rf"|\(\d{{2}}\)[\s-]?{_SUBSCRIBER}"
    rf"|\d{{2}}[\s-]{_SUBSCRIBER}"
    r")(?![\w-])"
)

_IPV4_RE = re.compile(r"(?<![\d.])\d{1,3}(?:\.\d{1,3}){3}(?!\d)(?!\.\d)")
_IPV6_RE = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:])")


def _card_is_valid(value: str) -> bool:
    digits = only_digits(value)
    return 13 <= len(digits) <= 19 and luhn_is_valid(digits)


def _phone_is_valid(value: str) -> bool:
    digits = only_digits(value)
    if value.lstrip().startswith("+55"):
        digits = digits[2:]
    return len(digits) in (10, 11) and int(digits[:2]) >= 11


def _ipv4_is_valid(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
    except ValueError:
        return False
    return True


def _ipv6_is_valid(value: str) -> bool:
    if not any(ch not in ":" for ch in value):
        return False
    try:
        ipaddress.IPv6Address(value)
    except ValueError:
        return False
    return True


class CpfDetector(RegexDetector):
    def __init__(self) -> None:
        super().__init__(PiiType.CPF, _CPF_RE, cpf_is_valid)


class CnpjDetector(RegexDetector):
    def __init__(self) -> None:
        super().__init__(PiiType.CNPJ, _CNPJ_RE, cnpj_is_valid)


class CardDetector(RegexDetector):
    def __init__(self) -> None:
        super().__init__(PiiType.CARD, _CARD_RE, _card_is_valid)


class EmailDetector(RegexDetector):
    def __init__(self) -> None:
        super().__init__(PiiType.EMAIL, _EMAIL_RE)


class PhoneDetector(RegexDetector):
    def __init__(self) -> None:
        super().__init__(PiiType.PHONE, _PHONE_RE, _phone_is_valid)


class Ipv4Detector(RegexDetector):
    def __init__(self) -> None:
        super().__init__(PiiType.IPV4, _IPV4_RE, _ipv4_is_valid)


class Ipv6Detector(RegexDetector):
    def __init__(self) -> None:
        super().__init__(PiiType.IPV6, _IPV6_RE, _ipv6_is_valid)


class CustomDetector:
    """Padrões extras da política do projeto (RF-04). Recebe padrões já validados pela política."""

    def __init__(self, patterns: Sequence[str]) -> None:
        self._patterns = tuple(re.compile(p) for p in patterns)

    @property
    def type(self) -> PiiType:
        return PiiType.CUSTOM

    def find(self, text: str) -> list[PiiFinding]:
        found: list[PiiFinding] = []
        for pattern in self._patterns:
            for match in pattern.finditer(text):
                if match.end() > match.start():
                    found.append(
                        PiiFinding(
                            PiiType.CUSTOM,
                            match.start(),
                            match.end(),
                            None,
                            make_preview(match.group(0)),
                        )
                    )
        return found


def default_detectors() -> list[RegexDetector]:
    """Os 7 detectores fixos (Q9)."""
    return [
        CpfDetector(),
        CnpjDetector(),
        EmailDetector(),
        PhoneDetector(),
        CardDetector(),
        Ipv4Detector(),
        Ipv6Detector(),
    ]
