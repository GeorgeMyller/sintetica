"""llm-provider: porta única de geração por LLM, com custo, teto e mascaramento."""

from sintetica.providers.domain import (
    CostEstimate,
    GenerationRequest,
    GenerationResult,
    ProviderChoice,
)
from sintetica.providers.errors import (
    CredentialError,
    HarnessLimitExceeded,
    HarnessResponsePending,
    MalformedResponse,
    MaskingUnavailable,
    ProviderError,
    ProviderExhausted,
    ProviderPolicyError,
    ProviderUnavailable,
    RequestStoreError,
    TransientProviderError,
)
from sintetica.providers.factory import build_provider
from sintetica.providers.ports import LLMProvider

__all__ = [
    "CostEstimate",
    "CredentialError",
    "GenerationRequest",
    "GenerationResult",
    "HarnessLimitExceeded",
    "HarnessResponsePending",
    "LLMProvider",
    "MalformedResponse",
    "MaskingUnavailable",
    "ProviderChoice",
    "ProviderError",
    "ProviderExhausted",
    "ProviderPolicyError",
    "ProviderUnavailable",
    "RequestStoreError",
    "TransientProviderError",
    "build_provider",
]
