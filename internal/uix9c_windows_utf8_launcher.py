"""Launch the frozen UIX-9C V2 runner under Python UTF-8 mode.

This is a host-compatibility and recovery-authorization shim only. It does not
modify experiment inputs, model/provider identity, execution order, evidence
logic, or scientific result classification. Python UTF-8 mode is required
because the Windows locale may otherwise decode Codex JSONL through cp1252 and
fail on valid UTF-8 output.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "uix9b_live_proof_runner_v2.py"
RECOVERY_AUTHORIZATION = ROOT / "docs" / "validation" / "uix9b-live-evidence-v2" / "recovery-authorization.v1.json"
AUTHORIZED_FRESH_EVIDENCE_ROOT = ROOT / "docs" / "validation" / "uix9b-live-evidence-v2" / "restart-20260827"


def _load_recovery_authorization() -> dict[str, Any]:
    value = json.loads(RECOVERY_AUTHORIZATION.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("RECOVERY_AUTHORIZATION_NOT_OBJECT")
    if value.get("schema_version") != "orchestra.uix9c-invalid-infrastructure-recovery.v1":
        raise RuntimeError("RECOVERY_AUTHORIZATION_SCHEMA_MISMATCH")
    if value.get("authorization_status") != "APPROVED" or value.get("authority_class") != "HUMAN_SCIENTIFIC_AUTHORIZATION":
        raise RuntimeError("RECOVERY_AUTHORIZATION_NOT_APPROVED")

    prior = value.get("prior_invalid_attempt")
    ceiling = value.get("restarted_effort_ceiling")
    fresh = value.get("fresh_campaign")
    if not isinstance(prior, dict) or not isinstance(ceiling, dict) or not isinstance(fresh, dict):
        raise RuntimeError("RECOVERY_AUTHORIZATION_MALFORMED")
    if prior.get("provider_interactions") != 1 or prior.get("scientific_observation") is not False:
        raise RuntimeError("PRIOR_INVALID_ATTEMPT_ACCOUNTING_MISMATCH")
    if ceiling.get("prior_invalid_infrastructure_interactions") != 1:
        raise RuntimeError("RECOVERY_PRIOR_INTERACTION_CEILING_MISMATCH")
    if ceiling.get("fresh_campaign_max_new_model_calls") != 6 or ceiling.get("fresh_campaign_max_new_provider_calls") != 6:
        raise RuntimeError("RECOVERY_FRESH_CALL_CEILING_MISMATCH")
    if ceiling.get("max_valid_observations") != 6 or ceiling.get("overall_experimental_interaction_ceiling") != 7:
        raise RuntimeError("RECOVERY_OVERALL_CEILING_MISMATCH")
    if ceiling.get("seventh_valid_observation_authorized") is not False or ceiling.get("additional_ceiling_expansion_authorized") is not False:
        raise RuntimeError("RECOVERY_AUTHORITY_EXPANSION_DETECTED")
    if fresh.get("execution_order") != ["A1", "B1", "B2", "A2", "A3", "B3"]:
        raise RuntimeError("RECOVERY_EXECUTION_ORDER_MISMATCH")
    if fresh.get("evidence_root") != "docs/validation/uix9b-live-evidence-v2/restart-20260827":
        raise RuntimeError("RECOVERY_EVIDENCE_ROOT_MISMATCH")
    if fresh.get("preserve_parent_failed_evidence") is not True or fresh.get("outcome_based_retry_authorized") is not False:
        raise RuntimeError("RECOVERY_EVIDENCE_OR_RETRY_POLICY_MISMATCH")
    if fresh.get("retry_may_extend_overall_ceiling") is not False:
        raise RuntimeError("RECOVERY_RETRY_CEILING_EXPANSION_DETECTED")
    return value


def _is_live_execute(arguments: Sequence[str]) -> bool:
    if not arguments or arguments[0] != "execute" or "--execution-mode" not in arguments:
        return False
    index = arguments.index("--execution-mode")
    return index + 1 < len(arguments) and arguments[index + 1] == "live"


def build_command(arguments: Sequence[str]) -> list[str]:
    forwarded = list(arguments)
    if _is_live_execute(forwarded):
        _load_recovery_authorization()
        if "--evidence-root" in forwarded:
            raise RuntimeError("RECOVERY_EVIDENCE_ROOT_IS_LAUNCHER_OWNED")
        forwarded.extend(["--evidence-root", str(AUTHORIZED_FRESH_EVIDENCE_ROOT)])
    return [sys.executable, "-X", "utf8", str(RUNNER), *forwarded]


def main(arguments: Sequence[str] | None = None) -> int:
    try:
        command = build_command(list(sys.argv[1:] if arguments is None else arguments))
        completed = subprocess.run(command, cwd=ROOT, shell=False, check=False)
        return completed.returncode
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"UIX_9C_RECOVERY_LAUNCH_REFUSED:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
