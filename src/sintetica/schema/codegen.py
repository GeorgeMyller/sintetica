"""Gerador determinístico de `schema.py` (RF-05, D-09 a D-11).

Regras de segurança (RN-02): nenhum texto da definição é interpolado como código. Nomes de
campo já chegam normalizados (identificadores ASCII); todo o resto entra por `py_str`.
Toda construção com colchetes ou parênteses sai expandida com vírgula final, o que torna a
saída estável sob `ruff format`.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from decimal import Decimal

from sintetica.schema.checks import parse_bound
from sintetica.schema.spec import FieldSpecModel, SchemaSpecModel

HEADER = "# Gerado por sintetica.schema; não edite."
VERSION_PREFIX = "# schema_version: "
MAX_LINE = 100

_SIMPLE = {
    "text": "str",
    "int": "int",
    "decimal": "Decimal",
    "bool": "bool",
    "date": "datetime.date",
    "datetime": "datetime.datetime",
}
_RESERVED_NAMES = frozenset(
    {
        "Record",
        "Message",
        "Labels",
        "Annotated",
        "Literal",
        "Decimal",
        "BaseModel",
        "ConfigDict",
        "Field",
        "AfterValidator",
    }
)


def _escape_code_point(code: int) -> str:
    if code < 0x100:
        return f"\\x{code:02x}"
    if code < 0x10000:
        return f"\\u{code:04x}"
    return f"\\U{code:08x}"


def py_str(text: str) -> str:
    """Literal de texto Python seguro, com a aspa que o `ruff format` escolheria."""
    quote = "'" if text.count('"') > text.count("'") else '"'
    out: list[str] = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == quote:
            out.append("\\" + quote)
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif not ch.isprintable():
            out.append(_escape_code_point(ord(ch)))
        else:
            out.append(ch)
    return quote + "".join(out) + quote


def _pascal(path: str) -> str:
    parts = [p for p in path.replace("[]", "_item").replace(".", "_").split("_") if p]
    return "".join(p[:1].upper() + p[1:] for p in parts) or "Campo"


def _expanded(head: str, items: list[str], indent: str, close: str) -> list[str]:
    lines = [f"{head}"]
    lines.extend(f"{indent}    {item}," for item in items)
    lines.append(f"{indent}{close}")
    return lines


@dataclass
class _Module:
    csv: bool
    imports: set[str] = field(default_factory=set)
    names: set[str] = field(default_factory=lambda: set(_RESERVED_NAMES))
    blocks: list[list[str]] = field(default_factory=list)

    def unique(self, base: str) -> str:
        name, n = base, 2
        while name in self.names:
            name, n = f"{base}{n}", n + 1
        self.names.add(name)
        return name

    # -- tipos --------------------------------------------------------------

    def literal(self, path: str, choices: list[str]) -> str:
        self.imports.add("Literal")
        alias = self.unique(_pascal(path) + "Choices")
        block = _expanded(f"{alias} = Literal[", [py_str(c) for c in choices], "", "]")
        self.blocks.append(block)
        return alias

    def base_type(self, path: str, f: FieldSpecModel) -> str:
        if f.type in _SIMPLE:
            if f.type == "decimal":
                self.imports.add("Decimal")
            if f.type in ("date", "datetime"):
                self.imports.add("datetime")
            return _SIMPLE[f.type]
        if f.type == "enum":
            return self.literal(path, f.constraints.choices or [])
        if f.type == "object":
            return self.model(self.unique(_pascal(path)), path, f.fields or [])
        assert f.items is not None
        return f"list[{self.item_type(path + '[]', f.items)}]"

    def item_type(self, path: str, item: FieldSpecModel) -> str:
        base = self.base_type(path, item)
        kwargs = self.field_kwargs(item, with_description=False, optional=False)
        validators = ["AfterValidator(no_pipe)"] if self.csv and item.type == "text" else []
        if not kwargs and not validators:
            return base
        self.imports.add("Annotated")
        if validators:
            self.imports.update({"no_pipe", "AfterValidator"})
        alias = self.unique(_pascal(path) + "Type")
        parts = [base]
        if kwargs:
            self.imports.add("Field")
            parts.append("\n".join(_expanded("Field(", kwargs, "    ", ")")))
        parts.extend(validators)
        self.blocks.append(_expanded(f"{alias} = Annotated[", parts, "", "]"))
        return alias

    # -- campos e modelos ----------------------------------------------------

    def field_kwargs(
        self, f: FieldSpecModel, *, with_description: bool, optional: bool
    ) -> list[str]:
        c = f.constraints
        kwargs: list[str] = []
        if optional:
            kwargs.append("default=None")
        for name in ("ge", "le"):
            value = getattr(c, name)
            if value is not None:
                kwargs.append(f"{name}={self.bound_literal(f.type, value)}")
        if c.min_length is not None:
            kwargs.append(f"min_length={c.min_length}")
        if c.max_length is not None:
            kwargs.append(f"max_length={c.max_length}")
        if c.pattern is not None:
            kwargs.append(f"pattern={py_str(c.pattern)}")
        if c.casas_decimais is not None:
            kwargs.append(f"decimal_places={c.casas_decimais}")
        if with_description:
            kwargs.append(f"description={py_str(f.description)}")
        return kwargs

    def bound_literal(self, field_type: str, value: int | float | str) -> str:
        parsed = parse_bound(field_type, value)
        if isinstance(parsed, Decimal):
            self.imports.add("Decimal")
            return f"Decimal({py_str(str(parsed))})"
        if isinstance(parsed, datetime.date):
            self.imports.add("datetime")
            return f"datetime.{field_type}.fromisoformat({py_str(parsed.isoformat())})"
        return str(parsed)

    def field_lines(self, path: str, f: FieldSpecModel) -> list[str]:
        base = self.base_type(path, f)
        type_expr = base if f.required else f"{base} | None"
        kwargs = self.field_kwargs(f, with_description=True, optional=not f.required)
        self.imports.update({"Annotated", "Field"})
        lines = [f"    {f.name}: Annotated["]
        lines.append(f"        {type_expr},")
        lines.extend(_expanded("        Field(", kwargs, "        ", "),"))
        lines.append("    ]")
        return lines

    def model(self, name: str, path: str, fields: list[FieldSpecModel]) -> str:
        body: list[str] = []
        for f in fields:
            child = f"{path}.{f.name}" if path else f.name
            body.extend(self.field_lines(child, f))
        self.imports.update({"BaseModel", "ConfigDict"})
        block = [f"class {name}(BaseModel):", '    model_config = ConfigDict(extra="forbid")', ""]
        block.extend(body)
        self.blocks.append(block)
        return name

    def conversation(self, labels: list[FieldSpecModel]) -> None:
        self.imports.update({"Annotated", "Literal", "Field", "BaseModel", "ConfigDict"})
        self.blocks.append(
            [
                "class Message(BaseModel):",
                '    model_config = ConfigDict(extra="forbid")',
                "",
                "    role: Literal[",
                '        "system",',
                '        "user",',
                '        "assistant",',
                "    ]",
                "    content: Annotated[",
                "        str,",
                "        Field(",
                "            min_length=1,",
                "        ),",
                "    ]",
            ]
        )
        self.model("Labels", "labels", labels)
        self.blocks.append(
            [
                "class Record(BaseModel):",
                '    model_config = ConfigDict(extra="forbid")',
                "",
                "    messages: Annotated[",
                "        list[Message],",
                "        Field(",
                "            min_length=1,",
                "        ),",
                "    ]",
                "    labels: Labels",
            ]
        )

    # -- saída ----------------------------------------------------------------

    def import_lines(self) -> list[str]:
        std: list[str] = []
        if "datetime" in self.imports:
            std.append("import datetime")
        if "Decimal" in self.imports:
            std.append("from decimal import Decimal")
        typing_names = sorted(n for n in ("Annotated", "Literal") if n in self.imports)
        if typing_names:
            std.append(f"from typing import {', '.join(typing_names)}")
        pyd = sorted(
            n for n in ("AfterValidator", "BaseModel", "ConfigDict", "Field") if n in self.imports
        )
        groups = [std, [f"from pydantic import {', '.join(pyd)}"]]
        if "no_pipe" in self.imports:
            groups.append(["from sintetica.schema.validators import no_pipe"])
        out: list[str] = []
        for group in groups:
            if group:
                if out:
                    out.append("")
                out.extend(group)
        return out


def generate_code(spec: SchemaSpecModel, version: str) -> str:
    """Código-fonte de `schema.py`. Mesma definição e versão: mesma saída, byte a byte."""
    mod = _Module(csv=spec.format == "csv")
    if spec.kind == "conversation":
        mod.conversation(list(spec.fields))
    else:
        mod.model("Record", "", list(spec.fields))
    lines = [HEADER, f"{VERSION_PREFIX}{version}", ""]
    lines.extend(mod.import_lines())
    for index, block in enumerate(mod.blocks):
        # isort pede 1 linha após os imports antes de atribuição e 2 antes de classe.
        first_after_imports = index == 0 and not block[0].startswith("class ")
        lines.extend([""] if first_after_imports else ["", ""])
        lines.extend(block)
    return "\n".join(_mark_long(line) for line in lines) + "\n"


def _mark_long(line: str) -> str:
    """Linhas longas só surgem com textos da definição; o formatador não quebra textos."""
    return f"{line}  # noqa: E501" if len(line) > MAX_LINE else line
