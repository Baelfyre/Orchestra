"""Deterministic UIX-9B preparation, fixture, and zero-call validation.

This module intentionally has no provider or model execution path. It validates
the frozen inputs and canary observations needed before a separately authorized
UIX-9C live campaign.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "ui" / "uix9-live-project"
PROJECT_ROOT = FIXTURE_ROOT / "project"
PLAN_PATH = ROOT / "machine" / "ui" / "uix9-live-proof-plan.v1.json"
GUIDANCE_MANIFEST_PATH = ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
OBSERVATION_SCHEMA_PATH = ROOT / "machine" / "schemas" / "uix-live-proof-observation.schema.json"
RESULT_SCHEMA_PATH = ROOT / "machine" / "schemas" / "uix-live-proof-result.schema.json"
RUNNER_PATH = Path(__file__).resolve()

PRIMARY_METRIC_NAMES = (
    "COMPONENT_REUSE",
    "DUPLICATE_COMPONENT_COUNT",
    "TOKEN_VIOLATIONS",
    "ARBITRARY_STYLE_DRIFT",
    "STATE_COVERAGE",
    "ASSET_PROVENANCE",
    "ASSET_SUBSTITUTION",
    "RESPONSIVE_CONTAINMENT",
    "ACCESSIBILITY_INVARIANTS",
    "UNRESOLVED_MAPPINGS",
    "REVISION_MISMATCH",
    "VISUAL_BASELINE_REPLACEMENT",
    "DETERMINISTIC_ACCEPTANCE",
)

ARM_IDS = (
    "BASELINE_NO_ORCHESTRA_UIX_GUIDANCE",
    "GOVERNED_CANONICAL_UIX_1_8_GUIDANCE",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(canonical_text(path).encode("utf-8"))


def digest_records(records: Iterable[tuple[str, str]]) -> str:
    payload = "\n".join(f"{path}\t{digest}" for path, digest in sorted(records))
    return digest_bytes(payload.encode("utf-8"))


def tree_records(root: Path, *, exclude_manifest: bool = False) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if exclude_manifest and relative == "fixture-manifest.json":
            continue
        if relative.startswith("project/dist/") or relative.startswith("project/node_modules/"):
            continue
        records.append((relative, digest_file(path)))
    return records


def fixture_digest() -> str:
    return digest_records(tree_records(FIXTURE_ROOT, exclude_manifest=True))


def task_digest() -> str:
    return digest_file(FIXTURE_ROOT / "task.md")


def requirements_digest() -> str:
    return digest_file(FIXTURE_ROOT / "requirements.json")


def validator_digest() -> str:
    return digest_file(RUNNER_PATH)


def guidance_records() -> list[dict[str, str]]:
    manifest = load_json(GUIDANCE_MANIFEST_PATH)
    records: list[dict[str, str]] = []
    for material in manifest["materials"]:
        path = ROOT / material["path"]
        if not path.is_file():
            raise AssertionError(f"missing canonical guidance material: {material['path']}")
        actual = digest_file(path)
        records.append({**material, "canonical_blob_digest": actual})
    return records


def guidance_digest(records: list[dict[str, str]] | None = None) -> str:
    values = records if records is not None else guidance_records()
    return digest_records(
        (item["path"], f"{item['canonical_blob_digest']}\t{item['role']}\t{item['revision_identity']}")
        for item in values
    )


def prompt_digest(arm_id: str, guidance_digest_or_none: str) -> str:
    task = canonical_text(FIXTURE_ROOT / "task.md")
    requirements = canonical_text(FIXTURE_ROOT / "requirements.json")
    payload = "\n".join((task, requirements, arm_id, guidance_digest_or_none, "uix9b-prompt-v1"))
    return digest_bytes(payload.encode("utf-8"))


def validator(path: Path) -> jsonschema.Draft202012Validator:
    schema = load_json(path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def validate_json(path: Path, schema_path: Path) -> dict[str, Any]:
    value = load_json(path)
    validator(schema_path).validate(value)
    return value


def git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def run_project_command(arguments: list[str]) -> str:
    executable = arguments[0]
    if os.name == "nt" and executable == "npm":
        executable = "npm.cmd"
    result = subprocess.run([executable, *arguments[1:]], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    if result.returncode:
        raise AssertionError(f"project command failed: {' '.join(arguments)}\n{result.stdout}\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


def validate_guidance_manifest() -> dict[str, Any]:
    manifest = load_json(GUIDANCE_MANIFEST_PATH)
    assert manifest["canonical_sha"] == "bf6f14316fa8814eeac91440c4a7d70be0d04b9e"
    actual = guidance_records()
    assert [item["path"] for item in actual] == [item["path"] for item in manifest["materials"]]
    for expected, observed in zip(manifest["materials"], actual):
        assert observed["canonical_blob_digest"] == expected["canonical_blob_digest"], observed["path"]
    assert manifest["guidance_digest"] == guidance_digest(actual)
    excluded = "\n".join(manifest["excluded_from_treatment"])
    assert "UIX_9" in excluded and "uix9" in excluded
    return manifest


def validate_fixture() -> dict[str, Any]:
    fixture_manifest = load_json(FIXTURE_ROOT / "fixture-manifest.json")
    actual_fixture_digest = fixture_digest()
    assert fixture_manifest["fixture_digest"] == actual_fixture_digest
    assert fixture_manifest["starting_tree_digest"] == actual_fixture_digest

    requirements = load_json(FIXTURE_ROOT / "requirements.json")
    validation_contract = load_json(FIXTURE_ROOT / "validation-contract.json")
    assert requirements["reference_identity"] == fixture_manifest["reference_identity"]
    assert validation_contract["reference_identity"] == fixture_manifest["reference_identity"]

    component_map = load_json(FIXTURE_ROOT / "component-map.json")
    for component in component_map["components"]:
        assert (FIXTURE_ROOT / component["path"]).is_file(), component["path"]
        assert component["disposition"] == "EXACT"

    tokens = load_json(FIXTURE_ROOT / "design-tokens.json")
    assert tokens["reference_identity"] == fixture_manifest["reference_identity"]
    asset_manifest = load_json(FIXTURE_ROOT / "asset-manifest.json")
    for asset in asset_manifest["approved_assets"]:
        asset_path = FIXTURE_ROOT / asset["path"]
        assert asset_path.is_file(), asset["path"]
        assert asset.get("content_digest") == digest_file(asset_path), asset["path"]
    state_contract = load_json(FIXTURE_ROOT / "state-contract.json")
    assert {state["id"] for state in state_contract["states"]} == {"DEFAULT", "LOADING", "EMPTY", "ERROR", "POPULATED"}
    accessibility = load_json(FIXTURE_ROOT / "accessibility-contract.json")
    assert len(accessibility["invariants"]) >= 10
    package = load_json(PROJECT_ROOT / "package.json")
    lockfile = load_json(PROJECT_ROOT / "package-lock.json")
    assert package.get("dependencies", {}) == {}
    assert package.get("devDependencies", {}) == {}
    assert lockfile["packages"][""]["name"] == package["name"]

    outputs = {
        "fresh_setup": run_project_command(["npm", "install", "--ignore-scripts", "--package-lock=false", "--offline"]),
        "typecheck": run_project_command(["npm", "run", "typecheck"]),
        "tests": run_project_command(["npm", "test"]),
        "build": run_project_command(["npm", "run", "build"]),
    }
    assert (PROJECT_ROOT / "dist" / "index.html").is_file()
    shutil.rmtree(PROJECT_ROOT / "dist", ignore_errors=True)

    first = fixture_digest()
    with tempfile.TemporaryDirectory(prefix="uix9b-reset-") as temporary:
        copied = Path(temporary) / "uix9-live-project"
        shutil.copytree(FIXTURE_ROOT, copied, ignore=shutil.ignore_patterns("dist", "node_modules"))
        second = digest_records(tree_records(copied, exclude_manifest=True))
    assert first == second == actual_fixture_digest
    return {"fixture_digest": actual_fixture_digest, "commands": outputs, "reset_determinism": True}


def validate_zero_call_canaries() -> dict[str, Any]:
    plan = validate_json(PLAN_PATH, ROOT / "machine" / "schemas" / "uix-live-proof-plan.schema.json")
    validate_json(ROOT / "tests" / "fixtures" / "ui" / "uix9-live-positive.json", OBSERVATION_SCHEMA_PATH)
    validate_json(ROOT / "tests" / "fixtures" / "ui" / "uix9-live-negative.json", OBSERVATION_SCHEMA_PATH)
    positive = load_json(ROOT / "tests" / "fixtures" / "ui" / "uix9-live-positive.json")
    negative = load_json(ROOT / "tests" / "fixtures" / "ui" / "uix9-live-negative.json")
    expected_fixture = fixture_digest()
    expected_requirements = requirements_digest()
    expected_task = task_digest()
    expected_validator = validator_digest()
    expected_guidance = guidance_digest()
    validate_canary_bundle(positive, "ZERO_CALL_CANARY_PASS", "NONE", expected_fixture, expected_requirements, expected_task, expected_validator)
    validate_canary_bundle(negative, "ZERO_CALL_CANARY_FAIL_CLOSED", expected_guidance, expected_fixture, expected_requirements, expected_task, expected_validator)
    assert positive["run_id"] == "A1" and negative["run_id"] == "B1"
    assert positive["arm_id"] == ARM_IDS[0] and negative["arm_id"] == ARM_IDS[1]
    assert positive["starting_tree"] == negative["starting_tree"]
    assert positive["final_tree"] == negative["final_tree"]
    assert positive["prompt_digest"] == prompt_digest(ARM_IDS[0], "NONE")
    assert negative["prompt_digest"] == prompt_digest(ARM_IDS[1], expected_guidance)
    assert positive["guidance_digest_or_NONE"] != negative["guidance_digest_or_NONE"]
    assert plan["resource_ceiling_proposal"]["max_external_repo_mutations"] == 0
    assert plan["retry_policy"]["valid_unfavorable_output"] == "KEEP_RESULT_NO_RETRY_FOR_OUTCOME"
    assert plan["primary_endpoints"] == ["OBJECTIVE_UI_FIDELITY_METRICS"]
    result_schema = load_json(RESULT_SCHEMA_PATH)
    classifications = result_schema["properties"]["result_classification"]["enum"]
    assert classifications == ["BENEFIT_ESTABLISHED", "NO_BENEFIT_ESTABLISHED", "MIXED_OR_INCONCLUSIVE", "PROTOCOL_INVALID"]
    return {"S0_POSITIVE_VALIDATOR_CANARY": "PASS", "S1_NEGATIVE_VALIDATOR_CANARY": "PASS"}


def validate_canary_bundle(
    bundle: dict[str, Any],
    expected_classification: str,
    expected_guidance: str,
    expected_fixture: str | None = None,
    expected_requirements: str | None = None,
    expected_task: str | None = None,
    expected_validator: str | None = None,
) -> None:
    """Apply cross-field canary controls that JSON Schema cannot express."""
    expected_fixture = expected_fixture or fixture_digest()
    expected_requirements = expected_requirements or requirements_digest()
    expected_task = expected_task or task_digest()
    expected_validator = expected_validator or validator_digest()
    assert bundle["starting_fixture_digest"] == expected_fixture
    assert bundle["requirements_digest"] == expected_requirements
    assert bundle["task_digest"] == expected_task
    assert bundle["validator_digest"] == expected_validator
    assert bundle["guidance_digest_or_NONE"] == expected_guidance
    assert bundle["model_call_count"] == bundle["provider_call_count"] == 0
    assert bundle["run_classification"] == expected_classification
    assert bundle["external_side_effects"]["external_repo_mutations"] == 0
    assert bundle["external_side_effects"]["secrets_or_customer_data_used"] is False


def validate_plan() -> dict[str, Any]:
    plan = validate_json(PLAN_PATH, ROOT / "machine" / "schemas" / "uix-live-proof-plan.schema.json")
    assert git_head() == plan["canonical_sha"]
    assert plan["fixture_digest"] == fixture_digest()
    assert plan["task_digest"] == task_digest()
    assert plan["validator_digest"] == validator_digest()
    assert plan["uix_guidance_digest"] == guidance_digest()
    assert plan["repetitions_per_arm"] == 3
    assert plan["total_valid_executions"] == 6
    assert plan["execution_order"] == ["A1", "B1", "B2", "A2", "A3", "B3"]
    assert plan["authority"]["live_model_calls_authorized"] is False
    assert plan["authority"]["provider_calls_authorized"] is False
    return plan


def environment() -> dict[str, str]:
    codex = shutil.which("codex")
    cli_version = "UNRESOLVED_PENDING_LIVE_AUTHORIZATION"
    if codex:
        result = subprocess.run([codex, "--version"], capture_output=True, text=True, check=False)
        if result.returncode == 0 and result.stdout.strip():
            cli_version = result.stdout.strip()
    return {
        "PROVIDER": "openai-codex",
        "MODEL": "UNRESOLVED_PENDING_LIVE_AUTHORIZATION",
        "MODEL_REVISION": "UNRESOLVED_PENDING_LIVE_AUTHORIZATION",
        "CODEX_CLI_VERSION": cli_version,
        "HOST_OS": platform.platform(),
        "HOST_ARCHITECTURE": platform.machine(),
    }


def freeze_summary() -> dict[str, Any]:
    records = guidance_records()
    return {
        "CANONICAL_SHA": git_head(),
        "FIXTURE_DIGEST": fixture_digest(),
        "REQUIREMENTS_DIGEST": requirements_digest(),
        "TASK_DIGEST": task_digest(),
        "VALIDATOR_DIGEST": validator_digest(),
        "UIX_GUIDANCE_DIGEST": guidance_digest(records),
        "PROMPT_DIGEST_ARM_A": prompt_digest(ARM_IDS[0], "NONE"),
        "PROMPT_DIGEST_ARM_B": prompt_digest(ARM_IDS[1], guidance_digest(records)),
        "GUIDANCE_MATERIALS": records,
        "ENVIRONMENT": environment(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["freeze-summary", "validate-plan", "validate-guidance", "validate-fixture", "zero-call-canary", "full-preparation-validation"])
    args = parser.parse_args()
    if args.command == "freeze-summary":
        print(json.dumps(freeze_summary(), indent=2, sort_keys=True))
        return 0
    if args.command == "validate-guidance":
        validate_guidance_manifest()
        print("GUIDANCE_MANIFEST=PASS")
        return 0
    if args.command == "validate-plan":
        validate_plan()
        print("LIVE_PLAN=PASS")
        return 0
    if args.command == "validate-fixture":
        result = validate_fixture()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.command == "zero-call-canary":
        print(json.dumps(validate_zero_call_canaries(), indent=2, sort_keys=True))
        return 0
    validate_guidance_manifest()
    validate_plan()
    validate_fixture()
    print(json.dumps(validate_zero_call_canaries(), indent=2, sort_keys=True))
    print("LIVE_MODEL_CALLS_EXECUTED=0")
    print("PROVIDER_CALLS_EXECUTED=0")
    print("EXTERNAL_REPO_MUTATIONS=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
