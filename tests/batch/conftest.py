"""Projeto com intenção, contrato e amostra aprovados; provedores simulados; Ollama local."""

from __future__ import annotations

import io
import json
import sys
import threading
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from sintetica.batch import load_run_state
from sintetica.cli import main
from sintetica.providers.domain import (
    STOP_BUDGET,
    CostEstimate,
    GenerationRequest,
    GenerationResult,
    ProviderChoice,
)
from sintetica.providers.errors import ProviderExhausted
from sintetica.providers.ports import LLMProvider
from sintetica.providers.prompt import build_user_prompt

JSON_DRAFT: dict[str, Any] = {
    "format": "json",
    "fields": [
        {"name": "cliente", "type": "text"},
        {
            "name": "valor",
            "type": "decimal",
            "constraints": {"ge": 5, "le": 50, "casas_decimais": 2},
        },
    ],
}

CSV_DRAFT: dict[str, Any] = {
    "format": "csv",
    "fields": [
        {"name": "nome", "type": "text"},
        {"name": "tags", "type": "list", "items": {"type": "text"}},
        {"name": "saldo", "type": "decimal", "constraints": {"casas_decimais": 2}},
    ],
}

CPF = "529.982.247-25"


def cli(project: Path, *args: str) -> int:
    return main([*args, "--project-dir", str(project)])


def dataset(project: Path, slug: str = "pedidos") -> Path:
    return project / "datasets" / slug


def submit(project: Path, monkeypatch: pytest.MonkeyPatch, rid: str, lines: list[Any]) -> int:
    text = "".join((ln if isinstance(ln, str) else json.dumps(ln)) + "\n" for ln in lines)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(text.encode("utf-8"))))
    return main(["submit", "pedidos", rid, "--project-dir", str(project)])


def write_sample(path: Path, lines: Sequence[str], version: str | None = None) -> None:
    """Grava a semente aprovada como a feature 005 faria."""
    if version is None:
        version = json.loads((path / "schema.state.json").read_text("utf-8"))["schema_version"]
    seeds = path / "seeds"
    seeds.mkdir(exist_ok=True)
    (seeds / "sample.jsonl").write_text("".join(f"{ln}\n" for ln in lines), "utf-8")
    meta = {
        "schema_version": version,
        "approved_at": "2026-10-12T00:00:00Z",
        "provider": "harness",
        "n_requested": len(lines),
        "n_records": len(lines),
        "partial": False,
        "rounds": 0,
    }
    (seeds / "sample.meta.json").write_text(json.dumps(meta), "utf-8")


def prepare(
    project: Path,
    *,
    volume: int = 20,
    draft: dict[str, Any] | None = None,
    mode: str = "guiado",
    sample: bool = True,
    seeds: Sequence[str] | None = None,
) -> Path:
    """Intenção confirmada, contrato aprovado e amostra aprovada (salvo `sample=False`)."""
    spec = draft or JSON_DRAFT
    assert cli(project, "start", "pedidos", "--mode", mode) == 0
    answers = ["--objective", "testar pedidos", "--structure", "cliente e valor"]
    answers += ["--unknown", "rules", "--format", spec["format"], "--volume", str(volume)]
    assert cli(project, "intent", "set", "pedidos", *answers) == 0
    if mode == "guiado":
        assert cli(project, "intent", "confirm", "pedidos") == 0
    path = dataset(project)
    (path / "schema.draft.json").write_text(json.dumps(spec), "utf-8")
    assert cli(project, "schema", "build", "pedidos") == 0
    if mode == "guiado":
        assert cli(project, "schema", "approve", "pedidos") == 0
    if sample:
        if seeds is None:
            seeds = (
                ['{"nome":"Ana","tags":["a"],"saldo":1.00}']
                if spec["format"] == "csv"
                else ['{"cliente":"Ana","valor":10.00}', '{"cliente":"Bia","valor":20.00}']
            )
        write_sample(path, seeds)
    return path


def make_records(start: int, count: int) -> list[dict[str, object]]:
    """Registros válidos e distintos do contrato JSON."""
    return [{"cliente": f"Cliente {i}", "valor": 5 + (i % 40)} for i in range(start, start + count)]


def run_state(project: Path) -> Any:
    state = load_run_state(dataset(project))
    assert state is not None
    return state


def all_text(project: Path) -> str:
    return "\n".join(
        p.read_text("utf-8", errors="ignore") for p in project.rglob("*") if p.is_file()
    )


Responder = Callable[[GenerationRequest, int], GenerationResult]


@dataclass
class FakeProvider:
    """Provedor automático simulado. `responder(pedido, n)` monta a resposta do n-ésimo pedido."""

    responder: Responder
    provider_name: str = "ollama"
    cost_per_request: Decimal = Decimal("0")
    estimate_usd: Decimal = Decimal("0")
    requires_authorization: bool = False
    price_known: bool = True
    requests: list[GenerationRequest] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.provider_name

    @property
    def is_local(self) -> bool:
        return self.provider_name == "ollama"

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        build_user_prompt(request)  # o mesmo prompt dos backends reais precisa ser serializável
        self.requests.append(request)
        return self.responder(request, len(self.requests))

    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate:
        return CostEstimate(
            self.provider_name,
            "modelo",
            n_records,
            avg_tokens,
            self.estimate_usd,
            self.requires_authorization,
            self.price_known,
        )


def counter_responder(
    *,
    fail_at: int | None = None,
    budget_at: int | None = None,
    cost: Decimal = Decimal("0"),
    start: int = 0,
) -> Responder:
    """Responde registros novos e válidos; pode falhar ou parar por teto no pedido n."""
    state = {"next": start}

    def respond(request: GenerationRequest, n: int) -> GenerationResult:
        if fail_at is not None and n >= fail_at:
            raise ProviderExhausted("5xx após 3 tentativas")
        if budget_at is not None and n >= budget_at:
            return GenerationResult((), 0, 0, Decimal("0"), "external", STOP_BUDGET)
        records = make_records(state["next"], request.n_records)
        state["next"] += request.n_records
        return GenerationResult(tuple(records), 10, 10, cost, "fake")

    return respond


@dataclass
class Factory:
    """Fábrica injetável no `generate`: registra os argumentos de cada chamada."""

    provider: LLMProvider
    choice: ProviderChoice = field(
        default_factory=lambda: ProviderChoice("ollama", "ollama", "ollama simulado")
    )
    calls: list[tuple[int, Decimal | None, Decimal | None]] = field(default_factory=list)

    def __call__(
        self,
        n: int,
        dataset_dir: Path,
        project_dir: Path,
        authorized: Decimal | None,
        per_request: Decimal | None,
    ) -> tuple[LLMProvider, ProviderChoice]:
        self.calls.append((n, authorized, per_request))
        return self.provider, self.choice


# -- Ollama local para o processo em background -------------------------------------------


@dataclass
class OllamaServer:
    url: str
    delay_s: float = 0.0
    chats: int = 0


def _handler(server: OllamaServer) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            pass

        def _send(self, body: dict[str, Any]) -> None:
            data = json.dumps(body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            self._send({"models": []})

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length))
            prompt = body["messages"][-1]["content"]
            n = int(prompt.split("Gere exatamente ", 1)[1].split(" ", 1)[0])
            server.chats += 1
            if server.delay_s:
                import time

                time.sleep(server.delay_s)
            start = server.chats * 1000
            content = json.dumps({"records": make_records(start, n)})
            self._send({"message": {"content": content}, "prompt_eval_count": 5, "eval_count": 5})

    return Handler


@pytest.fixture
def ollama(monkeypatch: pytest.MonkeyPatch) -> Iterator[OllamaServer]:
    info = OllamaServer(url="")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _handler(info))
    info.url = f"http://127.0.0.1:{httpd.server_address[1]}"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("OLLAMA_HOST", info.url)
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    yield info
    httpd.shutdown()


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return tmp_path
