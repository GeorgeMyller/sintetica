"""Revisão por bloco: validar, descartar duplicados, mascarar e revalidar (D-09).

O índice de duplicados guarda só o SHA-256 das linhas canônicas. Os hashes das linhas
brutas (antes do mascaramento) ficam só em memória e nunca vão ao disco.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError

from sintetica.sample.review import Masker, first_error, mask_value
from sintetica.schema import to_json_obj, to_jsonl_line


def _digest(line: str) -> bytes:
    return hashlib.sha256(line.encode("utf-8")).digest()


class DedupIndex:
    def __init__(self) -> None:
        self._masked: set[bytes] = set()
        self._raw: set[bytes] = set()

    def __len__(self) -> int:
        return len(self._masked)

    def add_masked(self, line: str) -> bool:
        """Registra a linha mascarada; `False` se ela já existia."""
        digest = _digest(line)
        if digest in self._masked:
            return False
        self._masked.add(digest)
        return True

    def add_raw(self, line: str) -> bool:
        """Registra a linha bruta; `False` se ela já existia."""
        digest = _digest(line)
        if digest in self._raw:
            return False
        self._raw.add(digest)
        return True


@dataclass
class BlockReview:
    accepted: list[str] = field(default_factory=list)
    invalid: int = 0
    duplicate: int = 0
    reasons: list[str] = field(default_factory=list)  # motivos, nunca valores


def review_block(
    raw: Sequence[Mapping[str, object]],
    model: type[BaseModel],
    index: DedupIndex,
    masker: Masker,
    limit: int,
) -> BlockReview:
    """Aceita até `limit` registros novos; registros além do pedido são ignorados."""
    result = BlockReview()
    for position, item in enumerate(raw, start=1):
        if len(result.accepted) >= limit:
            break
        try:
            record = model.model_validate(item)
        except ValidationError as exc:
            result.invalid += 1
            result.reasons.append(f"registro {position}: {first_error(exc)}")
            continue
        if not index.add_raw(to_jsonl_line(record)):
            result.duplicate += 1
            continue
        masked_obj = mask_value(to_json_obj(record), "", masker)
        try:
            masked = model.model_validate(masked_obj)
        except ValidationError as exc:
            result.invalid += 1
            result.reasons.append(
                f"registro {position}: o valor falso do mascaramento quebrou a regra "
                f"({first_error(exc)})"
            )
            continue
        line = to_jsonl_line(masked)
        if not index.add_masked(line):
            result.duplicate += 1
            continue
        result.accepted.append(line)
    return result
