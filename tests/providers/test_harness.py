"""`HarnessAgentProvider` e `RequestStore` (RN-02, RF-04, RF-14, D-12 a D-15)."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path

import pytest
from support import make_request

from sintetica.providers import HarnessLimitExceeded, HarnessResponsePending, RequestStoreError
from sintetica.providers.harness.provider import HarnessAgentProvider, estimate_tokens
from sintetica.providers.harness.store import RequestStore, request_id
from sintetica.providers.prompt import build_user_prompt

JSONL_10 = "".join(json.dumps({"nome": f"p{i}"}) + "\n" for i in range(10)).encode()


@pytest.fixture
def dataset(project: Path) -> Path:
    return project / "datasets" / "demo"


def test_harness_refuses_more_than_100_records(dataset: Path) -> None:
    with pytest.raises(HarnessLimitExceeded) as info:
        asyncio.run(HarnessAgentProvider(dataset).generate(make_request(n_records=101)))
    assert (info.value.n_records, info.value.limit) == (101, 100)
    assert not (dataset / "requests").exists()


def test_without_response_the_request_is_saved_and_pending(dataset: Path) -> None:
    provider = HarnessAgentProvider(dataset)
    request = make_request(n_records=10)
    with pytest.raises(HarnessResponsePending) as info:
        asyncio.run(provider.generate(request))
    rid = request_id(request)
    assert info.value.request_id == rid
    assert info.value.command == f"uv run sintetica submit demo {rid}"
    saved = json.loads((dataset / "requests" / f"{rid}.json").read_text("utf-8"))
    assert saved["id"] == rid and saved["n_records"] == 10 and saved["version"] == 1


def test_two_step_protocol(dataset: Path) -> None:
    provider = HarnessAgentProvider(dataset)
    request = make_request(n_records=10)
    rid = RequestStore(dataset).save_request(request)
    assert RequestStore(dataset).submit(rid, JSONL_10) == 10

    result = asyncio.run(provider.generate(request))
    assert len(result.records) == 10
    assert result.cost_usd == 0 and result.provider == "harness"
    assert result.input_tokens == math.ceil(len(build_user_prompt(request)) / 4)
    assert result.output_tokens == estimate_tokens(JSONL_10.decode())
    assert {p.name for p in (dataset / "requests").iterdir()} == {
        f"{rid}.json",
        f"{rid}.response.jsonl",
    }


def test_request_id_is_idempotent(dataset: Path) -> None:
    store = RequestStore(dataset)
    first = store.save_request(make_request())
    before = store.request_path(first).read_text("utf-8")
    assert store.save_request(make_request()) == first
    assert store.request_path(first).read_text("utf-8") == before
    assert request_id(make_request(n_records=3)) != first
    assert len(first) == 12 and int(first, 16) >= 0


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"", "recebidos 0"),
        (b"\n\n", "recebidos 0"),
        (b'{"a": 1}\n[1]\n', "linha 2"),
        (b'{"a": 1}\nnao json\n', "linha 2"),
        (b'{"a": 1}\n' * 3, "recebidos 3"),
        (b"\xff\xfe", "UTF-8"),
    ],
)
def test_invalid_submit_writes_nothing(dataset: Path, raw: bytes, message: str) -> None:
    store = RequestStore(dataset)
    rid = store.save_request(make_request(n_records=2))
    with pytest.raises(RequestStoreError, match=message) as info:
        store.submit(rid, raw)
    assert info.value.exit_code == 5
    assert not store.response_path(rid).exists()


def test_submit_unknown_request(dataset: Path) -> None:
    with pytest.raises(RequestStoreError, match="pedido inexistente") as info:
        RequestStore(dataset).submit("r9", b'{"a": 1}\n')
    assert info.value.exit_code == 4


def test_submit_too_large(dataset: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import sintetica.providers.harness.store as store_module

    monkeypatch.setattr(store_module, "MAX_SUBMIT_BYTES", 10)
    store = RequestStore(dataset)
    rid = store.save_request(make_request())
    with pytest.raises(RequestStoreError) as info:
        store.submit(rid, b'{"nome": "longo demais"}\n')
    assert info.value.exit_code == 5


def test_fewer_records_than_requested_are_accepted(dataset: Path) -> None:
    store = RequestStore(dataset)
    rid = store.save_request(make_request(n_records=5))
    assert store.submit(rid, b'{"a": 1}\n\n{"a": 2}\n') == 2
    loaded = store.load_response(rid)
    assert loaded is not None and loaded[1] == ({"a": 1}, {"a": 2})


def test_request_needs_at_least_one_record() -> None:
    with pytest.raises(ValueError, match="n_records"):
        make_request(n_records=0)


def test_load_request(dataset: Path) -> None:
    store = RequestStore(dataset)
    req = make_request(n_records=10, instructions="Instruções de teste")
    rid = store.save_request(req)
    loaded = store.load_request(rid)
    assert loaded is not None
    assert loaded.n_records == 10
    assert loaded.instructions == "Instruções de teste"
    assert loaded.schema_json == dict(req.schema_json)
    assert store.load_request("inexistente") is None
