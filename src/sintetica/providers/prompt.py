"""Prompt comum aos backends e parse de `{"records": [...]}` (D-21)."""

from __future__ import annotations

import json

from sintetica.providers.domain import GenerationRequest
from sintetica.providers.errors import MalformedResponse

SYSTEM_PROMPT = (
    "Você gera dados sintéticos. Responda apenas com um objeto JSON no formato "
    '{"records": [ ... ]}, em que cada item é um objeto que segue o JSON Schema informado. '
    "Não escreva texto fora do JSON."
)


def build_user_prompt(request: GenerationRequest) -> str:
    parts = [
        f"Gere exatamente {request.n_records} registros.",
        "Instruções:",
        request.instructions,
        "JSON Schema de cada registro:",
        json.dumps(request.schema_json, ensure_ascii=False, sort_keys=True),
    ]
    if request.seeds:
        parts += [
            "Exemplos aprovados (siga o estilo, não repita):",
            json.dumps(list(request.seeds), ensure_ascii=False, sort_keys=True),
        ]
    return "\n".join(parts)


def parse_records(text: str) -> tuple[dict[str, object], ...]:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise MalformedResponse("resposta do provedor não é JSON válido") from exc
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise MalformedResponse('resposta do provedor sem a lista "records"')
    records = data["records"]
    if not all(isinstance(r, dict) for r in records):
        raise MalformedResponse('"records" contém item que não é objeto JSON')
    return tuple(records)
