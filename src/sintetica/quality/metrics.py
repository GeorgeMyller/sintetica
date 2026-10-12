"""Métricas da avaliação: conformidade, unicidades, PII, duração e veredito (D-04 a D-11)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sintetica.pii.domain import PiiFinding
from sintetica.quality.reader import Item
from sintetica.quality.semantic import near_duplicates
from sintetica.quality.text import free_text, has_free_text, shingles
from sintetica.schema import to_json_obj
from sintetica.schema.spec import SchemaSpecModel

CONFORMITY_TARGET = Decimal("95")
UNIQUENESS_TARGET = Decimal("90")
TIME_TARGET_MIN = Decimal("10")
TIME_TARGET_MAX_VOLUME = 100
METRIC_ORDER = ("conformidade", "unicidade_estrutural", "unicidade_semantica", "pii")

Leaks = Callable[[str, str], list[PiiFinding]]  # (texto, caminho do campo) -> vazamentos


@dataclass(frozen=True, slots=True)
class PiiHit:
    index: int
    field: str
    type: str
    preview: str


@dataclass
class Stats:
    records_read: int = 0
    valid: int = 0
    invalid: list[int] = field(default_factory=list)
    duplicates: list[int] = field(default_factory=list)
    near_duplicates: list[int] = field(default_factory=list)
    with_text: int = 0
    pii: list[PiiHit] = field(default_factory=list)


def pct(part: int, whole: int) -> Decimal:
    """Percentual com 1 casa (`ROUND_HALF_UP`); 0 quando não há base."""
    if whole <= 0:
        return Decimal("0.0")
    return (Decimal(part) * 100 / Decimal(whole)).quantize(Decimal("0.1"), ROUND_HALF_UP)


def string_leaves(value: Any, path: str = "") -> Iterator[tuple[str, str]]:
    """Cada texto do registro com o caminho do campo (`end.cidade`, `tags[]`)."""
    if isinstance(value, str):
        yield path or "registro", value
    elif isinstance(value, Mapping):
        for key, sub in value.items():
            yield from string_leaves(sub, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for sub in value:
            yield from string_leaves(sub, f"{path}[]")


def collect(items: Iterable[Item], spec: SchemaSpecModel, leaks: Leaks) -> Stats:
    """1 passada pelo dataset; a unicidade semântica é calculada no fim."""
    stats = Stats()
    seen: set[bytes] = set()
    text_sets: list[frozenset[str]] = []
    text_owner: list[int] = []
    applicable = has_free_text(spec)
    for item in items:
        stats.records_read += 1
        digest = hashlib.sha256(item.canonical.encode("utf-8")).digest()
        if digest in seen:
            stats.duplicates.append(item.index)
        seen.add(digest)
        if item.record is None:
            stats.invalid.append(item.index)
            leaves: Iterable[tuple[str, str]] = [("registro", item.canonical)]
        else:
            stats.valid += 1
            obj = to_json_obj(item.record)
            leaves = string_leaves(obj)
            if applicable:
                words = shingles(free_text(obj, spec))
                if words:
                    text_sets.append(words)
                    text_owner.append(item.index)
        for path, text in leaves:
            for finding in leaks(text, path):
                stats.pii.append(PiiHit(item.index, path, finding.type, finding.preview))
    stats.with_text = len(text_sets)
    stats.near_duplicates = [text_owner[i] for i in near_duplicates(text_sets)]
    return stats


def duration_min(started_at: str | None, finished: datetime) -> Decimal | None:
    """Minutos com 1 casa entre `started_at` (UTC) e a emissão; `None` se não medida."""
    if not started_at:
        return None
    try:
        start = datetime.strptime(started_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    seconds = Decimal(str((finished - start).total_seconds()))
    return (seconds / 60).quantize(Decimal("0.1"), ROUND_HALF_UP)


def time_target_met(volume: int, duration: Decimal | None) -> bool | None:
    if duration is None or volume > TIME_TARGET_MAX_VOLUME:
        return None
    return duration < TIME_TARGET_MIN


def verdict(
    conformity: Decimal, structural: Decimal, semantic: Decimal | None, leaks: int
) -> tuple[str, list[str]]:
    """`APROVADO` só com todas as metas; a semântica "não aplicável" (`None`) não conta."""
    failed = {
        "conformidade": conformity < CONFORMITY_TARGET,
        "unicidade_estrutural": structural < UNIQUENESS_TARGET,
        "unicidade_semantica": semantic is not None and semantic < UNIQUENESS_TARGET,
        "pii": leaks > 0,
    }
    names = [name for name in METRIC_ORDER if failed[name]]
    return ("REPROVADO" if names else "APROVADO"), names
