"""Skills do instalador (feature 008): comandos citados, política padrão e versão (D-12, D-15)."""

from __future__ import annotations

import argparse
import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from sintetica.cli import _parser
from sintetica.pii.policy import load_custom_patterns
from sintetica.providers.policy import load_provider_policy

ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "installer"
SKILLS = [
    "sintetica-start",
    "sintetica-schema",
    "sintetica-sample",
    "sintetica-generate",
    "sintetica-eval",
]
COMMAND = re.compile(r"\.sintetica[/\\]bin[/\\]sintetica(?:\.cmd)?((?: [a-z][a-z-]*){1,2})")


def _subcommands(parser: argparse.ArgumentParser) -> dict[str, argparse.ArgumentParser]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    return {}


def _skill_text(name: str) -> str:
    return (INSTALLER / "skills" / name / "SKILL.md").read_text("utf-8")


@pytest.mark.parametrize("name", SKILLS)
def test_skill_has_frontmatter(name: str) -> None:
    text = _skill_text(name)
    assert text.startswith(f"---\nname: {name}\ndescription: ")
    assert "\n---\n" in text[4:]


@pytest.mark.parametrize("name", SKILLS)
def test_every_cited_command_exists(name: str) -> None:
    top = _subcommands(_parser())
    found = COMMAND.findall(_skill_text(name))
    assert found, name
    for words in found:
        parts = words.split()
        assert parts[0] in top, f"{name}: comando {parts[0]!r}"
        nested = _subcommands(top[parts[0]])
        if nested and len(parts) > 1:
            assert parts[1] in nested, f"{name}: subcomando {parts[0]} {parts[1]!r}"


def test_skills_never_cite_uv_run() -> None:
    for name in SKILLS:
        assert "uv run sintetica" not in _skill_text(name), name


def test_default_policy_is_accepted_by_the_runtime() -> None:
    path = INSTALLER / "templates" / "policy.json"
    policy = load_provider_policy(path)
    assert policy.cost_ceiling_usd == Decimal("5")
    assert policy.pii_premask is True
    assert policy.provider_priority == ("harness", "ollama", "external")
    assert load_custom_patterns(path) == ()
    assert json.loads(path.read_text("utf-8"))["telemetry"] is False


def test_npm_and_python_versions_match() -> None:
    package = json.loads((INSTALLER / "package.json").read_text("utf-8"))
    # Sem tomllib: o projeto aceita Python 3.10.
    match = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text("utf-8"), re.M)
    assert match is not None and package["version"] == match.group(1)
