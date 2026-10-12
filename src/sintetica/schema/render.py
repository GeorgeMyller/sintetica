"""Tabela Markdown do contrato e diferenças entre versões (RF-14, RF-15)."""

from __future__ import annotations

from dataclasses import dataclass

from sintetica.schema.spec import FieldSpecModel, SchemaSpecModel
from sintetica.schema.walk import walk

_TYPE_LABEL = {
    "text": "texto",
    "int": "inteiro",
    "decimal": "decimal",
    "bool": "booleano",
    "date": "data",
    "datetime": "data-hora",
    "enum": "enum",
    "list": "lista",
    "object": "objeto",
}


def _cell(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def describe_constraints(field: FieldSpecModel) -> str:
    c = field.constraints
    parts: list[str] = []
    if c.ge is not None:
        parts.append(f"≥ {c.ge}")
    if c.le is not None:
        parts.append(f"≤ {c.le}")
    if c.min_length is not None:
        parts.append(f"tamanho ≥ {c.min_length}")
    if c.max_length is not None:
        parts.append(f"tamanho ≤ {c.max_length}")
    if c.pattern is not None:
        parts.append(f"padrão {c.pattern}")
    if c.choices:
        parts.append("valores " + ", ".join(c.choices))
    if c.casas_decimais is not None:
        parts.append(f"{c.casas_decimais} casas decimais")
    return "; ".join(parts)


def _type_label(field: FieldSpecModel) -> str:
    label = _TYPE_LABEL[field.type]
    if field.items is not None:
        label += f" de {_TYPE_LABEL[field.items.type]}"
    return label


def render_table(spec: SchemaSpecModel) -> str:
    rows = [
        "| campo | tipo | obrigatório | restrições | descrição |",
        "|-------|------|-------------|------------|-----------|",
    ]
    if spec.kind == "conversation":
        rows.append("| messages | lista de mensagens | sim | tamanho ≥ 1 | turnos da conversa |")
    for path, field, is_item in walk(spec.fields):
        if is_item:
            continue
        name = f"labels.{path}" if spec.kind == "conversation" else path
        rows.append(
            "| "
            + " | ".join(
                _cell(cell)
                for cell in (
                    name,
                    _type_label(field),
                    "sim" if field.required else "não",
                    describe_constraints(field),
                    field.description,
                )
            )
            + " |"
        )
    return "\n".join(rows)


def _flat(spec: SchemaSpecModel) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for path, field, _ in walk(spec.fields):
        attrs: dict[str, object] = {
            "tipo": field.type,
            "obrigatório": field.required,
            "descrição": field.description,
        }
        for name in field.constraints.set_names():
            attrs[name] = getattr(field.constraints, name)
        out[path] = attrs
    return out


@dataclass(frozen=True, slots=True)
class SpecDiff:
    added: list[str]
    removed: list[str]
    changed: list[str]  # "caminho: atributo antes → depois"

    @property
    def empty(self) -> bool:
        return not (self.added or self.removed or self.changed)


def diff_specs(before: SchemaSpecModel, after: SchemaSpecModel) -> SpecDiff:
    old, new = _flat(before), _flat(after)
    added = [p for p in new if p not in old]
    removed = [p for p in old if p not in new]
    changed: list[str] = []
    for path in new:
        if path not in old:
            continue
        for attr in sorted(set(old[path]) | set(new[path])):
            a, b = old[path].get(attr), new[path].get(attr)
            if a != b:
                changed.append(f"{path}: {attr} {a} → {b}")
    return SpecDiff(added, removed, changed)
