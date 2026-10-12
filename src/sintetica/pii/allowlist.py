"""Allowlist em arquivo: 1 hash SHA-256 por linha, só de valores falsos (D-09, D-10)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from sintetica.pii.domain import PiiType
from sintetica.pii.normalize import normalize

ALLOWLIST_FILENAME = ".pii_allowlist"


def fingerprint(pii_type: PiiType, value: str) -> str:
    return hashlib.sha256(normalize(pii_type, value).encode("utf-8")).hexdigest()


class FileAllowlistStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._hashes: set[str] = set()
        if path.exists():
            with path.open(encoding="utf-8") as f:
                self._hashes = {line.strip() for line in f if line.strip()}

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists()

    def contains(self, pii_type: PiiType, value: str) -> bool:
        return fingerprint(pii_type, value) in self._hashes

    def add(self, pii_type: PiiType, value: str) -> None:
        digest = fingerprint(pii_type, value)
        if digest in self._hashes:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(digest + "\n")
            f.flush()
            os.fsync(f.fileno())
        self._hashes.add(digest)
