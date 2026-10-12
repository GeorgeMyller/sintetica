"""Meta-modelo da definição do contrato (`schema.draft.json` e `schema.json`), D-04."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

FieldType = Literal["text", "int", "decimal", "bool", "date", "datetime", "enum", "list", "object"]
DatasetFormat = Literal["csv", "json", "jsonl"]
SpecKind = Literal["records", "conversation"]
# bool primeiro: sem ele, o Pydantic converteria True em 1 e a validação não o veria.
Bound = bool | int | float | str


@dataclass(frozen=True, slots=True)
class SchemaIssue:
    """Um problema da definição, com o caminho do campo (RF-02)."""

    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class Constraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ge: Bound | None = None
    le: Bound | None = None
    min_length: int | None = Field(default=None, ge=0)
    max_length: int | None = Field(default=None, ge=0)
    pattern: str | None = None
    choices: list[str] | None = None
    casas_decimais: int | None = None

    def set_names(self) -> list[str]:
        """Nomes das restrições definidas, na ordem do modelo."""
        return [name for name in type(self).model_fields if getattr(self, name) is not None]


class FieldSpecModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = ""
    type: FieldType
    required: bool = True
    description: str = ""
    constraints: Constraints = Field(default_factory=Constraints)
    items: FieldSpecModel | None = None
    fields: list[FieldSpecModel] | None = None


class SchemaSpecModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: Literal["Record"] = "Record"
    format: DatasetFormat
    kind: SpecKind = "records"
    fields: list[FieldSpecModel] = Field(min_length=1)


def _path(loc: tuple[int | str, ...]) -> str:
    out = ""
    for part in loc:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}" if out else part
    return out or "(raiz)"


def parse_spec(data: object) -> SchemaSpecModel | list[SchemaIssue]:
    """Valida a estrutura da definição. Devolve o modelo ou todos os problemas encontrados."""
    try:
        return SchemaSpecModel.model_validate(data)
    except ValidationError as exc:
        return [SchemaIssue(_path(tuple(err["loc"])), err["msg"]) for err in exc.errors()]


def dump_spec(spec: SchemaSpecModel) -> dict[str, object]:
    """Forma serializável e estável da definição (sem valores ausentes)."""
    return spec.model_dump(mode="json", exclude_none=True)
