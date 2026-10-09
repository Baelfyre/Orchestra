from __future__ import annotations

import hashlib

import pytest

from orchestra_runtime import evidence
from orchestra_runtime.shared import canonicalization


SHA40_UPPER = "A" * 40
SHA64_UPPER = "B" * 64


def test_legacy_evidence_exports_are_shared_canonicalization_symbols():
    assert evidence.canonical_json_bytes is canonicalization.canonical_json_bytes
    assert evidence.normalize_git_sha is canonicalization.normalize_git_sha
    assert evidence.normalize_sha256 is canonicalization.normalize_sha256
    assert evidence.normalize_timestamp is canonicalization.normalize_timestamp
    assert evidence.receipt_digest is canonicalization.receipt_digest


def test_normalizers_preserve_legacy_canonical_forms():
    assert canonicalization.normalize_git_sha(SHA40_UPPER) == "a" * 40
    assert canonicalization.normalize_sha256(SHA64_UPPER) == "b" * 64
    assert canonicalization.normalize_timestamp("2026-09-02T08:30:45+08:00") == "2026-09-02T00:30:45Z"
    assert canonicalization.normalize_timestamp("2026-09-02T00:30:45.999Z") == "2026-09-02T00:30:45Z"


@pytest.mark.parametrize(
    ("normalizer", "value"),
    [
        (canonicalization.normalize_git_sha, "a" * 39),
        (canonicalization.normalize_git_sha, "g" * 40),
        (canonicalization.normalize_sha256, "b" * 63),
        (canonicalization.normalize_sha256, "g" * 64),
    ],
)
def test_digest_normalizers_reject_noncanonical_lengths_or_hex(normalizer, value):
    with pytest.raises(ValueError):
        normalizer(value)


def test_timestamp_requires_timezone_and_rejects_invalid_input():
    with pytest.raises(ValueError, match="include a timezone"):
        canonicalization.normalize_timestamp("2026-09-02T00:30:45")
    with pytest.raises(ValueError, match="RFC3339/ISO-8601"):
        canonicalization.normalize_timestamp("not-a-time")


def test_canonical_json_is_deterministic_compact_utf8_and_strict():
    value = {"z": "ñ", "a": [3, 2, 1], "nested": {"b": True, "a": None}}
    expected = b'{"a":[3,2,1],"nested":{"a":null,"b":true},"z":"\xc3\xb1"}'
    assert canonicalization.canonical_json_bytes(value) == expected
    assert canonicalization.canonical_json_bytes(value) == evidence.canonical_json_bytes(value)

    with pytest.raises(ValueError, match="canonical Orchestra JSON"):
        canonicalization.canonical_json_bytes({"bad": float("nan")})
    with pytest.raises(ValueError, match="canonical Orchestra JSON"):
        canonicalization.canonical_json_bytes({"bad": object()})


def test_receipt_digest_is_sha256_of_canonical_json_bytes():
    value = {"phase": "AR-2", "revision": 2, "ready": True}
    expected = hashlib.sha256(canonicalization.canonical_json_bytes(value)).hexdigest()
    assert canonicalization.receipt_digest(value) == expected
    assert evidence.receipt_digest(value) == expected


def test_evidence_receipts_remain_compatible_through_shared_primitives():
    source = evidence.SourceStateReceipt(
        repository="Baelfyre/Orchestra",
        canonical_branch="main",
        live_canonical_sha=SHA40_UPPER,
        verification_timestamp="2026-09-02T08:30:45+08:00",
        verification_method="GITHUB_API",
    )
    assert source.live_canonical_sha == "a" * 40
    assert source.verification_timestamp == "2026-09-02T00:30:45Z"
    assert source.digest == canonicalization.receipt_digest(source.to_dict())

    validation = evidence.build_validation_execution_receipt(
        command_id="shared-canonicalization",
        command=("python", "-m", "pytest"),
        exit_code=0,
        started_at="2026-09-02T00:30:45Z",
        finished_at="2026-09-02T00:30:46Z",
        stdout="pass",
        stderr=b"",
        head_before="c" * 40,
        head_after="c" * 40,
    )
    assert validation.verdict == "PASS"
    assert validation.exact_state_preserved is True
    assert validation.digest == canonicalization.receipt_digest(validation.to_dict())
