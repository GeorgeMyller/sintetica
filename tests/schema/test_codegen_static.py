"""Verificação estática do código gerado: mypy --strict e ruff (RF-20, Q36, D-20)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from sintetica.schema.codegen import generate_code
from sintetica.schema.csvflat import flatten_for_csv
from sintetica.schema.names import normalize_names
from sintetica.schema.version import schema_version

from .conftest import VALID_FIXTURES, load_fixture, spec_of

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"

pytestmark = pytest.mark.codegen


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("generated")
    for name in VALID_FIXTURES:
        spec, _ = normalize_names(spec_of(load_fixture(name)))
        if spec.format == "csv":
            flat = flatten_for_csv(spec)
            assert not isinstance(flat, list)
            spec = flat[0]
        (out / f"schema_{name}.py").write_text(generate_code(spec, schema_version(spec)), "utf-8")
    return out


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, cwd=ROOT, check=False)


def _tool(name: str) -> str:
    path = shutil.which(name, path=str(Path(sys.executable).parent))
    if path is None:
        pytest.skip(f"{name} indisponível")
    return path


def test_generated_code_passes_mypy_strict(generated: Path) -> None:
    files = sorted(str(p) for p in generated.glob("*.py"))
    result = _run(_tool("mypy"), "--strict", "--config-file", str(PYPROJECT), *files)
    assert result.returncode == 0, result.stdout + result.stderr


def test_generated_code_passes_ruff_check(generated: Path) -> None:
    result = _run(_tool("ruff"), "check", "--config", str(PYPROJECT), str(generated))
    assert result.returncode == 0, result.stdout + result.stderr


def test_generated_code_is_ruff_formatted(generated: Path) -> None:
    result = _run(_tool("ruff"), "format", "--check", "--config", str(PYPROJECT), str(generated))
    assert result.returncode == 0, result.stdout + result.stderr


def test_static_checks_detect_errors(tmp_path: Path) -> None:
    """Controle negativo: as mesmas chamadas falham num arquivo com erro."""
    bad = tmp_path / "ruim.py"
    bad.write_text('x: int = "texto"\nimport os\n', "utf-8")
    assert (
        _run(_tool("mypy"), "--strict", "--config-file", str(PYPROJECT), str(bad)).returncode != 0
    )
    assert _run(_tool("ruff"), "check", "--config", str(PYPROJECT), str(tmp_path)).returncode != 0
