"""Arquivo parcial, retomada e conversão final (D-12, D-13, D-19).

`records.partial.jsonl` é a fonte da verdade do progresso: cada bloco é anexado com `fsync`
antes de `run.json` mudar. Tudo é lido e escrito em fluxo, sem carregar o lote na memória.
"""

from __future__ import annotations

import csv
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel

from sintetica.batch.review import DedupIndex
from sintetica.sample.review import parse_line
from sintetica.schema import csv_columns, to_csv_row


def append_block(path: Path, lines: list[str]) -> None:
    """Anexa o bloco com `fsync`. Em erro, trunca o arquivo ao fim do bloco anterior."""
    if not lines:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    start = path.stat().st_size if path.exists() else 0
    data = "".join(f"{line}\n" for line in lines).encode("utf-8")
    with path.open("ab") as f:
        try:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        except OSError:
            try:
                f.truncate(start)
                f.flush()
                os.fsync(f.fileno())
            except OSError:
                pass  # a leitura descarta a linha incompleta (load_partial)
            raise


def load_partial(path: Path, index: DedupIndex) -> int:
    """Conta os registros gravados e reconstrói o índice de duplicados.

    Uma última linha sem quebra (queda no meio da escrita) é descartada do arquivo.
    """
    if not path.exists():
        return 0
    count = 0
    offset = 0
    torn: int | None = None
    with path.open("rb") as f:
        for raw in f:
            if not raw.endswith(b"\n"):
                torn = offset
                break
            offset += len(raw)
            line = raw.decode("utf-8").rstrip("\n")
            if line:
                index.add_masked(line)
                count += 1
    if torn is not None:
        with path.open("r+b") as f:
            f.truncate(torn)
            f.flush()
            os.fsync(f.fileno())
    return count


def _lines(path: Path) -> Iterator[str]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line:
                yield line


def convert_final(src: Path, dest: Path, fmt: str, model: type[BaseModel]) -> Path:
    """Converte o parcial em `dataset.<ext>`: lista JSON, JSONL ou CSV pela RFC 4180."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as out:
            if fmt == "csv":
                columns = csv_columns(model)
                writer = csv.writer(out, lineterminator="\r\n")
                writer.writerow(columns)
                for line in _lines(src):
                    row = to_csv_row(model.model_validate(parse_line(line)))
                    writer.writerow([row[name] for name in columns])
            elif fmt == "json":
                first = True
                out.write("[")
                for line in _lines(src):
                    out.write(f"\n{line}" if first else f",\n{line}")
                    first = False
                out.write("]\n" if first else "\n]\n")
            else:
                for line in _lines(src):
                    out.write(f"{line}\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, dest)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return dest
