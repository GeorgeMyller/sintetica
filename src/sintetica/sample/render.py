"""Exibição da amostra: tabela para CSV, blocos JSON para JSON e JSONL (D-10)."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel

from sintetica.sample.review import parse_line
from sintetica.schema import csv_columns, to_csv_row, to_json_obj
from sintetica.schema.formats import to_json_text


def _cell(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_records(lines: Sequence[str], model: type[BaseModel], fmt: str) -> list[str]:
    if not lines:
        return ["(nenhum registro aceito)"]
    records = [model.model_validate(parse_line(line)) for line in lines]
    if fmt == "csv":
        columns = csv_columns(model)
        out = [
            "| " + " | ".join(columns) + " |",
            "|" + "|".join("---" for _ in columns) + "|",
        ]
        for record in records:
            row = to_csv_row(record)
            out.append("| " + " | ".join(_cell(row[c]) for c in columns) + " |")
        return out
    out = []
    for number, record in enumerate(records, start=1):
        out.append(f"Registro {number}:")
        out.append("```json")
        out.extend(to_json_text(to_json_obj(record), indent=2).splitlines())
        out.append("```")
    return out
