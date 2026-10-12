"""Trava por dataset em `output/run.lock` (D-16).

A trava é do sistema operacional e some quando o processo termina, mesmo morto à força;
por isso ela, e não o PID, diz se o lote ainda roda. Em POSIX, o processo em background
herda o descritor do processo que o iniciou.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


def _try_lock(fd: int) -> bool:
    if sys.platform == "win32":
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(fd: int) -> None:
    if sys.platform == "win32":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)


class DatasetLock:
    def __init__(self, path: Path, fd: int | None = None) -> None:
        self.path = path
        self._fd = fd

    @classmethod
    def adopt(cls, path: Path, fd: int) -> DatasetLock:
        """Trava já obtida pelo processo pai e herdada pelo descritor `fd`."""
        return cls(path, fd)

    @property
    def held(self) -> bool:
        return self._fd is not None

    def fileno(self) -> int:
        if self._fd is None:
            raise RuntimeError("trava não obtida")
        return self._fd

    def acquire(self) -> bool:
        """Tenta obter a trava sem esperar."""
        if self._fd is not None:
            return True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        if not _try_lock(fd):
            os.close(fd)
            return False
        self._fd = fd
        return True

    def release(self) -> None:
        if self._fd is None:
            return
        try:
            _unlock(self._fd)
        finally:
            os.close(self._fd)
            self._fd = None

    def detach(self) -> None:
        """Fecha a cópia deste processo sem destravar: o processo filho mantém a trava."""
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None


def is_locked(path: Path) -> bool:
    """`True` se outro descritor (deste ou de outro processo) segura a trava."""
    if not path.exists():
        return False
    probe = DatasetLock(path)
    if not probe.acquire():
        return True
    probe.release()
    return False
