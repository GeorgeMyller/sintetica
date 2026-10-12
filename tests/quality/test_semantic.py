"""Quase-duplicados: limiar, ordem e equivalência do filtro de prefixo (D-07, D-08)."""

from __future__ import annotations

import random

from sintetica.quality.semantic import near_duplicates, similar
from sintetica.quality.text import shingles


def test_threshold_is_point_eight() -> None:
    a = frozenset(str(i) for i in range(10))
    assert similar(a, a | {"x", "y"})  # 10/12 = 0,83
    assert not similar(a, a | {"x", "y", "z"})  # 10/13 = 0,77
    assert similar(frozenset("abcd"), frozenset("abcde"))  # 4/5 = 0,8
    assert not similar(frozenset(), frozenset())


def test_punctuation_and_case_make_near_duplicates() -> None:
    sets = [
        shingles("O cliente pediu a troca do produto ontem."),
        shingles("o CLIENTE, pediu a troca do produto ontem"),
        shingles("Entrega atrasada em três dias úteis"),
    ]
    assert near_duplicates(sets) == [1]
    assert near_duplicates(sets, force_prefix=True) == [1]


def test_only_the_later_record_counts() -> None:
    same = shingles("um dois três quatro")
    assert near_duplicates([same, same, same]) == [1, 2]


def test_prefix_filter_matches_pairwise() -> None:
    rng = random.Random(20261012)
    vocab = [f"p{i}" for i in range(40)]
    for _ in range(30):
        sets: list[frozenset[str]] = []
        base = [frozenset(rng.sample(vocab, rng.randint(1, 12))) for _ in range(8)]
        for _ in range(60):
            seed = rng.choice(base)
            extra = frozenset(rng.sample(vocab, rng.randint(0, 3)))
            drop = frozenset(rng.sample(sorted(seed), rng.randint(0, min(2, len(seed) - 1))))
            sets.append((seed - drop) | extra)
        assert near_duplicates(sets, force_prefix=True) == near_duplicates(sets)


def test_large_input_uses_prefix_filter() -> None:
    sets = [frozenset({f"t{i}"}) for i in range(1001)] + [frozenset({"t5"})]
    assert near_duplicates(sets) == [1001]
