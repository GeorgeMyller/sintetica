"""Pedidos e respostas do harness em `datasets/<slug>/requests/` (RF-14).

Contrato em interfaces/harness-cli.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sintetica.providers.domain import GenerationRequest
from sintetica.providers.errors import RequestStoreError

REQUESTS_DIRNAME = "requests"
MAX_HARNESS_RECORDS = 100
MAX_SUBMIT_BYTES = 10 * 1024 * 1024
RESPONSE_FORMAT = "1 objeto JSON por linha (JSONL), sem texto extra"

EXIT_MISSING_REQUEST = 4
EXIT_INVALID_RESPONSE = 5


def _canonical(request: GenerationRequest) -> dict[str, object]:
    return {
        "n_records": request.n_records,
        "instructions": request.instructions,
        "schema_json": dict(request.schema_json),
        "seeds": [dict(s) for s in request.seeds],
    }


def request_id(request: GenerationRequest) -> str:
    """12 hex do SHA-256 do pedido canônico: mesmo conteúdo, mesmo id (D-12)."""
    text = json.dumps(_canonical(request), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


class RequestStore:
    def __init__(self, dataset_dir: Path) -> None:
        self._dir = dataset_dir / REQUESTS_DIRNAME

    def request_path(self, rid: str) -> Path:
        return self._dir / f"{rid}.json"

    def response_path(self, rid: str) -> Path:
        return self._dir / f"{rid}.response.jsonl"

    def save_request(self, request: GenerationRequest) -> str:
        """Grava o pedido se ainda não existe e devolve o id. Nunca reescreve um pedido."""
        rid = request_id(request)
        path = self.request_path(rid)
        if not path.exists():
            body = {
                "version": 1,
                "id": rid,
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                **_canonical(request),
                "response_format": RESPONSE_FORMAT,
            }
            _write_atomic(path, json.dumps(body, ensure_ascii=False, indent=2) + "\n")
        return rid

    def _n_records(self, rid: str) -> int:
        path = self.request_path(rid)
        if not path.exists():
            raise RequestStoreError(f"pedido inexistente: {rid}", EXIT_MISSING_REQUEST)
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data["n_records"])

    def submit(self, rid: str, raw: bytes) -> int:
        """Valida o JSONL e grava a resposta. Em qualquer erro, nada é gravado (D-14)."""
        n_records = self._n_records(rid)
        if len(raw) > MAX_SUBMIT_BYTES:
            raise RequestStoreError(
                f"entrada maior que {MAX_SUBMIT_BYTES // (1024 * 1024)} MB", EXIT_INVALID_RESPONSE
            )
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise RequestStoreError("entrada não está em UTF-8", EXIT_INVALID_RESPONSE) from None
        records: list[str] = []
        for number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                item = None
            if not isinstance(item, dict):
                raise RequestStoreError(
                    f"linha {number}: não é um objeto JSON", EXIT_INVALID_RESPONSE
                )
            records.append(json.dumps(item, ensure_ascii=False))
        if not 1 <= len(records) <= n_records:
            raise RequestStoreError(
                f"recebidos {len(records)} registros; esperado de 1 a {n_records}",
                EXIT_INVALID_RESPONSE,
            )
        _write_atomic(self.response_path(rid), "\n".join(records) + "\n")
        return len(records)

    def load_response(self, rid: str) -> tuple[str, tuple[dict[str, object], ...]] | None:
        """Texto bruto e registros da resposta, ou `None` se o agente ainda não enviou."""
        path = self.response_path(rid)
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        records = tuple(json.loads(line) for line in text.splitlines() if line.strip())
        return text, records
