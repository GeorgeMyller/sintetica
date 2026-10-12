"""Caminhos de falha de escrita (RF-16, D-15) e injeção do mascaramento."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sintetica import fsutil
from sintetica.intent import Answers, confirm, set_answers, start
from sintetica.intent import model as intent_model
from sintetica.intent.answers import Masker
from sintetica.intent.model import load_intent_model
from sintetica.pii import PiiType

from .conftest import dataset


def _fail_replace(src: object, dst: object) -> None:
    raise OSError(28, "No space left on device", str(dst))


def test_write_atomic_leaves_no_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "x.json"
    target.write_text("antigo", "utf-8")
    monkeypatch.setattr(os, "replace", _fail_replace)
    with pytest.raises(OSError):
        fsutil.write_atomic(target, "novo")
    assert target.read_text("utf-8") == "antigo"
    assert [p.name for p in tmp_path.iterdir()] == ["x.json"]


def _broken_save(*_: object) -> None:
    raise OSError(13, "Permission denied", "intent.json")


def test_set_and_confirm_report_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert start(tmp_path, "d").code == 0
    answers = Answers({"objective": "o", "structure": "s", "rules": "r"}, "json", "5")
    assert set_answers(tmp_path, "d", answers).code == 0
    import sintetica.intent.service as service

    monkeypatch.setattr(service, "save_intent", _broken_save)
    result = set_answers(tmp_path, "d", Answers(format="csv"))
    assert result.code == 10 and "não foi possível gravar" in result.err[0]
    rejected = set_answers(tmp_path, "d", Answers(volume="0"))
    assert rejected.code == 10  # nem o contador de recusas foi gravado
    assert confirm(tmp_path, "d").code == 10
    assert load_intent_model(dataset(tmp_path, "d")).format == "json"


def test_start_reports_intent_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(intent_model, "write_atomic", _broken_save)
    import sintetica.intent.service as service

    monkeypatch.setattr(service, "save_intent", _broken_save)
    result = start(tmp_path, "d")
    assert result.code == 10 and "intent.json" in result.err[0]


class _Upper:
    def mask_text(self, text: str, item: str) -> tuple[str, dict[PiiType, int]]:
        return text.upper(), {}


def test_injected_masker_factory(tmp_path: Path) -> None:
    seen: list[tuple[Path, Path]] = []

    def factory(dataset_dir: Path, policy: Path) -> Masker:
        seen.append((dataset_dir, policy))
        return _Upper()

    start(tmp_path, "d")
    result = set_answers(tmp_path, "d", Answers({"rules": "abc"}), masker_factory=factory)
    assert result.code == 0
    assert load_intent_model(dataset(tmp_path, "d")).rules.text == "ABC"
    assert seen == [(dataset(tmp_path, "d"), tmp_path / ".sintetica" / "policy.json")]
