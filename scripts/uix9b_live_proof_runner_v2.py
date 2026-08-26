"""UIX-9B V2 identity gate and dormant UIX-9C execution adapter.

The frozen experiment base and the canonical preparation ref are separate
identities. The adapter is deliberately dormant unless both an explicit
live-call gate and an approved machine authorization record are present.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

import jsonschema

try:
    from . import uix9_live_metric_evaluator_v2 as evaluator
    from . import uix9b_live_proof_adjudicator_v2 as adjudicator
except ImportError:
    import uix9_live_metric_evaluator_v2 as evaluator
    import uix9b_live_proof_adjudicator_v2 as adjudicator


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "machine" / "ui" / "uix9b-live-proof-plan.v2.json"
PLAN_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-proof-plan.v2.schema.json"
IDENTITY_PATH = ROOT / "machine" / "ui" / "uix9b-live-proof-v2-identity.json"
IDENTITY_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-proof-v2-identity.schema.json"
PREPARATION_IDENTITY_PATH = ROOT / "machine" / "ui" / "uix9b-live-preparation-identity.v2.json"
PREPARATION_IDENTITY_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-preparation-identity.v2.schema.json"
AUTHORIZATION_PATH = ROOT / "machine" / "ui" / "uix9b-live-call-authorization-request.v2.json"
AUTHORIZATION_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-call-authorization.v2.schema.json"
CALIBRATION_MANIFEST = ROOT / "machine" / "ui" / "uix9b-live-calibration-manifest.v2.json"
CALIBRATION_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-calibration-manifest.v2.schema.json"
GUIDANCE_MANIFEST = ROOT / "machine" / "ui" / "uix9-live-guidance-manifest.v1.json"
GUIDANCE_SCHEMA = ROOT / "machine" / "schemas" / "uix-live-guidance-manifest.schema.json"
VALIDATOR_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-validator-result.v2.schema.json"
METRIC_RESULT_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-metric-result.v2.schema.json"
OBSERVATION_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-proof-observation.v2.schema.json"
PAIR_SCHEMA = ROOT / "machine" / "schemas" / "uix9b-live-pair-adjudication.v2.schema.json"
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "ui" / "uix9-live-project"
EVIDENCE_ROOT = ROOT / "docs" / "validation" / "uix9b-live-evidence-v2"

FROZEN_BASE_SHA = "bf6f14316fa8814eeac91440c4a7d70be0d04b9e"
REVIEWED_CANONICAL_SHA = "7e08a1d4aa09cbdf7632f5a86461fb3cd3e50fe9"
EXPECTED_MODEL = "gpt-5.6-luna"
EXPECTED_REASONING_EFFORT = "xhigh"
EXPECTED_CODEX_CLI_VERSION = "0.148.0"
EXECUTION_ORDER = ("A1", "B1", "B2", "A2", "A3", "B3")
MAX_VALID_EXPERIMENTAL_SESSIONS = 6
MAX_TOTAL_MODEL_CALLS = 6
MAX_PROVIDER_CALLS = 6
MAX_TOTAL_PROVIDER_INTERACTIONS = 7
MAX_RETRIES_FOR_INVALID_RUN = 1
PER_RUN_TIMEOUT_SECONDS = 900
TOTAL_CAMPAIGN_TIMEOUT_SECONDS = 7_200
MAX_TOKENS_PER_RUN = 20_000
EVIDENCE_STATE_VERSION = "orchestra.uix9b-live-evidence-state.v1"

FROZEN_IDENTITY_FIELDS = (
    "canonical_sha", "evaluator_version", "evaluator_source", "evaluator_digest",
    "fixture_digest", "task_digest", "validator_digest", "uix_guidance_revision",
    "uix_guidance_digest", "model_calls_authorized", "provider_calls_authorized",
    "external_repo_mutations_authorized",
)
UIX9_RESULT_LOGIC_MARKERS = (
    "benefit_established", "no_benefit_established", "mixed_or_inconclusive",
    "protocol_invalid", "model_behavior_claim", "primary_metrics",
    "result_classification", "campaign_outcome",
)


class ExecutionRefused(RuntimeError):
    """The live execution gate is not satisfied."""


class ProviderOutage(RuntimeError):
    """The provider emitted an explicit failure event."""


class ProtocolBreach(RuntimeError):
    """The adapter could not prove a valid bounded session."""


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def load_git_json(revision: str, relative_path: str) -> dict[str, Any]:
    value = json.loads(git_bytes("show", f"{revision}:{relative_path}").decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"CANONICAL_ARTIFACT_NOT_OBJECT:{relative_path}")
    return value


def validate(value: dict[str, Any], schema_path: Path) -> None:
    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(value)


def git_value(*arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_check(*arguments: str) -> bool:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False)
    return result.returncode == 0


def git_bytes(*arguments: str) -> bytes:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def canonical_bytes(value: bytes) -> bytes:
    return value.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_file_digest(revision: str, relative_path: str) -> str:
    return digest_bytes(canonical_bytes(git_bytes("show", f"{revision}:{relative_path}")))


def git_paths(revision: str, relative_root: str) -> list[str]:
    output = git_value("ls-tree", "-r", "--name-only", revision, "--", relative_root)
    return [line for line in output.splitlines() if line]


def canonical_fixture_digest(revision: str) -> str:
    prefix = "tests/fixtures/ui/uix9-live-project/"
    records: list[tuple[str, str]] = []
    for path in git_paths(revision, "tests/fixtures/ui/uix9-live-project"):
        relative = path.removeprefix(prefix)
        if relative == "fixture-manifest.json" or relative.startswith("project/dist/") or relative.startswith("project/node_modules/"):
            continue
        records.append((relative, git_file_digest(revision, path)))
    if not records:
        raise RuntimeError("CANONICAL_FIXTURE_MISSING")
    return evaluator.digest_records(records)


def canonical_guidance_digest(revision: str, manifest: dict[str, Any]) -> str:
    records: list[tuple[str, str]] = []
    for material in manifest["materials"]:
        path = material["path"]
        actual = git_file_digest(revision, path)
        if actual != material["canonical_blob_digest"]:
            raise RuntimeError(f"CANONICAL_GUIDANCE_DRIFT:{path}")
        records.append((path, f"{actual}\t{material['role']}\t{material['revision_identity']}"))
    return evaluator.digest_records(records)


def verify_canonical_preparation(plan: dict[str, Any], identity: dict[str, Any]) -> dict[str, Any]:
    preparation = load_json(PREPARATION_IDENTITY_PATH)
    validate(preparation, PREPARATION_IDENTITY_SCHEMA)
    if preparation["frozen_experiment_base_sha"] != identity["canonical_sha"] or identity["canonical_sha"] != FROZEN_BASE_SHA:
        raise RuntimeError("FROZEN_BASE_IDENTITY_MISMATCH")
    if preparation["reviewed_canonical_sha"] != REVIEWED_CANONICAL_SHA:
        raise RuntimeError("REVIEWED_CANONICAL_IDENTITY_MISMATCH")

    current_canonical = git_value("rev-parse", "origin/main")
    if current_canonical == FROZEN_BASE_SHA:
        raise RuntimeError("CANONICAL_PREPARATION_MISSING")
    if not git_check("merge-base", "--is-ancestor", FROZEN_BASE_SHA, current_canonical):
        raise RuntimeError("FROZEN_BASE_NOT_IN_CANONICAL_LINEAGE")
    if not git_check("merge-base", "--is-ancestor", preparation["reviewed_canonical_sha"], current_canonical):
        raise RuntimeError("CANONICAL_PREPARATION_LINEAGE_DRIFT")

    guidance = load_git_json(current_canonical, "machine/ui/uix9-live-guidance-manifest.v1.json")
    validate(guidance, GUIDANCE_SCHEMA)
    if guidance.get("canonical_sha") != FROZEN_BASE_SHA:
        raise RuntimeError("CANONICAL_GUIDANCE_BASE_DRIFT")
    required_paths = set(preparation["required_paths"])
    required_paths.update(material["path"] for material in guidance["materials"])
    for relative_path in sorted(required_paths):
        if not git_check("cat-file", "-e", f"{current_canonical}:{relative_path}"):
            raise RuntimeError(f"CANONICAL_PREPARATION_ARTIFACT_MISSING:{relative_path}")

    canonical_identity = load_git_json(current_canonical, "machine/ui/uix9b-live-proof-v2-identity.json")
    validate(canonical_identity, IDENTITY_SCHEMA)
    for field in FROZEN_IDENTITY_FIELDS:
        if canonical_identity[field] != identity[field]:
            raise RuntimeError(f"CANONICAL_FROZEN_IDENTITY_DRIFT:{field}")

    canonical_plan = load_git_json(current_canonical, "machine/ui/uix9b-live-proof-plan.v2.json")
    validate(canonical_plan, PLAN_SCHEMA)
    if canonical_plan != plan:
        raise RuntimeError("CANONICAL_PROOF_PLAN_DRIFT")
    if canonical_guidance_digest(current_canonical, guidance) != identity["uix_guidance_digest"]:
        raise RuntimeError("CANONICAL_GUIDANCE_MANIFEST_DRIFT")
    if git_file_digest(current_canonical, identity["evaluator_source"]) != identity["evaluator_digest"]:
        raise RuntimeError("CANONICAL_EVALUATOR_DRIFT")
    if git_file_digest(current_canonical, "scripts/uix9_live_proof_runner.py") != identity["validator_digest"]:
        raise RuntimeError("CANONICAL_VALIDATOR_DRIFT")
    if canonical_fixture_digest(current_canonical) != identity["fixture_digest"]:
        raise RuntimeError("CANONICAL_FIXTURE_DRIFT")
    if git_file_digest(current_canonical, "tests/fixtures/ui/uix9-live-project/task.md") != identity["task_digest"]:
        raise RuntimeError("CANONICAL_TASK_DRIFT")
    return {
        "frozen_experiment_base_sha": identity["canonical_sha"],
        "current_canonical_preparation_sha": current_canonical,
        "reviewed_canonical_sha": preparation["reviewed_canonical_sha"],
        "canonical_lineage_verified": True,
        "preparation_content_verified": True,
        "required_preparation_paths": len(required_paths),
    }


def verify_frozen_identities() -> dict[str, Any]:
    plan = load_json(PLAN_PATH)
    validate(plan, PLAN_SCHEMA)
    identity = load_json(IDENTITY_PATH)
    validate(identity, IDENTITY_SCHEMA)
    evaluator.verify_identity(IDENTITY_PATH, evaluator.DEFAULT_FIXTURE_ROOT)
    calibration = load_json(CALIBRATION_MANIFEST)
    validate(calibration, CALIBRATION_SCHEMA)
    authorization = load_json(AUTHORIZATION_PATH)
    validate(authorization, AUTHORIZATION_SCHEMA)
    counters = authorization["new_campaign_authorization_counters"]
    if any(value != 0 for value in counters.values()):
        raise RuntimeError("UIX9C_CAMPAIGN_COUNTERS_NONZERO")
    preparation = verify_canonical_preparation(plan, identity)
    expected_cases = {item["case_id"] for item in calibration["cases"]}
    if expected_cases != {"EXPECTED_POSITIVE", "EXPECTED_NEGATIVE", "BOUNDARY_STRUCTURAL_LITERAL", "MALFORMED_CANDIDATE", "MISSING_REQUIRED_ARTIFACT"}:
        raise RuntimeError("CALIBRATION_CASE_SET_MISMATCH")
    if plan["fixture_digest"] != identity["fixture_digest"] or plan["task_digest"] != identity["task_digest"] or plan["validator_digest"] != identity["validator_digest"] or plan["uix_guidance_digest"] != identity["uix_guidance_digest"]:
        raise RuntimeError("PLAN_IDENTITY_MISMATCH")
    if plan["evaluator_digest"] != identity["evaluator_digest"] or calibration["evaluator_digest"] != identity["evaluator_digest"]:
        raise RuntimeError("EVALUATOR_IDENTITY_MISMATCH")
    return {
        "canonical_sha": identity["canonical_sha"],
        **preparation,
        "fixture_digest": plan["fixture_digest"],
        "task_digest": plan["task_digest"],
        "validator_digest": plan["validator_digest"],
        "uix_guidance_digest": plan["uix_guidance_digest"],
        "evaluator_digest": plan["evaluator_digest"],
        "calibration_cases": sorted(expected_cases),
        "authorization_status": authorization["authorization_status"],
        "experimental_model_calls": counters["experimental_model_calls"],
        "experimental_provider_calls": counters["experimental_provider_calls"],
        "live_calls_executed": 0,
        "provider_calls_executed": 0,
        "external_repo_mutations": 0,
    }


def arm_for_run(run_id: str) -> dict[str, Any]:
    if run_id not in EXECUTION_ORDER:
        raise ProtocolBreach(f"unexpected run id: {run_id}")
    is_baseline = run_id.startswith("A")
    return {
        "run_id": run_id,
        "arm_id": "BASELINE_NO_ORCHESTRA_UIX_GUIDANCE" if is_baseline else "GOVERNED_CANONICAL_UIX_1_8_GUIDANCE",
        "guidance_digest_or_NONE": "NONE" if is_baseline else load_json(GUIDANCE_MANIFEST)["guidance_digest"],
        "pair_id": f"PAIR_{run_id[1]}",
        "repetition": int(run_id[1]),
        "execution_order": EXECUTION_ORDER.index(run_id) + 1,
    }


def guidance_prompt_material() -> str:
    manifest = load_json(GUIDANCE_MANIFEST)
    materials: list[str] = []
    for material in manifest["materials"]:
        content = (ROOT / material["path"]).read_text(encoding="utf-8")
        lowered = content.lower()
        if any(marker in lowered for marker in UIX9_RESULT_LOGIC_MARKERS):
            raise ProtocolBreach(f"UIX9_RESULT_LOGIC_IN_GUIDANCE:{material['path']}")
        materials.append(f"## {material['role']}\n\n{content}")
    return "\n\n".join(materials)


def build_prompt(arm_id: str) -> tuple[str, str]:
    if arm_id not in {"BASELINE_NO_ORCHESTRA_UIX_GUIDANCE", "GOVERNED_CANONICAL_UIX_1_8_GUIDANCE"}:
        raise ProtocolBreach(f"unexpected arm: {arm_id}")
    task = (FIXTURE_ROOT / "task.md").read_text(encoding="utf-8")
    requirements = (FIXTURE_ROOT / "requirements.json").read_text(encoding="utf-8")
    prompt = f"Implement the supplied UI task in the current workspace.\n\nTask:\n{task}\n\nAcceptance requirements:\n{requirements}\n\nUse only the files and dependencies already supplied in the workspace. Preserve the supplied reference identities, accessibility requirements, responsive constraints, and external-mutation boundary. Do not access, commit, push, publish, deploy, or mutate any repository or system outside this isolated workspace. Return a concise implementation summary after completing the work."
    if arm_id == "BASELINE_NO_ORCHESTRA_UIX_GUIDANCE":
        guidance_digest = "NONE"
    else:
        prompt += "\n\nApply exactly the following canonical UIX-1 through UIX-8 treatment guidance. This treatment contains no experiment result logic or outcome information.\n\n" + guidance_prompt_material()
        guidance_digest = load_json(GUIDANCE_MANIFEST)["guidance_digest"]
    return prompt, digest_bytes(prompt.replace("\r\n", "\n").encode("utf-8"))


def build_codex_command(*, prompt: str, workspace_dir: Path, model: str = EXPECTED_MODEL, reasoning_effort: str = EXPECTED_REASONING_EFFORT) -> list[str]:
    if model != EXPECTED_MODEL or reasoning_effort != EXPECTED_REASONING_EFFORT:
        raise ProtocolBreach("provider/model/reasoning substitution is prohibited")
    return [
        "codex", "--ask-for-approval", "never", "exec", "--ephemeral", "--json", "--sandbox", "workspace-write",
        "--skip-git-repo-check", "--ignore-user-config", "--model",
        EXPECTED_MODEL, "--cd", str(workspace_dir.resolve()), "-c", 'approval_policy="never"',
        "-c", 'web_search="disabled"', "-c", f'model_reasoning_effort="{EXPECTED_REASONING_EFFORT}"', prompt,
    ]


def parse_codex_jsonl(raw_output: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(raw_output.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ProtocolBreach(f"malformed Codex JSONL line {line_number}") from exc
        if not isinstance(event, dict):
            raise ProtocolBreach(f"Codex JSONL line {line_number} is not an object")
        events.append(event)
    if not events or not any(event.get("type") == "thread.started" for event in events):
        raise ProtocolBreach("Codex JSONL is missing thread.started")
    if any(event.get("type") in {"turn.failed", "error"} for event in events):
        raise ProviderOutage("Codex reported an explicit provider failure")
    completed = [event for event in events if event.get("type") == "turn.completed"]
    if len(completed) != 1:
        raise ProtocolBreach(f"Codex JSONL requires one turn.completed, got {len(completed)}")
    usage = completed[0].get("usage")
    token_counts: dict[str, int] | None = None
    fields = ("input_tokens", "output_tokens", "total_tokens")
    if isinstance(usage, dict) and all(isinstance(usage.get(field), int) and usage[field] >= 0 for field in fields):
        token_counts = {field: usage[field] for field in fields}
        if token_counts["total_tokens"] > MAX_TOKENS_PER_RUN:
            raise ProtocolBreach("per-run token ceiling exceeded")
    messages = []
    for event in events:
        if event.get("type") != "item.completed" or not isinstance(event.get("item"), dict):
            continue
        item = event["item"]
        if item.get("type") == "agent_message" and isinstance(item.get("text"), str) and item["text"].strip():
            messages.append(item["text"])
    if not messages:
        raise ProtocolBreach("Codex JSONL is missing a completed agent message")
    observed_models = {str(event[field]) for event in events for field in ("model", "model_name") if isinstance(event.get(field), str)}
    if observed_models and observed_models != {EXPECTED_MODEL}:
        raise ProtocolBreach("provider/model substitution detected in Codex output")
    return {"events": events, "response": messages[-1], "token_counts": token_counts}


def verify_codex_cli_version() -> str:
    try:
        completed = subprocess.run(["codex", "--version"], capture_output=True, text=True, shell=False, check=False)
    except OSError as exc:
        raise ProtocolBreach(f"Codex CLI unavailable: {exc}") from exc
    if completed.returncode != 0:
        raise ProtocolBreach("Codex CLI version check failed")
    versions = set(re.findall(r"\d+\.\d+\.\d+", f"{completed.stdout}\n{completed.stderr}"))
    if versions != {EXPECTED_CODEX_CLI_VERSION}:
        raise ProtocolBreach("Codex CLI version substitution detected")
    return EXPECTED_CODEX_CLI_VERSION


def snapshot_workspace(root: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ProtocolBreach(f"symlink in isolated workspace: {path}")
        if path.is_file():
            records[path.relative_to(root).as_posix()] = digest_bytes(canonical_bytes(path.read_bytes()))
    return records


def _check(status: str, details: str) -> dict[str, Any]:
    return {"status": status, "deterministic": True, "details": details}


def _run_project_command(project_root: Path, arguments: list[str]) -> dict[str, Any]:
    command = list(arguments)
    if os.name == "nt" and command[0] == "npm":
        command[0] = "npm.cmd"
    environment = os.environ.copy()
    environment.update({
        "npm_config_offline": "true",
        "npm_config_audit": "false",
        "npm_config_fund": "false",
        "npm_config_update_notifier": "false",
    })
    try:
        completed = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
            timeout=PER_RUN_TIMEOUT_SECONDS,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        return {"status": "FAIL", "details": f"timeout: {' '.join(arguments)}"}
    except OSError as exc:
        return {"status": "FAIL", "details": f"{arguments[0]} unavailable: {exc}"}
    details = f"exit={completed.returncode}: {' '.join(arguments)}"
    return {"status": "PASS" if completed.returncode == 0 else "FAIL", "details": details}


def _tree_object(root: Path) -> dict[str, Any]:
    records = evaluator.tree_records(root)
    return {"digest": evaluator.digest_records(records), "files": [path for path, _ in records]}


def _changed_files(starting: dict[str, str], ending: dict[str, str]) -> list[str]:
    return sorted(path for path in set(starting) | set(ending) if starting.get(path) != ending.get(path))


def _tree_diff_digest(starting: dict[str, str], ending: dict[str, str]) -> str:
    payload = {"starting_tree": starting, "final_tree": ending}
    return digest_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def run_independent_validator(fixture_root: Path, candidate_root: Path, run_root: Path) -> dict[str, Any]:
    """Run candidate-only deterministic checks and write its independent record."""
    identity = load_json(IDENTITY_PATH)
    candidate_digest = evaluator.tree_digest(candidate_root)
    fixture_digest = evaluator.tree_digest(fixture_root)
    project_root = candidate_root / "project"
    if not project_root.is_dir():
        raise ProtocolBreach("VALIDATOR_FAILURE:MISSING_PROJECT_ROOT")

    commands = {
        "fresh_setup": ["npm", "install", "--ignore-scripts", "--package-lock=false", "--offline"],
        "typecheck": ["npm", "run", "typecheck"],
        "unit_component_tests": ["npm", "test"],
        "production_build": ["npm", "run", "build"],
    }
    checks = {name: _run_project_command(project_root, command) for name, command in commands.items()}
    shutil.rmtree(project_root / "dist", ignore_errors=True)

    try:
        requirements, component_map, tokens, _state_contract, _ = evaluator.load_fixture_contracts(fixture_root, candidate_root)
        accessibility = evaluator.load_json(candidate_root / "accessibility-contract.json")
        asset_manifest = evaluator.load_json(candidate_root / "asset-manifest.json")
        files = evaluator.source_files(candidate_root)
        asset_provenance, asset_substitution = evaluator.asset_metrics(fixture_root, candidate_root, asset_manifest, files)
        responsive = evaluator.responsive_containment(tokens, files)
        accessibility_ok = evaluator.accessibility_invariants(accessibility, files)
    except Exception as exc:
        raise ProtocolBreach(f"VALIDATOR_FAILURE:{type(exc).__name__}:{exc}") from exc

    required_contracts = (
        "project/package-lock.json",
        "asset-manifest.json",
        "component-map.json",
        "design-tokens.json",
    )
    contract_checks = {
        "dependency_manifest_equality": evaluator.digest_file(fixture_root / "project" / "package-lock.json") == evaluator.digest_file(candidate_root / "project" / "package-lock.json"),
        "asset_manifest_equality": evaluator.digest_file(fixture_root / "asset-manifest.json") == evaluator.digest_file(candidate_root / "asset-manifest.json"),
        "component_map_equality": evaluator.digest_file(fixture_root / "component-map.json") == evaluator.digest_file(candidate_root / "component-map.json"),
        "design_token_equality": evaluator.digest_file(fixture_root / "design-tokens.json") == evaluator.digest_file(candidate_root / "design-tokens.json"),
        "validator_digest_equality": evaluator.digest_file(ROOT / "scripts" / "uix9_live_proof_runner.py") == identity["validator_digest"],
    }
    with tempfile.TemporaryDirectory(prefix="uix9b-validator-reset-") as temporary:
        reset_root = Path(temporary) / "fixture"
        shutil.copytree(fixture_root, reset_root, ignore=shutil.ignore_patterns("dist", "node_modules"))
        reset_ok = evaluator.tree_digest(reset_root) == fixture_digest

    checks.update({
        name: {"status": value["status"], "details": value["details"]}
        for name, value in checks.items()
    })
    checks.update({
        "fixture_reset": {"status": "PASS" if reset_ok else "FAIL", "details": "fresh fixture reset digest comparison"},
        **{name: {"status": "PASS" if value else "FAIL", "details": f"{name} comparison"} for name, value in contract_checks.items()},
        "asset_reference_integrity": {"status": "PASS" if asset_provenance and not asset_substitution else "FAIL", "details": "frozen asset digest and reference comparison"},
        "responsive_validation": {"status": "PASS" if responsive else "FAIL", "details": "frozen breakpoint and containment predicates"},
        "accessibility_validation": {"status": "PASS" if accessibility_ok else "FAIL", "details": "frozen accessibility invariant predicates"},
    })

    first_checks = json.dumps(checks, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    second_checks = json.dumps(dict(checks), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checks["validator_determinism"] = {"status": "PASS" if first_checks == second_checks else "FAIL", "details": "repeat deterministic validator projection"}
    checks = {name: _check(value["status"], value["details"]) for name, value in checks.items()}
    result = {
        "$schema": "../../../machine/schemas/uix9b-validator-result.v2.schema.json",
        "schema_version": "orchestra.uix9b-validator-result.v2",
        "role": "UIX_9B_INDEPENDENT_VALIDATOR_RESULT",
        "candidate_tree_digest": candidate_digest,
        "fixture_digest": fixture_digest,
        "validator_digest": identity["validator_digest"],
        "dependency_manifest_digest": evaluator.digest_file(fixture_root / "project" / "package-lock.json"),
        "asset_manifest_digest": evaluator.digest_file(fixture_root / "asset-manifest.json"),
        "component_map_digest": evaluator.digest_file(fixture_root / "component-map.json"),
        "design_token_digest": evaluator.digest_file(fixture_root / "design-tokens.json"),
        "checks": checks,
        "model_calls": 0,
        "provider_calls": 0,
        "network_access": 0,
        "external_repo_mutations": 0,
    }
    validate(result, VALIDATOR_SCHEMA)
    _atomic_json(run_root / "validator-result.json", result)
    return result


def _build_observation(
    *,
    run: dict[str, Any],
    prompt_digest: str,
    starting: dict[str, str],
    ending: dict[str, str],
    validator_result: dict[str, Any],
    metric_result: dict[str, Any],
    raw_result: dict[str, Any],
    start_timestamp: str,
    end_timestamp: str,
) -> dict[str, Any]:
    parsed = raw_result.get("parsed", {})
    token_counts = parsed.get("token_counts") if isinstance(parsed, dict) else None
    if not isinstance(token_counts, dict):
        token_record = {"status": "UNAVAILABLE", "input": None, "output": None, "total": None}
    else:
        token_record = {"status": "TRUSTWORTHY", "input": token_counts.get("input_tokens"), "output": token_counts.get("output_tokens"), "total": token_counts.get("total_tokens")}
    starting_tree = _tree_object(FIXTURE_ROOT)
    final_records = sorted(ending.items())
    final_tree = {"digest": evaluator.digest_records(final_records), "files": [path for path, _ in final_records]}
    checks = validator_result["checks"]
    details = lambda name: checks[name]["details"]
    return {
        "$schema": "../../../machine/schemas/uix9b-live-proof-observation.v2.schema.json",
        "schema_version": "orchestra.uix9b-live-proof-observation.v2",
        "role": "UIX_9B_LIVE_PROOF_OBSERVATION",
        "run_id": run["run_id"],
        "arm_id": run["arm_id"],
        "pair_id": run["pair_id"],
        "repetition": run["repetition"],
        "execution_order": run["execution_order"],
        "provider": "openai-codex",
        "model": EXPECTED_MODEL,
        "model_revision": "UNRESOLVED_PENDING_LIVE_AUTHORIZATION",
        "reasoning_effort": EXPECTED_REASONING_EFFORT,
        "codex_cli_version": f"codex-cli {EXPECTED_CODEX_CLI_VERSION}",
        "host_os": platform.platform(),
        "starting_fixture_digest": evaluator.digest_records(sorted(starting.items())),
        "requirements_digest": evaluator.digest_file(FIXTURE_ROOT / "requirements.json"),
        "task_digest": evaluator.digest_file(FIXTURE_ROOT / "task.md"),
        "prompt_digest": prompt_digest,
        "guidance_digest_or_NONE": run["guidance_digest_or_NONE"],
        "validator_digest": validator_result["validator_digest"],
        "evaluator_version": metric_result["evaluator_version"],
        "evaluator_digest": metric_result["evaluator_digest"],
        "metric_result_digest": metric_result["metric_result_digest"],
        "starting_tree": starting_tree,
        "final_tree": final_tree,
        "changed_file_manifest": _changed_files(starting, ending),
        "git_diff_digest": _tree_diff_digest(starting, ending),
        "build_result": _check(checks["production_build"]["status"], details("production_build")),
        "test_result": _check(checks["unit_component_tests"]["status"], details("unit_component_tests")),
        "validator_result": _check("PASS" if all(value["status"] == "PASS" for value in checks.values()) else "FAIL", "independent validator result"),
        "primary_metrics": metric_result["metrics"],
        "secondary_metrics": {
            "IMPLEMENTATION_DIFF_SIZE": None,
            "NEW_COMPONENT_COUNT": None,
            "NEW_ARBITRARY_TOKEN_VALUE_COUNT": None,
            "VALIDATION_REMEDIATION_COUNT": None,
            "WALL_CLOCK_EXECUTION_TIME": None,
            "INPUT_TOKENS": token_record["input"],
            "OUTPUT_TOKENS": token_record["output"],
            "TOTAL_TOKENS": token_record["total"],
            "metric_status": {
                "WALL_CLOCK_EXECUTION_TIME": "UNAVAILABLE",
                "INPUT_TOKENS": "AVAILABLE" if token_record["status"] == "TRUSTWORTHY" else "UNAVAILABLE",
                "OUTPUT_TOKENS": "AVAILABLE" if token_record["status"] == "TRUSTWORTHY" else "UNAVAILABLE",
                "TOTAL_TOKENS": "AVAILABLE" if token_record["status"] == "TRUSTWORTHY" else "UNAVAILABLE",
            },
        },
        "failure_codes": [],
        "model_call_count": 1,
        "provider_call_count": 1,
        "token_counts_if_trustworthy": token_record,
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "run_classification": "VALID_UNFAVORABLE_OUTPUT",
        "outage_or_invalid_reason": None,
        "external_side_effects": {
            "model_calls": 1,
            "provider_calls": 1,
            "external_repo_mutations": 0,
            "orderly_mutations": 0,
            "padayon_mutations": 0,
            "registry_mutations": 0,
            "production_mutations": 0,
            "installed_integration_mutations": 0,
            "release_tag_mutations": 0,
            "deployments": 0,
            "secrets_or_customer_data_used": False,
        },
    }


def _verify_candidate_tree(candidate_root: Path, stage_root: Path) -> dict[str, str]:
    candidate = candidate_root.resolve()
    stage = stage_root.resolve()
    if candidate != stage and stage not in candidate.parents:
        raise ProtocolBreach("CANDIDATE_TREE_OUTSIDE_ISOLATED_STAGE")
    return {path: digest for path, digest in evaluator.tree_records(candidate_root)}


def _run_session_pipeline(
    *,
    run: dict[str, Any],
    prompt_digest: str,
    workspace: Path,
    stage_root: Path,
    raw_result: dict[str, Any],
    validator_runner: Callable[[Path, Path, Path], dict[str, Any]],
    evaluator_runner: Callable[[Path, Path, Path, Path], dict[str, Any]],
) -> dict[str, Any]:
    _atomic_json(stage_root / "raw-session-result.json", raw_result)
    if raw_result.get("classification") != "OUTPUT_CAPTURED_PENDING_VALIDATOR":
        raise ProtocolBreach(f"SESSION_NOT_VALID:{raw_result.get('classification', 'UNKNOWN')}")
    starting = {path: digest for path, digest in evaluator.tree_records(FIXTURE_ROOT)}
    ending = _verify_candidate_tree(workspace, stage_root)
    validator_result = validator_runner(FIXTURE_ROOT, workspace, stage_root)
    validate(validator_result, VALIDATOR_SCHEMA)
    metric_result = evaluator_runner(FIXTURE_ROOT, workspace, stage_root / "validator-result.json", IDENTITY_PATH)
    validate(metric_result, METRIC_RESULT_SCHEMA)
    if metric_result.get("status") != "PASS" or not isinstance(metric_result.get("metrics"), dict) or set(metric_result["metrics"]) != set(evaluator.PRIMARY_METRICS):
        raise ProtocolBreach(f"EVALUATOR_FAILURE:{','.join(metric_result.get('failure_codes', ['UNKNOWN']))}")
    ending = _verify_candidate_tree(workspace, stage_root)
    observation = _build_observation(
        run=run,
        prompt_digest=prompt_digest,
        starting=starting,
        ending=ending,
        validator_result=validator_result,
        metric_result=metric_result,
        raw_result=raw_result,
        start_timestamp=datetime.now(timezone.utc).isoformat(),
        end_timestamp=datetime.now(timezone.utc).isoformat(),
    )
    validate(observation, OBSERVATION_SCHEMA)
    persist_evaluated_artifacts(stage_root, run["run_id"], observation, metric_result)
    capture_supplemental_ui_evidence(stage_root)
    return observation


def run_codex_session(workspace: Path, prompt: str) -> dict[str, Any]:
    verify_codex_cli_version()
    command = build_codex_command(prompt=prompt, workspace_dir=workspace)
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=workspace, capture_output=True, text=True, shell=False, check=False, timeout=PER_RUN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        return {"classification": "RESOURCE_CEILING_EXCEEDED", "command": command, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "duration_seconds": time.monotonic() - started}
    except OSError as exc:
        return {"classification": "HOST_CRASH", "command": command, "error": str(exc), "duration_seconds": time.monotonic() - started}
    if completed.returncode != 0:
        try:
            parse_codex_jsonl(completed.stdout or "")
        except ProviderOutage:
            classification = "PROVIDER_OUTAGE"
        except ProtocolBreach:
            classification = "HOST_CRASH"
        else:
            classification = "HOST_CRASH"
        return {"classification": classification, "command": command, "stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode, "duration_seconds": time.monotonic() - started}
    parsed = parse_codex_jsonl(completed.stdout or "")
    return {"classification": "OUTPUT_CAPTURED_PENDING_VALIDATOR", "command": command, "stdout": completed.stdout, "stderr": completed.stderr, "parsed": parsed, "duration_seconds": time.monotonic() - started}


def _json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    _json_dump(temporary, value)
    temporary.replace(path)


def _ensure_evidence_root(path: Path) -> Path:
    resolved = path.resolve()
    allowed = EVIDENCE_ROOT.resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise ExecutionRefused("evidence must remain under the authorized UIX-9B V2 evidence surface")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


@contextmanager
def evidence_lock(root: Path) -> Iterator[None]:
    lock_path = root / ".campaign.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ExecutionRefused("another UIX-9C campaign is active") from exc
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def _state_path(root: Path) -> Path:
    return root / "campaign-state.json"


def _load_state(root: Path) -> dict[str, Any]:
    path = _state_path(root)
    if not path.exists():
        return {"schema_version": EVIDENCE_STATE_VERSION, "runs": {}, "counters": {"model_calls": 0, "provider_calls": 0, "provider_interactions": 0, "invalid_retries": 0}}
    state = load_json(path)
    if state.get("schema_version") != EVIDENCE_STATE_VERSION or not isinstance(state.get("runs"), dict) or not isinstance(state.get("counters"), dict):
        raise ExecutionRefused("malformed campaign accounting state")
    return state


def _authorize_live(auth: dict[str, Any], *, live_call_gate: bool) -> None:
    if not live_call_gate:
        raise ExecutionRefused("EXPLICIT_LIVE_CALL_GATE_REQUIRED")
    if auth["authorization_status"] != "APPROVED" or not auth["live_model_calls_authorized"] or not auth["provider_calls_authorized"] or not auth["uix9c_execution_authorized"]:
        raise ExecutionRefused("HUMAN_LIVE_AUTHORIZATION_REQUIRED")
    if auth["current_request_max_new_live_calls"] != MAX_TOTAL_MODEL_CALLS:
        raise ExecutionRefused("LIVE_AUTHORIZATION_CEILING_MISMATCH")


def capture_supplemental_ui_evidence(
    run_root: Path,
    *,
    screenshot_hook: Callable[[Path], Iterable[Path | str]] | None = None,
    dom_hook: Callable[[Path], Iterable[Path | str]] | None = None,
    accessibility_hook: Callable[[Path], Iterable[Path | str]] | None = None,
    console_hook: Callable[[Path], Iterable[Path | str]] | None = None,
) -> dict[str, Any]:
    evidence: dict[str, Any] = {"primary_scoring": False, "capture_order": ["screenshot", "dom", "accessibility", "console"], "artifacts": {}}
    for name, hook in (("screenshot", screenshot_hook), ("dom", dom_hook), ("accessibility", accessibility_hook), ("console", console_hook)):
        if hook is None:
            evidence["artifacts"][name] = {"status": "NOT_CONFIGURED", "paths": []}
            continue
        paths = []
        for raw_path in hook(run_root):
            path = Path(raw_path).resolve()
            if path != run_root.resolve() and run_root.resolve() not in path.parents:
                raise ProtocolBreach(f"supplemental evidence escaped run root: {path}")
            paths.append(path.relative_to(run_root.resolve()).as_posix())
        evidence["artifacts"][name] = {"status": "CAPTURED", "paths": sorted(set(paths))}
    _json_dump(run_root / "supplemental-ui-evidence.json", evidence)
    return evidence


def persist_evaluated_artifacts(evidence_root: Path, run_id: str, observation: dict[str, Any], metric_result: dict[str, Any]) -> None:
    root = _ensure_evidence_root(evidence_root)
    if run_id not in EXECUTION_ORDER:
        raise ProtocolBreach(f"unexpected run id: {run_id}")
    validate(observation, OBSERVATION_SCHEMA)
    validate(metric_result, METRIC_RESULT_SCHEMA)
    if observation["run_id"] != run_id or observation["metric_result_digest"] != metric_result["metric_result_digest"]:
        raise ProtocolBreach("observation/evaluator identity mismatch")
    observation_path = root / "observations" / f"{run_id}.json"
    metric_path = root / "metric-results" / f"{run_id}.json"
    if observation_path.exists() or metric_path.exists():
        raise ExecutionRefused(f"EVIDENCE_ALREADY_RECORDED:{run_id}")
    _atomic_json(observation_path, observation)
    _atomic_json(metric_path, metric_result)


def _required_stage_files(stage_root: Path, run_id: str, pair_id: str) -> list[Path]:
    return [
        stage_root / "raw-session-result.json",
        stage_root / "validator-result.json",
        stage_root / "observations" / f"{run_id}.json",
        stage_root / "metric-results" / f"{run_id}.json",
        stage_root / "supplemental-ui-evidence.json",
        stage_root.parent / "pair-adjudication.json",
    ]


def _verify_stage_files(stage_root: Path, run_id: str, pair_id: str) -> None:
    missing = [path.as_posix() for path in _required_stage_files(stage_root, run_id, pair_id) if not path.is_file()]
    if missing:
        raise ProtocolBreach(f"MISSING_FINAL_ARTIFACT:{','.join(missing)}")


def _record_run_failure(root: Path, run_id: str, reason: str) -> None:
    stage_root = root / ".staging" / "pairs" / f"PAIR_{run_id[1]}" / run_id
    stage_root.mkdir(parents=True, exist_ok=True)
    _atomic_json(stage_root / "failure.json", {"run_id": run_id, "classification": "PROTOCOL_BREACH", "reason": reason})


def execute_campaign(
    *,
    evidence_root: Path = EVIDENCE_ROOT,
    live_call_gate: bool = False,
    session_runner: Callable[[Path, str], dict[str, Any]] = run_codex_session,
    validator_runner: Callable[[Path, Path, Path], dict[str, Any]] = run_independent_validator,
    evaluator_runner: Callable[[Path, Path, Path, Path], dict[str, Any]] = evaluator.evaluate,
    adjudicator_runner: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] = adjudicator.pair_adjudication,
) -> dict[str, Any]:
    report = verify_frozen_identities()
    auth = load_json(AUTHORIZATION_PATH)
    validate(auth, AUTHORIZATION_SCHEMA)
    _authorize_live(auth, live_call_gate=live_call_gate)
    root = _ensure_evidence_root(evidence_root)
    started = time.monotonic()
    with evidence_lock(root):
        state = _load_state(root)
        if state["runs"]:
            raise ExecutionRefused("RECOVERY_REQUIRES_AUDIT_NO_DOUBLE_COUNT")
        pending: dict[str, dict[str, Any]] = {}
        for run_id in EXECUTION_ORDER:
            if time.monotonic() - started > TOTAL_CAMPAIGN_TIMEOUT_SECONDS:
                raise ExecutionRefused("TOTAL_CAMPAIGN_TIMEOUT_EXCEEDED")
            arm = arm_for_run(run_id)
            prompt, prompt_digest = build_prompt(arm["arm_id"])
            pair_id = arm["pair_id"]
            pair_stage = root / ".staging" / "pairs" / pair_id
            stage_root = pair_stage / run_id
            stage_root.mkdir(parents=True)
            workspace = stage_root / "fixture"
            shutil.copytree(FIXTURE_ROOT, workspace, ignore=shutil.ignore_patterns("dist", "node_modules"))
            state["runs"][run_id] = {
                "status": "STARTED",
                "valid_session": False,
                "arm_id": arm["arm_id"],
                "pair_id": pair_id,
                "repetition": arm["repetition"],
                "execution_order": arm["execution_order"],
                "prompt_digest": prompt_digest,
                "attempts": 0,
                "model_calls": 0,
                "provider_calls": 0,
            }
            _atomic_json(_state_path(root), state)
            attempts = 0
            while True:
                attempts += 1
                if attempts > 1:
                    shutil.rmtree(workspace)
                    shutil.copytree(FIXTURE_ROOT, workspace, ignore=shutil.ignore_patterns("dist", "node_modules"))
                state["runs"][run_id]["attempts"] = attempts
                if any(state["counters"][key] + 1 > limit for key, limit in (
                    ("model_calls", MAX_TOTAL_MODEL_CALLS),
                    ("provider_calls", MAX_PROVIDER_CALLS),
                    ("provider_interactions", MAX_TOTAL_PROVIDER_INTERACTIONS),
                )):
                    _record_run_failure(root, run_id, "IMMUTABLE_PROVIDER_CEILING_REACHED")
                    raise ExecutionRefused("IMMUTABLE_PROVIDER_CEILING_REACHED")
                state["runs"][run_id]["model_calls"] += 1
                state["runs"][run_id]["provider_calls"] += 1
                state["counters"]["model_calls"] += 1
                state["counters"]["provider_calls"] += 1
                state["counters"]["provider_interactions"] += 1
                _atomic_json(_state_path(root), state)
                try:
                    result = session_runner(workspace, prompt)
                except OSError as exc:
                    result = {"classification": "HOST_CRASH", "error": str(exc)}
                except Exception as exc:
                    result = {"classification": "PROTOCOL_BREACH", "error": str(exc)}
                if not isinstance(result, dict):
                    result = {"classification": "PROTOCOL_BREACH", "error": "session runner returned malformed evidence"}
                _atomic_json(stage_root / f"codex-attempt-{attempts}.json", result)
                classification = result.get("classification")
                if classification in {"HOST_CRASH", "PROVIDER_OUTAGE"} and attempts <= MAX_RETRIES_FOR_INVALID_RUN and state["counters"]["model_calls"] < MAX_TOTAL_MODEL_CALLS:
                    state["counters"]["invalid_retries"] += 1
                    state["runs"][run_id]["status"] = classification
                    _atomic_json(_state_path(root), state)
                    continue
                if classification != "OUTPUT_CAPTURED_PENDING_VALIDATOR":
                    state["runs"][run_id]["status"] = classification or "PROTOCOL_BREACH"
                    _atomic_json(stage_root / "failure.json", {"run_id": run_id, "classification": state["runs"][run_id]["status"], "reason": result.get("error") or "session did not produce a candidate"})
                    _atomic_json(_state_path(root), state)
                    raise ProtocolBreach(f"SESSION_NOT_VALID:{state['runs'][run_id]['status']}")
                try:
                    observation = _run_session_pipeline(
                        run=arm,
                        prompt_digest=prompt_digest,
                        workspace=workspace,
                        stage_root=stage_root,
                        raw_result=result,
                        validator_runner=validator_runner,
                        evaluator_runner=evaluator_runner,
                    )
                except Exception as exc:
                    state["runs"][run_id]["status"] = "PROTOCOL_BREACH"
                    state["runs"][run_id]["valid_session"] = False
                    _atomic_json(stage_root / "failure.json", {"run_id": run_id, "classification": "PROTOCOL_BREACH", "reason": str(exc)})
                    _atomic_json(_state_path(root), state)
                    raise ProtocolBreach(f"EVIDENCE_PIPELINE_FAILURE:{type(exc).__name__}:{exc}") from exc
                pending[run_id] = observation
                state["runs"][run_id]["status"] = "OBSERVATION_PERSISTED_PENDING_ADJUDICATION"
                state["runs"][run_id]["starting_tree"] = _tree_object(FIXTURE_ROOT)
                state["runs"][run_id]["ending_tree"] = _tree_object(workspace)
                state["runs"][run_id]["valid_session"] = False
                _atomic_json(_state_path(root), state)
                break

            pair_run_ids = [candidate for candidate in EXECUTION_ORDER if candidate[1] == run_id[1]]
            if not all(candidate in pending for candidate in pair_run_ids):
                continue
            first, second = pair_run_ids
            try:
                pair_result = adjudicator_runner(pending[first], pending[second])
                validate(pair_result, PAIR_SCHEMA)
                _atomic_json(pair_stage / "pair-adjudication.json", pair_result)
                _verify_stage_files(pair_stage / first, first, pair_id)
                _verify_stage_files(pair_stage / second, second, pair_id)
                final_pair = root / "pairs" / pair_id
                if final_pair.exists():
                    raise ExecutionRefused(f"EVIDENCE_ALREADY_RECORDED:{pair_id}")
                final_pair.parent.mkdir(parents=True, exist_ok=True)
                os.replace(pair_stage, final_pair)
            except Exception as exc:
                for candidate in pair_run_ids:
                    state["runs"][candidate]["status"] = "PROTOCOL_BREACH"
                    state["runs"][candidate]["valid_session"] = False
                _atomic_json(pair_stage / "adjudication-failure.json", {"pair_id": pair_id, "classification": "PROTOCOL_BREACH", "reason": str(exc)})
                _atomic_json(_state_path(root), state)
                raise ProtocolBreach(f"ADJUDICATION_PIPELINE_FAILURE:{type(exc).__name__}:{exc}") from exc
            for candidate in pair_run_ids:
                state["runs"][candidate]["status"] = "VALID_UNFAVORABLE_OUTPUT"
                state["runs"][candidate]["valid_session"] = True
            _atomic_json(_state_path(root), state)
            pending.pop(first)
            pending.pop(second)
        report["campaign_state"] = "SIX_SESSIONS_CAPTURED_PENDING_CAMPAIGN_RESULT"
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["verify-frozen-identities", "execute"])
    parser.add_argument("--execution-mode", choices=["dry-run", "live"], default="dry-run")
    parser.add_argument("--live-call-gate", action="store_true")
    parser.add_argument("--evidence-root", type=Path, default=EVIDENCE_ROOT)
    args = parser.parse_args()
    try:
        report = verify_frozen_identities()
        if args.command == "execute":
            if args.execution_mode != "live" or not args.live_call_gate:
                print("UIX_9C_EXECUTION_REFUSED_EXPLICIT_LIVE_GATE_REQUIRED")
                print(json.dumps(report, indent=2, sort_keys=True))
                return 2
            report = execute_campaign(evidence_root=args.evidence_root, live_call_gate=True)
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0
        print(json.dumps(report, indent=2, sort_keys=True))
        print("V2_FROZEN_IDENTITIES=PASS")
        return 0
    except (ExecutionRefused, ProtocolBreach, ProviderOutage, RuntimeError, OSError, json.JSONDecodeError, jsonschema.exceptions.ValidationError) as exc:
        print(f"V2_FROZEN_IDENTITIES=FAIL_CLOSED:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
