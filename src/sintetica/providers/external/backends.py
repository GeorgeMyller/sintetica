"""Adaptadores finos por backend: montar a requisição e ler texto e tokens (interfaces/*.md).

A chave chega como argumento no momento da requisição e nunca fica guardada (RN-07).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from sintetica.providers.errors import (
    CredentialError,
    MalformedResponse,
    ProviderError,
    TransientProviderError,
)
from sintetica.providers.models import model_env_var

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
ANTHROPIC_VERSION = "2023-06-01"
ANTHROPIC_MAX_TOKENS = 8192


@dataclass(frozen=True, slots=True)
class HttpCall:
    url: str
    headers: dict[str, str]
    body: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int


class Backend(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def key_env_var(self) -> str | None: ...

    def build(self, model: str, system: str, user: str, key: str | None) -> HttpCall: ...

    def parse(self, payload: Any) -> Completion: ...


def ollama_host() -> str:
    host = os.environ.get("OLLAMA_HOST", "").strip() or DEFAULT_OLLAMA_HOST
    if "://" not in host:
        host = "http://" + host
    return host.rstrip("/")


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


class OpenAIBackend:
    name = "openai"
    key_env_var: str | None = "OPENAI_API_KEY"

    def build(self, model: str, system: str, user: str, key: str | None) -> HttpCall:
        return HttpCall(
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "response_format": {"type": "json_object"},
            },
        )

    def parse(self, payload: Any) -> Completion:
        try:
            text = payload["choices"][0]["message"]["content"]
            usage = payload.get("usage") or {}
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise MalformedResponse("openai: resposta sem choices[0].message.content") from exc
        if not isinstance(text, str):
            raise MalformedResponse("openai: conteúdo da resposta não é texto")
        return Completion(
            text, _int(usage.get("prompt_tokens")), _int(usage.get("completion_tokens"))
        )


class AnthropicBackend:
    name = "anthropic"
    key_env_var: str | None = "ANTHROPIC_API_KEY"

    def build(self, model: str, system: str, user: str, key: str | None) -> HttpCall:
        return HttpCall(
            "https://api.anthropic.com/v1/messages",
            {
                "x-api-key": key or "",
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            {
                "model": model,
                "max_tokens": ANTHROPIC_MAX_TOKENS,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )

    def parse(self, payload: Any) -> Completion:
        try:
            if payload.get("stop_reason") == "max_tokens":
                raise MalformedResponse("anthropic: resposta truncada por max_tokens")
            blocks = payload["content"]
            text = "".join(b["text"] for b in blocks if b.get("type") == "text")
            usage = payload.get("usage") or {}
        except (KeyError, TypeError, AttributeError) as exc:
            raise MalformedResponse("anthropic: resposta sem blocos de texto") from exc
        return Completion(text, _int(usage.get("input_tokens")), _int(usage.get("output_tokens")))


class GeminiBackend:
    name = "gemini"
    key_env_var: str | None = "GEMINI_API_KEY"

    def build(self, model: str, system: str, user: str, key: str | None) -> HttpCall:
        # A chave vai no cabeçalho, nunca na URL, para não aparecer em log de URL.
        return HttpCall(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"x-goog-api-key": key or "", "Content-Type": "application/json"},
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            },
        )

    def parse(self, payload: Any) -> Completion:
        try:
            parts = payload["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
            usage = payload.get("usageMetadata") or {}
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise MalformedResponse("gemini: resposta sem candidates[0].content.parts") from exc
        return Completion(
            text, _int(usage.get("promptTokenCount")), _int(usage.get("candidatesTokenCount"))
        )


class OllamaBackend:
    name = "ollama"
    key_env_var: str | None = None

    def build(self, model: str, system: str, user: str, key: str | None) -> HttpCall:
        return HttpCall(
            f"{ollama_host()}/api/chat",
            {"Content-Type": "application/json"},
            {
                "model": model,
                "stream": False,
                "format": "json",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )

    def parse(self, payload: Any) -> Completion:
        try:
            text = payload["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise MalformedResponse("ollama: resposta sem message.content") from exc
        if not isinstance(text, str):
            raise MalformedResponse("ollama: conteúdo da resposta não é texto")
        return Completion(
            text, _int(payload.get("prompt_eval_count")), _int(payload.get("eval_count"))
        )


BACKENDS: dict[str, Backend] = {
    b.name: b for b in (OpenAIBackend(), AnthropicBackend(), GeminiBackend(), OllamaBackend())
}


def check_status(backend: Backend, model: str, response: httpx.Response) -> None:
    """Classifica o status HTTP: temporário (retry), credencial ou definitivo (sem retry)."""
    status = response.status_code
    if status < 400:
        return
    if status == 429 or status >= 500:
        raise TransientProviderError(f"{backend.name}: HTTP {status}")
    env_var = backend.key_env_var
    if env_var is not None and (
        status in (401, 403) or (status == 400 and "api key" in response.text.lower())
    ):
        raise CredentialError(env_var, backend.name)
    if status == 404:
        if backend.name == "ollama":
            raise ProviderError(
                f"ollama: modelo {model!r} não encontrado. Execute: ollama pull {model}"
            )
        raise ProviderError(
            f"{backend.name}: modelo {model!r} não encontrado (HTTP 404). "
            f"Defina {model_env_var(backend.name)} com um modelo vigente."
        )
    raise ProviderError(f"{backend.name}: HTTP {status}")
