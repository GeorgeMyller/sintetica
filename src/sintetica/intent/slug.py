"""Slug do dataset e criação da pasta sem corrida (RN-02, D-04, R-05)."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path

MAX_SLUG = 60


def base_slug(name: str | None, now: datetime) -> str:
    """kebab-case ASCII do nome; sem nome útil, `dataset-AAAAMMDD-HHMMSS` (UTC)."""
    text = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:MAX_SLUG].strip("-")
    return slug or f"dataset-{now:%Y%m%d-%H%M%S}"


def create_dataset_dir(datasets_dir: Path, name: str | None, now: datetime) -> tuple[str, Path]:
    """Cria `datasets/<slug>/`; com a pasta já existente, tenta `-2`, `-3`… (sem corrida)."""
    base = base_slug(name, now)
    n = 1
    while True:
        slug = base if n == 1 else f"{base}-{n}"
        path = datasets_dir / slug
        try:
            path.mkdir(exist_ok=False)
        except FileExistsError:
            n += 1
            continue
        return slug, path
