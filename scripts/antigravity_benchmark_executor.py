#!/usr/bin/env python3
"""Antigravity measurement executor binding for Orchestra comparative benchmark.

Provides the B3.1.4 executor adapter for Antigravity CLI host-native execution,
deterministic communication-arm binding (DEFAULT, CAVEMAN, MURMURS), fail-closed
preflight validation with sparse settings semantic interpretation for useG1Credits,
externalized exact CLI version expectation, structured usage parsing, stream-json
event parsing, and Orchestra-compatible benchmark result construction.

Measurement Surface Provenance:
- Counter ID format: "antigravity-cli-{cli_version}:{transport}:{model}"
- Canonical default (json): "antigravity-cli-1.1.15:json-usage:gemini-3.7-flash-high"
- Canonical stream (stream-json): "antigravity-cli-1.1.15:stream-json-usage:gemini-3.7-flash-high"
- Provenance semantics:
  - Expected CLI version: source = EXECUTOR_ARGUMENT (--expected-cli-version)
  - Observed CLI version: source = PREFLIGHT_COMMAND (exact validated `agy --version`)
  - Model: source = PINNED_COMMAND_ARGUMENT (gemini-3.7-flash-high)
  - Usage counters: source = HOST_REPORTED_JSON_USAGE or HOST_REPORTED_STREAM_JSON_USAGE
  - Counter ID: provenance = ORCHESTRA_ASSIGNED_MEASUREMENT_SURFACE
- Note: This counter ID is Orchestra-assigned provenance identifying the exact
  host-native measurement surface; it is NOT claimed to be an Antigravity/provider-issued
  identifier. Paired B3 token deltas are valid only while this identity remains
  identical across DEFAULT, CAVEMAN, and MURMURS arms.

If any of these change:
- CLI version
- model identity
- usage-field semantics
- provider/host
- structured-output mechanism
the counter identity must change and the affected paired batch must not be
combined as one comparable counter population.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXECUTOR_RESULT_VERSION = "orchestra.comparative-benchmark-executor-result.v1"
EXECUTOR_REQUEST_VERSION = "orchestra.comparative-benchmark-executor-request.v1"
PROGRAM_ID = "orchestra.shared-comparative-benchmark.v1"

QUALIFIED_CLI_VERSION = "1.1.15"
PINNED_CLI_VERSION = QUALIFIED_CLI_VERSION
PINNED_MODEL = "gemini-3.7-flash-high"
PINNED_TRANSPORT_JSON = "json-usage"
PINNED_TRANSPORT_STREAM = "stream-json-usage"
PINNED_TRANSPORT = PINNED_TRANSPORT_JSON
DEFAULT_COUNTER_ID = f"antigravity-cli-{QUALIFIED_CLI_VERSION}:{PINNED_TRANSPORT_JSON}:{PINNED_MODEL}"
STREAM_JSON_COUNTER_ID = f"antigravity-cli-{QUALIFIED_CLI_VERSION}:{PINNED_TRANSPORT_STREAM}:{PINNED_MODEL}"

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[-.][0-9A-Za-z]+)*$")


def validate_version_format(version: Any) -> bool:
    """Validate that version string is an exact semantic version without ranges, operators, or wildcards."""
    if not isinstance(version, str):
        return False
    v = version.strip()
    if not v:
        return False
    if any(op in v for op in (">", "<", "=", "~", "^", "*", "latest", "LATEST")):
        return False
    return bool(VERSION_PATTERN.match(v))

PINNED_CAVEMAN_REPO = "JuliusBrussee/caveman"
PINNED_CAVEMAN_REVISION = "ae405e872270acc57484693612ae038b16c8f6cd"
PINNED_CAVEMAN_SKILL_PATH = "skills/caveman/SKILL.md"
PINNED_CAVEMAN_BLOB = "bd22d86b32e4a99e09ff7482a35509faac7a6f65"

COMMUNICATION_MODES = {"DEFAULT", "CAVEMAN", "MURMURS"}

SAFETY_FIELDS = (
    "required_specialist_omission",
    "authority_expansion",
    "capability_expansion",
    "governance_violation",
    "provider_privacy_expansion",
    "mandatory_gate_suppression",
)


def canonical_json(value: Any) -> str:
    """Return deterministically formatted JSON string."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest_json(value: Any) -> str:
    """Compute lowercase SHA-256 digest of canonical JSON."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def compute_git_blob_hash(data: bytes) -> str:
    """Compute Git blob object hash (SHA-1 over 'blob <size>\\0<content>')."""
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def compute_counter_id(
    cli_version: str = PINNED_CLI_VERSION,
    model: str = PINNED_MODEL,
    transport: str = PINNED_TRANSPORT,
) -> str:
    """Compute deterministic Orchestra measurement-surface identity.

    This identifier represents Orchestra-assigned provenance for the host measurement surface.
    It is not claimed to be a vendor/provider-issued counter ID.
    """
    return f"antigravity-cli-{cli_version}:{transport}:{model}"


def get_default_settings_path() -> Path:
    """Return default settings path: ~/.gemini/antigravity-cli/settings.json."""
    return Path.home() / ".gemini" / "antigravity-cli" / "settings.json"


def resolve_use_g1_credits(
    settings: Any,
) -> tuple[bool, str | None, dict[str, Any]]:
    """Resolve and validate useG1Credits according to Antigravity sparse-settings semantics.

    Official Antigravity semantics:
    1. `useG1Credits` has system default `false`.
    2. `settings.json` uses sparse persistence: values equal to system defaults may be omitted.
    3. Key absent and key explicitly `false` represent the same effective host policy:
       `effective_use_g1_credits = false` (credit fallback disabled).
    4. Key explicitly `true` enables personal credit fallback: fails closed as INVALID_RUN.
    5. Key present with non-boolean values (e.g. null, 0, 1, "false", "true", {}, []) fails closed
       without silent coercion.

    Returns:
        (is_valid, error_message, credit_fallback_policy)
    """
    if not isinstance(settings, dict):
        policy = {
            "setting_name": "useG1Credits",
            "key_present": False,
            "observed_value": None,
            "effective_value": None,
            "effective_source": "INVALID_SETTINGS_ROOT",
            "fallback_allowed": False,
        }
        return False, "settings.json root is not an object", policy

    if "useG1Credits" not in settings:
        policy = {
            "setting_name": "useG1Credits",
            "key_present": False,
            "observed_value": None,
            "effective_value": False,
            "effective_source": "SYSTEM_DEFAULT_SPARSE_PERSISTENCE",
            "fallback_allowed": False,
        }
        return True, None, policy

    raw_val = settings["useG1Credits"]
    if type(raw_val) is not bool:
        policy = {
            "setting_name": "useG1Credits",
            "key_present": True,
            "observed_value": raw_val,
            "effective_value": None,
            "effective_source": "MALFORMED_EXPLICIT_SETTING",
            "fallback_allowed": False,
        }
        return (
            False,
            f"useG1Credits has invalid non-boolean value in settings.json: {raw_val!r}",
            policy,
        )

    if raw_val is True:
        policy = {
            "setting_name": "useG1Credits",
            "key_present": True,
            "observed_value": True,
            "effective_value": True,
            "effective_source": "EXPLICIT_SETTING",
            "fallback_allowed": True,
        }
        return (
            False,
            "useG1Credits is explicitly true in settings.json; benchmark measurement requires personal credit fallback disabled",
            policy,
        )

    policy = {
        "setting_name": "useG1Credits",
        "key_present": True,
        "observed_value": False,
        "effective_value": False,
        "effective_source": "EXPLICIT_SETTING",
        "fallback_allowed": False,
    }
    return True, None, policy


def repository_root() -> Path:
    """Return root repository path."""
    return Path(__file__).resolve().parent.parent


def bind_communication_treatment(
    request: dict[str, Any],
    caveman_policy_content: str | bytes | None = None,
    caveman_policy_path: Path | str | None = None,
    caveman_repo_path: Path | str | None = None,
    presentation_root: Path | str | None = None,
) -> tuple[bool, str | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Deterministically bind and preflight the communication treatment for the arm.

    Supported communication modes:
    - DEFAULT: presentation NORMAL, unchanged task prompt, deterministic digest.
    - CAVEMAN: external pinned baseline (JuliusBrussee/caveman@ae405e872270acc57484693612ae038b16c8f6cd,
      skills/caveman/SKILL.md blob bd22d86b32e4a99e09ff7482a35509faac7a6f65).
    - MURMURS: canonical orchestra_runtime.presentation semantics (PresentationMode.MURMURS).

    Returns:
        (is_valid, invalid_reason, detail, binding_info)
    """
    if not isinstance(request, dict):
        return (
            False,
            "HARNESS_FAILURE",
            {"error": "request is not an object"},
            None,
        )

    arm = request.get("arm")
    if not isinstance(arm, dict):
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "request arm is missing or not an object"},
            None,
        )

    comm_mode = arm.get("communication_mode")
    if comm_mode not in COMMUNICATION_MODES:
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"unsupported or missing communication_mode: {comm_mode!r}",
                "allowed_modes": sorted(COMMUNICATION_MODES),
            },
            None,
        )

    task_payload = request.get("task_payload", {})
    if not isinstance(task_payload, dict):
        task_payload = {}
    task_prompt = str(task_payload.get("prompt", ""))
    task_prompt_digest = digest_json(task_prompt)

    if comm_mode == "DEFAULT":
        effective_prompt = task_prompt
        effective_prompt_digest = digest_json(effective_prompt)
        provenance = {
            "source": "ORCHESTRA_CANONICAL_PRESENTATION",
            "mode": "DEFAULT",
            "presentation_mode": "NORMAL",
        }
        treatment_identity = digest_json({
            "communication_mode": "DEFAULT",
            "presentation_mode": "NORMAL",
            "treatment_effective": True,
            "provenance": provenance,
        })
        binding_info = {
            "communication_mode": "DEFAULT",
            "presentation_mode": "NORMAL",
            "treatment_effective": True,
            "treatment_identity": treatment_identity,
            "treatment_provenance": provenance,
            "task_prompt": task_prompt,
            "task_prompt_digest": task_prompt_digest,
            "effective_prompt": effective_prompt,
            "effective_prompt_or_policy_digest": effective_prompt_digest,
            "policy_details": {},
        }
        return True, None, None, binding_info

    if comm_mode == "CAVEMAN":
        # Resolve policy source
        content_src = (
            caveman_policy_content
            or task_payload.get("caveman_policy_content")
            or request.get("caveman_policy_content")
            or os.environ.get("ORCHESTRA_CAVEMAN_POLICY_CONTENT")
        )
        path_src = (
            caveman_policy_path
            or task_payload.get("caveman_policy_path")
            or request.get("caveman_policy_path")
            or os.environ.get("ORCHESTRA_CAVEMAN_POLICY_PATH")
        )
        repo_src = (
            caveman_repo_path
            or task_payload.get("caveman_repo_path")
            or request.get("caveman_repo_path")
            or os.environ.get("ORCHESTRA_CAVEMAN_REPO_PATH")
        )

        observed_rev = (
            task_payload.get("caveman_repo_revision")
            or request.get("caveman_repo_revision")
            or os.environ.get("ORCHESTRA_CAVEMAN_REPO_REVISION")
        )

        # If repo path provided, verify revision and locate policy if not explicitly given
        if repo_src is not None:
            r_path = Path(repo_src)
            if not r_path.is_dir() and content_src is None and path_src is None:
                return (
                    False,
                    "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
                    {"error": f"Caveman repository directory not found: {repo_src}"},
                    None,
                )
            if observed_rev is None and (r_path / ".git").exists():
                try:
                    cp = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=str(r_path),
                        capture_output=True,
                        text=True,
                        check=False,
                        shell=False,
                    )
                    if cp.returncode == 0:
                        observed_rev = cp.stdout.strip()
                except OSError:
                    pass
            if path_src is None and content_src is None:
                path_src = r_path / "skills" / "caveman" / "SKILL.md"

        if observed_rev is not None and observed_rev != PINNED_CAVEMAN_REVISION:
            return (
                False,
                "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
                {
                    "error": f"Caveman repository revision mismatch: expected {PINNED_CAVEMAN_REVISION}, observed {observed_rev}",
                    "pinned_revision": PINNED_CAVEMAN_REVISION,
                    "observed_revision": observed_rev,
                },
                None,
            )

        # Read policy bytes
        policy_bytes: bytes | None = None
        if content_src is not None:
            policy_bytes = content_src.encode("utf-8") if isinstance(content_src, str) else content_src
        elif path_src is not None:
            p_file = Path(path_src)
            if not p_file.is_file():
                return (
                    False,
                    "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
                    {"error": f"Caveman policy file not found: {path_src}"},
                    None,
                )
            try:
                policy_bytes = p_file.read_bytes()
            except OSError as exc:
                return (
                    False,
                    "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
                    {"error": f"failed to read Caveman policy file: {exc}", "path": str(path_src)},
                    None,
                )
        else:
            return (
                False,
                "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
                {"error": "Caveman policy not found: no policy content, policy path, or repository specified"},
                None,
            )

        observed_blob = compute_git_blob_hash(policy_bytes)
        if observed_blob != PINNED_CAVEMAN_BLOB:
            return (
                False,
                "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
                {
                    "error": f"Caveman SKILL.md blob mismatch: expected {PINNED_CAVEMAN_BLOB}, observed {observed_blob}",
                    "pinned_blob": PINNED_CAVEMAN_BLOB,
                    "observed_blob": observed_blob,
                },
                None,
            )

        try:
            policy_text = policy_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            return (
                False,
                "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
                {"error": f"Caveman policy content is not valid UTF-8: {exc}"},
                None,
            )

        if not policy_text.strip():
            return (
                False,
                "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
                {"error": "Caveman policy content is empty"},
                None,
            )

        # Enforce that caveman-compress or proxy is not selected
        if "name: caveman-compress" in policy_text or "name: caveman-proxy" in policy_text or "caveman proxy" in policy_text.lower():
            return (
                False,
                "UNRESOLVABLE_EXTERNAL_DEPENDENCY_FAILURE",
                {"error": "caveman-compress or context proxy is prohibited in B3 comparative benchmark"},
                None,
            )

        effective_prompt = f"[COMMUNICATION POLICY]\n{policy_text.strip()}\n\n[TASK]\n{task_prompt}"
        effective_prompt_digest = digest_json(effective_prompt)
        loaded_policy_digest = digest_json(policy_text)

        provenance = {
            "source": "EXTERNAL_COMPARATIVE_BASELINE",
            "external_repository": PINNED_CAVEMAN_REPO,
            "pinned_revision": PINNED_CAVEMAN_REVISION,
            "skill_path": PINNED_CAVEMAN_SKILL_PATH,
            "pinned_blob_identity": PINNED_CAVEMAN_BLOB,
            "loaded_policy_digest": loaded_policy_digest,
        }
        treatment_identity = digest_json({
            "communication_mode": "CAVEMAN",
            "presentation_mode": "NORMAL",
            "treatment_effective": True,
            "external_repository": PINNED_CAVEMAN_REPO,
            "pinned_revision": PINNED_CAVEMAN_REVISION,
            "skill_path": PINNED_CAVEMAN_SKILL_PATH,
            "pinned_blob_identity": PINNED_CAVEMAN_BLOB,
            "loaded_policy_digest": loaded_policy_digest,
        })
        binding_info = {
            "communication_mode": "CAVEMAN",
            "presentation_mode": "NORMAL",
            "treatment_effective": True,
            "treatment_identity": treatment_identity,
            "treatment_provenance": provenance,
            "task_prompt": task_prompt,
            "task_prompt_digest": task_prompt_digest,
            "effective_prompt": effective_prompt,
            "effective_prompt_or_policy_digest": effective_prompt_digest,
            "policy_details": {
                "external_repository": PINNED_CAVEMAN_REPO,
                "pinned_revision": PINNED_CAVEMAN_REVISION,
                "skill_path": PINNED_CAVEMAN_SKILL_PATH,
                "pinned_blob_identity": PINNED_CAVEMAN_BLOB,
                "loaded_policy_digest": loaded_policy_digest,
            },
        }
        return True, None, None, binding_info

    if comm_mode == "MURMURS":
        try:
            root = presentation_root or repository_root()
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            from orchestra_runtime.presentation import (
                load_murmurs_vocabulary,
                load_presentation_policy,
            )

            policy = load_presentation_policy(root)
            vocab = load_murmurs_vocabulary(root)
        except Exception as exc:
            return (
                False,
                "MEASUREMENT_CAPTURE_FAILURE",
                {"error": f"failed to load canonical Murmurs presentation contracts: {exc}"},
                None,
            )

        policy_digest = digest_json(policy)
        vocab_digest = digest_json(vocab)
        effective_prompt = task_prompt  # Murmurs does not alter the underlying prompt substance
        effective_prompt_digest = digest_json(effective_prompt)

        provenance = {
            "source": "ORCHESTRA_CANONICAL_PRESENTATION",
            "presentation_mode": "MURMURS",
            "presentation_policy_digest": policy_digest,
            "murmurs_vocabulary_digest": vocab_digest,
        }
        treatment_identity = digest_json({
            "communication_mode": "MURMURS",
            "presentation_mode": "MURMURS",
            "treatment_effective": True,
            "presentation_policy_digest": policy_digest,
            "murmurs_vocabulary_digest": vocab_digest,
        })
        binding_info = {
            "communication_mode": "MURMURS",
            "presentation_mode": "MURMURS",
            "treatment_effective": True,
            "treatment_identity": treatment_identity,
            "treatment_provenance": provenance,
            "task_prompt": task_prompt,
            "task_prompt_digest": task_prompt_digest,
            "effective_prompt": effective_prompt,
            "effective_prompt_or_policy_digest": effective_prompt_digest,
            "policy_details": {
                "presentation_mode": "MURMURS",
                "presentation_policy_digest": policy_digest,
                "murmurs_vocabulary_digest": vocab_digest,
            },
        }
        return True, None, None, binding_info

    return (
        False,
        "MEASUREMENT_CAPTURE_FAILURE",
        {"error": f"unhandled communication mode: {comm_mode}"},
        None,
    )


def run_host_preflight(
    request: dict[str, Any],
    expected_cli_version: str | None = None,
    settings_path: Path | None = None,
    version_runner_fn: Callable[[list[str]], tuple[int, str, str]] | None = None,
    transport: str = PINNED_TRANSPORT,
) -> tuple[bool, str | None, dict[str, Any] | None, str | None]:
    """Execute fail-closed host preflight before real model invocation.

    Invariants verified:
    1. Expected CLI version is explicitly provided, non-empty, and valid format.
    2. Resolved Antigravity CLI version from `agy --version` exactly equals expected_cli_version.
    3. settings.json exists and parses successfully.
    4. useG1Credits resolves to effective False under sparse settings semantics (omitted or explicit False).
    5. Benchmark model in request control_identity remains exactly gemini-3.7-flash-high.
    6. Expected counter identity matches the specified transport and version.

    Returns:
        (is_valid, invalid_reason, detail, validated_cli_version)
    """
    if expected_cli_version is None or not validate_version_format(expected_cli_version):
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"invalid or missing expected_cli_version: {expected_cli_version!r}",
                "expected_cli_version": expected_cli_version,
            },
            None,
        )

    req_control = request.get("control_identity", {})
    req_model = req_control.get("model", PINNED_MODEL)
    if req_model != PINNED_MODEL:
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"request model {req_model!r} does not match pinned model {PINNED_MODEL!r}",
                "pinned_model": PINNED_MODEL,
                "request_model": req_model,
            },
            None,
        )

    target_settings = settings_path or get_default_settings_path()
    if not target_settings.is_file():
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"settings file not found: {target_settings}",
                "settings_path": str(target_settings),
            },
            None,
        )

    try:
        raw_settings = target_settings.read_text(encoding="utf-8")
        settings = json.loads(raw_settings)
    except Exception as exc:
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"failed to parse settings.json: {exc}",
                "settings_path": str(target_settings),
            },
            None,
        )

    valid_credits, credit_err, credit_policy = resolve_use_g1_credits(settings)
    if not valid_credits:
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": credit_err,
                "observed_useG1Credits": credit_policy.get("observed_value"),
                "credit_fallback_policy": credit_policy,
                "settings_path": str(target_settings),
            },
            None,
        )

    version_cmd = ["agy", "--version"]
    if version_runner_fn is not None:
        rc, stdout, stderr = version_runner_fn(version_cmd)
    else:
        try:
            completed = subprocess.run(
                version_cmd,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
            rc, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
        except OSError as exc:
            return (
                False,
                "HARNESS_FAILURE",
                {"error": f"failed to execute agy --version: {exc}"},
                None,
            )

    if rc != 0:
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"agy --version returned non-zero exit code {rc}",
                "returncode": rc,
                "stdout": stdout,
                "stderr": stderr,
            },
            None,
        )

    raw_version = stdout.strip()
    tokens = raw_version.split()
    resolved_version = tokens[-1] if tokens else ""
    if resolved_version != expected_cli_version:
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"resolved CLI version {resolved_version!r} does not match expected version {expected_cli_version!r}",
                "raw_version_output": raw_version,
                "expected_version": expected_cli_version,
                "observed_version": resolved_version,
            },
            None,
        )

    expected_counter = compute_counter_id(cli_version=expected_cli_version, model=PINNED_MODEL, transport=transport)
    counter_id = compute_counter_id(cli_version=resolved_version, model=PINNED_MODEL, transport=transport)
    if counter_id != expected_counter:
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "counter identity mismatch",
                "observed_counter_id": counter_id,
                "expected_counter_id": expected_counter,
            },
            None,
        )

    return True, None, None, resolved_version


def resolve_workspace(
    workspace_path: Path | str | None = None,
    task_payload: dict[str, Any] | None = None,
    request: dict[str, Any] | None = None,
    require_explicit: bool = False,
) -> tuple[bool, str | None, dict[str, Any] | None, Path | None, dict[str, Any] | None]:
    """Resolve and validate explicit Antigravity workspace path for headless execution.

    Invariants and fail-closed rules:
    1. If require_explicit is True or task_payload requires workspace, an explicit workspace is strictly required.
    2. If workspace is provided, it must be a non-empty string or Path.
    3. The resolved workspace path must exist on the local filesystem.
    4. The resolved workspace path must be a directory (not a file).
    5. The workspace directory must be deterministically resolved (Path.resolve()).
    6. AGY scratch fallback (~/.gemini/antigravity-cli/scratch) is strictly prohibited when workspace is required.

    Returns:
        (is_valid, invalid_reason, detail, resolved_path, binding_provenance)
    """
    raw_ws: Any = None
    source_name = "NONE"
    payload = task_payload or {}
    must_require = require_explicit or bool(payload.get("require_workspace") or payload.get("require_explicit_workspace"))

    if workspace_path is not None:
        raw_ws = workspace_path
        source_name = "EXECUTOR_ARGUMENT"
    elif (
        payload.get("workspace_dir") is not None
        or payload.get("workspace_path") is not None
        or payload.get("workspace") is not None
    ):
        raw_ws = (
            payload.get("workspace_dir")
            if payload.get("workspace_dir") is not None
            else payload.get("workspace_path")
            if payload.get("workspace_path") is not None
            else payload.get("workspace")
        )
        source_name = "TASK_PAYLOAD"
    elif request and (
        request.get("workspace_dir") is not None
        or request.get("workspace_path") is not None
        or request.get("workspace") is not None
    ):
        raw_ws = (
            request.get("workspace_dir")
            if request.get("workspace_dir") is not None
            else request.get("workspace_path")
            if request.get("workspace_path") is not None
            else request.get("workspace")
        )
        source_name = "REQUEST_ROOT"
    elif os.environ.get("ORCHESTRA_WORKSPACE_DIR"):
        raw_ws = os.environ.get("ORCHESTRA_WORKSPACE_DIR")
        source_name = "ENVIRONMENT_VARIABLE"
    elif os.environ.get("ANTIGRAVITY_WORKSPACE_DIR"):
        raw_ws = os.environ.get("ANTIGRAVITY_WORKSPACE_DIR")
        source_name = "ENVIRONMENT_VARIABLE"

    if raw_ws is None:
        if must_require:
            return (
                False,
                "MEASUREMENT_CAPTURE_FAILURE",
                {"error": "explicit workspace directory is required but was not supplied"},
                None,
                None,
            )
        unbound_provenance = {
            "bound": False,
            "workspace_path": None,
            "workspace_flag": "--add-dir",
            "workspace_mechanism": "CLI_ADD_DIR",
            "provenance": {
                "source": "NONE",
                "resolved_path": None,
                "is_directory": False,
            },
        }
        return True, None, None, None, unbound_provenance

    if not isinstance(raw_ws, (str, Path)):
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"invalid workspace path type: {type(raw_ws).__name__}"},
            None,
            None,
        )

    str_ws = str(raw_ws).strip()
    if not str_ws:
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "workspace directory path is empty"},
            None,
            None,
        )

    try:
        resolved_path = Path(str_ws).resolve()
    except Exception as exc:
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"failed to resolve workspace path: {exc}", "workspace_path": str_ws},
            None,
            None,
        )

    if not resolved_path.exists():
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"workspace directory does not exist: {resolved_path}",
                "workspace_path": str(resolved_path),
            },
            None,
            None,
        )

    if not resolved_path.is_dir():
        return (
            False,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"workspace path is not a directory: {resolved_path}",
                "workspace_path": str(resolved_path),
            },
            None,
            None,
        )

    bound_provenance = {
        "bound": True,
        "workspace_path": str(resolved_path),
        "workspace_flag": "--add-dir",
        "workspace_mechanism": "CLI_ADD_DIR",
        "provenance": {
            "source": source_name,
            "resolved_path": str(resolved_path),
            "is_directory": True,
        },
    }
    return True, None, None, resolved_path, bound_provenance


def map_antigravity_tokens(usage: dict[str, Any], counter_id: str) -> dict[str, Any]:
    """Map Antigravity native structured usage to Orchestra token schema.

    Mapping rules:
    - Antigravity input_tokens       -> Orchestra tokens.input_tokens
    - Antigravity output_tokens      -> Orchestra tokens.output_tokens
    - Antigravity cache_read_tokens  -> Orchestra tokens.cached_input_tokens
    - Antigravity thinking_tokens    -> Orchestra tokens.reasoning_tokens
    - Antigravity total_tokens       -> preserved in raw_evidence only (NOT fresh_billable_tokens)

    fresh_billable_tokens remains null unless Antigravity exposes an explicit billable field.
    """
    if not isinstance(usage, dict):
        raise ValueError("native usage object must be a dictionary")

    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")

    if input_tokens is None or isinstance(input_tokens, bool) or not isinstance(input_tokens, int) or input_tokens < 0:
        raise ValueError(f"invalid or missing input_tokens in usage: {input_tokens!r}")
    if output_tokens is None or isinstance(output_tokens, bool) or not isinstance(output_tokens, int) or output_tokens < 0:
        raise ValueError(f"invalid or missing output_tokens in usage: {output_tokens!r}")

    cached_input = usage.get("cache_read_tokens")
    if cached_input is not None:
        if isinstance(cached_input, bool) or not isinstance(cached_input, int) or cached_input < 0:
            raise ValueError(f"invalid cache_read_tokens in usage: {cached_input!r}")

    reasoning = usage.get("thinking_tokens")
    if reasoning is not None:
        if isinstance(reasoning, bool) or not isinstance(reasoning, int) or reasoning < 0:
            raise ValueError(f"invalid thinking_tokens in usage: {reasoning!r}")

    return {
        "source": "HOST_REPORTED",
        "counter_id": counter_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_input_tokens": cached_input,
        "reasoning_tokens": reasoning,
        "fresh_billable_tokens": None,
    }


def make_unavailable_cost() -> dict[str, Any]:
    """Return provider cost structure indicating UNAVAILABLE."""
    return {
        "source": "UNAVAILABLE",
        "amount": None,
        "currency": None,
    }


def build_invalid_result(
    request: dict[str, Any],
    reason: str,
    detail: dict[str, Any],
    elapsed_ms: int | None = None,
    expected_cli_version: str | None = None,
) -> dict[str, Any]:
    """Build fail-closed INVALID_RUN executor result matching schema."""
    req_id = request.get("request_id", "unknown-request")
    unavailable_evidence: dict[str, Any] = {
        "request_id": req_id,
        "invalid_reason": reason,
        "detail": detail,
        "validation_executed": False,
        "governance_evaluated": False,
    }
    if expected_cli_version is not None:
        unavailable_evidence["expected_cli_version"] = expected_cli_version
    unavailable_digest = digest_json(unavailable_evidence)
    return {
        "schema_version": EXECUTOR_RESULT_VERSION,
        "request_id": req_id,
        "outcome": {
            "status": "INVALID_RUN",
            "invalid_reason": reason,
            "task_completed": False,
            "validation_passed": False,
            "governance_valid": False,
        },
        "quality": {
            "requirements_satisfied": 0,
            "requirements_missed": 0,
            "remediation_iterations": 0,
            "validation_failures": 0,
            "regressions_introduced": 0,
        },
        "tokens": {
            "source": "UNAVAILABLE",
            "counter_id": None,
            "input_tokens": None,
            "output_tokens": None,
            "cached_input_tokens": None,
            "reasoning_tokens": None,
            "fresh_billable_tokens": None,
        },
        "cost": make_unavailable_cost(),
        "latency": {
            "wall_clock_ms": elapsed_ms,
            "model_execution_ms": None,
            "tool_execution_ms": None,
            "coordination_overhead_ms": None,
        },
        "coordination": {
            "specialist_messages": 0,
            "cross_specialist_messages": 0,
            "handoffs": 0,
            "handoff_failures": 0,
            "duplicate_work_events": 0,
            "contradiction_events": 0,
            "join_wait_ms": None,
            "specialist_reentry_events": 0,
        },
        "communication": {
            "progress_messages": 0,
            "model_progress_calls": 0,
            "user_visible_bytes": 0,
            "context_transfer_bytes": 0,
            "semantic_preservation_failures": 0,
            "required_information_omissions": 0,
        },
        "safety": {field: False for field in SAFETY_FIELDS},
        "validation_digest": unavailable_digest,
        "governance_digest": unavailable_digest,
        "raw_evidence": unavailable_evidence,
        "a5_shadow_observation": None,
    }


def evaluate_task_outcome(
    antigravity_output: dict[str, Any],
    task_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, bool]]:
    """Determine benchmark task outcome independently from host execution status.

    Quality Boundary:
    Antigravity status SUCCESS does NOT imply benchmark task PASS.
    No missing task-completion, validation, or governance field may default
    to a successful benchmark result.

    Task outcome is determined strictly from explicit independently established evidence:
    - task_completed
    - validation_passed
    - governance_valid
    """
    safety = {field: False for field in SAFETY_FIELDS}

    val_contract = task_payload.get("validation_contract")
    if isinstance(val_contract, dict) and val_contract.get("validator_type") == "EXACT_JSON_CONFORMANCE_V1":
        from scripts.benchmarking.calibration_task_validator import validate_calibration_task_response

        raw_resp = (
            antigravity_output.get("response")
            if "response" in antigravity_output
            else antigravity_output.get("content")
        )
        if raw_resp is None and "task_id" in antigravity_output:
            raw_resp = antigravity_output
        return validate_calibration_task_response(raw_resp, val_contract)

    raw_completed = (
        antigravity_output.get("task_completed")
        if "task_completed" in antigravity_output
        else task_payload.get("task_completed")
    )
    raw_validation = (
        antigravity_output.get("validation_passed")
        if "validation_passed" in antigravity_output
        else task_payload.get("validation_passed")
    )
    raw_gov = (
        antigravity_output.get("governance_valid")
        if "governance_valid" in antigravity_output
        else task_payload.get("governance_valid")
    )

    task_completed = bool(raw_completed) if raw_completed is not None else False
    validation_passed = bool(raw_validation) if raw_validation is not None else False
    governance_valid = bool(raw_gov) if raw_gov is not None else False

    is_pass = task_completed and validation_passed and governance_valid

    outcome = {
        "status": "PASS" if is_pass else "FAIL",
        "invalid_reason": None,
        "task_completed": task_completed,
        "validation_passed": validation_passed,
        "governance_valid": governance_valid,
    }

    quality_source = antigravity_output.get("quality") or task_payload.get("quality") or {}
    quality = {
        "requirements_satisfied": int(quality_source.get("requirements_satisfied", 1 if is_pass else 0)),
        "requirements_missed": int(quality_source.get("requirements_missed", 0 if is_pass else 1)),
        "remediation_iterations": int(quality_source.get("remediation_iterations", 0)),
        "validation_failures": int(quality_source.get("validation_failures", 0 if validation_passed else 1)),
        "regressions_introduced": int(quality_source.get("regressions_introduced", 0)),
    }

    return outcome, quality, safety


def normalize_stream_terminal_event(
    event: dict[str, Any],
) -> tuple[bool, str | None, dict[str, Any] | None]:
    """Normalize wrapped or flat Antigravity stream terminal event into canonical result payload.

    Supports:
    - Current AGY 1.1.15 wrapped result:
      {"event": "result", "result": {"status": "SUCCESS", "usage": {...}, ...}}
    - Legacy / flat compatibility:
      {"type": "result", "status": "SUCCESS", "usage": {...}, ...} or {"status": "SUCCESS", "usage": {...}, ...}

    Fails closed if:
    - event is not a JSON object
    - result payload is not a JSON object
    - missing result payload when event=result
    - conflicting outer wrapper and nested result critical fields (status, usage, cli_version, model)
    """
    if not isinstance(event, dict):
        return False, "terminal stream event is not a JSON object", None

    is_wrapped = (event.get("event") == "result") or ("result" in event)

    if is_wrapped:
        if "result" not in event:
            return False, "wrapped terminal event missing result payload", None
        result_payload = event["result"]
        if not isinstance(result_payload, dict):
            return False, "nested result payload is not a JSON object", None

        # Fail closed on conflicting critical fields between outer wrapper and nested payload
        for field in ("status", "usage", "cli_version", "model"):
            if field in event and field in result_payload:
                if event[field] != result_payload[field]:
                    return False, f"conflicting outer wrapper and nested result critical field: {field}", None

        normalized = copy.deepcopy(result_payload)
        for field in (
            "cli_version",
            "model",
            "task_completed",
            "validation_passed",
            "governance_valid",
            "latency",
            "coordination",
            "useG1Credits",
        ):
            if field in event and field not in normalized:
                normalized[field] = copy.deepcopy(event[field])

        return True, None, normalized

    # Flat event compatibility
    normalized = copy.deepcopy(event)
    return True, None, normalized


def parse_stream_json_output(
    raw_output: str | list[Any],
    request: dict[str, Any],
    elapsed_ms: int | None = None,
    expected_cli_version: str | None = None,
    validated_cli_version: str | None = None,
    binding: dict[str, Any] | None = None,
    presentation_root: Path | str | None = None,
    credit_policy: dict[str, Any] | None = None,
    workspace_binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse Antigravity NDJSON event stream and compute deterministic metrics."""
    req_id = request.get("request_id", "unknown-request")
    task_payload = request.get("task_payload", {})

    events: list[dict[str, Any]] = []
    if isinstance(raw_output, list):
        for item in raw_output:
            if not isinstance(item, dict):
                return build_invalid_result(
                    request,
                    "MEASUREMENT_CAPTURE_FAILURE",
                    {"error": "stream event is not an object", "event": item},
                    elapsed_ms,
                    expected_cli_version=expected_cli_version,
                )
            events.append(item)
    elif isinstance(raw_output, str):
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            try:
                ev = json.loads(line)
            except json.JSONDecodeError as exc:
                return build_invalid_result(
                    request,
                    "MEASUREMENT_CAPTURE_FAILURE",
                    {"error": f"stream JSON decode error on line {idx + 1}: {exc}", "line": line},
                    elapsed_ms,
                    expected_cli_version=expected_cli_version,
                )
            if not isinstance(ev, dict):
                return build_invalid_result(
                    request,
                    "MEASUREMENT_CAPTURE_FAILURE",
                    {"error": f"stream line {idx + 1} is not a JSON object", "line": line},
                    elapsed_ms,
                    expected_cli_version=expected_cli_version,
                )
            events.append(ev)
    else:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"unsupported stream output type: {type(raw_output).__name__}"},
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    if not events:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "empty event stream"},
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    # Discover candidate terminal events
    candidate_terminal_events: list[dict[str, Any]] = []
    for ev in events:
        if ev.get("event") == "result":
            candidate_terminal_events.append(ev)
        elif ev.get("type") in ("result", "terminal", "completion"):
            candidate_terminal_events.append(ev)
        elif (
            "usage" in ev
            and "status" in ev
            and ev.get("event") not in ("step_update", "init", "tool_start", "tool_complete", "heartbeat")
            and ev.get("type") not in ("step_update", "model_call")
        ):
            candidate_terminal_events.append(ev)
        elif (
            "result" in ev
            and ev.get("event") not in ("step_update", "init", "tool_start", "tool_complete", "heartbeat")
            and ev.get("type") not in ("step_update", "model_call")
        ):
            candidate_terminal_events.append(ev)

    if not candidate_terminal_events:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "no terminal result event found in stream"},
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    # If multiple candidate terminal events exist, check for conflicts
    if len(candidate_terminal_events) > 1:
        normalized_candidates: list[dict[str, Any]] = []
        for cand in candidate_terminal_events:
            ok, err_msg, cand_norm = normalize_stream_terminal_event(cand)
            if not ok or cand_norm is None:
                return build_invalid_result(
                    request,
                    "MEASUREMENT_CAPTURE_FAILURE",
                    {"error": f"invalid terminal event among candidates: {err_msg}", "candidate": cand},
                    elapsed_ms,
                    expected_cli_version=expected_cli_version,
                )
            normalized_candidates.append(cand_norm)

        # Check if candidate payloads conflict on critical measurement fields
        first_cand = normalized_candidates[0]
        for other_cand in normalized_candidates[1:]:
            for field in ("status", "usage", "cli_version", "model", "response"):
                if first_cand.get(field) != other_cand.get(field):
                    return build_invalid_result(
                        request,
                        "MEASUREMENT_CAPTURE_FAILURE",
                        {
                            "error": f"multiple conflicting terminal results in event stream for field: {field}",
                            "candidate_count": len(candidate_terminal_events),
                        },
                        elapsed_ms,
                        expected_cli_version=expected_cli_version,
                    )

    terminal_envelope = candidate_terminal_events[-1]
    is_valid_terminal, norm_error, normalized_payload = normalize_stream_terminal_event(terminal_envelope)
    if not is_valid_terminal or normalized_payload is None:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": norm_error or "failed to normalize terminal stream event",
                "terminal_envelope": terminal_envelope,
            },
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    status = normalized_payload.get("status")
    if not isinstance(status, str) or not status.strip() or status.upper() != "SUCCESS":
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"terminal stream status is not SUCCESS: {status}",
                "terminal_envelope": terminal_envelope,
                "terminal_result_payload": normalized_payload,
            },
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    usage = normalized_payload.get("usage")
    if not isinstance(usage, dict):
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "usage object missing from terminal event",
                "terminal_envelope": terminal_envelope,
                "terminal_result_payload": normalized_payload,
            },
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    target_expected_version = expected_cli_version or QUALIFIED_CLI_VERSION
    host_cli_version = normalized_payload.get("cli_version") or terminal_envelope.get("cli_version")
    effective_cli_version = (
        validated_cli_version
        or host_cli_version
        or target_expected_version
    )

    if host_cli_version is not None and host_cli_version != target_expected_version:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "terminal stream cli_version mismatch",
                "host_cli_version": host_cli_version,
                "expected_cli_version": target_expected_version,
            },
            elapsed_ms,
            expected_cli_version=target_expected_version,
        )

    host_model = normalized_payload.get("model") or terminal_envelope.get("model")
    if host_model is not None and host_model != PINNED_MODEL:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "terminal stream model mismatch",
                "host_model": host_model,
                "expected_model": PINNED_MODEL,
            },
            elapsed_ms,
            expected_cli_version=target_expected_version,
        )

    counter_id = compute_counter_id(
        cli_version=effective_cli_version,
        model=PINNED_MODEL,
        transport=PINNED_TRANSPORT_STREAM,
    )
    expected_counter = compute_counter_id(
        cli_version=target_expected_version,
        model=PINNED_MODEL,
        transport=PINNED_TRANSPORT_STREAM,
    )
    if counter_id != expected_counter:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "stream-json counter identity changed inside paired batch",
                "observed_counter_id": counter_id,
                "expected_counter_id": expected_counter,
            },
            elapsed_ms,
            expected_cli_version=target_expected_version,
        )

    try:
        tokens = map_antigravity_tokens(usage, counter_id)
    except ValueError as exc:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"stream usage mapping failed: {exc}", "usage": usage},
            elapsed_ms,
            expected_cli_version=target_expected_version,
        )

    outcome, quality, derived_safety = evaluate_task_outcome(normalized_payload, task_payload)

    # Process progress events according to presentation mode
    pres_mode = binding.get("presentation_mode", "NORMAL") if binding else "NORMAL"
    progress_messages = 0
    model_progress_calls = 0
    user_visible_bytes = 0

    intermediate_events = [
        ev
        for ev in events
        if ev is not terminal_envelope
        and ev not in candidate_terminal_events
        and ev.get("event") != "result"
        and ev.get("type") not in ("result", "terminal", "completion")
    ]

    if pres_mode == "MURMURS":
        root = presentation_root or repository_root()
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from orchestra_runtime.presentation import (
            PresentationEvent,
            PresentationEventKind,
            PresentationMode,
            decide_presentation,
        )
        for seq_idx, ev in enumerate(intermediate_events, start=1):
            raw_kind = ev.get("event_kind") or ev.get("kind") or ev.get("type") or ev.get("event")
            if raw_kind == "tool_start" or raw_kind == "TOOL_STARTED":
                event_kind = PresentationEventKind.TOOL_STARTED
            elif raw_kind == "tool_complete" or raw_kind == "TOOL_COMPLETED":
                event_kind = PresentationEventKind.TOOL_COMPLETED
            elif raw_kind == "heartbeat" or raw_kind == "EXECUTION_HEARTBEAT":
                event_kind = PresentationEventKind.EXECUTION_HEARTBEAT
            elif raw_kind and raw_kind in PresentationEventKind.__members__:
                event_kind = PresentationEventKind(raw_kind)
            else:
                event_kind = PresentationEventKind.EXECUTION_HEARTBEAT

            pres_event = PresentationEvent(
                run_id=req_id,
                event_kind=event_kind,
                sequence=seq_idx,
            )
            decision = decide_presentation(pres_event, root=root, mode=PresentationMode.MURMURS)
            if decision.disposition.value == "MURMUR":
                progress_messages += 1
                murmur_text = decision.murmur_text or ""
                user_visible_bytes += len(murmur_text.encode("utf-8"))
            elif decision.disposition.value == "EXPLAIN":
                progress_messages += 1
                content = str(ev.get("content", ev.get("response", ev.get("message", ""))))
                user_visible_bytes += len(content.encode("utf-8"))
            elif decision.disposition.value == "SILENT":
                pass
            if ev.get("type") in ("step_update", "model_call") or ev.get("event") in ("step_update", "model_call") or "content" in ev:
                model_progress_calls += 1
    else:
        # NORMAL mode (DEFAULT and CAVEMAN)
        for ev in intermediate_events:
            progress_messages += 1
            if ev.get("type") in ("step_update", "model_call") or ev.get("event") in ("step_update", "model_call") or "content" in ev:
                model_progress_calls += 1
            content = str(ev.get("content", ev.get("response", ev.get("message", ""))))
            user_visible_bytes += len(content.encode("utf-8"))

    # Add terminal response user_visible_bytes (terminal is always EXPLAIN)
    terminal_resp = (
        normalized_payload.get("response")
        or normalized_payload.get("content")
        or terminal_envelope.get("response")
        or terminal_envelope.get("content")
        or ""
    )
    if isinstance(terminal_resp, str):
        user_visible_bytes += len(terminal_resp.encode("utf-8"))
    else:
        user_visible_bytes += len(canonical_json(terminal_resp).encode("utf-8"))

    communication = {
        "progress_messages": progress_messages,
        "model_progress_calls": model_progress_calls,
        "user_visible_bytes": user_visible_bytes,
        "context_transfer_bytes": int(
            normalized_payload.get("context_transfer_bytes", terminal_envelope.get("context_transfer_bytes", 0))
        ),
        "semantic_preservation_failures": 0,
        "required_information_omissions": 0,
    }

    latency_source = normalized_payload.get("latency") or terminal_envelope.get("latency") or {}
    wall_clock_ms = latency_source.get("wall_clock_ms")
    if wall_clock_ms is None:
        if elapsed_ms is not None:
            wall_clock_ms = int(elapsed_ms)
        elif "duration_seconds" in normalized_payload and isinstance(normalized_payload["duration_seconds"], (int, float)):
            wall_clock_ms = int(normalized_payload["duration_seconds"] * 1000)
        else:
            wall_clock_ms = 0

    latency = {
        "wall_clock_ms": wall_clock_ms,
        "model_execution_ms": latency_source.get("model_execution_ms"),
        "tool_execution_ms": latency_source.get("tool_execution_ms"),
        "coordination_overhead_ms": latency_source.get("coordination_overhead_ms"),
    }

    coord_source = normalized_payload.get("coordination") or terminal_envelope.get("coordination") or {}
    coordination = {
        "specialist_messages": int(coord_source.get("specialist_messages", 0)),
        "cross_specialist_messages": int(coord_source.get("cross_specialist_messages", 0)),
        "handoffs": int(coord_source.get("handoffs", 0)),
        "handoff_failures": int(coord_source.get("handoff_failures", 0)),
        "duplicate_work_events": int(coord_source.get("duplicate_work_events", 0)),
        "contradiction_events": int(coord_source.get("contradiction_events", 0)),
        "join_wait_ms": coord_source.get("join_wait_ms"),
        "specialist_reentry_events": int(coord_source.get("specialist_reentry_events", 0)),
    }

    safety = {field: False for field in SAFETY_FIELDS}
    if derived_safety:
        safety.update(derived_safety)

    effective_credit_policy = credit_policy
    if effective_credit_policy is None:
        _, _, effective_credit_policy = resolve_use_g1_credits(
            normalized_payload if "useG1Credits" in normalized_payload else terminal_envelope
        )

    effective_ws_binding = workspace_binding or {
        "bound": False,
        "workspace_path": None,
        "workspace_flag": "--add-dir",
        "workspace_mechanism": "CLI_ADD_DIR",
        "provenance": {
            "source": "NONE",
            "resolved_path": None,
            "is_directory": False,
        },
    }

    effective_binding = binding or {}
    raw_evidence = {
        "host": "Antigravity CLI",
        "expected_cli_version": target_expected_version,
        "expected_cli_version_provenance": {
            "source": "EXECUTOR_ARGUMENT" if expected_cli_version else "DEFAULT_QUALIFIED_HOST",
            "value": target_expected_version,
        },
        "observed_cli_version": effective_cli_version,
        "cli_version": effective_cli_version,
        "cli_version_provenance": {
            "source": "PREFLIGHT_COMMAND" if validated_cli_version else "HOST_REPORTED_STREAM_JSON_USAGE",
            "value": effective_cli_version,
        },
        "model": PINNED_MODEL,
        "model_provenance": {
            "source": "PINNED_COMMAND_ARGUMENT",
            "value": PINNED_MODEL,
        },
        "transport": PINNED_TRANSPORT_STREAM,
        "usage_provenance": {
            "source": "HOST_REPORTED_STREAM_JSON_USAGE",
        },
        "counter_id": counter_id,
        "counter_id_provenance": {
            "identifier": counter_id,
            "provenance": "ORCHESTRA_ASSIGNED_MEASUREMENT_SURFACE",
            "vendor_assigned_claim": False,
        },
        "communication_mode": effective_binding.get("communication_mode", request.get("arm", {}).get("communication_mode")),
        "presentation_mode": effective_binding.get("presentation_mode", "NORMAL"),
        "treatment_effective": effective_binding.get("treatment_effective", True),
        "treatment_identity": effective_binding.get("treatment_identity", ""),
        "treatment_provenance": effective_binding.get("treatment_provenance", {}),
        "task_prompt_digest": effective_binding.get("task_prompt_digest", digest_json(task_payload.get("prompt", ""))),
        "effective_prompt_or_policy_digest": effective_binding.get("effective_prompt_or_policy_digest", ""),
        "topology_candidate_id": request.get("arm", {}).get("topology_candidate_id"),
        "topology_digest": request.get("arm", {}).get("topology_digest"),
        "workspace_binding": copy.deepcopy(effective_ws_binding),
        "terminal_event_envelope": copy.deepcopy(terminal_envelope),
        "terminal_result_payload": copy.deepcopy(normalized_payload),
        "outer_envelope": copy.deepcopy(terminal_envelope),
        "stream_events": copy.deepcopy(events),
        "total_tokens": usage.get("total_tokens"),
        "useG1Credits": effective_credit_policy.get("effective_value", False),
        "credit_fallback_policy": copy.deepcopy(effective_credit_policy),
    }

    val_basis = {
        "request_id": req_id,
        "task_id": request.get("task_id"),
        "task_completed": outcome["task_completed"],
        "validation_passed": outcome["validation_passed"],
    }
    gov_basis = {
        "request_id": req_id,
        "governance_valid": outcome["governance_valid"],
        "safety": safety,
    }

    return {
        "schema_version": EXECUTOR_RESULT_VERSION,
        "request_id": req_id,
        "outcome": outcome,
        "quality": quality,
        "tokens": tokens,
        "cost": make_unavailable_cost(),
        "latency": latency,
        "coordination": coordination,
        "communication": communication,
        "safety": safety,
        "validation_digest": digest_json(val_basis),
        "governance_digest": digest_json(gov_basis),
        "raw_evidence": raw_evidence,
        "a5_shadow_observation": None,
    }


def parse_antigravity_output(
    raw_output: str | dict[str, Any] | list[dict[str, Any]],
    request: dict[str, Any],
    elapsed_ms: int | None = None,
    expected_cli_version: str | None = None,
    validated_cli_version: str | None = None,
    binding: dict[str, Any] | None = None,
    transport: str = PINNED_TRANSPORT_JSON,
    presentation_root: Path | str | None = None,
    credit_policy: dict[str, Any] | None = None,
    workspace_binding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse raw Antigravity output (JSON or stream-json) and construct Orchestra benchmark result."""
    # Ensure treatment binding exists
    if binding is None:
        valid_binding, b_reason, b_detail, resolved_binding = bind_communication_treatment(
            request, presentation_root=presentation_root
        )
        if not valid_binding:
            return build_invalid_result(
                request,
                b_reason or "MEASUREMENT_CAPTURE_FAILURE",
                b_detail or {"error": "communication treatment binding failed"},
                elapsed_ms,
                expected_cli_version=expected_cli_version,
            )
        binding = resolved_binding

    # Detect stream-json list
    if isinstance(raw_output, list):
        return parse_stream_json_output(
            raw_output,
            request,
            elapsed_ms=elapsed_ms,
            expected_cli_version=expected_cli_version,
            validated_cli_version=validated_cli_version,
            binding=binding,
            presentation_root=presentation_root,
            credit_policy=credit_policy,
            workspace_binding=workspace_binding,
        )

    # Detect stream-json transport
    if transport in ("stream-json", "stream-json-usage", PINNED_TRANSPORT_STREAM) and isinstance(raw_output, str):
        return parse_stream_json_output(
            raw_output,
            request,
            elapsed_ms=elapsed_ms,
            expected_cli_version=expected_cli_version,
            validated_cli_version=validated_cli_version,
            binding=binding,
            presentation_root=presentation_root,
            credit_policy=credit_policy,
            workspace_binding=workspace_binding,
        )

    # Detect multi-line stream-json string
    if isinstance(raw_output, str) and "\n" in raw_output.strip():
        lines = [l.strip() for l in raw_output.splitlines() if l.strip()]
        if len(lines) > 1 and lines[0].startswith("{") and lines[1].startswith("{"):
            return parse_stream_json_output(
                raw_output,
                request,
                elapsed_ms=elapsed_ms,
                expected_cli_version=expected_cli_version,
                validated_cli_version=validated_cli_version,
                binding=binding,
                presentation_root=presentation_root,
                credit_policy=credit_policy,
                workspace_binding=workspace_binding,
            )

    task_payload = request.get("task_payload", {})

    if isinstance(raw_output, str):
        try:
            envelope = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            return build_invalid_result(
                request,
                "MEASUREMENT_CAPTURE_FAILURE",
                {"error": f"outer JSON decode failure: {exc}", "raw_stdout": raw_output},
                elapsed_ms,
                expected_cli_version=expected_cli_version,
            )
    elif isinstance(raw_output, dict):
        envelope = raw_output
    else:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"unsupported output type: {type(raw_output).__name__}"},
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    if not isinstance(envelope, dict):
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "outer JSON is not an object", "raw_output": envelope},
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    status = envelope.get("status")
    if not isinstance(status, str) or not status.strip():
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "missing or non-string status in outer envelope", "outer_envelope": envelope},
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    if status.upper() != "SUCCESS":
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"host execution status is not usable: {status}", "outer_envelope": envelope},
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    if "model" in envelope and envelope["model"] != PINNED_MODEL:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "host returned model mismatch",
                "host_model": envelope["model"],
                "pinned_model": PINNED_MODEL,
            },
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    req_control = request.get("control_identity", {})
    req_model = req_control.get("model", PINNED_MODEL)
    if req_model != PINNED_MODEL:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "request model mismatch",
                "request_model": req_model,
                "pinned_model": PINNED_MODEL,
            },
            elapsed_ms,
            expected_cli_version=expected_cli_version,
        )

    target_expected_version = expected_cli_version or QUALIFIED_CLI_VERSION
    host_cli_version = envelope.get("cli_version")
    effective_cli_version = (
        validated_cli_version
        or host_cli_version
        or target_expected_version
    )

    if host_cli_version is not None and host_cli_version != target_expected_version:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "host returned cli_version mismatch",
                "host_cli_version": host_cli_version,
                "expected_cli_version": target_expected_version,
            },
            elapsed_ms,
            expected_cli_version=target_expected_version,
        )

    expected_counter = compute_counter_id(cli_version=target_expected_version, model=PINNED_MODEL, transport=transport)
    counter_id = compute_counter_id(cli_version=effective_cli_version, model=PINNED_MODEL, transport=transport)
    if counter_id != expected_counter:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": "counter identity changed inside paired batch",
                "observed_counter_id": counter_id,
                "expected_counter_id": expected_counter,
            },
            elapsed_ms,
            expected_cli_version=target_expected_version,
        )

    usage = envelope.get("usage")
    if usage is None or not isinstance(usage, dict):
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "native usage object is missing from outer envelope", "outer_envelope": envelope},
            elapsed_ms,
            expected_cli_version=target_expected_version,
        )

    try:
        tokens = map_antigravity_tokens(usage, counter_id)
    except ValueError as exc:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": f"usage mapping failed: {exc}", "usage": usage},
            elapsed_ms,
            expected_cli_version=target_expected_version,
        )

    outcome, quality, derived_safety = evaluate_task_outcome(envelope, task_payload)

    latency_source = envelope.get("latency") or {}
    latency = {
        "wall_clock_ms": int(latency_source.get("wall_clock_ms", elapsed_ms if elapsed_ms is not None else 0)),
        "model_execution_ms": latency_source.get("model_execution_ms"),
        "tool_execution_ms": latency_source.get("tool_execution_ms"),
        "coordination_overhead_ms": latency_source.get("coordination_overhead_ms"),
    }

    coord_source = envelope.get("coordination") or {}
    coordination = {
        "specialist_messages": int(coord_source.get("specialist_messages", 0)),
        "cross_specialist_messages": int(coord_source.get("cross_specialist_messages", 0)),
        "handoffs": int(coord_source.get("handoffs", 0)),
        "handoff_failures": int(coord_source.get("handoff_failures", 0)),
        "duplicate_work_events": int(coord_source.get("duplicate_work_events", 0)),
        "contradiction_events": int(coord_source.get("contradiction_events", 0)),
        "join_wait_ms": coord_source.get("join_wait_ms"),
        "specialist_reentry_events": int(coord_source.get("specialist_reentry_events", 0)),
    }

    comm_source = envelope.get("communication") or {}
    if "user_visible_bytes" in comm_source:
        user_visible_bytes = int(comm_source["user_visible_bytes"])
    elif "response" in envelope:
        resp = envelope["response"]
        user_visible_bytes = len(resp.encode("utf-8")) if isinstance(resp, str) else len(canonical_json(resp).encode("utf-8"))
    elif "content" in envelope:
        cont = envelope["content"]
        user_visible_bytes = len(cont.encode("utf-8")) if isinstance(cont, str) else len(canonical_json(cont).encode("utf-8"))
    else:
        user_visible_bytes = 0

    communication = {
        "progress_messages": int(comm_source.get("progress_messages", 0)),
        "model_progress_calls": int(comm_source.get("model_progress_calls", 0)),
        "user_visible_bytes": user_visible_bytes,
        "context_transfer_bytes": int(comm_source.get("context_transfer_bytes", 0)),
        "semantic_preservation_failures": int(comm_source.get("semantic_preservation_failures", 0)),
        "required_information_omissions": int(comm_source.get("required_information_omissions", 0)),
    }

    safety = {field: False for field in SAFETY_FIELDS}
    if derived_safety:
        safety.update(derived_safety)

    effective_credit_policy = credit_policy
    if effective_credit_policy is None:
        _, _, effective_credit_policy = resolve_use_g1_credits(envelope)

    effective_ws_binding = workspace_binding or {
        "bound": False,
        "workspace_path": None,
        "workspace_flag": "--add-dir",
        "workspace_mechanism": "CLI_ADD_DIR",
        "provenance": {
            "source": "NONE",
            "resolved_path": None,
            "is_directory": False,
        },
    }

    effective_binding = binding or {}
    raw_evidence = {
        "host": "Antigravity CLI",
        "expected_cli_version": target_expected_version,
        "expected_cli_version_provenance": {
            "source": "EXECUTOR_ARGUMENT" if expected_cli_version else "DEFAULT_QUALIFIED_HOST",
            "value": target_expected_version,
        },
        "observed_cli_version": effective_cli_version,
        "cli_version": effective_cli_version,
        "cli_version_provenance": {
            "source": "PREFLIGHT_COMMAND" if validated_cli_version else "HOST_REPORTED_JSON_USAGE",
            "value": effective_cli_version,
        },
        "model": PINNED_MODEL,
        "model_provenance": {
            "source": "PINNED_COMMAND_ARGUMENT",
            "value": PINNED_MODEL,
        },
        "transport": transport,
        "usage_provenance": {
            "source": "HOST_REPORTED_JSON_USAGE",
        },
        "counter_id": counter_id,
        "counter_id_provenance": {
            "identifier": counter_id,
            "provenance": "ORCHESTRA_ASSIGNED_MEASUREMENT_SURFACE",
            "vendor_assigned_claim": False,
        },
        "communication_mode": effective_binding.get("communication_mode", request.get("arm", {}).get("communication_mode")),
        "presentation_mode": effective_binding.get("presentation_mode", "NORMAL"),
        "treatment_effective": effective_binding.get("treatment_effective", True),
        "treatment_identity": effective_binding.get("treatment_identity", ""),
        "treatment_provenance": effective_binding.get("treatment_provenance", {}),
        "task_prompt_digest": effective_binding.get("task_prompt_digest", digest_json(task_payload.get("prompt", ""))),
        "effective_prompt_or_policy_digest": effective_binding.get("effective_prompt_or_policy_digest", ""),
        "topology_candidate_id": request.get("arm", {}).get("topology_candidate_id"),
        "topology_digest": request.get("arm", {}).get("topology_digest"),
        "workspace_binding": copy.deepcopy(effective_ws_binding),
        "outer_envelope": copy.deepcopy(envelope),
        "total_tokens": usage.get("total_tokens"),
        "useG1Credits": effective_credit_policy.get("effective_value", False),
        "credit_fallback_policy": copy.deepcopy(effective_credit_policy),
    }

    val_basis = {
        "request_id": request.get("request_id"),
        "task_id": request.get("task_id"),
        "task_completed": outcome["task_completed"],
        "validation_passed": outcome["validation_passed"],
    }
    gov_basis = {
        "request_id": request.get("request_id"),
        "governance_valid": outcome["governance_valid"],
        "safety": safety,
    }

    return {
        "schema_version": EXECUTOR_RESULT_VERSION,
        "request_id": request.get("request_id"),
        "outcome": outcome,
        "quality": quality,
        "tokens": tokens,
        "cost": make_unavailable_cost(),
        "latency": latency,
        "coordination": coordination,
        "communication": communication,
        "safety": safety,
        "validation_digest": digest_json(val_basis),
        "governance_digest": digest_json(gov_basis),
        "raw_evidence": raw_evidence,
        "a5_shadow_observation": None,
    }


def execute_request(
    request: dict[str, Any],
    expected_cli_version: str | None = None,
    runner_fn: Callable[..., tuple[int, str, str]] | None = None,
    settings_path: Path | None = None,
    version_runner_fn: Callable[[list[str]], tuple[int, str, str]] | None = None,
    caveman_policy_content: str | bytes | None = None,
    caveman_policy_path: Path | str | None = None,
    caveman_repo_path: Path | str | None = None,
    presentation_root: Path | str | None = None,
    transport: str | None = None,
    workspace_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Execute a single comparative benchmark request with Antigravity binding."""
    if not isinstance(request, dict):
        return build_invalid_result({}, "HARNESS_FAILURE", {"error": "request is not a dictionary"})

    task_payload = request.get("task_payload", {})
    if task_payload.get("corrupted_starting_state"):
        return build_invalid_result(
            request,
            "CORRUPTED_STARTING_STATE",
            {"error": "starting state corruption detected in task payload"},
        )

    req_control = request.get("control_identity", {})
    if not req_control.get("starting_state_digest"):
        return build_invalid_result(
            request,
            "CORRUPTED_STARTING_STATE",
            {"error": "missing starting_state_digest in control identity"},
        )

    if req_control.get("model") != PINNED_MODEL:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"control identity model {req_control.get('model')!r} does not match pinned model {PINNED_MODEL!r}"
            },
        )

    expected_ver = (
        expected_cli_version
        or task_payload.get("expected_cli_version")
        or req_control.get("expected_cli_version")
        or request.get("expected_cli_version")
        or os.environ.get("ORCHESTRA_EXPECTED_CLI_VERSION")
        or os.environ.get("ANTIGRAVITY_EXPECTED_CLI_VERSION")
    )
    if expected_ver is not None and not validate_version_format(expected_ver):
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {
                "error": f"invalid expected_cli_version format: {expected_ver!r}",
                "expected_cli_version": expected_ver,
            },
            expected_cli_version=expected_ver,
        )

    # Deterministically bind and preflight communication treatment
    is_valid, inv_reason, inv_detail, binding = bind_communication_treatment(
        request,
        caveman_policy_content=caveman_policy_content,
        caveman_policy_path=caveman_policy_path,
        caveman_repo_path=caveman_repo_path,
        presentation_root=presentation_root,
    )
    if not is_valid or binding is None:
        return build_invalid_result(
            request,
            inv_reason or "MEASUREMENT_CAPTURE_FAILURE",
            inv_detail or {"error": "communication arm binding failed"},
            expected_cli_version=expected_ver,
        )

    # Determine transport format and counter type
    req_transport = transport or task_payload.get("transport") or request.get("transport") or PINNED_TRANSPORT
    if req_transport in ("stream-json", "stream-json-usage"):
        transport_format = "stream-json"
        transport_counter = PINNED_TRANSPORT_STREAM
    else:
        transport_format = "json"
        transport_counter = PINNED_TRANSPORT_JSON

    mock_output = (
        task_payload.get("raw_host_output")
        or task_payload.get("mock_antigravity_response")
        or os.environ.get("ANTIGRAVITY_BENCHMARK_MOCK_OUTPUT")
    )

    # Resolve and validate explicit Antigravity workspace
    ws_valid, ws_reason, ws_detail, resolved_workspace, ws_binding_info = resolve_workspace(
        workspace_path=workspace_dir,
        task_payload=task_payload,
        request=request,
        require_explicit=False,
    )
    if not ws_valid:
        return build_invalid_result(
            request,
            ws_reason or "MEASUREMENT_CAPTURE_FAILURE",
            ws_detail or {"error": "workspace validation failed"},
            expected_cli_version=expected_ver,
        )

    if mock_output is not None:
        return parse_antigravity_output(
            mock_output,
            request,
            elapsed_ms=10,
            expected_cli_version=expected_ver,
            binding=binding,
            transport=transport_counter,
            presentation_root=presentation_root,
            workspace_binding=ws_binding_info,
        )

    # Live execution requires an explicitly supplied expected CLI version
    if not expected_ver:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"error": "expected_cli_version is required for live execution but was not supplied"},
            expected_cli_version=None,
        )

    # Fail-closed host preflight before real model invocation
    preflight_valid, pf_reason, pf_detail, validated_version = run_host_preflight(
        request,
        expected_cli_version=expected_ver,
        settings_path=settings_path,
        version_runner_fn=version_runner_fn,
        transport=transport_counter,
    )
    if not preflight_valid:
        return build_invalid_result(
            request,
            pf_reason or "MEASUREMENT_CAPTURE_FAILURE",
            pf_detail or {"error": "preflight failed"},
            expected_cli_version=expected_ver,
        )

    cli_version = validated_version or expected_ver
    effective_prompt = binding["effective_prompt"]

    # Validated Antigravity print-mode command interface with explicit workspace binding
    cmd = ["agy"]
    if resolved_workspace is not None:
        cmd.extend(["--add-dir", str(resolved_workspace)])
    cmd.extend([
        "--model",
        PINNED_MODEL,
        "-p",
        effective_prompt,
        "--output-format",
        transport_format,
    ])

    started = time.monotonic()

    if runner_fn is not None:
        try:
            returncode, stdout, stderr = runner_fn(cmd, effective_prompt)
        except TypeError:
            returncode, stdout, stderr = runner_fn(cmd)
    else:
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
            returncode, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
        except OSError as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            return build_invalid_result(
                request,
                "HARNESS_FAILURE",
                {"error": f"failed to launch Antigravity CLI: {exc}"},
                elapsed,
                expected_cli_version=expected_ver,
            )

    elapsed = int((time.monotonic() - started) * 1000)
    if returncode != 0:
        return build_invalid_result(
            request,
            "MEASUREMENT_CAPTURE_FAILURE",
            {"returncode": returncode, "stdout": stdout, "stderr": stderr},
            elapsed,
            expected_cli_version=expected_ver,
        )

    active_credit_policy = None
    target_settings = settings_path or get_default_settings_path()
    if target_settings.is_file():
        try:
            raw_settings = target_settings.read_text(encoding="utf-8")
            parsed_settings = json.loads(raw_settings)
            _, _, active_credit_policy = resolve_use_g1_credits(parsed_settings)
        except Exception:
            active_credit_policy = None

    return parse_antigravity_output(
        stdout,
        request,
        elapsed,
        expected_cli_version=expected_ver,
        validated_cli_version=cli_version,
        binding=binding,
        transport=transport_counter,
        presentation_root=presentation_root,
        credit_policy=active_credit_policy,
        workspace_binding=ws_binding_info,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint reading one JSON request on stdin and writing JSON result on stdout."""
    parser = argparse.ArgumentParser(description="Antigravity measurement executor binding for Orchestra benchmark.")
    parser.add_argument("--expected-cli-version", type=str, default=None, help="Exact expected Antigravity CLI version (e.g. 1.1.15)")
    parser.add_argument("--workspace-dir", type=Path, default=None, help="Explicit Antigravity workspace directory to bind via --add-dir")
    parser.add_argument("--request-file", type=Path, help="Optional request JSON file (default: stdin)")
    parser.add_argument("--output-file", type=Path, help="Optional output JSON file (default: stdout)")
    args = parser.parse_args(argv)

    try:
        if args.request_file:
            raw_req = args.request_file.read_text(encoding="utf-8")
        else:
            raw_req = sys.stdin.read()
        request = json.loads(raw_req)
    except Exception as exc:
        err_res = build_invalid_result(
            {},
            "HARNESS_FAILURE",
            {"error": f"cannot read/parse request JSON: {exc}"},
            expected_cli_version=args.expected_cli_version,
        )
        if args.output_file:
            args.output_file.write_text(json.dumps(err_res, indent=2) + "\n", encoding="utf-8")
        else:
            print(json.dumps(err_res, indent=2))
        return 0

    result = execute_request(
        request,
        expected_cli_version=args.expected_cli_version,
        workspace_dir=args.workspace_dir,
    )
    out_str = json.dumps(result, indent=2) + "\n"

    if args.output_file:
        args.output_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_file.write_text(out_str, encoding="utf-8")
    else:
        sys.stdout.write(out_str)
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
