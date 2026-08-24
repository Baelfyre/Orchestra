from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "machine" / "schemas" / "ui-profile-registry.schema.json"
REGISTRY_PATH = ROOT / "machine" / "ui" / "ui-profile-registry.v1.json"
VALID_COMPOSITION = ROOT / "tests" / "fixtures" / "ui" / "uix3-valid-profile-composition.json"
INVALID_COMPOSITION = ROOT / "tests" / "fixtures" / "ui" / "uix3-invalid-full-system-mix.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _composition_errors(selection: dict, registry: dict) -> list[str]:
    rules = registry["composition_rules"]
    profiles = {profile["profile_id"]: profile for profile in registry["profiles"]}
    errors: list[str] = []

    for category in rules["required_categories"]:
        if len(selection.get(category, [])) != 1:
            errors.append(f"{category} must have exactly one selection")

    for category in rules["required_categories"] + rules["optional_categories"]:
        selected = selection.get(category, [])
        if not isinstance(selected, list):
            errors.append(f"{category} selection must be a list")
            continue
        maximum = rules["maximum_selections_by_category"][category]
        if len(selected) > maximum:
            errors.append(f"{category} exceeds its maximum selection count")
        for profile_id in selected:
            profile = profiles.get(profile_id)
            if profile is None:
                errors.append(f"unknown profile: {profile_id}")
            elif profile["category"] != category:
                errors.append(f"{profile_id} is not a {category} profile")

    selected_ids = [profile_id for values in selection.values() for profile_id in values]
    if len(selected_ids) != len(set(selected_ids)):
        errors.append("a profile cannot be selected more than once")

    for rule in rules["incompatibility_rules"]:
        selected_count = len(set(selected_ids).intersection(rule["profile_ids"]))
        if rule["kind"] == "CATEGORY_MUTUALLY_EXCLUSIVE" and selected_count > 1:
            errors.append(rule["rule_id"])
        if rule["kind"] == "CATEGORY_MAXIMUM" and selected_count > 1:
            errors.append(rule["rule_id"])

    return errors


def test_uix3_schema_and_registry_are_valid() -> None:
    registry = _load(REGISTRY_PATH)
    _validator().validate(registry)

    assert registry["schema_version"] == "orchestra.ui-profile-registry.v1"
    assert len(registry["profiles"]) == 10
    assert {profile["profile_id"] for profile in registry["profiles"]} == {
        "minimalist",
        "bento_grid",
        "dark_cyberpunk",
        "neo_brutalism",
        "material_3",
        "retro_web_90s",
        "glassmorphism",
        "neumorphism",
        "claymorphism",
        "aurora",
    }


def test_uix3_taxonomy_separates_foundation_layout_system_and_effect() -> None:
    registry = _load(REGISTRY_PATH)
    profiles = {profile["profile_id"]: profile for profile in registry["profiles"]}

    assert profiles["minimalist"]["category"] == "foundation"
    assert profiles["bento_grid"]["category"] == "layout"
    assert profiles["material_3"]["category"] == "full_theme_or_system"
    assert profiles["glassmorphism"]["category"] == "optional_effect"
    assert registry["composition_rules"]["layout_classification"] == "BENTO_GRID_IS_LAYOUT_NOT_THEME"
    assert registry["composition_rules"]["full_system_mix_policy"] == "MUTUALLY_EXCLUSIVE"


def test_uix3_valid_and_invalid_compositions_are_deterministic() -> None:
    registry = _load(REGISTRY_PATH)
    valid = _load(VALID_COMPOSITION)
    invalid = _load(INVALID_COMPOSITION)

    assert _composition_errors(valid["selection"], registry) == []
    assert "full-system-mutual-exclusion" in _composition_errors(invalid["selection"], registry)


def test_uix3_accessibility_invariants_are_theme_neutral() -> None:
    registry = _load(REGISTRY_PATH)
    invariant_ids = {item["invariant_id"] for item in registry["accessibility_invariants"]}
    assert {"REDUCED_MOTION", "FORCED_COLORS", "INTERACTION_CRITICAL_CONTRAST"} <= invariant_ids

    for profile in registry["profiles"]:
        behavior = profile["accessibility_behavior"]
        assert behavior["reduced_motion"] == "INHERIT_GLOBAL_INVARIANT"
        assert behavior["forced_colors"] == "INHERIT_GLOBAL_INVARIANT"
    for profile_id in registry["taxonomy"]["optional_effect"]:
        assert profiles_by_id(registry)[profile_id]["accessibility_behavior"]["contrast"] == (
            "RESTRICT_INTERACTION_CRITICAL_SURFACES"
        )


def profiles_by_id(registry: dict) -> dict:
    return {profile["profile_id"]: profile for profile in registry["profiles"]}


def test_uix3_profile_names_do_not_grant_css_or_implementation_authority() -> None:
    registry = _load(REGISTRY_PATH)
    assert registry["composition_rules"]["profile_name_authority"] == (
        "PROFILE_IDENTIFIERS_DO_NOT_AUTHORIZE_ARBITRARY_CSS_VALUES"
    )
    assert registry["composition_rules"]["project_precedence"] == (
        "EXISTING_PROJECT_DESIGN_SYSTEM_OVERRIDES_PROFILE_DEFAULTS"
    )
    assert all(value is False for value in registry["authority"].values())

    invalid = json.loads(json.dumps(registry))
    invalid["profiles"][0]["css_values"] = {"color": "#fff"}
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(invalid)
