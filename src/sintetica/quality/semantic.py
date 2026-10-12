"""Quase-duplicados por Jaccard ≥ 0,8, com busca exata (D-07, D-08).

Até 1.000 registros, compara par a par. Acima disso, usa o filtro de prefixo (AllPairs):
com os trechos de cada registro em ordem global de raridade, 2 conjuntos com Jaccard ≥ t
compartilham ao menos 1 trecho dos prefixos de tamanho `n - ⌈t·n⌉ + 1`. Os candidatos passam
pelo filtro de tamanho e pelo Jaccard exato, então o resultado é o mesmo do par a par.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

PAIRWISE_LIMIT = 1000
# Limiar 0,8 = 4/5, em inteiros para não depender de ponto flutuante.
_NUM, _DEN = 4, 5


def similar(a: frozenset[str], b: frozenset[str]) -> bool:
    """Jaccard(a, b) ≥ 0,8."""
    if not a or not b:
        return False
    small, large = (len(a), len(b)) if len(a) <= len(b) else (len(b), len(a))
    if small * _DEN < large * _NUM:  # filtro de tamanho
        return False
    inter = len(a & b)
    return inter * _DEN >= (len(a) + len(b) - inter) * _NUM


def _pairwise(sets: Sequence[frozenset[str]]) -> list[int]:
    return [i for i, s in enumerate(sets) if any(similar(sets[j], s) for j in range(i))]


def _prefix_len(n: int) -> int:
    return n - (_NUM * n + _DEN - 1) // _DEN + 1  # n - ⌈0,8·n⌉ + 1


def _prefix_filter(sets: Sequence[frozenset[str]]) -> list[int]:
    freq = Counter(token for s in sets for token in s)
    index: dict[str, list[int]] = {}
    marked: list[int] = []
    for i, s in enumerate(sets):
        if not s:
            continue
        prefix = sorted(s, key=lambda t: (freq[t], t))[: _prefix_len(len(s))]
        seen: set[int] = set()
        found = False
        for token in prefix:
            for j in index.get(token, ()):
                if j in seen:
                    continue
                seen.add(j)
                if similar(sets[j], s):
                    found = True
                    break
            if found:
                break
        if found:
            marked.append(i)
        for token in prefix:
            index.setdefault(token, []).append(i)
    return marked


def near_duplicates(sets: Sequence[frozenset[str]], *, force_prefix: bool = False) -> list[int]:
    """Posições dos conjuntos com Jaccard ≥ 0,8 em relação a algum anterior."""
    if force_prefix or len(sets) > PAIRWISE_LIMIT:
        return _prefix_filter(sets)
    return _pairwise(sets)
