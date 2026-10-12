"""`ExternalAPIProvider`: 4 backends sobre `httpx.AsyncClient` (D-03)."""

from __future__ import annotations

import logging
import os
from decimal import Decimal

import httpx

from sintetica.providers.domain import OLLAMA, CostEstimate, GenerationRequest, GenerationResult
from sintetica.providers.errors import (
    CredentialError,
    MalformedResponse,
    TransientProviderError,
)
from sintetica.providers.external.backends import BACKENDS, check_status
from sintetica.providers.models import resolve_model
from sintetica.providers.pricing import ZERO, PriceTable
from sintetica.providers.prompt import SYSTEM_PROMPT, build_user_prompt, parse_records

logger = logging.getLogger("sintetica.providers")

REQUEST_TIMEOUT_S = 60.0


class ExternalAPIProvider:
    def __init__(
        self,
        backend: str,
        *,
        prices: PriceTable,
        ceiling_usd: Decimal,
        model: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_s: float = REQUEST_TIMEOUT_S,
    ) -> None:
        self._backend = BACKENDS[backend]
        self._model = model or resolve_model(backend)
        self._prices = prices
        self._ceiling = ceiling_usd
        self._transport = transport
        self._timeout = timeout_s

    @property
    def name(self) -> str:
        return self._backend.name

    @property
    def model(self) -> str:
        return self._model

    @property
    def is_local(self) -> bool:
        return self._backend.name == OLLAMA

    def _key(self) -> str | None:
        env_var = self._backend.key_env_var
        if env_var is None:
            return None
        key = os.environ.get(env_var, "").strip()
        if not key:
            raise CredentialError(env_var, self._backend.name)
        return key

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        # A chave é lida aqui e vive só nesta chamada (RN-07).
        call = self._backend.build(
            self._model, SYSTEM_PROMPT, build_user_prompt(request), self._key()
        )
        async with httpx.AsyncClient(transport=self._transport, timeout=self._timeout) as client:
            try:
                response = await client.post(call.url, headers=call.headers, json=call.body)
            except httpx.TimeoutException:
                # `from None`: a exceção do httpx carrega a requisição, com os cabeçalhos.
                raise TransientProviderError(
                    f"{self.name}: timeout de {self._timeout:g} s"
                ) from None
            except httpx.TransportError:
                raise TransientProviderError(f"{self.name}: falha de conexão") from None
        check_status(self._backend, self._model, response)
        try:
            payload = response.json()
        except ValueError:
            raise MalformedResponse(f"{self.name}: corpo da resposta não é JSON") from None
        completion = self._backend.parse(payload)
        records = parse_records(completion.text)
        return GenerationResult(
            records,
            completion.input_tokens,
            completion.output_tokens,
            self._real_cost(completion.input_tokens, completion.output_tokens),
            self.name,
        )

    def _real_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        if self.is_local:
            return ZERO
        cost = self._prices.real_cost(self._model, input_tokens, output_tokens)
        if cost is None:
            logger.warning(
                "modelo %s sem preço conhecido; custo real registrado como 0", self._model
            )
            return ZERO
        return cost

    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate:
        if self.is_local:
            return CostEstimate(self.name, self._model, n_records, avg_tokens, ZERO, False)
        usd = self._prices.estimate(self._model, n_records, avg_tokens)
        if usd is None:
            # Preço desconhecido conta como acima do teto (EC-04).
            return CostEstimate(self.name, self._model, n_records, avg_tokens, ZERO, True, False)
        return CostEstimate(self.name, self._model, n_records, avg_tokens, usd, usd > self._ceiling)
