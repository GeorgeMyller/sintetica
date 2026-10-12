"""Testes do módulo dotenv (carregamento de variáveis de ambiente de .env)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sintetica.dotenv import load_dotenv


def test_load_dotenv_nonexistent_file(tmp_path: Path) -> None:
    assert load_dotenv(tmp_path / ".env") == {}


def test_load_dotenv_parses_values_and_comments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
# Comentário no início
OPENAI_API_KEY="sk-fake-openai"
ANTHROPIC_API_KEY='sk-ant-fake'
GEMINI_API_KEY=AIzaSyFakeKey

# Linha vazia acima e com espaços
OLLAMA_HOST = http://127.0.0.1:11434
INVALID_LINE_WITHOUT_EQUALS
EMPTY_KEY=
""",
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    loaded = load_dotenv(env_file)
    assert loaded["OPENAI_API_KEY"] == "sk-fake-openai"
    assert loaded["ANTHROPIC_API_KEY"] == "sk-ant-fake"
    assert loaded["GEMINI_API_KEY"] == "AIzaSyFakeKey"
    assert loaded["OLLAMA_HOST"] == "http://127.0.0.1:11434"

    assert os.environ["OPENAI_API_KEY"] == "sk-fake-openai"
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-fake"
    assert os.environ["GEMINI_API_KEY"] == "AIzaSyFakeKey"
    assert os.environ["OLLAMA_HOST"] == "http://127.0.0.1:11434"


def test_load_dotenv_does_not_overwrite_existing_env_vars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=do-arquivo\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "do-ambiente-existente")

    load_dotenv(env_file)
    assert os.environ["OPENAI_API_KEY"] == "do-ambiente-existente"
