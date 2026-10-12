"""Integração do instalador com o runtime real (feature 008, T011).

Copia o pacote npm, gera o wheel com `uv build`, instala num projeto temporário pelo
`bin/sintetica.js` e roda o lançador `.sintetica/bin/sintetica`. Pulado sem `uv` ou `node`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INSTALLER = ROOT / "installer"


def _tool(name: str, *fallbacks: Path) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    return next((str(p) for p in fallbacks if p.exists()), None)


UV = _tool("uv", Path.home() / ".local" / "bin" / "uv")
NODE = _tool("node", Path.home() / ".volta" / "bin" / "node")

pytestmark = pytest.mark.skipif(
    UV is None or NODE is None or os.name == "nt", reason="exige uv e node (POSIX)"
)


@pytest.fixture(scope="module")
def package(tmp_path_factory: pytest.TempPathFactory) -> Path:
    pkg = tmp_path_factory.mktemp("pkg")
    for name in ("bin", "src", "skills", "templates"):
        shutil.copytree(INSTALLER / name, pkg / name)
    shutil.copy(INSTALLER / "package.json", pkg / "package.json")
    assert UV is not None
    subprocess.run(
        [UV, "build", "--wheel", "--out-dir", str(pkg / "runtime"), str(ROOT)],
        check=True,
        capture_output=True,
    )
    return pkg


def _env() -> dict[str, str]:
    assert UV is not None
    env = {k: v for k, v in os.environ.items() if k not in ("SINTETICA_CMD", "VIRTUAL_ENV")}
    env["PATH"] = os.pathsep.join([str(Path(UV).parent), "/usr/bin", "/bin"])
    return env


def test_launcher_runs_the_installed_wheel(package: Path, tmp_path: Path) -> None:
    project = tmp_path / "projeto"
    (project / ".claude").mkdir(parents=True)
    assert NODE is not None
    install = subprocess.run(
        [NODE, str(package / "bin" / "sintetica.js"), "install", "--dir", str(project)],
        capture_output=True,
        text=True,
        env=_env(),
        stdin=subprocess.DEVNULL,
    )
    assert install.returncode == 0, install.stdout + install.stderr
    assert "✓ Runtime: .sintetica/bin/sintetica (wheel sintetica-0.1.0)" in install.stdout
    launcher = project / ".sintetica" / "bin" / "sintetica"
    started = subprocess.run(
        [str(launcher), "start", "Pedidos"], cwd=project, capture_output=True, text=True, env=_env()
    )
    assert started.returncode == 0, started.stderr
    assert "Próximo: .sintetica/bin/sintetica intent questions --mode guiado" in started.stdout
    assert (project / "datasets" / "pedidos" / "intent.json").exists()
    assert not (project / "pyproject.toml").exists()
