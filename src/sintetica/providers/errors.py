"""Erros do llm-provider. Nenhum erro guarda o valor de uma chave de API (RN-07, D-20)."""

from __future__ import annotations

from collections.abc import Sequence


class ProviderError(Exception):
    """Falha definitiva do provedor: não entra no retry."""


class TransientProviderError(ProviderError):
    """Falha temporária (429, 5xx, timeout, conexão): entra no retry (RF-09)."""


class MalformedResponse(TransientProviderError):
    """Resposta que não é `{"records": [...]}` válido: conta como falha temporária (EC-06)."""


class ProviderExhausted(ProviderError):
    """Tentativas esgotadas após falhas temporárias."""

    reason = "falha do provedor"


class CredentialError(ProviderError):
    """Chave recusada (401 ou 403). Cita só o nome da variável (RF-10)."""

    def __init__(self, env_var: str, backend: str) -> None:
        super().__init__(
            f"{backend}: chave de API ausente ou recusada. "
            f"Confira a variável de ambiente {env_var}."
        )
        self.env_var = env_var
        self.backend = backend


class ProviderUnavailable(ProviderError):
    """Nenhum provedor disponível. Lista o que foi verificado (RF-12)."""

    def __init__(self, checked: Sequence[str]) -> None:
        super().__init__(
            "Nenhum provedor de LLM disponível. Verificado: " + ", ".join(checked) + "."
        )
        self.checked = tuple(checked)


class HarnessLimitExceeded(ProviderError):
    def __init__(self, n_records: int, limit: int) -> None:
        super().__init__(
            f"O provedor do harness atende até {limit} registros por pedido; pedido: {n_records}."
        )
        self.n_records = n_records
        self.limit = limit


class HarnessResponsePending(ProviderError):
    """O pedido foi gravado e espera o `submit` do agente (D-13)."""

    def __init__(self, request_id: str, command: str) -> None:
        super().__init__(f"Pedido {request_id} aguardando resposta do agente. Execute: {command}")
        self.request_id = request_id
        self.command = command


class MaskingUnavailable(ProviderError):
    """Mascaramento obrigatório indisponível: o pedido não é enviado (RN-03, D-07)."""


class ProviderPolicyError(ProviderError):
    """`.sintetica/policy.json` com conteúdo inválido para o llm-provider (D-23)."""


class RequestStoreError(ProviderError):
    """Erro do protocolo request/submit. `exit_code` segue interfaces/harness-cli.md."""

    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code
