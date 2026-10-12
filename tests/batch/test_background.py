"""Trava, background com processo real e retomada (D-15 a D-17, Q45)."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from sintetica.batch import service
from sintetica.batch.background import popen_options, worker_command
from sintetica.batch.lock import DatasetLock, is_locked
from sintetica.batch.state import lock_path

from .conftest import CPF, OllamaServer, dataset, prepare, run_state

WAIT_S = 60.0


def _wait(condition: Callable[[], bool], timeout: float = WAIT_S) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.1)
    raise AssertionError("tempo esgotado")


def _status_is(project: Path, *statuses: str) -> Callable[[], bool]:
    def check() -> bool:
        path = dataset(project) / "output" / "run.json"
        if not path.exists():
            return False
        status = json.loads(path.read_text("utf-8"))["status"]
        return status in statuses and not is_locked(lock_path(dataset(project)))

    return check


def test_lock_is_exclusive_and_released(tmp_path: Path) -> None:
    path = tmp_path / "output" / "run.lock"
    assert not is_locked(path)
    first = DatasetLock(path)
    assert first.acquire() and first.acquire() and first.held
    assert is_locked(path)
    assert not DatasetLock(path).acquire()
    first.release()
    first.release()
    assert not is_locked(path)
    try:
        DatasetLock(path).fileno()
    except RuntimeError:
        pass
    else:
        raise AssertionError("fileno sem trava")


def test_lock_dies_with_the_process(tmp_path: Path) -> None:
    path = tmp_path / "run.lock"
    code = (
        "import sys, time; from pathlib import Path; "
        "from sintetica.batch.lock import DatasetLock; "
        f"lock = DatasetLock(Path({str(path)!r})); assert lock.acquire(); "
        "print('ok', flush=True); time.sleep(60)"
    )
    proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE)
    assert proc.stdout is not None and proc.stdout.readline().strip() == b"ok"
    assert is_locked(path)
    proc.kill()
    proc.wait()
    assert not is_locked(path)


def test_popen_options_per_platform() -> None:
    posix = popen_options(7, windows=False)
    assert posix == {"start_new_session": True, "pass_fds": (7,)}
    assert popen_options(None, windows=False) == {"start_new_session": True}
    windows = popen_options(None, windows=True)
    assert windows["creationflags"] == 0x00000008 | 0x00000200
    cmd = worker_command(Path("/p"), "pedidos", 7)
    assert cmd[1:] == ["-m", "sintetica.batch.worker", "/p", "pedidos", "--lock-fd", "7"]
    assert "--lock-fd" not in worker_command(Path("/p"), "pedidos", None)


def test_background_lot_returns_fast_and_finishes(project: Path, ollama: OllamaServer) -> None:
    prepare(project, volume=150)
    started = time.monotonic()
    result = service.generate(project, "pedidos")
    assert result.code == 0, result.err
    assert time.monotonic() - started <= 5
    assert any("uv run sintetica status pedidos" in line for line in result.out)
    _wait(_status_is(project, "concluido"))
    state = run_state(project)
    assert state.mode == "background" and state.pid is not None and state.pid != os.getpid()
    lines = (dataset(project) / "output" / "dataset.json").read_text("utf-8")
    assert len(json.loads(lines)) == 150
    log = (dataset(project) / "output" / "worker.log").read_text("utf-8")
    assert "Bloco 1/15" in log and "Lote concluido" in log
    shown = service.status(project, "pedidos")
    assert shown.code == 0 and "concluido" in shown.out[0]


def test_killed_process_is_detected_and_resumed(project: Path, ollama: OllamaServer) -> None:
    ollama.delay_s = 0.3
    prepare(project, volume=400)
    assert service.generate(project, "pedidos").code == 0
    partial = dataset(project) / "output" / "records.partial.jsonl"
    _wait(lambda: partial.exists() and partial.stat().st_size > 0)
    running = service.status(project, "pedidos")
    assert running.code == 0 and "em_andamento" in running.out[0]
    busy = service.generate(project, "pedidos", resume=True)
    assert busy.code == 16 and "em andamento" in busy.err[0]
    pid = run_state(project).pid
    assert pid is not None
    os.kill(pid, signal.SIGKILL)
    _wait(lambda: not is_locked(lock_path(dataset(project))))
    stopped = service.status(project, "pedidos")
    assert any("Processo encerrado" in line for line in stopped.out)
    assert any("--resume" in line for line in stopped.out)
    ollama.delay_s = 0.0
    assert service.generate(project, "pedidos", resume=True).code == 0
    _wait(_status_is(project, "concluido"))
    records = json.loads((dataset(project) / "output" / "dataset.json").read_text("utf-8"))
    assert len(records) == 400 and len({json.dumps(r) for r in records}) == 400


def test_status_without_lot(project: Path) -> None:
    assert service.status(project, "pedidos").code == 2
    prepare(project, volume=10)
    result = service.status(project, "pedidos")
    assert result.code == 16 and "nenhum lote" in result.err[0]
    (dataset(project) / "output").mkdir()
    (dataset(project) / "output" / "run.json").write_text("[]", "utf-8")
    assert service.status(project, "pedidos").code == 2


def test_spawner_failure_and_worker_guard(project: Path) -> None:
    prepare(project, volume=150)

    def broken(*_: object) -> int:
        raise OSError(12, "Cannot allocate memory")

    result = service.generate(project, "pedidos", spawner=broken)
    assert result.code == 10 and "iniciar o processo" in result.err[0]
    assert service.run_worker(project, "outro").code == 2
    state_file = dataset(project) / "output" / "run.json"
    data = json.loads(state_file.read_text("utf-8"))
    data["status"] = "concluido"
    state_file.write_text(json.dumps(data), "utf-8")
    assert service.run_worker(project, "pedidos").code == 16


def test_worker_refuses_when_lock_is_taken(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sintetica.batch import worker

    prepare(project, volume=150)
    lock = DatasetLock(lock_path(dataset(project)))
    assert lock.acquire()
    monkeypatch.setattr(worker, "STARTING_GRACE_S", 0)
    try:
        assert worker.main([str(project), "pedidos"]) == 16
    finally:
        lock.release()


def test_worker_hides_unexpected_errors(
    project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from sintetica.batch import worker

    def boom(*_: object, **__: object) -> object:
        raise TypeError(f"valor {CPF} inesperado")

    monkeypatch.setattr(worker, "run_worker", boom)
    prepare(project, volume=150)
    assert worker.main([str(project), "pedidos"]) == 1
    out = capsys.readouterr().out
    assert "erro inesperado no lote: TypeError" in out and CPF not in out
    assert not is_locked(lock_path(dataset(project)))
