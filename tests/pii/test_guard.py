"""Cenários Gherkin de requirements.md#7 sobre a fachada PiiGuard."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from sintetica.pii import MaskResult, PiiGuard, PiiType, PolicyError
from sintetica.pii.allowlist import ALLOWLIST_FILENAME, FileAllowlistStore
from sintetica.pii.checksums import cnpj_is_valid, cpf_is_valid
from sintetica.pii.guard import CHUNK_SIZE, CHUNK_THRESHOLD


def _guard(tmp_path: Path, patterns: list[str] | None = None, seed: int | None = 7) -> PiiGuard:
    policy = tmp_path / "policy.json"
    if patterns is not None:
        policy.write_text(json.dumps({"pii_custom_patterns": patterns}), "utf-8")
    return PiiGuard.for_dataset(tmp_path / "ds", policy, seed=seed)


def _types(guard: PiiGuard, text: str) -> list[PiiType]:
    return [f.type for f in guard.scan(text)]


def test_mask_real_cpf_from_interview(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    result = guard.mask("Meu CPF é 529.982.247-25")
    new_cpf = result.text.removeprefix("Meu CPF é ")
    assert new_cpf != "529.982.247-25"
    assert cpf_is_valid(new_cpf)
    assert len(new_cpf) == 14 and new_cpf[3] == "." and new_cpf[11] == "-"
    assert result.counts == {PiiType.CPF: 1}
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert "529.982.247-25" not in path.read_text("utf-8")
            assert "52998224725" not in path.read_text("utf-8")


def test_ignore_numeric_sequence_that_is_not_cpf(tmp_path: Path) -> None:
    assert _guard(tmp_path).scan("Pedido 11111111112") == []


def test_card_valid_and_invalid_by_luhn(tmp_path: Path) -> None:
    text = "4111 1111 1111 1111 e 4111 1111 1111 1112"
    assert _types(_guard(tmp_path), text) == [PiiType.CARD]


def test_cnpj_valid_and_wrong_check_digit(tmp_path: Path) -> None:
    text = "11.222.333/0001-81 e 11.222.333/0001-82"
    assert _types(_guard(tmp_path), text) == [PiiType.CNPJ]


def test_ignore_run_of_digits_that_looks_like_phone(tmp_path: Path) -> None:
    assert _guard(tmp_path).scan("Chave 11912345678") == []


def test_detect_email_phone_and_ips(tmp_path: Path) -> None:
    text = "ana@exemplo.com, (11) 91234-5678, 192.168.0.1 e 2001:db8::1"
    findings = _guard(tmp_path).scan(text)
    got = {f.type: text[f.start : f.end] for f in findings}
    assert got == {
        PiiType.EMAIL: "ana@exemplo.com",
        PiiType.PHONE: "(11) 91234-5678",
        PiiType.IPV4: "192.168.0.1",
        PiiType.IPV6: "2001:db8::1",
    }


def test_mask_is_reproducible_with_seed(tmp_path: Path) -> None:
    text = "CPF 529.982.247-25 e ana@exemplo.com"
    first = _guard(tmp_path / "a", seed=42).mask(text)
    second = _guard(tmp_path / "b", seed=42).mask(text)
    assert first.text == second.text


def test_coverage_lists_types_patterns_and_limits(tmp_path: Path) -> None:
    coverage = _guard(tmp_path, [r"MAT-\d{6}"]).coverage()
    assert len(coverage.types) == 7
    assert PiiType.CUSTOM not in coverage.types
    assert coverage.custom_patterns == 1
    assert any("Nomes" in limit for limit in coverage.limits)


def test_custom_pattern(tmp_path: Path) -> None:
    findings = _guard(tmp_path, [r"MAT-\d{6}"]).scan("MAT-123456")
    assert [f.type for f in findings] == [PiiType.CUSTOM]


def test_masked_value_is_not_a_leak(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    result = guard.mask("CPF 529.982.247-25, cartão 4111 1111 1111 1111, tel +55 11 91234-5678")
    assert guard.scan(result.text) != []
    assert guard.leaks(result.text) == []


def test_invalid_custom_pattern_rejects_policy(tmp_path: Path) -> None:
    with pytest.raises(PolicyError) as exc:
        _guard(tmp_path, [r"OK-\d+", r"(sem-fechar"])
    assert exc.value.index == 1


def test_missing_allowlist_counts_every_finding_as_leak(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    masked = guard.mask("CPF 529.982.247-25").text
    (tmp_path / "ds" / ALLOWLIST_FILENAME).unlink()
    fresh = _guard(tmp_path)
    assert not fresh.allowlist_available
    assert [f.type for f in fresh.leaks(masked)] == [PiiType.CPF]


class _BrokenGenerator:
    def generate(self, pii_type: PiiType, original: str) -> str:
        raise RuntimeError("falha simulada")


def test_substitute_failure_falls_back_to_asterisks(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    allowlist = FileAllowlistStore(tmp_path / ALLOWLIST_FILENAME)
    guard = PiiGuard(allowlist, substitutes=_BrokenGenerator())
    with caplog.at_level(logging.WARNING, logger="sintetica.pii"):
        result = guard.mask("CPF 529.982.247-25")
    assert result == MaskResult("CPF **************", {PiiType.CPF: 1}, 1)
    assert "529.982.247-25" not in caplog.text
    assert not allowlist.exists()


# Complementos de cobertura dos requisitos.


def test_field_is_attached_to_findings(tmp_path: Path) -> None:
    findings = _guard(tmp_path).scan("ana@exemplo.com", field="email_contato")
    assert findings[0].field == "email_contato"
    assert findings[0].preview == "an***"


def test_mask_is_idempotent_for_already_masked_values(tmp_path: Path) -> None:
    guard = _guard(tmp_path)
    once = guard.mask("CNPJ 11.222.333/0001-81").text
    twice = guard.mask(once)
    assert twice.text == once
    assert twice.counts == {}
    assert cnpj_is_valid(once.removeprefix("CNPJ "))


def test_mask_preserves_unformatted_shapes(tmp_path: Path) -> None:
    result = _guard(tmp_path).mask("52998224725 +5511912345678")
    cpf, phone = result.text.split(" ")
    assert cpf.isdigit() and len(cpf) == 11 and cpf_is_valid(cpf)
    assert phone.startswith("+55") and len(phone) == 14


def test_overlap_prefers_longest_finding(tmp_path: Path) -> None:
    assert _types(_guard(tmp_path), "4111111111111111") == [PiiType.CARD]


def test_large_text_is_scanned_in_chunks_without_duplicates(tmp_path: Path) -> None:
    filler = "x" * (CHUNK_SIZE - 5)
    text = (filler + " ana@exemplo.com ") * ((CHUNK_THRESHOLD // CHUNK_SIZE) + 2)
    findings = _guard(tmp_path).scan(text)
    expected = text.count("ana@exemplo.com")
    assert len(findings) == expected
    assert all(text[f.start : f.end] == "ana@exemplo.com" for f in findings)


def test_custom_pattern_is_masked(tmp_path: Path) -> None:
    guard = _guard(tmp_path, [r"MAT-\d{6}"])
    result = guard.mask("MAT-123456")
    assert result.text != "MAT-123456"
    assert result.text.startswith("MAT-")
    assert guard.leaks(result.text) == []


def test_empty_custom_match_is_ignored(tmp_path: Path) -> None:
    assert _guard(tmp_path, ["z*"]).scan("abc") == []


@pytest.mark.parametrize(
    ("text", "pii_type"),
    [
        ("ip 192.168.0.1", PiiType.IPV4),
        ("ip 2001:db8::1", PiiType.IPV6),
        ("tel (11) 3456-7890", PiiType.PHONE),
        ("tel 11 3456 7890", PiiType.PHONE),
    ],
)
def test_mask_other_types_keeps_type(tmp_path: Path, text: str, pii_type: PiiType) -> None:
    guard = _guard(tmp_path)
    result = guard.mask(text)
    assert result.counts == {pii_type: 1}
    assert result.fallbacks == 0
    assert [f.type for f in guard.scan(result.text)] == [pii_type]
    assert guard.leaks(result.text) == []


def test_custom_pattern_with_letters_only(tmp_path: Path) -> None:
    guard = _guard(tmp_path, [r"\bSigilo[A-Z][a-z]\b"])
    result = guard.mask("SigiloAb")
    assert result.counts == {PiiType.CUSTOM: 1}
    assert result.text != "SigiloAb"
