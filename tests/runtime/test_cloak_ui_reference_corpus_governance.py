from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "machine/governance/cloak-ui-reference-corpus-policy.v1.json"
POLICY_SCHEMA_PATH = ROOT / "machine/schemas/cloak-ui-reference-corpus-policy.v1.schema.json"
SOURCE_SCHEMA_PATH = ROOT / "machine/schemas/cloak-ui-reference-source-record.v1.schema.json"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def valid_reference_record(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "orchestra.cloak-ui-reference-source-record.v1",
        "record_id": "nazia-99.example-ui.0123456789ab",
        "repository": "Nazia-99/Example-UI",
        "owner": "Nazia-99",
        "source_revision": "1" * 40,
        "source_paths_or_artifact_ids": ["index.html", "style.css"],
        "source_category": "UI_REFERENCE",
        "license_identifier": "NONE_DETECTED",
        "license_evidence": [
            {
                "type": "ABSENCE_CHECK",
                "reference": "No license file or repository license metadata detected at pinned revision",
                "source_revision": "1" * 40,
            }
        ],
        "reuse_classification": "REFERENCE_ONLY",
        "attribution_or_notice_requirements": [
            "Acknowledge Nazia-99 and repository Nazia-99/Example-UI in the retained pattern record"
        ],
        "pattern_or_asset_summary": "Reference-only layout and interaction concepts.",
        "what_was_learned_or_reused": ["General card hierarchy and state grouping concept"],
        "what_was_not_copied": ["No original source code, assets, or substantial implementation expression copied"],
        "review_owner": "Artificer",
    }
    payload.update(overrides)
    return payload


def test_machine_policy_validates_against_cuir0_schema() -> None:
    policy = load_json(POLICY_PATH)
    schema = load_json(POLICY_SCHEMA_PATH)

    Draft202012Validator(schema).validate(policy)
    assert policy["schema_version"] == "orchestra.cloak-ui-reference-corpus-policy.v1"
    assert policy["plan_id"] == "CLOAK_UI_REFERENCE_CORPUS_V1"
    assert policy["phase"] == "CUIR-0"


def test_ui_repository_count_is_discovered_in_cuir1_not_hard_coded() -> None:
    policy = load_json(POLICY_PATH)
    ui_reference = policy["corpus"]["ui_reference"]

    assert ui_reference["initial_account"] == "Nazia-99"
    assert ui_reference["repository_count"] == "DISCOVER_AT_CUIR_1"
    assert not isinstance(ui_reference["repository_count"], int)


def test_icon_corpus_remains_separate_and_exactly_scoped() -> None:
    policy = load_json(POLICY_PATH)
    icon_reference = policy["corpus"]["icon_reference"]

    assert icon_reference["separate_subcorpus"] is True
    assert icon_reference["repositories"] == [
        "simple-icons/simple-icons",
        "tabler/tabler-icons",
        "lucide-icons/lucide",
    ]


def test_account_wide_license_inference_and_automatic_ingestion_are_disabled() -> None:
    policy = load_json(POLICY_PATH)
    eligibility = policy["eligibility"]

    assert eligibility["license_classified_per_repository"] is True
    assert eligibility["account_wide_license_inference"] is False
    assert eligibility["automatic_ingestion"] is False
    assert eligibility["exact_revision_required_before_deep_analysis"] is True


def test_missing_or_ambiguous_license_fails_closed_for_direct_reuse() -> None:
    policy = load_json(POLICY_PATH)
    fail_closed = policy["reuse"]["license_fail_closed"]

    assert fail_closed["missing_or_ambiguous_license_pattern_treatment"] == "REFERENCE_ONLY"
    assert fail_closed["missing_or_ambiguous_license_direct_reuse"] == "PROHIBITED"
    assert fail_closed["unresolved_rights_direct_reuse"] == "PROHIBITED"
    assert policy["reuse"]["direct_reuse_requires_verified_permission"] is True


def test_external_repository_execution_is_completely_disabled() -> None:
    policy = load_json(POLICY_PATH)
    execution = policy["external_execution"]

    assert execution == {
        "allowed": False,
        "run_build_scripts": False,
        "install_project_dependencies": False,
        "execute_application_code": False,
        "execute_unknown_scripts": False,
    }


def test_data_minimization_prevents_default_repository_mirroring() -> None:
    policy = load_json(POLICY_PATH)
    minimization = policy["data_minimization"]

    assert minimization["retain_only_relevant_evidence"] is True
    assert minimization["mirror_entire_repository"] is False
    assert minimization["retain_unneeded_assets"] is False
    assert minimization["pattern_records_must_be_concept_level_by_default"] is True


def test_source_record_schema_preserves_plan_required_fields() -> None:
    policy = load_json(POLICY_PATH)
    schema = load_json(SOURCE_SCHEMA_PATH)
    required = set(schema["required"])

    assert set(policy["provenance"]["required_fields"]).issubset(required)
    assert {
        "repository",
        "owner",
        "source_revision",
        "source_paths_or_artifact_ids",
        "source_category",
        "license_identifier",
        "license_evidence",
        "reuse_classification",
        "attribution_or_notice_requirements",
        "pattern_or_asset_summary",
        "what_was_learned_or_reused",
        "what_was_not_copied",
        "review_owner",
    }.issubset(required)


def test_reference_only_unlicensed_nazia_record_is_valid() -> None:
    schema = load_json(SOURCE_SCHEMA_PATH)

    Draft202012Validator(schema).validate(valid_reference_record())


def test_unlicensed_record_cannot_claim_reuse_with_notice() -> None:
    schema = load_json(SOURCE_SCHEMA_PATH)

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(
            valid_reference_record(reuse_classification="REUSE_WITH_NOTICE")
        )


def test_ambiguous_license_cannot_claim_rights_review_reuse() -> None:
    schema = load_json(SOURCE_SCHEMA_PATH)

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(
            valid_reference_record(
                license_identifier="AMBIGUOUS",
                reuse_classification="REUSE_WITH_RIGHTS_REVIEW",
            )
        )


def test_nazia_reference_record_requires_nazia_attribution() -> None:
    schema = load_json(SOURCE_SCHEMA_PATH)

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(
            valid_reference_record(
                attribution_or_notice_requirements=["Specific repository acknowledgement required"]
            )
        )


def test_source_revision_must_be_exact_commit_sha() -> None:
    schema = load_json(SOURCE_SCHEMA_PATH)

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(valid_reference_record(source_revision="main"))


def test_source_record_fails_when_non_copying_evidence_is_missing() -> None:
    schema = load_json(SOURCE_SCHEMA_PATH)
    record = valid_reference_record()
    record.pop("what_was_not_copied")

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(record)


def test_source_record_rejects_unknown_reuse_classification() -> None:
    schema = load_json(SOURCE_SCHEMA_PATH)

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(
            valid_reference_record(reuse_classification="PUBLIC_REPO_FREE_TO_COPY")
        )


def test_policy_authority_is_non_authorizing() -> None:
    policy = load_json(POLICY_PATH)

    assert policy["authority"] == {
        "external_code_execution_authorized": False,
        "automatic_ingestion_authorized": False,
        "code_implementation_authorized": False,
        "merge_authorized": False,
        "release_authorized": False,
        "deployment_authorized": False,
        "policy_activation_authorized": False,
        "automatic_provider_routing_authorized": False,
    }


def test_specialist_ownership_keeps_artificer_and_cloak_non_implementing() -> None:
    policy = load_json(POLICY_PATH)

    assert set(policy["roles"]) == {
        "Artificer",
        "Cloak",
        "Governor",
        "Clockwork",
        "Ponytail",
        "Overseer",
        "Arbiter",
    }
    assert policy["handoff"]["artificer_cannot_self_approve_implementation"] is True
    assert policy["handoff"]["cloak_has_code_implementation_authority"] is False
    assert policy["handoff"]["cuir1_requires_cuir0_pass"] is True


def test_policy_schema_prevents_authority_widening() -> None:
    policy = load_json(POLICY_PATH)
    schema = load_json(POLICY_SCHEMA_PATH)
    widened = copy.deepcopy(policy)
    widened["authority"]["code_implementation_authorized"] = True

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(widened)


def test_policy_schema_prevents_external_execution_widening() -> None:
    policy = load_json(POLICY_PATH)
    schema = load_json(POLICY_SCHEMA_PATH)
    widened = copy.deepcopy(policy)
    widened["external_execution"]["allowed"] = True

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(widened)
