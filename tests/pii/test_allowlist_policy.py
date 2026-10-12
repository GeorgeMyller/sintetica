from __future__ import annotations

import json
from pathlib import Path

import pytest

from sintetica.pii import PiiType, PolicyError
from sintetica.pii.allowlist import FileAllowlistStore, fingerprint
from sintetica.pii.normalize import normalize
from sintetica.pii.policy import MAX_PATTERN_LENGTH, load_custom_patterns

# Allowlist


def test_allowlist_appends_one_hash_per_value(tmp_path: Path) -> None:
    path = tmp_path / "ds" / ".pii_allowlist"
    store = FileAllowlistStore(path)
    assert not store.exists()
    store.add(PiiType.CPF, "529.982.247-25")
    store.add(PiiType.CPF, "52998224725")  # mesmo valor normalizado
    store.add(PiiType.EMAIL, "ana@exemplo.com")
    lines = path.read_text("utf-8").splitlines()
    assert len(lines) == 2
    assert all(len(line) == 64 for line in lines)
    assert "529" not in path.read_text("utf-8").replace(lines[0], "").replace(lines[1], "")


def test_allowlist_reload_removes_duplicates(tmp_path: Path) -> None:
    path = tmp_path / ".pii_allowlist"
    digest = fingerprint(PiiType.CPF, "529.982.247-25")
    path.write_text(f"{digest}\n{digest}\n\n", "utf-8")
    store = FileAllowlistStore(path)
    assert store.contains(PiiType.CPF, "52998224725")
    assert store.path == path


def test_allowlist_missing_file_contains_nothing(tmp_path: Path) -> None:
    store = FileAllowlistStore(tmp_path / "nada")
    assert not store.contains(PiiType.EMAIL, "ana@exemplo.com")


@pytest.mark.parametrize(
    ("pii_type", "a", "b"),
    [
        (PiiType.CPF, "529.982.247-25", "52998224725"),
        (PiiType.CNPJ, "11.222.333/0001-81", "11222333000181"),
        (PiiType.CARD, "4111 1111 1111 1111", "4111-1111-1111-1111"),
        (PiiType.PHONE, "+55 (11) 91234-5678", "(11) 91234-5678"),
        (PiiType.EMAIL, " Ana@Exemplo.COM ", "ana@exemplo.com"),
        (PiiType.IPV6, "2001:0db8:0000:0000:0000:0000:0000:0001", "2001:db8::1"),
        (PiiType.IPV4, "192.168.0.1", "192.168.0.1"),
        (PiiType.CUSTOM, "MAT-1", "MAT-1"),
    ],
)
def test_normalize_equivalent_forms(pii_type: PiiType, a: str, b: str) -> None:
    assert normalize(pii_type, a) == normalize(pii_type, b)


# Política


def _write(tmp_path: Path, content: object) -> Path:
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(content) if not isinstance(content, str) else content, "utf-8")
    return path


def test_policy_missing_file(tmp_path: Path) -> None:
    assert load_custom_patterns(tmp_path / "nao-existe.json") == ()


def test_policy_missing_key(tmp_path: Path) -> None:
    assert load_custom_patterns(_write(tmp_path, {"telemetry": False})) == ()


def test_policy_valid_patterns(tmp_path: Path) -> None:
    path = _write(tmp_path, {"pii_custom_patterns": [r"MAT-\d{6}", "ABC"]})
    assert load_custom_patterns(path) == (r"MAT-\d{6}", "ABC")


@pytest.mark.parametrize(
    ("content", "index"),
    [
        ("{ inválido", -1),
        ([1, 2], -1),
        ({"pii_custom_patterns": "MAT"}, -1),
        ({"pii_custom_patterns": ["ok", "(aberto"]}, 1),
        ({"pii_custom_patterns": ["x" * (MAX_PATTERN_LENGTH + 1)]}, 0),
        ({"pii_custom_patterns": ["ok", 3]}, 1),
        ({"pii_custom_patterns": [""]}, 0),
    ],
)
def test_policy_errors(tmp_path: Path, content: object, index: int) -> None:
    with pytest.raises(PolicyError) as exc:
        load_custom_patterns(_write(tmp_path, content))
    assert exc.value.index == index
