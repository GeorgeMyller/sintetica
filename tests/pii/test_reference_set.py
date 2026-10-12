"""Conjunto de referência (Q24): 100% dos positivos detectados e ≤ 5% de falsos positivos."""

import json
from pathlib import Path

import pytest

from sintetica.pii.detectors import default_detectors
from sintetica.pii.domain import PiiType

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "pii_reference"
TYPES = ["cpf", "cnpj", "email", "phone", "card", "ipv4", "ipv6"]
MAX_FALSE_POSITIVE_RATE = 0.05


def _load(name: str) -> dict[str, list[str]]:
    data: dict[str, list[str]] = json.loads((FIXTURES / f"{name}.json").read_text("utf-8"))
    return data


def _detector(name: str):  # type: ignore[no-untyped-def]
    return next(d for d in default_detectors() if d.type is PiiType(name))


@pytest.mark.parametrize("name", TYPES)
def test_reference_set_size(name: str) -> None:
    data = _load(name)
    assert len(data["positives"]) == 20
    assert len(data["negatives"]) == 20


@pytest.mark.parametrize("name", TYPES)
def test_all_positives_detected(name: str) -> None:
    detector = _detector(name)
    missed = [s for s in _load(name)["positives"] if not detector.find(s)]
    assert missed == []


@pytest.mark.parametrize("name", TYPES)
def test_false_positive_rate(name: str) -> None:
    detector = _detector(name)
    negatives = _load(name)["negatives"]
    false_positives = [s for s in negatives if detector.find(s)]
    assert len(false_positives) / len(negatives) <= MAX_FALSE_POSITIVE_RATE, false_positives
