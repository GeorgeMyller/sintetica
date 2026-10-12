"""Respostas, padrões, validação e mascaramento (RF-04 a RF-11)."""

from __future__ import annotations

import pytest

from sintetica.intent.answers import (
    Answers,
    InvalidAnswer,
    Masker,
    MaskingUnavailable,
    apply_answers,
    parse_volume,
)
from sintetica.intent.model import IntentModel, Item
from sintetica.pii import PiiType, PolicyError


class FakeMasker:
    """Troca a palavra SEGREDO por XXXXXX e conta 1 e-mail por troca."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def mask_text(self, text: str, item: str) -> tuple[str, dict[PiiType, int]]:
        self.calls.append(item)
        hits = text.count("SEGREDO")
        return text.replace("SEGREDO", "XXXXXX"), ({PiiType.EMAIL: hits} if hits else {})


def _intent(**kw: object) -> IntentModel:
    return IntentModel.model_validate({"slug": "d", "started_at": "2026-10-12T08:00:00Z", **kw})


def _apply(intent: IntentModel, answers: Answers) -> tuple[IntentModel, list[str]]:
    masker = FakeMasker()

    def factory() -> Masker:
        return masker

    return apply_answers(intent, answers, factory)


def test_text_items_are_defined_and_masked() -> None:
    new, warnings = _apply(_intent(), Answers({"objective": "contato SEGREDO", "rules": "x"}))
    assert new.objective == Item(status="definido", text="contato XXXXXX")
    assert new.rules.status == "definido" and new.structure.status == "pendente"
    assert new.pii_masked is True
    assert warnings == ["dados pessoais substituídos por valores falsos em objetivo: e-mail (1)"]


def test_all_five_items_in_one_call() -> None:
    answers = Answers(
        {"objective": "o", "structure": "s", "rules": "r"}, format="CSV", volume="2.000"
    )
    new, _ = _apply(_intent(), answers)
    assert (new.format, new.format_source, new.volume, new.volume_source) == (
        "csv",
        "usuario",
        2000,
        "usuario",
    )
    assert new.pii_masked is False


def test_unknown_items_use_defaults() -> None:
    answers = Answers(unknown={"rules", "format", "volume", "objective"})
    new, warnings = _apply(_intent(), answers)
    assert new.rules == Item(status="indefinido", text=None)
    assert new.objective.status == "indefinido"
    assert (new.format, new.format_source) == ("jsonl", "padrao")
    assert (new.volume, new.volume_source) == (10, "padrao")
    assert any("JSONL" in w for w in warnings) and any("padrão 10" in w for w in warnings)


@pytest.mark.parametrize("fmt", ["parquet", "xlsx", ""])
def test_unsupported_format(fmt: str) -> None:
    with pytest.raises(InvalidAnswer) as exc:
        _apply(_intent(), Answers(format=fmt))
    assert "CSV, JSON ou JSONL" in exc.value.messages[0]


def test_volume_rejections_then_default() -> None:
    intent = _intent()
    for raw in ("50.000", "0"):
        with pytest.raises(InvalidAnswer) as exc:
            _apply(intent, Answers(volume=raw))
        assert "1 a 10.000" in exc.value.messages[0]
        intent = exc.value.intent
    assert intent.volume_rejections == 2
    new, warnings = _apply(intent, Answers(volume="-5"))
    assert (new.volume, new.volume_source, new.volume_rejections) == (10, "padrao", 0)
    assert "pela 3ª vez" in warnings[0]


def test_valid_volume_resets_rejections() -> None:
    new, _ = _apply(_intent(volume_rejections=2), Answers(volume="300"))
    assert new.volume == 300 and new.volume_rejections == 0


def test_all_or_nothing_with_invalid_item() -> None:
    with pytest.raises(InvalidAnswer) as exc:
        _apply(_intent(), Answers({"objective": "o"}, format="xml", volume="7"))
    assert exc.value.intent.objective.status == "pendente"
    assert exc.value.intent.volume is None


def test_empty_text_is_rejected() -> None:
    with pytest.raises(InvalidAnswer, match="--unknown rules"):
        _apply(_intent(), Answers({"rules": "   "}))


def test_masking_failure_writes_nothing() -> None:
    def broken() -> Masker:
        raise PolicyError(0, "padrão 0: regex inválida")

    with pytest.raises(MaskingUnavailable, match="regex inválida"):
        apply_answers(_intent(), Answers({"objective": "o"}), broken)


def test_masker_is_not_called_without_text() -> None:
    def must_not_run() -> Masker:
        raise AssertionError("mascaramento chamado sem texto")

    new, _ = apply_answers(_intent(), Answers(format="json"), must_not_run)
    assert new.format == "json"


def test_new_answer_clears_confirmation() -> None:
    confirmed = _intent(confirmed_at="2026-10-12T09:00:00Z")
    new, _ = _apply(confirmed, Answers(format="csv"))
    assert new.confirmed_at is None


@pytest.mark.parametrize(
    ("raw", "value"),
    [("2000", 2000), ("2.000", 2000), ("2 000", 2000), ("-5", -5), ("dez", None), ("1e3", None)],
)
def test_parse_volume(raw: str, value: int | None) -> None:
    assert parse_volume(raw) == value


def test_answers_helpers() -> None:
    assert Answers().empty
    assert Answers(format="x", unknown={"format", "rules"}).conflicts() == ["format"]
    assert Answers({"rules": "r"}, volume="1", unknown={"volume"}).conflicts() == ["volume"]
