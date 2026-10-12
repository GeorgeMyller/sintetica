"""Tabela de preços: `defaults.json` embutido, sobrescrito por `.sintetica/pricing.json` (D-17).

Estimativa pelo preço de saída, que superestima (lado seguro do teto); custo real pelos 2 preços
(D-16, Q33).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from importlib import resources
from pathlib import Path

from sintetica.providers.domain import ModelPrice
from sintetica.providers.errors import ProviderPolicyError

PRICING_RELATIVE_PATH = Path(".sintetica") / "pricing.json"
ZERO = Decimal("0")


def load_defaults() -> dict[str, object]:
    text = resources.files("sintetica.providers").joinpath("data/defaults.json").read_text("utf-8")
    data: dict[str, object] = json.loads(text)
    return data


def _parse_prices(raw: object, source: str) -> dict[str, ModelPrice]:
    if not isinstance(raw, dict):
        raise ProviderPolicyError(f"{source}: preços devem ser um objeto JSON")
    prices: dict[str, ModelPrice] = {}
    for model, entry in raw.items():
        if not isinstance(entry, dict):
            raise ProviderPolicyError(f"{source}: preço de {model!r} deve ser um objeto")
        try:
            # str() evita passar por float: "0.00001" vira Decimal exato.
            price = ModelPrice(
                Decimal(str(entry["input_usd_per_token"])),
                Decimal(str(entry["output_usd_per_token"])),
            )
        except (KeyError, InvalidOperation) as exc:
            raise ProviderPolicyError(
                f"{source}: preço de {model!r} exige input_usd_per_token e "
                "output_usd_per_token numéricos"
            ) from exc
        prices[str(model)] = price
    return prices


class PriceTable:
    def __init__(self, prices: Mapping[str, ModelPrice]) -> None:
        self._prices = dict(prices)

    @classmethod
    def load(cls, project_dir: Path) -> PriceTable:
        prices = _parse_prices(load_defaults()["prices"], "defaults.json")
        override = project_dir / PRICING_RELATIVE_PATH
        if override.exists():
            try:
                raw = json.loads(override.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ProviderPolicyError(f"pricing.json inválido: {exc.msg}") from exc
            prices.update(_parse_prices(raw, "pricing.json"))
        return cls(prices)

    def price(self, model: str) -> ModelPrice | None:
        return self._prices.get(model)

    def estimate(self, model: str, n_records: int, avg_tokens: int) -> Decimal | None:
        """`n_records * avg_tokens * preço de saída`. `None` quando o modelo não tem preço."""
        price = self.price(model)
        if price is None:
            return None
        return n_records * avg_tokens * price.output_usd_per_token

    def real_cost(self, model: str, input_tokens: int, output_tokens: int) -> Decimal | None:
        price = self.price(model)
        if price is None:
            return None
        return input_tokens * price.input_usd_per_token + output_tokens * price.output_usd_per_token
