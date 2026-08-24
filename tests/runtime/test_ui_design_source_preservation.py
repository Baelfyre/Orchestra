from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_SCHEMA = ROOT / "machine" / "schemas" / "design-source-preservation-workflow.schema.json"
WORKFLOW_RECORD = ROOT / "machine" / "ui" / "design-source-preservation-workflow.v1.json"
REPORT_SCHEMA = ROOT / "machine" / "schemas" / "design-source-preservation-report.schema.json"
VALID_REPORT = ROOT / "tests" / "fixtures" / "ui" / "uix2-valid-preservation-report.json"
INVALID_REPORTS = (
    ROOT / "tests" / "fixtures" / "ui" / "uix2-invalid-blocking-ready.json",
    ROOT / "tests" / "fixtures" / "ui" / "uix2-invalid-adaptation-without-approval.json",
)
UIX1_SCHEMA = ROOT / "machine" / "schemas" / "ui-design-contract.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(path: Path) -> jsonschema.Draft202012Validator:
    schema = _load(path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_uix2_workflow_record_is_schema_valid_and_library_neutral() -> None:
    workflow = _load(WORKFLOW_RECORD)
    _validator(WORKFLOW_SCHEMA).validate(workflow)

    assert UIX1_SCHEMA.is_file()
    assert workflow["consumes"]["ui_design_contract_schema"] == "machine/schemas/ui-design-contract.schema.json"
    assert workflow["consumes"]["supported_source_providers"] == [
        "FIGMA",
        "PROJECT_NATIVE",
        "STORYBOOK",
        "SCREENSHOT",
        "REFERENCE_IMAGE",
        "OTHER_STRUCTURED",
        "NONE",
    ]
    assert workflow["required_rules"]["external_tool_is_authority"] is False
    assert workflow["required_rules"]["silent_inference_allowed"] is False


def test_uix2_preservation_order_requires_project_reuse_before_approved_adaptation() -> None:
    workflow = _load(WORKFLOW_RECORD)
    assert workflow["preservation_precedence"] == [
        "EXACT_SUPPLIED_OR_PROJECT_EVIDENCE",
        "EXISTING_PROJECT_COMPONENT",
        "SEMANTIC_TOKEN_MAPPING",
        "APPROVED_ADAPTATION",
        "UNRESOLVED_NO_GUESS",
    ]
    assert workflow["intake_order"][-2:] == [
        "REPORT_UNRESOLVED_EVIDENCE",
        "ISSUE_PRE_IMPLEMENTATION_HANDOFF",
    ]


def test_uix2_project_native_reference_report_is_valid_without_figma() -> None:
    report = _load(VALID_REPORT)
    _validator(REPORT_SCHEMA).validate(report)

    assert report["source"]["provider"] == "PROJECT_NATIVE"
    assert report["handoff"] == {"status": "READY_FOR_IMPLEMENTATION", "blockers": []}
    assert report["authority"]["report_grants_implementation_authority"] is False
    assert report["authority"]["external_tools_grant_authority"] is False


@pytest.mark.parametrize("fixture_path", INVALID_REPORTS)
def test_uix2_invalid_preservation_reports_are_rejected(fixture_path: Path) -> None:
    with pytest.raises(jsonschema.ValidationError):
        _validator(REPORT_SCHEMA).validate(_load(fixture_path))


def test_uix2_inference_and_adaptation_require_explicit_approval() -> None:
    report = copy.deepcopy(_load(VALID_REPORT))
    item = report["evidence_items"][0]
    item["confidence"] = "INFERRED_WITH_EXPLICIT_APPROVAL"
    item["preservation"] = "ADAPT_WITH_APPROVAL"
    item["reason"] = "A bounded inference is necessary because the exact token mapping is unavailable."

    with pytest.raises(jsonschema.ValidationError):
        _validator(REPORT_SCHEMA).validate(report)

    item["approval_ref"] = "human-approval:uix2-bounded-adaptation"
    _validator(REPORT_SCHEMA).validate(report)


def test_uix2_implementation_blocking_unresolved_evidence_fails_closed() -> None:
    report = copy.deepcopy(_load(VALID_REPORT))
    report["unresolved"] = [
        {
            "subject_ref": "component:checkout-payment",
            "reason": "The source design does not identify which project component owns payment-method selection.",
            "blocking": "IMPLEMENTATION_BLOCKING",
            "required_resolution": "Resolve the project component mapping before implementation.",
        }
    ]

    with pytest.raises(jsonschema.ValidationError):
        _validator(REPORT_SCHEMA).validate(report)

    report["handoff"] = {
        "status": "BLOCKED_UNRESOLVED_EVIDENCE",
        "blockers": ["component:checkout-payment"],
    }
    _validator(REPORT_SCHEMA).validate(report)


def test_uix2_workflow_cannot_turn_evidence_into_authority() -> None:
    workflow = _load(WORKFLOW_RECORD)
    assert workflow["authority"] == {
        "workflow_grants_implementation_authority": False,
        "external_tools_grant_authority": False,
        "report_grants_authority": False,
        "dependency_adoption_authorized": False,
        "figma_mutation_authorized": False,
    }
