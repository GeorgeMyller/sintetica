"""Plano de blocos: tamanho médio, bloco adaptativo e divisão (D-05, Q46)."""

from __future__ import annotations

import pytest

from sintetica.batch.plan import avg_tokens, block_size, split


def test_avg_tokens_uses_four_chars_per_token() -> None:
    assert avg_tokens(["x" * 40, "x" * 80]) == 15
    assert avg_tokens(["{}"]) == 1
    with pytest.raises(ValueError):
        avg_tokens([])


def test_short_records_get_blocks_of_ten() -> None:
    assert block_size(avg_tokens(['{"cliente":"Ana","valor":10.00}'])) == 10


def test_long_records_shrink_the_block() -> None:
    assert block_size(avg_tokens(["x" * 4000])) == 4  # cerca de 1.000 tokens
    assert block_size(1500) == 2
    assert block_size(9000) == 1


def test_override_wins_within_limits() -> None:
    assert block_size(1000, 25) == 25
    for bad in (0, 101):
        with pytest.raises(ValueError, match="--block-size"):
            block_size(10, bad)


def test_split_covers_the_missing_records() -> None:
    assert split(25, 10) == [10, 10, 5]
    assert split(1000, 10) == [10] * 100
    assert split(3, 10) == [3]
    assert split(0, 10) == []
