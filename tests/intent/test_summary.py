"""Resumo e regras de confirmação (RF-12 a RF-14, Q39)."""

from __future__ import annotations

from pathlib import Path

from sintetica.intent.model import IntentModel
from sintetica.intent.summary import (
    is_complete,
    is_critical,
    is_ready,
    missing_items,
    needs_confirmation,
    render_summary,
)

DEFINED = {"status": "definido", "text": "x"}
UNKNOWN = {"status": "indefinido", "text": None}


def _intent(**kw: object) -> IntentModel:
    base: dict[str, object] = {
        "slug": "demo",
        "started_at": "2026-10-12T08:00:00Z",
        "objective": DEFINED,
        "structure": DEFINED,
        "rules": UNKNOWN,
        "format": "json",
        "format_source": "usuario",
        "volume": 50,
        "volume_source": "usuario",
    }
    base.update(kw)
    return IntentModel.model_validate(base)


def test_incomplete_lists_missing_items(tmp_path: Path) -> None:
    intent = IntentModel(slug="demo", started_at="2026-10-12T08:00:00Z")
    assert missing_items(intent) == ["objetivo", "estrutura", "regras", "formato", "volume"]
    assert not is_complete(intent) and not needs_confirmation(intent) and not is_ready(intent)
    lines = render_summary(intent, tmp_path)
    assert lines[-1] == "Faltam: objetivo, estrutura, regras, formato, volume."
    assert "  formato:   pendente" in lines


def test_guided_requires_confirmation(tmp_path: Path) -> None:
    intent = _intent()
    assert needs_confirmation(intent)
    assert render_summary(intent, tmp_path)[-1] == (
        "Confirme a intenção: uv run sintetica intent confirm demo"
    )
    confirmed = intent.model_copy(update={"confirmed_at": "2026-10-12T09:00:00Z"})
    assert is_ready(confirmed)
    assert render_summary(confirmed, tmp_path)[-1] == (
        "Próximo passo: uv run sintetica schema build demo"
    )


def test_express_ready_without_confirmation(tmp_path: Path) -> None:
    intent = _intent(mode="expresso", rules=UNKNOWN)
    assert not is_critical(intent) and is_ready(intent)
    assert "schema build demo" in render_summary(intent, tmp_path)[-1]


def test_express_critical_asks_confirmation(tmp_path: Path) -> None:
    intent = _intent(mode="expresso", objective=UNKNOWN, structure=UNKNOWN)
    assert is_critical(intent) and needs_confirmation(intent)
    last = render_summary(intent, tmp_path)[-1]
    assert "1 campo genérico" in last and "intent confirm demo" in last
    only_objective = _intent(mode="expresso", objective=UNKNOWN)
    assert not is_critical(only_objective) and is_ready(only_objective)


def test_marks_defaults_and_truncates_long_text(tmp_path: Path) -> None:
    long_text = "palavra " * 30
    intent = _intent(
        objective={"status": "definido", "text": long_text},
        format="jsonl",
        format_source="padrao",
        volume=10,
        volume_source="padrao",
    )
    lines = render_summary(intent, tmp_path)
    assert "  formato:   jsonl (padrão)" in lines and "  volume:    10 (padrão)" in lines
    objective = next(line for line in lines if "objetivo" in line)
    shown = objective.split('"')[1]
    assert len(shown) == 80 and shown.endswith("…")
    assert lines[1] == f"Pasta: {tmp_path.resolve()}"
    assert "  regras:    indefinido" in lines
