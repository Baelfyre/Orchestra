"""UIX-9C V3 transport-only adapter for the frozen V2 scientific campaign.

V3 preserves V2 scientific inputs and result logic while moving the exact
prompt from the Windows argv vector to Codex exec stdin using the explicit
`-` sentinel. Live execution remains fail-closed until the separate V3 human
scientific authorization record is APPROVED.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import uix9b_live_proof_runner_v2 as v2  # noqa: E402

AUTHORIZATION_PATH = (
    ROOT
    / "docs"
    / "validation"
    / "uix9b-live-evidence-v2"
    / "v3-stdin-transport-authorization.v1.json"
)
EVIDENCE_ROOT = (
    ROOT
    / "docs"
    / "validation"
    / "uix9b-live-evidence-v2"
    / "v3-stdin-transport-20260827"
)

EXPECTED_A_PROMPT_DIGEST = "9116cd67a55cfcc4c44f671c8ac69d2a22c55f2efc70c4f2c8fec45039caebb8"
EXPECTED_B_PROMPT_DIGEST = "0d25f263abe967184ac61c500bdd75d3af310256b376619eb586ad8bbe9c6bac"
INVALID_REPLACEMENT_CLASSIFICATIONS = frozenset({"HOST_CRASH", "PROVIDER_OUTAGE"})


class V3ExecutionRefused(RuntimeError):
    """V3 transport or scientific authority is not satisfied."""


def _load_authorization() -> dict[str, Any]:
    value = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise V3ExecutionRefused("V3_AUTHORIZATION_NOT_OBJECT")
    if value.get("schema_version") != "orchestra.uix9c-v3-stdin-transport-authorization.v1":
        raise V3ExecutionRefused("V3_AUTHORIZATION_SCHEMA_MISMATCH")

    transport = value.get("transport")
    scientific = value.get("scientific_inputs")
    ceiling = value.get("fresh_campaign_proposed_ceiling")
    evidence = value.get("evidence_policy")
    boundary = value.get("authority_boundary")
    if not all(isinstance(item, dict) for item in (transport, scientific, ceiling, evidence, boundary)):
        raise V3ExecutionRefused("V3_AUTHORIZATION_MALFORMED")

    if transport != {
        "version": "V3_STDIN_UTF8",
        "prompt_transport": "STDIN",
        "stdin_encoding": "UTF-8",
        "codex_exec_stdin_sentinel": "-",
        "prompt_in_argv": False,
        "windows_createprocess_argv_limit_bypassed": True,
    }:
        raise V3ExecutionRefused("V3_TRANSPORT_AUTHORIZATION_MISMATCH")

    if scientific.get("task_fixture_prompt_guidance_evaluator_validator_unchanged") is not True:
        raise V3ExecutionRefused("V3_SCIENTIFIC_INPUT_CHANGE_DETECTED")
    if scientific.get("execution_order") != list(v2.EXECUTION_ORDER):
        raise V3ExecutionRefused("V3_EXECUTION_ORDER_MISMATCH")
    if scientific.get("max_valid_observations") != 6:
        raise V3ExecutionRefused("V3_VALID_OBSERVATION_CEILING_MISMATCH")
    if scientific.get("outcome_based_retry_authorized") is not False:
        raise V3ExecutionRefused("V3_OUTCOME_BASED_RETRY_PROHIBITION_MISSING")

    if ceiling.get("max_new_model_calls") != 7:
        raise V3ExecutionRefused("V3_MODEL_CALL_CEILING_MISMATCH")
    if ceiling.get("max_new_provider_calls") != 7:
        raise V3ExecutionRefused("V3_PROVIDER_CALL_CEILING_MISMATCH")
    if ceiling.get("max_new_provider_interactions") != 7:
        raise V3ExecutionRefused("V3_PROVIDER_INTERACTION_CEILING_MISMATCH")
    if ceiling.get("max_invalid_infrastructure_replacements") != 1:
        raise V3ExecutionRefused("V3_INVALID_REPLACEMENT_CEILING_MISMATCH")
    if ceiling.get("max_valid_observations") != 6:
        raise V3ExecutionRefused("V3_MAX_VALID_OBSERVATIONS_MISMATCH")
    if ceiling.get("seventh_valid_observation_authorized") is not False:
        raise V3ExecutionRefused("V3_SEVENTH_VALID_OBSERVATION_MUST_BE_FALSE")
    if ceiling.get("additional_ceiling_expansion_authorized") is not False:
        raise V3ExecutionRefused("V3_ADDITIONAL_CEILING_EXPANSION_MUST_BE_FALSE")

    if evidence.get("reuse_prior_a1_observation") is not False:
        raise V3ExecutionRefused("V3_PRIOR_A1_REUSE_PROHIBITION_MISSING")
    if evidence.get("preserve_all_prior_invalid_evidence") is not True:
        raise V3ExecutionRefused("V3_PRIOR_INVALID_EVIDENCE_PRESERVATION_MISSING")
    if evidence.get("fresh_evidence_root") != "docs/validation/uix9b-live-evidence-v2/v3-stdin-transport-20260827":
        raise V3ExecutionRefused("V3_EVIDENCE_ROOT_MISMATCH")
    if evidence.get("prior_invalid_evidence_is_scientific_result") is not False:
        raise V3ExecutionRefused("V3_INVALID_EVIDENCE_SCIENTIFIC_CLAIM_DETECTED")

    if any(boundary.get(field) is not False for field in (
        "merge_authorized",
        "release_authorized",
        "deployment_authorized",
        "policy_activation_authorized",
        "external_repository_mutation_authorized",
        "destructive_cleanup_authorized",
        "branch_deletion_authorized",
        "force_push_or_history_rewrite_authorized",
    )):
        raise V3ExecutionRefused("V3_PROTECTED_ACTION_AUTHORITY_EXPANSION_DETECTED")
    return value


def build_stdin_command(*, workspace_dir: Path) -> list[str]:
    """Build the V2-equivalent Codex command without placing the prompt in argv."""
    return [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--ephemeral",
        "--json",
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--model",
        v2.EXPECTED_MODEL,
        "--cd",
        str(workspace_dir.resolve()),
        "-c",
        'approval_policy="never"',
        "-c",
        'web_search="disabled"',
        "-c",
        f'model_reasoning_effort="{v2.EXPECTED_REASONING_EFFORT}"',
        "-",
    ]


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def run_codex_session_stdin(workspace: Path, prompt: str) -> dict[str, Any]:
    """Run the exact V2 prompt through explicit UTF-8 stdin instead of argv."""
    v2.verify_codex_cli_version()
    command = build_stdin_command(workspace_dir=workspace)
    prompt_digest = v2.digest_bytes(prompt.replace("\r\n", "\n").encode("utf-8"))
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            shell=False,
            check=False,
            timeout=v2.PER_RUN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "classification": "RESOURCE_CEILING_EXCEEDED",
            "command": command,
            "prompt_transport": "STDIN_UTF8",
            "prompt_digest": prompt_digest,
            "stdout": _timeout_text(exc.stdout),
            "stderr": _timeout_text(exc.stderr),
            "duration_seconds": time.monotonic() - started,
        }
    except OSError as exc:
        return {
            "classification": "HOST_CRASH",
            "command": command,
            "prompt_transport": "STDIN_UTF8",
            "prompt_digest": prompt_digest,
            "error": str(exc),
            "duration_seconds": time.monotonic() - started,
        }

    if completed.returncode != 0:
        try:
            v2.parse_codex_jsonl(completed.stdout or "")
        except v2.ProviderOutage:
            classification = "PROVIDER_OUTAGE"
        except v2.ProtocolBreach:
            classification = "HOST_CRASH"
        else:
            classification = "HOST_CRASH"
        return {
            "classification": classification,
            "command": command,
            "prompt_transport": "STDIN_UTF8",
            "prompt_digest": prompt_digest,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
            "duration_seconds": time.monotonic() - started,
        }

    parsed = v2.parse_codex_jsonl(completed.stdout or "")
    return {
        "classification": "OUTPUT_CAPTURED_PENDING_VALIDATOR",
        "command": command,
        "prompt_transport": "STDIN_UTF8",
        "prompt_digest": prompt_digest,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "parsed": parsed,
        "duration_seconds": time.monotonic() - started,
    }


def verify_transport() -> dict[str, Any]:
    """Zero-call verification of V3 transport and frozen scientific identities."""
    authorization = _load_authorization()
    frozen = v2.verify_frozen_identities()
    a_prompt, a_digest = v2.build_prompt("BASELINE_NO_ORCHESTRA_UIX_GUIDANCE")
    b_prompt, b_digest = v2.build_prompt("GOVERNED_CANONICAL_UIX_1_8_GUIDANCE")
    if a_digest != EXPECTED_A_PROMPT_DIGEST or b_digest != EXPECTED_B_PROMPT_DIGEST:
        raise V3ExecutionRefused("V3_FROZEN_PROMPT_DIGEST_DRIFT")

    probe_workspace = v2.FIXTURE_ROOT / "project"
    command = build_stdin_command(workspace_dir=probe_workspace)
    if command[-1] != "-":
        raise V3ExecutionRefused("V3_STDIN_SENTINEL_MISSING")
    if a_prompt in command or b_prompt in command:
        raise V3ExecutionRefused("V3_PROMPT_LEAKED_INTO_ARGV")
    argv_chars = sum(len(item) + 1 for item in command)
    if argv_chars >= 8192:
        raise V3ExecutionRefused("V3_COMMAND_VECTOR_UNEXPECTEDLY_LARGE")

    return {
        "transport": "V3_STDIN_UTF8",
        "authorization_status": authorization["authorization_status"],
        "live_execution_authorized": authorization["authority_boundary"]["live_execution_authorized"],
        "frozen_identity_verified": True,
        "v2_frozen_identity": frozen,
        "execution_order": list(v2.EXECUTION_ORDER),
        "a_prompt_digest": a_digest,
        "b_prompt_digest": b_digest,
        "a_prompt_chars": len(a_prompt),
        "b_prompt_chars": len(b_prompt),
        "argv_chars_without_prompt": argv_chars,
        "prompt_in_argv": False,
        "stdin_sentinel": command[-1],
        "experimental_model_calls": 0,
        "experimental_provider_calls": 0,
    }


def _authorize_live_v3(authorization: dict[str, Any], *, live_call_gate: bool) -> None:
    if authorization.get("authorization_status") != "APPROVED":
        raise V3ExecutionRefused("V3_LIVE_EXECUTION_NOT_HUMAN_AUTHORIZED")
    if authorization.get("authority_class") != "HUMAN_SCIENTIFIC_AUTHORIZATION":
        raise V3ExecutionRefused("V3_HUMAN_SCIENTIFIC_AUTHORITY_CLASS_REQUIRED")
    if authorization["authority_boundary"].get("live_execution_authorized") is not True:
        raise V3ExecutionRefused("V3_LIVE_EXECUTION_AUTHORITY_FLAG_FALSE")
    if not live_call_gate:
        raise V3ExecutionRefused("V3_EXPLICIT_LIVE_GATE_REQUIRED")


@contextmanager
def _v3_execution_envelope(authorization: dict[str, Any]) -> Iterator[None]:
    """Temporarily bind the frozen V2 executor to the approved V3 envelope.

    V3 performs the human authority check before entering this context. This
    context changes no repository file and restores every V2 process-global
    value even when execution fails. It replaces only the superseded V2
    six-call authorization check; V2 scientific identity verification,
    accounting, execution order, evaluator, validator, adjudicator, and result
    logic remain active.
    """
    ceiling = authorization["fresh_campaign_proposed_ceiling"]
    original = {
        "max_model": v2.MAX_TOTAL_MODEL_CALLS,
        "max_provider": v2.MAX_PROVIDER_CALLS,
        "max_interactions": v2.MAX_TOTAL_PROVIDER_INTERACTIONS,
        "max_retries": v2.MAX_RETRIES_FOR_INVALID_RUN,
        "authorize_live": v2._authorize_live,
    }

    def v3_authorize_bridge(_v2_auth: dict[str, Any], *, live_call_gate: bool) -> None:
        if not live_call_gate:
            raise v2.ExecutionRefused("V3_EXPLICIT_LIVE_CALL_GATE_REQUIRED")

    v2.MAX_TOTAL_MODEL_CALLS = ceiling["max_new_model_calls"]
    v2.MAX_PROVIDER_CALLS = ceiling["max_new_provider_calls"]
    v2.MAX_TOTAL_PROVIDER_INTERACTIONS = ceiling["max_new_provider_interactions"]
    v2.MAX_RETRIES_FOR_INVALID_RUN = ceiling["max_invalid_infrastructure_replacements"]
    v2._authorize_live = v3_authorize_bridge
    try:
        yield
    finally:
        v2.MAX_TOTAL_MODEL_CALLS = original["max_model"]
        v2.MAX_PROVIDER_CALLS = original["max_provider"]
        v2.MAX_TOTAL_PROVIDER_INTERACTIONS = original["max_interactions"]
        v2.MAX_RETRIES_FOR_INVALID_RUN = original["max_retries"]
        v2._authorize_live = original["authorize_live"]


def _single_replacement_session_runner() -> Callable[[Path, str], dict[str, Any]]:
    """Return a session runner allowing at most one replacement campaign-wide.

    The frozen V2 executor owns the actual retry transition. After the first
    invalid infrastructure/provider attempt has triggered that transition, the
    replacement invocation disables further automatic retries for the rest of
    the process-bound V3 campaign. A later invalid attempt is preserved with
    its real classification and stops rather than receiving another retry.
    """
    replacement_pending = False

    def runner(workspace: Path, prompt: str) -> dict[str, Any]:
        nonlocal replacement_pending
        if replacement_pending:
            v2.MAX_RETRIES_FOR_INVALID_RUN = 0
            replacement_pending = False
        result = run_codex_session_stdin(workspace, prompt)
        if (
            result.get("classification") in INVALID_REPLACEMENT_CLASSIFICATIONS
            and v2.MAX_RETRIES_FOR_INVALID_RUN > 0
        ):
            replacement_pending = True
        return result

    return runner


def execute_v3(*, live_call_gate: bool) -> dict[str, Any]:
    authorization = _load_authorization()
    _authorize_live_v3(authorization, live_call_gate=live_call_gate)
    with _v3_execution_envelope(authorization):
        return v2.execute_campaign(
            evidence_root=EVIDENCE_ROOT,
            live_call_gate=True,
            session_runner=_single_replacement_session_runner(),
        )


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["verify-transport", "execute"])
    parser.add_argument("--execution-mode", choices=["dry-run", "live"], default="dry-run")
    parser.add_argument("--live-call-gate", action="store_true")
    args = parser.parse_args(list(arguments) if arguments is not None else None)
    try:
        report = verify_transport()
        if args.command == "verify-transport":
            print(json.dumps(report, indent=2, sort_keys=True))
            print("UIX9C_V3_STDIN_TRANSPORT=PASS_ZERO_CALL")
            return 0
        if args.execution_mode != "live" or not args.live_call_gate:
            raise V3ExecutionRefused("V3_EXPLICIT_LIVE_EXECUTION_MODE_AND_GATE_REQUIRED")
        result = execute_v3(live_call_gate=True)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (
        V3ExecutionRefused,
        v2.ExecutionRefused,
        v2.ProtocolBreach,
        v2.ProviderOutage,
        RuntimeError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"UIX9C_V3_FAIL_CLOSED:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
