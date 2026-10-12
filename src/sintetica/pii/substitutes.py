"""Gerador de substitutos sobre Faker `pt_BR`, com formato espelhado do original (D-07)."""

from __future__ import annotations

import string

from faker import Faker

from sintetica.pii.checksums import luhn_check_digit, only_digits
from sintetica.pii.domain import PiiType


def _lay_digits(template: str, digits: str) -> str:
    """Troca os dígitos de `template`, na ordem, pelos de `digits`; mantém a pontuação."""
    it = iter(digits)
    return "".join(next(it) if ch.isdigit() else ch for ch in template)


class FakerSubstituteGenerator:
    def __init__(self, seed: int | None = None) -> None:
        self._fake = Faker("pt_BR")
        if seed is not None:
            self._fake.seed_instance(seed)

    def _digit(self, low: int = 0, high: int = 9) -> str:
        return str(self._fake.random_int(low, high))

    def _digits(self, n: int) -> str:
        return "".join(self._digit() for _ in range(n))

    def generate(self, pii_type: PiiType, original: str) -> str:
        if pii_type is PiiType.CPF:
            return _lay_digits(original, only_digits(str(self._fake.cpf())))
        if pii_type is PiiType.CNPJ:
            return _lay_digits(original, only_digits(str(self._fake.cnpj())))
        if pii_type is PiiType.EMAIL:
            return str(self._fake.email())
        if pii_type is PiiType.PHONE:
            return self._phone(original)
        if pii_type is PiiType.CARD:
            return self._card(original)
        if pii_type is PiiType.IPV4:
            return str(self._fake.ipv4_public())
        if pii_type is PiiType.IPV6:
            return str(self._fake.ipv6())
        return self._custom(original)

    def _phone(self, original: str) -> str:
        digits = only_digits(original)
        prefix = ""
        if original.lstrip().startswith("+55"):
            prefix, digits = "55", digits[2:]
        ddd = str(self._fake.random_int(11, 99))
        subscriber_len = len(digits) - 2
        if subscriber_len == 9:
            subscriber = "9" + self._digits(8)
        else:
            subscriber = self._digit(2, 5) + self._digits(subscriber_len - 1)
        return _lay_digits(original, prefix + ddd + subscriber)

    def _card(self, original: str) -> str:
        n = len(only_digits(original))
        partial = "4" + self._digits(n - 2)
        return _lay_digits(original, partial + luhn_check_digit(partial))

    def _custom(self, original: str) -> str:
        out: list[str] = []
        # Com dígitos, troca só os dígitos: prefixos fixos (ex.: "MAT-") continuam casando.
        has_digits = any(ch.isdigit() for ch in original)
        for ch in original:
            if ch.isdigit():
                out.append(self._digit())
            elif has_digits:
                out.append(ch)
            elif ch in string.ascii_uppercase:
                out.append(str(self._fake.random_uppercase_letter()))
            elif ch in string.ascii_lowercase:
                out.append(str(self._fake.random_lowercase_letter()))
            else:
                out.append(ch)
        return "".join(out)
