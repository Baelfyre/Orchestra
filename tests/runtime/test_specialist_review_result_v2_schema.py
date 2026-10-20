# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "machine" / "schemas"


def _load_schema(version: int) -> dict[str, object]:
    path = SCHEMAS / f"specialist-review-result.v{version}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _review_v1() -> dict[str, object]:
    digest = "a" * 64
    return {
        "review_version": "orchestra.specialist-review-result.v1",
        "review_id": f"specialist-review.{digest[:24]}",
        "review_digest": digest,
        "request_id": "review-request-1",
        "request_digest": "b" * 64,
        "operation_id": "defensive-security-review",
        "specialist": "cipher",
        "status": "FINDINGS",
        "conclusion": "One defensive finding was identified.",
        "findings": ["Review candidate authorization boundary."],
        "evidence_refs": ["snapshot:src/auth.py"],
        "workspace_snapshot_digest": "c" * 64,
    }


def _review_v2() -> dict[str, object]:
    result = _review_v1()
    result.update(
        review_version="orchestra.specialist-review-result.v2",
        runtime_identity_digest="d" * 64,
    )
    return result


def test_v2_schema_accepts_runtime_bound_substantive_review() -> None:
    schema = _load_schema(2)
    Draft202012Validator.check_schema(schema)

    assert Draft202012Validator(schema).is_valid(_review_v2())


def test_v1_shape_remains_valid_and_is_not_reinterpreted_as_v2() -> None:
    v1 = Draft202012Validator(_load_schema(1))
    v2 = Draft202012Validator(_load_schema(2))

    assert v1.is_valid(_review_v1())
    assert not v1.is_valid(_review_v2())
    assert not v2.is_valid(_review_v1())


def test_v2_schema_rejects_authority_fields_and_unknown_properties() -> None:
    validator = Draft202012Validator(_load_schema(2))

    for key, value in (
        ("governance_validated", True),
        ("governanceReceiptRef", "receipt-1"),
        ("unexpected", "value"),
    ):
        result = _review_v2()
        result[key] = value
        assert not validator.is_valid(result)


def test_v2_schema_rejects_malformed_digests_and_missing_evidence() -> None:
    validator = Draft202012Validator(_load_schema(2))

    malformed_digest = _review_v2()
    malformed_digest["runtime_identity_digest"] = "not-a-sha256"
    assert not validator.is_valid(malformed_digest)

    missing_evidence = _review_v2()
    missing_evidence["evidence_refs"] = []
    assert not validator.is_valid(missing_evidence)
