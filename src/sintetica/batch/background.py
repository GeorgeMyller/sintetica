"""Início do lote em background, num processo separado em sessão própria (D-15, Q45)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from sintetica.batch.lock import DatasetLock
from sintetica.batch.state import log_path

WORKER_MODULE = "sintetica.batch.worker"


def worker_command(project: Path, slug: str, lock_fd: int | None) -> list[str]:
    cmd = [sys.executable, "-m", WORKER_MODULE, str(project), slug]
    if lock_fd is not None:
        cmd += ["--lock-fd", str(lock_fd)]
    return cmd


def popen_options(lock_fd: int | None, *, windows: bool) -> dict[str, Any]:
    """Opções do `Popen` para desligar o processo do terminal e do harness."""
    if windows:
        flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200
        )
        return {"creationflags": flags}
    options: dict[str, Any] = {"start_new_session": True}
    if lock_fd is not None:
        options["pass_fds"] = (lock_fd,)
    return options


def start_background(project: Path, dataset_dir: Path, slug: str, lock: DatasetLock) -> int:
    """Inicia o processo do lote e devolve o PID.

    Em POSIX, o filho herda o descritor da trava e este processo fecha a sua cópia sem
    destravar. No Windows, a trava é solta antes e o filho a pega de novo (estado `iniciando`).
    """
    windows = sys.platform == "win32"
    lock_fd = None if windows else lock.fileno()
    if windows:
        lock.release()
    log = log_path(dataset_dir)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("ab") as out:
        process = subprocess.Popen(
            worker_command(project, slug, lock_fd),
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            cwd=project,
            **popen_options(lock_fd, windows=windows),
        )
    lock.detach()
    return process.pid
