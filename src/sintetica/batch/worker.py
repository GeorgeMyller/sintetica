"""Ponto de entrada do processo em background (`python -m sintetica.batch.worker`).

Não é comando para o usuário. A saída vai para `output/worker.log`, só com contagens.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from sintetica.batch.lock import DatasetLock
from sintetica.batch.service import EXIT_BUSY, STARTING_GRACE_S, run_worker
from sintetica.batch.state import lock_path


def _progress(line: str) -> None:
    print(line, flush=True)


def _lock(dataset: Path, fd: int | None) -> DatasetLock | None:
    path = lock_path(dataset)
    if fd is not None:
        return DatasetLock.adopt(path, fd)
    lock = DatasetLock(path)  # Windows: a trava foi solta pelo pai (D-16)
    deadline = time.monotonic() + STARTING_GRACE_S
    while not lock.acquire():
        if time.monotonic() > deadline:
            return None
        time.sleep(0.2)
    return lock


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sintetica-worker")
    parser.add_argument("project", type=Path)
    parser.add_argument("slug")
    parser.add_argument("--lock-fd", type=int, default=None)
    args = parser.parse_args(argv)
    lock = _lock(args.project / "datasets" / args.slug, args.lock_fd)
    if lock is None:
        print("erro: outro processo segura a trava do lote", flush=True)
        return EXIT_BUSY
    try:
        result = run_worker(args.project, args.slug, progress=_progress)
    except Exception as exc:  # sem traceback no log: a mensagem poderia citar um registro
        print(f"erro inesperado no lote: {type(exc).__name__}", flush=True)
        return 1
    finally:
        lock.release()
    for line in result.out:
        print(line, flush=True)
    for line in result.err:
        print(f"erro: {line}", flush=True)
    return result.code


if __name__ == "__main__":
    sys.exit(main())
