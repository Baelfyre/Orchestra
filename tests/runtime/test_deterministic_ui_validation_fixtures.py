from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "tests" / "fixtures" / "ui" / "uix7-deterministic-validation-fixtures.schema.json"
SUITE_PATH = ROOT / "tests" / "fixtures" / "ui" / "uix7-deterministic-validation-suite.json"
PROFILE_REGISTRY_PATH = ROOT / "machine" / "ui" / "ui-profile-registry.v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _profile_errors(selection: dict, registry: dict) -> list[str]:
    rules = registry["composition_rules"]
    profiles = {profile["profile_id"]: profile for profile in registry["profiles"]}
    errors: list[str] = []

    for category in rules["required_categories"]:
        if len(selection.get(category, [])) != 1:
            errors.append(f"{category}:required-exactly-one")

    for category in rules["required_categories"] + rules["optional_categories"]:
        selected = selection.get(category, [])
        maximum = rules["maximum_selections_by_category"][category]
        if len(selected) > maximum:
            errors.append(f"{category}:maximum")
        for profile_id in selected:
            profile = profiles.get(profile_id)
            if profile is None:
                errors.append(f"unknown:{profile_id}")
            elif profile["category"] != category:
                errors.append(f"wrong-category:{profile_id}")

    selected_ids = [profile_id for values in selection.values() for profile_id in values]
    if len(selected_ids) != len(set(selected_ids)):
        errors.append("duplicate-profile")

    for rule in rules["incompatibility_rules"]:
        selected_count = len(set(selected_ids).intersection(rule["profile_ids"]))
        if rule["kind"] in {"CATEGORY_MUTUALLY_EXCLUSIVE", "CATEGORY_MAXIMUM"} and selected_count > 1:
            errors.append(rule["rule_id"])

    return errors


def _evaluate(case: dict, registry: dict) -> tuple[str, str | None]:
    category = case["category"]
    data = case["input"]

    if category == "COMPONENT_REUSE":
        violation = data["requested_component"] == data["existing_component"] and (
            data["implementation_component"] != data["existing_component"] or data["duplicate_created"]
        )
        return ("FAIL_CLOSED", "COMPONENT_REUSE_VIOLATION") if violation else ("PASS", None)

    if category == "TOKEN_PRESERVATION":
        return ("PASS", None) if data["source_token_ref"] == data["implementation_token_ref"] else ("FAIL_CLOSED", "TOKEN_REFERENCE_DRIFT")

    if category == "ARBITRARY_VALUE_DRIFT":
        if data["project_token_available"] and data["arbitrary_value_used"]:
            return "FAIL_CLOSED", "ARBITRARY_VALUE_WITH_AVAILABLE_TOKEN"
        return "PASS", None

    if category == "STATE_COMPLETENESS":
        if not set(data["required_states"]).issubset(data["implemented_states"]):
            return "FAIL_CLOSED", "REQUIRED_STATE_MISSING"
        return "PASS", None

    if category == "PROFILE_CONFLICT":
        return ("FAIL_CLOSED", "PROFILE_COMPOSITION_CONFLICT") if _profile_errors(data["selection"], registry) else ("PASS", None)

    if category == "ASSET_PROVENANCE":
        if data["source_identity"] == data["implementation_source_identity"]:
            return "PASS", None
        if data["substitution_approved"] and data["approval_ref"]:
            return "PASS", None
        return "FAIL_CLOSED", "UNAPPROVED_ASSET_SUBSTITUTION"

    if category == "RESPONSIVE_CONTAINMENT":
        if data["overflow_x"] or data["content_width"] > data["viewport_width"]:
            return "FAIL_CLOSED", "RESPONSIVE_OVERFLOW"
        return "PASS", None

    if category == "ACCESSIBILITY_INVARIANTS":
        if not all((data["reduced_motion_respected"], data["forced_colors_respected"], data["interaction_critical_contrast_passed"])):
            return "FAIL_CLOSED", "ACCESSIBILITY_INVARIANT_VIOLATION"
        return "PASS", None

    if category == "REFERENCE_IDENTITY":
        if data["expected_reference_identity"] != data["observed_reference_identity"] or data["expected_revision"] != data["observed_revision"]:
            return "FAIL_CLOSED", "REFERENCE_IDENTITY_MISMATCH"
        return "PASS", None

    if category == "VISUAL_BASELINE_REPLACEMENT":
        if not data["baseline_replaced"]:
            return "PASS", None
        if data["prior_comparison_result"] == "FAIL":
            return "FAIL_CLOSED", "FAILING_BASELINE_REPLACEMENT_PROHIBITED"
        if not data["approval_ref"] or not data["replacement_reason"]:
            return "FAIL_CLOSED", "UNAPPROVED_BASELINE_REPLACEMENT"
        return "PASS", None

    raise AssertionError(f"Unhandled category: {category}")


def test_uix7_schema_suite_and_source_refs_are_valid() -> None:
    suite = _load(SUITE_PATH)
    _validator().validate(suite)
    assert suite["schema_version"] == "orchestra.ui-deterministic-validation-fixtures.v1"
    assert suite["entry_baseline"] == "67af42002a18ac3b58811cb2877d285bc8604ce0"
    assert len(suite["categories"]) == 10
    assert len(suite["cases"]) == 20
    assert all((ROOT / ref).is_file() for ref in suite["source_contracts"])
    assert all((ROOT / ref).exists() for case in suite["cases"] for ref in case["evidence_refs"])


def test_uix7_has_one_pass_and_one_fail_closed_case_per_required_category() -> None:
    suite = _load(SUITE_PATH)
    for category in suite["categories"]:
        category_cases = [case for case in suite["cases"] if case["category"] == category]
        assert len(category_cases) == 2
        assert {case["expectation"] for case in category_cases} == {"PASS", "FAIL_CLOSED"}


@pytest.mark.parametrize("case", _load(SUITE_PATH)["cases"], ids=lambda case: case["case_id"])
def test_uix7_fixture_outcomes_are_deterministic(case: dict) -> None:
    expectation, failure_code = _evaluate(case, _load(PROFILE_REGISTRY_PATH))
    assert expectation == case["expectation"]
    assert failure_code == case["failure_code"]


def test_uix7_failing_visual_comparison_cannot_be_erased_by_baseline_replacement() -> None:
    case = next(case for case in _load(SUITE_PATH)["cases"] if case["case_id"] == "uix7-visual-baseline-erase-failure")
    assert case["input"]["approval_ref"]
    assert _evaluate(case, _load(PROFILE_REGISTRY_PATH)) == ("FAIL_CLOSED", "FAILING_BASELINE_REPLACEMENT_PROHIBITED")


def test_uix7_authority_is_fail_closed_and_schema_rejects_escalation() -> None:
    suite = _load(SUITE_PATH)
    assert all(value is False for value in suite["authority"].values())
    invalid = copy.deepcopy(suite)
    invalid["authority"]["fixture_result_grants_authority"] = True
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)


def test_uix7_schema_rejects_unrecognized_or_underspecified_cases() -> None:
    suite = _load(SUITE_PATH)
    invalid = copy.deepcopy(suite)
    invalid["cases"][0]["input"]["undeclared_css"] = "#fff"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)
    invalid = copy.deepcopy(suite)
    invalid["cases"][0]["expectation"] = "FAIL_CLOSED"
    invalid["cases"][0]["failure_code"] = None
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)
