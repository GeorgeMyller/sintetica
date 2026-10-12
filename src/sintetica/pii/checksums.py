"""Validação de dígitos verificadores. Funções puras, sem dependências."""

from __future__ import annotations


def only_digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def _mod11_digit(digits: str, weights: tuple[int, ...]) -> int:
    total = sum(int(d) * w for d, w in zip(digits, weights, strict=True))
    rest = total % 11
    return 0 if rest < 2 else 11 - rest


_CPF_W1 = (10, 9, 8, 7, 6, 5, 4, 3, 2)
_CPF_W2 = (11, 10, 9, 8, 7, 6, 5, 4, 3, 2)
_CNPJ_W1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_CNPJ_W2 = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def cpf_check_digits(base9: str) -> str:
    """Calcula os 2 dígitos verificadores de um CPF a partir dos 9 primeiros dígitos."""
    d1 = _mod11_digit(base9, _CPF_W1)
    d2 = _mod11_digit(base9 + str(d1), _CPF_W2)
    return f"{d1}{d2}"


def cnpj_check_digits(base12: str) -> str:
    """Calcula os 2 dígitos verificadores de um CNPJ a partir dos 12 primeiros dígitos."""
    d1 = _mod11_digit(base12, _CNPJ_W1)
    d2 = _mod11_digit(base12 + str(d1), _CNPJ_W2)
    return f"{d1}{d2}"


def cpf_is_valid(value: str) -> bool:
    """CPF com 11 dígitos, dígitos verificadores corretos e sem todos os dígitos iguais."""
    digits = only_digits(value)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    return digits[9:] == cpf_check_digits(digits[:9])


def cnpj_is_valid(value: str) -> bool:
    """CNPJ numérico: 14 dígitos, verificadores corretos e sem todos os dígitos iguais."""
    digits = only_digits(value)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    return digits[12:] == cnpj_check_digits(digits[:12])


def luhn_check_digit(partial: str) -> str:
    """Dígito que torna `partial + dígito` válido pelo algoritmo de Luhn."""
    total = 0
    for i, ch in enumerate(reversed(partial)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - total % 10) % 10)


def luhn_is_valid(value: str) -> bool:
    """Verificação de Luhn sobre os dígitos de `value` (mínimo de 2 dígitos)."""
    digits = only_digits(value)
    if len(digits) < 2:
        return False
    return digits[-1] == luhn_check_digit(digits[:-1])
