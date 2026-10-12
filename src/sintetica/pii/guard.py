"""Fachada `PiiGuard`: scan, mask, leaks e coverage."""

from __future__ import annotations

import dataclasses
import logging
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from sintetica.pii.allowlist import ALLOWLIST_FILENAME, FileAllowlistStore
from sintetica.pii.detectors import CustomDetector, default_detectors
from sintetica.pii.domain import FIXED_TYPES, Coverage, MaskResult, PiiFinding, PiiType
from sintetica.pii.policy import load_custom_patterns
from sintetica.pii.ports import AllowlistStore, Detector, SubstituteGenerator
from sintetica.pii.substitutes import FakerSubstituteGenerator

logger = logging.getLogger("sintetica.pii")

# Empate de tamanho entre achados sobrepostos: vence o primeiro desta ordem (D-05).
_PRIORITY: dict[PiiType, int] = {
    PiiType.CARD: 0,
    PiiType.CNPJ: 1,
    PiiType.CPF: 2,
    PiiType.PHONE: 3,
    PiiType.IPV6: 4,
    PiiType.IPV4: 5,
    PiiType.EMAIL: 6,
    PiiType.CUSTOM: 7,
}

CHUNK_THRESHOLD = 1024 * 1024  # textos maiores são processados em blocos (D-12)
CHUNK_SIZE = 64 * 1024
CHUNK_OVERLAP = 64
MAX_SUBSTITUTE_ATTEMPTS = 5

KNOWN_LIMITS: tuple[str, ...] = (
    "Nomes de pessoas não são detectados.",
    "Endereços em texto livre não são detectados.",
    "CNPJ alfanumérico não é detectado; só o formato numérico.",
    "Telefone só é detectado com formatação ou prefixo +55; dígitos corridos não contam.",
    "Números de versão no formato a.b.c.d podem ser detectados como IPv4 (falso positivo aceito).",
    "Um CPF ou CNPJ falso válido pode coincidir com um documento real de outra pessoa.",
)


def _resolve_overlaps(findings: list[PiiFinding]) -> list[PiiFinding]:
    ranked = sorted(findings, key=lambda f: (-(f.end - f.start), _PRIORITY[f.type], f.start))
    chosen: list[PiiFinding] = []
    for f in ranked:
        if all(f.end <= c.start or f.start >= c.end for c in chosen):
            chosen.append(f)
    return sorted(chosen, key=lambda f: f.start)


class PiiGuard:
    def __init__(
        self,
        allowlist: AllowlistStore,
        custom_patterns: Sequence[str] = (),
        seed: int | None = None,
        substitutes: SubstituteGenerator | None = None,
    ) -> None:
        self._allowlist = allowlist
        self._custom_count = len(custom_patterns)
        detectors: list[Detector] = list(default_detectors())
        if custom_patterns:
            detectors.append(CustomDetector(custom_patterns))
        self._detectors = detectors
        self._by_type: dict[PiiType, Detector] = {d.type: d for d in detectors}
        self._substitutes: SubstituteGenerator = substitutes or FakerSubstituteGenerator(seed)

    @classmethod
    def for_dataset(cls, dataset_dir: Path, policy_path: Path, seed: int | None = None) -> PiiGuard:
        allowlist = FileAllowlistStore(dataset_dir / ALLOWLIST_FILENAME)
        return cls(allowlist, load_custom_patterns(policy_path), seed)

    @property
    def allowlist_available(self) -> bool:
        """Falso quando o arquivo da allowlist não existe: todo achado conta como vazamento."""
        return self._allowlist.exists()

    def _scan_raw(self, text: str) -> list[PiiFinding]:
        found: list[PiiFinding] = []
        for detector in self._detectors:
            found.extend(detector.find(text))
        return _resolve_overlaps(found)

    def scan(self, text: str, field: str | None = None) -> list[PiiFinding]:
        if len(text) <= CHUNK_THRESHOLD:
            findings = self._scan_raw(text)
        else:
            findings = self._scan_chunked(text)
        if field is not None:
            findings = [dataclasses.replace(f, field=field) for f in findings]
        return findings

    def _scan_chunked(self, text: str) -> list[PiiFinding]:
        # Cada janela cobre [início - sobreposição, início + bloco + sobreposição) e aceita só
        # os achados que começam dentro de [início, início + bloco). Achados de até 64 caracteres
        # aparecem inteiros em exatamente uma janela.
        found: list[PiiFinding] = []
        for start in range(0, len(text), CHUNK_SIZE):
            left = max(0, start - CHUNK_OVERLAP)
            right = min(len(text), start + CHUNK_SIZE + CHUNK_OVERLAP)
            for f in self._scan_raw(text[left:right]):
                absolute = dataclasses.replace(f, start=f.start + left, end=f.end + left)
                if start <= absolute.start < start + CHUNK_SIZE:
                    found.append(absolute)
        return _resolve_overlaps(found)

    def _is_detectable(self, pii_type: PiiType, candidate: str) -> bool:
        detector = self._by_type[pii_type]
        return any(f.start == 0 and f.end == len(candidate) for f in detector.find(candidate))

    def _substitute(self, pii_type: PiiType, original: str) -> str | None:
        for _ in range(MAX_SUBSTITUTE_ATTEMPTS):
            try:
                candidate = self._substitutes.generate(pii_type, original)
            except Exception:
                logger.warning("falha ao gerar substituto do tipo %s", pii_type.value)
                continue
            if candidate != original and self._is_detectable(pii_type, candidate):
                return candidate
        return None

    def mask(self, text: str, field: str | None = None) -> MaskResult:
        counts: Counter[PiiType] = Counter()
        fallbacks = 0
        out = text
        for f in reversed(self.scan(text, field)):
            original = text[f.start : f.end]
            if self._allowlist.contains(f.type, original):
                continue  # já é um valor falso inserido antes
            substitute = self._substitute(f.type, original)
            if substitute is None:
                substitute = "*" * len(original)
                fallbacks += 1
                logger.warning("substituto indisponível para o tipo %s; usado ***", f.type.value)
            else:
                self._allowlist.add(f.type, substitute)
            out = out[: f.start] + substitute + out[f.end :]
            counts[f.type] += 1
        return MaskResult(out, dict(counts), fallbacks)

    def leaks(self, text: str, field: str | None = None) -> list[PiiFinding]:
        return [
            f
            for f in self.scan(text, field)
            if not self._allowlist.contains(f.type, text[f.start : f.end])
        ]

    def coverage(self) -> Coverage:
        return Coverage(FIXED_TYPES, self._custom_count, KNOWN_LIMITS)
