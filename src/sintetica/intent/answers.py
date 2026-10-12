"""Validação, mascaramento e aplicação das respostas (D-06 a D-10, RN-04 a RN-07)."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from sintetica.intent.model import (
    DEFAULT_FORMAT,
    DEFAULT_VOLUME,
    FORMATS,
    LABELS,
    MAX_VOLUME,
    MIN_VOLUME,
    TEXT_ITEMS,
    IntentModel,
    Item,
)
from sintetica.pii import PiiGuard, PiiType, PolicyError

MAX_VOLUME_REJECTIONS = 3

_PII_LABELS = {
    PiiType.CPF: "CPF",
    PiiType.CNPJ: "CNPJ",
    PiiType.EMAIL: "e-mail",
    PiiType.PHONE: "telefone",
    PiiType.CARD: "cartão",
    PiiType.IPV4: "IPv4",
    PiiType.IPV6: "IPv6",
    PiiType.CUSTOM: "padrão do projeto",
}


class InvalidAnswer(Exception):
    """Resposta fora do aceito (código 8). `intent` traz só o contador de volume atualizado."""

    def __init__(self, messages: list[str], intent: IntentModel) -> None:
        super().__init__("; ".join(messages))
        self.messages = messages
        self.intent = intent


class MaskingUnavailable(Exception):
    """Mascaramento indisponível: nada pode ser gravado (código 9, falha segura)."""


class Masker(Protocol):
    """O que a entrevista precisa do mascaramento: texto novo e contagem por tipo."""

    def mask_text(self, text: str, item: str) -> tuple[str, dict[PiiType, int]]: ...


class PiiGuardMasker:
    """Adaptador da fachada `PiiGuard` (feature 001)."""

    def __init__(self, guard: PiiGuard) -> None:
        self._guard = guard

    def mask_text(self, text: str, item: str) -> tuple[str, dict[PiiType, int]]:
        result = self._guard.mask(text, field=item)
        return result.text, dict(result.counts)


MaskerFactory = Callable[[], Masker]


@dataclass
class Answers:
    texts: dict[str, str] = field(default_factory=dict)
    format: str | None = None
    volume: str | None = None
    unknown: set[str] = field(default_factory=set)

    @property
    def empty(self) -> bool:
        return not (
            self.texts or self.format is not None or self.volume is not None or self.unknown
        )

    def conflicts(self) -> list[str]:
        given = set(self.texts)
        if self.format is not None:
            given.add("format")
        if self.volume is not None:
            given.add("volume")
        return sorted(given & self.unknown)


def parse_volume(raw: str) -> int | None:
    """Aceita `2000`, `2.000`, `2 000`; devolve None se não for um inteiro."""
    text = raw.strip()
    if not re.fullmatch(r"-?\d[\d. _]*", text):
        return None
    return int(re.sub(r"[. _]", "", text))


def apply_answers(
    intent: IntentModel, answers: Answers, masker_factory: MaskerFactory
) -> tuple[IntentModel, list[str]]:
    """Intenção nova e avisos. Tudo ou nada: com erro, levanta InvalidAnswer."""
    errors: list[str] = []
    warnings: list[str] = []
    update: dict[str, object] = {}

    for name, text in answers.texts.items():
        if not text.strip():
            errors.append(f"{LABELS[name]}: resposta vazia; para 'não sei', use --unknown {name}")

    if answers.format is not None:
        fmt = answers.format.strip().lower()
        if fmt in FORMATS:
            update.update(format=fmt, format_source="usuario")
        else:
            errors.append(f"formato '{answers.format}' não suportado; use CSV, JSON ou JSONL")

    rejections = intent.volume_rejections
    if answers.volume is not None:
        volume = parse_volume(answers.volume)
        if volume is not None and MIN_VOLUME <= volume <= MAX_VOLUME:
            update.update(volume=volume, volume_source="usuario")
            rejections = 0
        else:
            rejections += 1
            if rejections >= MAX_VOLUME_REJECTIONS:
                update.update(volume=DEFAULT_VOLUME, volume_source="padrao")
                rejections = 0
                warnings.append(
                    f"volume '{answers.volume}' fora de 1 a 10.000 pela 3ª vez; "
                    f"usado o padrão {DEFAULT_VOLUME}"
                )
            else:
                errors.append(f"volume '{answers.volume}' fora do intervalo; informe de 1 a 10.000")

    for name in sorted(answers.unknown):
        if name == "format":
            update.update(format=DEFAULT_FORMAT, format_source="padrao")
            warnings.append(f"formato não definido: usado o padrão {DEFAULT_FORMAT.upper()}")
        elif name == "volume":
            update.update(volume=DEFAULT_VOLUME, volume_source="padrao")
            rejections = 0
            warnings.append(f"volume não definido: usado o padrão {DEFAULT_VOLUME}")
        else:
            update[name] = Item(status="indefinido", text=None)

    update["volume_rejections"] = rejections
    if errors:
        raise InvalidAnswer(errors, intent.model_copy(update={"volume_rejections": rejections}))

    if answers.texts:
        try:
            masker = masker_factory()
            masked_any = False
            for name in TEXT_ITEMS:
                if name not in answers.texts:
                    continue
                text, counts = masker.mask_text(answers.texts[name], name)
                if counts:
                    masked_any = True
                    found = ", ".join(f"{_PII_LABELS[t]} ({n})" for t, n in sorted(counts.items()))
                    warnings.append(
                        f"dados pessoais substituídos por valores falsos em {LABELS[name]}: {found}"
                    )
                update[name] = Item(status="definido", text=text)
        except (PolicyError, OSError) as exc:
            raise MaskingUnavailable(f"mascaramento de PII indisponível: {exc}") from exc
        if masked_any:
            update["pii_masked"] = True

    if any(key in update for key in ("objective", "structure", "rules", "format", "volume")):
        update["confirmed_at"] = None  # resposta nova exige nova confirmação
    return intent.model_copy(update=update), warnings
