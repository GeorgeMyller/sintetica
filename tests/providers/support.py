"""Apoio aos testes do llm-provider: corpos por backend, servidor simulado e sleep falso."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from sintetica.providers.domain import GenerationRequest

ENV_VARS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "OLLAMA_HOST",
    "SINTETICA_OPENAI_MODEL",
    "SINTETICA_ANTHROPIC_MODEL",
    "SINTETICA_GEMINI_MODEL",
    "SINTETICA_OLLAMA_MODEL",
    "SINTETICA_EXTERNAL_BACKEND",
)
FAKE_KEY = "sk-test-NAO-VAZAR-1234567890"
RECORDS: list[dict[str, Any]] = [{"nome": "Ana"}, {"nome": "Bruno"}]


def ok_body(
    backend: str,
    records: Sequence[dict[str, Any]] = RECORDS,
    input_tokens: int = 100,
    output_tokens: int = 400,
    text: str | None = None,
) -> dict[str, Any]:
    """Corpo de sucesso no formato de cada backend (interfaces/*.md)."""
    content = text if text is not None else json.dumps({"records": list(records)})
    if backend == "openai":
        return {
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": input_tokens, "completion_tokens": output_tokens},
        }
    if backend == "anthropic":
        return {
            "content": [{"type": "text", "text": content}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        }
    if backend == "gemini":
        return {
            "candidates": [{"content": {"parts": [{"text": content}]}}],
            "usageMetadata": {
                "promptTokenCount": input_tokens,
                "candidatesTokenCount": output_tokens,
            },
        }
    return {
        "message": {"content": content},
        "prompt_eval_count": input_tokens,
        "eval_count": output_tokens,
    }


Reply = httpx.Response | Exception


@dataclass
class FakeServer:
    """Responde em sequência; depois da última resposta, repete a última."""

    replies: list[Reply]
    calls: list[httpx.Request] = field(default_factory=list)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        reply = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        if isinstance(reply, Exception):
            raise reply
        return reply

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handler)

    def bodies(self) -> list[str]:
        return [c.content.decode("utf-8") for c in self.calls]


def json_reply(body: Any, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=body)


@dataclass
class FakeSleep:
    delays: list[float] = field(default_factory=list)

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def make_request(
    n_records: int = 2,
    instructions: str = "clientes de uma loja",
    seeds: Sequence[dict[str, object]] = (),
    schema: dict[str, object] | None = None,
) -> GenerationRequest:
    return GenerationRequest(
        schema_json=schema or {"type": "object", "properties": {"nome": {"type": "string"}}},
        seeds=list(seeds),
        instructions=instructions,
        n_records=n_records,
    )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
