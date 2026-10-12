"""Revisão: validação, duplicados, mascaramento e revalidação (D-07, D-08)."""

from __future__ import annotations

from pathlib import Path

from sintetica.sample.review import parse_line, review_records
from sintetica.schema import load_record_model

from .conftest import prepare


def _identity(text: str, path: str) -> str:
    return text


def test_valid_invalid_and_duplicates(project: Path) -> None:
    model = load_record_model(prepare(project))
    raw: list[dict[str, object]] = [
        {"cliente": "Ana", "valor": "19.9"},
        {"cliente": "Bia", "valor": 99},
        {"cliente": "Ana", "valor": "19.90"},  # duplicado no mesmo lote
        {"cliente": "Caio", "valor": 7},
        {"cliente": "Duda", "valor": 8, "extra": 1},
    ]
    result = review_records(raw, model, ['{"cliente":"Caio","valor":7.00}'], _identity, 3)
    assert result.accepted == ['{"cliente":"Ana","valor":19.90}']
    assert result.rejected == [
        "registro 2: valor: Input should be less than or equal to 50",
        "registro 3: duplicado",
        "registro 4: duplicado",
        "registro 5: extra: Extra inputs are not permitted",
    ]
    assert "99" not in " ".join(result.rejected)


def test_limit_discards_extra_records(project: Path) -> None:
    model = load_record_model(prepare(project))
    raw = [{"cliente": c, "valor": 10} for c in ("A", "B", "C")]
    result = review_records(raw, model, [], _identity, 2)
    assert len(result.accepted) == 2
    assert result.rejected == ["registro 3: excede os 2 pedidos"]


def test_masking_is_applied_with_field_path(project: Path) -> None:
    model = load_record_model(prepare(project))
    seen: list[str] = []

    def masker(text: str, path: str) -> str:
        seen.append(path)
        return text.upper()

    result = review_records([{"cliente": "ana", "valor": 10}], model, [], masker, 3)
    assert seen == ["cliente"]
    assert parse_line(result.accepted[0])["cliente"] == "ANA"


def test_mask_that_breaks_the_contract_rejects_record(project: Path) -> None:
    draft = {
        "format": "json",
        "fields": [{"name": "codigo", "type": "text", "constraints": {"pattern": "^[a-z]+$"}}],
    }
    model = load_record_model(prepare(project, draft=draft))

    def breaking(text: str, path: str) -> str:
        return "XYZ"

    result = review_records([{"codigo": "abc"}], model, [], breaking, 3)
    assert result.accepted == []
    assert result.rejected[0].startswith("registro 1: o valor falso do mascaramento quebrou")
