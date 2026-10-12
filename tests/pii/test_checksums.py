import pytest

from sintetica.pii.checksums import (
    cnpj_check_digits,
    cnpj_is_valid,
    cpf_check_digits,
    cpf_is_valid,
    luhn_check_digit,
    luhn_is_valid,
    only_digits,
)


def test_only_digits() -> None:
    assert only_digits("529.982.247-25") == "52998224725"
    assert only_digits("sem dígitos") == ""


@pytest.mark.parametrize("value", ["529.982.247-25", "52998224725"])
def test_cpf_valid(value: str) -> None:
    assert cpf_is_valid(value)


@pytest.mark.parametrize(
    "value",
    ["111.111.111-12", "529.982.247-26", "111.111.111-11", "000.000.000-00", "5299822472", ""],
)
def test_cpf_invalid(value: str) -> None:
    assert not cpf_is_valid(value)


def test_cpf_check_digits() -> None:
    assert cpf_check_digits("529982247") == "25"


@pytest.mark.parametrize("value", ["11.222.333/0001-81", "11222333000181"])
def test_cnpj_valid(value: str) -> None:
    assert cnpj_is_valid(value)


@pytest.mark.parametrize(
    "value", ["11.222.333/0001-82", "00.000.000/0000-00", "11111111111111", "1122233300018"]
)
def test_cnpj_invalid(value: str) -> None:
    assert not cnpj_is_valid(value)


def test_cnpj_check_digits() -> None:
    assert cnpj_check_digits("112223330001") == "81"


@pytest.mark.parametrize("value", ["4111 1111 1111 1111", "4111-1111-1111-1111", "79927398713"])
def test_luhn_valid(value: str) -> None:
    assert luhn_is_valid(value)


@pytest.mark.parametrize("value", ["4111 1111 1111 1112", "79927398710", "7", ""])
def test_luhn_invalid(value: str) -> None:
    assert not luhn_is_valid(value)


def test_luhn_check_digit() -> None:
    assert luhn_check_digit("7992739871") == "3"
