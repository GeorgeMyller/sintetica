"""CLI `sintetica request` / `submit` contra interfaces/harness-cli.md."""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import pytest

from sintetica.cli import main


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "datasets" / "demo").mkdir(parents=True)
    (tmp_path / "schema.json").write_text(
        json.dumps({"type": "object", "properties": {"nome": {"type": "string"}}}), "utf-8"
    )
    return tmp_path


def _request(project: Path, *extra: str, n: str = "10") -> int:
    return main(
        [
            "request",
            "demo",
            "--n-records",
            n,
            "--instructions",
            "clientes de uma loja",
            "--schema",
            str(project / "schema.json"),
            "--project-dir",
            str(project),
            *extra,
        ]
    )


def _submit(project: Path, rid: str, data: bytes, monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(data)))
    return main(["submit", "demo", rid, "--project-dir", str(project)])


def _rid(output: str) -> str:
    match = re.search(r"id: ([0-9a-f]{12})", output)
    assert match is not None
    return match.group(1)


def _requests(project: Path) -> set[str]:
    folder = project / "datasets" / "demo" / "requests"
    return {p.name for p in folder.iterdir()} if folder.exists() else set()


def test_full_protocol(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _request(project) == 0
    out = capsys.readouterr().out
    rid = _rid(out)
    assert f"uv run sintetica submit demo {rid}" in out
    assert str((project / "datasets" / "demo" / "requests" / f"{rid}.json").resolve()) in out

    records = "".join(json.dumps({"nome": f"p{i}"}) + "\n" for i in range(10)).encode()
    assert _submit(project, rid, records, monkeypatch) == 0
    assert "10 registros" in capsys.readouterr().out
    assert _requests(project) == {f"{rid}.json", f"{rid}.response.jsonl"}

    assert _submit(project, rid, records[:20], monkeypatch) == 5  # linha cortada
    assert _submit(project, rid, b'{"nome": "x"}\n', monkeypatch) == 0
    assert "substituída" in capsys.readouterr().out


def test_submit_unknown_request(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _submit(project, "r9", b'{"a": 1}\n', monkeypatch) == 4
    assert "pedido inexistente" in capsys.readouterr().err
    assert _requests(project) == set()


@pytest.mark.parametrize("data", [b"", b"[1]\n", b'{"a": 1}\n' * 11])
def test_submit_invalid_response(
    project: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    data: bytes,
) -> None:
    assert _request(project) == 0
    rid = _rid(capsys.readouterr().out)
    assert _submit(project, rid, data, monkeypatch) == 5
    assert _requests(project) == {f"{rid}.json"}


def test_request_limit_and_validation(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _request(project, n="101") == 3
    assert "até 100 registros" in capsys.readouterr().err
    assert _request(project, n="0") == 2
    assert _requests(project) == set()


def test_unknown_dataset(
    project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    code = main(["submit", "outro", "abc", "--project-dir", str(project)])
    assert code == 2
    assert "datasets/outro" in capsys.readouterr().err
    code = main(
        [
            *("request", "outro", "--n-records", "1", "--instructions", "x"),
            *("--schema", "s.json", "--project-dir", str(project)),
        ]
    )
    assert code == 2


def test_request_with_seeds(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    seeds = project / "seeds.jsonl"
    seeds.write_text('{"nome": "Ana"}\n\n{"nome": "Bia"}\n', "utf-8")
    assert _request(project, "--seeds", str(seeds)) == 0
    rid = _rid(capsys.readouterr().out)
    saved = json.loads(
        (project / "datasets" / "demo" / "requests" / f"{rid}.json").read_text("utf-8")
    )
    assert saved["seeds"] == [{"nome": "Ana"}, {"nome": "Bia"}]


@pytest.mark.parametrize(
    ("schema", "seeds"),
    [("{nao json", None), ("[1]", None), ('{"type": "object"}', "[1]\n")],
)
def test_request_with_invalid_files(
    project: Path, schema: str, seeds: str | None, capsys: pytest.CaptureFixture[str]
) -> None:
    (project / "schema.json").write_text(schema, "utf-8")
    extra: list[str] = []
    if seeds is not None:
        (project / "seeds.jsonl").write_text(seeds, "utf-8")
        extra = ["--seeds", str(project / "seeds.jsonl")]
    assert _request(project, *extra) == 2
    assert capsys.readouterr().err.startswith("erro:")
    assert _requests(project) == set()
