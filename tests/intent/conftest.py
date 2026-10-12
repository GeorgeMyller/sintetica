from __future__ import annotations

from pathlib import Path

import pytest

from sintetica.cli import main


def run(project: Path, *args: str) -> int:
    """Executa `sintetica` com `--project-dir` no final do subcomando."""
    return main([*args, "--project-dir", str(project)])


def dataset(project: Path, slug: str) -> Path:
    return project / "datasets" / slug


def all_text(project: Path) -> str:
    """Conteúdo de todos os arquivos do projeto, para procurar valores originais de PII."""
    return "\n".join(
        p.read_text("utf-8", errors="ignore") for p in project.rglob("*") if p.is_file()
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return tmp_path
