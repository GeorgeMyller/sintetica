"""schema-builder: contrato de dados do dataset."""

from sintetica.schema.formats import csv_columns, to_csv_row, to_json_obj, to_jsonl_line
from sintetica.schema.loader import GeneratedCodeError, SchemaNotFoundError, load_record_model
from sintetica.schema.spec import SchemaIssue

__all__ = [
    "GeneratedCodeError",
    "SchemaIssue",
    "SchemaNotFoundError",
    "csv_columns",
    "load_record_model",
    "to_csv_row",
    "to_json_obj",
    "to_jsonl_line",
]
