"""Resumo da intenção e regras de confirmação (D-11, D-12, D-17, data-delta.md#2)."""

from __future__ import annotations

from pathlib import Path

from sintetica.command import cli_command
from sintetica.intent.model import LABELS, TEXT_ITEMS, IntentModel

MAX_SHOWN = 80


def missing_items(intent: IntentModel) -> list[str]:
    missing = [LABELS[n] for n in TEXT_ITEMS if intent.item(n).status == "pendente"]
    if intent.format is None:
        missing.append(LABELS["format"])
    if intent.volume is None:
        missing.append(LABELS["volume"])
    return missing


def is_complete(intent: IntentModel) -> bool:
    return not missing_items(intent)


def is_critical(intent: IntentModel) -> bool:
    """Objetivo e estrutura indefinidos: o contrato será o padrão de 1 campo (Q39)."""
    return intent.objective.status == "indefinido" and intent.structure.status == "indefinido"


def needs_confirmation(intent: IntentModel) -> bool:
    if not is_complete(intent) or intent.confirmed_at is not None:
        return False
    return intent.mode == "guiado" or is_critical(intent)


def is_ready(intent: IntentModel) -> bool:
    return is_complete(intent) and not needs_confirmation(intent)


def _shown(text: str) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= MAX_SHOWN else flat[: MAX_SHOWN - 1] + "…"


def _item_line(intent: IntentModel, name: str) -> str:
    item = intent.item(name)
    line = f"  {LABELS[name] + ':':<10} {item.status}"
    if item.status == "definido" and item.text is not None:
        line += f' — "{_shown(item.text)}"'
    return line


def _value_line(name: str, value: object, source: str | None) -> str:
    label = f"{LABELS[name] + ':':<10}"
    if value is None:
        return f"  {label} pendente"
    suffix = " (padrão)" if source == "padrao" else ""
    return f"  {label} {value}{suffix}"


def render_summary(intent: IntentModel, dataset_dir: Path) -> list[str]:
    lines = [
        f"Intenção do dataset {intent.slug} (modo {intent.mode})",
        f"Pasta: {dataset_dir.resolve()}",
    ]
    lines.extend(_item_line(intent, n) for n in TEXT_ITEMS)
    lines.append(_value_line("format", intent.format, intent.format_source))
    lines.append(_value_line("volume", intent.volume, intent.volume_source))
    command_tail = f"{intent.slug}"
    if not is_complete(intent):
        lines.append(f"Faltam: {', '.join(missing_items(intent))}.")
    elif needs_confirmation(intent):
        if is_critical(intent):
            lines.append(
                "Objetivo e estrutura indefinidos: o contrato terá 1 campo genérico. "
                f"Confirme: {cli_command()} intent confirm {command_tail}"
            )
        else:
            lines.append(f"Confirme a intenção: {cli_command()} intent confirm {command_tail}")
    else:
        lines.append(f"Próximo passo: {cli_command()} schema build {command_tail}")
    return lines
