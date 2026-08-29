#!/usr/bin/env python3
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internal.codex_app_server_bridge import (  # noqa: E402
    CodexAppServerExecutionEngine,
)
from internal.codex_user_model_selection import (  # noqa: E402
    MODEL_SELECTION_SOURCE,
    VALIDATION_MODEL_SELECTION_SOURCE,
    CodexUserModelSelection,
    build_read_only_config,
)
from orchestra_runtime.mcp_specialist_execution import (  # noqa: E402
    build_mcp_stdio_transport_with_specialist_execution,
)
from orchestra_runtime.mcp_transport import (  # noqa: E402
    MCP_CLIENT_CAPABILITIES_META_KEY,
    MCP_CLIENT_INFO_META_KEY,
    MCP_PROTOCOL_VERSION,
    MCP_PROTOCOL_VERSION_META_KEY,
)
from orchestra_runtime.specialist_execution import (  # noqa: E402
    SpecialistExecutionMode,
    SpecialistExecutionStatus,
)


FIXTURE_PATH = Path("tests/fixtures/specialist_execution/e5_scribe_read_only.md")
TASK_MARKERS = (
    "E5-SCRIBE-20260829",
    "ALDER-47",
    "REVISION_DECLARED=3",
    "REVISION_FOOTER=4",
)
EVIDENCE_SCHEMA = "orchestra.e5.codex-read-only-scribe-proof.v1"


class E5ProofError(RuntimeError):
    pass


def _run(args: list[str], *, cwd: Path = ROOT, timeout: int = 30) -> str:
    completed = subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        check=False,
        timeout=timeout,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[-1200:]
        raise E5ProofError(f"command failed ({completed.returncode}): {detail}")
    return (completed.stdout or "").strip()


def _git(*args: str) -> str:
    return _run(["git", "-C", str(ROOT), *args])


def _snapshot() -> dict[str, Any]:
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    return {
        "branch": _git("branch", "--show-current"),
        "head": _git("rev-parse", "HEAD"),
        "tree": _git("rev-parse", "HEAD^{tree}"),
        "clean": not bool(status.strip()),
        "status_sha256": sha256(status.encode("utf-8")).hexdigest(),
    }


def _validate_before_snapshot(snapshot: dict[str, Any]) -> None:
    if not snapshot.get("head"):
        raise E5ProofError("E5 could not capture the repository HEAD")
    if not snapshot.get("tree"):
        raise E5ProofError("E5 could not capture the repository tree")
    if not snapshot.get("clean"):
        raise E5ProofError("E5 requires a clean worktree")


def _validate_after_snapshot(
    before: dict[str, Any], after: dict[str, Any]
) -> None:
    if not after.get("clean"):
        raise E5ProofError("E5 read-only proof left the worktree dirty")
    if after.get("head") != before.get("head"):
        raise E5ProofError("repository HEAD changed during E5 read-only proof")
    if after.get("tree") != before.get("tree"):
        raise E5ProofError("repository tree changed during E5 read-only proof")
    if after != before:
        raise E5ProofError("repository state changed during E5 read-only proof")


def _stable_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(raw).hexdigest()


def _meta() -> dict[str, object]:
    return {
        MCP_PROTOCOL_VERSION_META_KEY: MCP_PROTOCOL_VERSION,
        MCP_CLIENT_INFO_META_KEY: {"name": "orchestra-e5-proof", "version": "1"},
        MCP_CLIENT_CAPABILITIES_META_KEY: {},
    }


def _call(prompt: str) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "_meta": _meta(),
            "name": "review-docs",
            "arguments": {"prompt": prompt},
        },
    }


def _prompt() -> str:
    return (
        "Perform a source-backed documentation review of "
        "tests/fixtures/specialist_execution/e5_scribe_read_only.md. "
        "Identify the intentional revision inconsistency and ground the finding in the exact document values. "
        "The analysis must reference DOCUMENT_ID E5-SCRIBE-20260829, CHECKSUM ALDER-47, "
        "REVISION_DECLARED=3, and REVISION_FOOTER=4. "
        "Do not modify files, use network access, invoke MCP tools, delegate, or broaden scope."
    )


def _validate_output(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise E5ProofError("specialist output was not the bridge's structured JSON result") from exc
    if not isinstance(parsed, dict):
        raise E5ProofError("specialist output must be a JSON object")
    if parsed.get("non_mutating") is not True:
        raise E5ProofError("specialist output did not preserve the non-mutating assertion")
    haystack = re.sub(r"\s*=\s*", "=", json.dumps(parsed, sort_keys=True))
    for marker in TASK_MARKERS:
        if marker not in haystack:
            raise E5ProofError(f"task-specific marker was missing from specialist output: {marker}")
    return parsed


def run(model: str, reasoning_effort: str | None, evidence_root: Path) -> dict[str, Any]:
    selection = CodexUserModelSelection(
        model=model,
        reasoning_effort=reasoning_effort,
    )
    before = _snapshot()
    _validate_before_snapshot(before)

    fixture = ROOT / FIXTURE_PATH
    if not fixture.is_file():
        raise E5ProofError(f"E5 fixture is missing: {FIXTURE_PATH.as_posix()}")
    fixture_digest = sha256(fixture.read_bytes()).hexdigest()

    created_engines: list[CodexAppServerExecutionEngine] = []

    def engine_factory() -> CodexAppServerExecutionEngine:
        engine = CodexAppServerExecutionEngine(
            ROOT,
            config=build_read_only_config(
                selection,
                turn_timeout_seconds=240,
            ),
        )
        created_engines.append(engine)
        return engine

    transport = build_mcp_stdio_transport_with_specialist_execution(
        ROOT,
        execution_engine_factory=engine_factory,
        execution_mode=SpecialistExecutionMode.HOST_NATIVE,
        backing_adapter="codex",
    )
    response = transport.handle_message(_call(_prompt()))
    result = response.get("result")
    if not isinstance(result, dict):
        raise E5ProofError(f"MCP response did not contain a result: {response}")
    if result.get("isError") is not False:
        content = result.get("content")
        raise E5ProofError(f"MCP specialist execution failed: {content}")
    content = result.get("content")
    if not isinstance(content, list) or not content or not isinstance(content[0], dict):
        raise E5ProofError("MCP result content was malformed")
    output_text = content[0].get("text")
    if not isinstance(output_text, str) or not output_text.strip():
        raise E5ProofError("MCP result did not contain substantive output")
    parsed_output = _validate_output(output_text)

    if len(created_engines) != 1:
        raise E5ProofError(f"expected exactly one execution engine, observed {len(created_engines)}")
    engine = created_engines[0]
    request = engine.last_request
    receipt = engine.last_receipt
    if request is None or receipt is None:
        raise E5ProofError("host bridge did not expose the executed request and receipt")
    if request.command_name != "review-docs" or request.specialist != "scribe":
        raise E5ProofError("runtime request did not bind review-docs to Scribe")
    if request.execution_mode is not SpecialistExecutionMode.HOST_NATIVE:
        raise E5ProofError("runtime request did not use HOST_NATIVE execution mode")
    if receipt.status is not SpecialistExecutionStatus.COMPLETED:
        raise E5ProofError(f"host receipt was not completed: {receipt.status.value}")
    receipt.assert_matches(
        request,
        engine_id=engine.engine_id,
        engine_version=engine.engine_version,
    )
    if f"specialist-source-sha256:{request.skill_source_digest}" not in receipt.evidence_refs:
        raise E5ProofError("receipt did not bind the exact Scribe guidance digest")
    if not any("mcp_servers.orchestra.enabled=false" in item for item in engine.last_host_command):
        raise E5ProofError("Codex host command did not disable recursive Orchestra MCP loading")
    if not any('sandbox_mode="read-only"' in item for item in engine.last_host_command):
        raise E5ProofError("Codex host command did not freeze read-only sandbox mode")
    if not any('approval_policy="never"' in item for item in engine.last_host_command):
        raise E5ProofError("Codex host command did not freeze approval policy")

    after = _snapshot()
    _validate_after_snapshot(before, after)

    evidence = {
        "schema_version": EVIDENCE_SCHEMA,
        "status": "PASS",
        "scope": {
            "host": "CODEX",
            "command": "review-docs",
            "specialist": "scribe",
            "mode": "READ_ONLY",
            "mutation_allowed": False,
            "model": selection.model,
            "reasoning_effort": selection.reasoning_effort,
            "model_selection_source": VALIDATION_MODEL_SELECTION_SOURCE,
            "model_configuration_source": MODEL_SELECTION_SOURCE,
        },
        "repository": {
            **before,
            "after": after,
        },
        "repository_checks": {
            "HEAD_CAPTURED": bool(before["head"]),
            "TREE_CAPTURED": bool(before["tree"]),
            "WORKTREE_CLEAN_BEFORE": before["clean"],
            "WORKTREE_CLEAN_AFTER": after["clean"],
            "HEAD_UNCHANGED_AFTER": after["head"] == before["head"],
            "TREE_UNCHANGED_AFTER": after["tree"] == before["tree"],
            "WORKTREE_UNCHANGED_AFTER": after == before,
        },
        "fixture": {
            "path": FIXTURE_PATH.as_posix(),
            "sha256": fixture_digest,
            "required_markers": list(TASK_MARKERS),
        },
        "mcp": {
            "protocol_version": MCP_PROTOCOL_VERSION,
            "command_accepted": True,
            "response_output_sha256": sha256(output_text.encode("utf-8")).hexdigest(),
            "task_specific_output_verified": True,
        },
        "runtime": {
            "request_id": request.request_id,
            "request_digest": request.request_digest,
            "command_name": request.command_name,
            "specialist": request.specialist,
            "skill_source_path": request.skill_source_path,
            "skill_source_digest": request.skill_source_digest,
            "authority_decision_ref": request.authority_decision_ref,
            "capability_decision_ref": request.capability_decision_ref,
            "governance_status": request.governance_status,
            "evaluated_governance_rules": list(request.evaluated_governance_rules),
            "execution_mode": request.execution_mode.value,
        },
        "host_receipt": {
            "receipt_id": receipt.receipt_id,
            "request_id": receipt.request_id,
            "request_digest": receipt.request_digest,
            "engine_id": receipt.engine_id,
            "engine_version": receipt.engine_version,
            "host_execution_id": receipt.host_execution_id,
            "status": receipt.status.value,
            "reason_code": receipt.reason_code,
            "side_effect_class": receipt.side_effect_class.value,
            "changed_paths": list(receipt.changed_paths),
            "host_identity": receipt.host_identity,
            "sandbox_identity": receipt.sandbox_identity,
            "approval_policy_identity": receipt.approval_policy_identity,
            "evidence_refs": list(receipt.evidence_refs),
        },
        "blockers": {
            "NO_RECURSIVE_ORCHESTRA_MCP_LOOP": "PASS",
            "WORKTREE_UNCHANGED": "PASS",
            "NO_PROVIDER_SECRET_IN_RUNTIME_AUDIT": "PASS_MINIMIZED_EVIDENCE",
            "READ_ONLY_SANDBOX": "PASS",
            "APPROVAL_POLICY_NEVER": "PASS",
        },
        "claims": {
            "HOST_BRIDGE_E2E": "VERIFIED_FOR_CODEX_READ_ONLY_SCRIBE_FIXTURE",
            "SUBSTANTIVE_SPECIALIST_EXECUTION_E2E": (
                "VERIFIED_FOR_CODEX_READ_ONLY_SCRIBE_FIXTURE"
            ),
            "E6": "NOT_RUN_BY_E5_PROOF",
            "PROMOTION": "PENDING",
        },
        "output_validation": {
            "structured_result_sha256": _stable_digest(parsed_output),
            "validated_markers": list(TASK_MARKERS),
            "raw_prompt_persisted": False,
            "full_output_persisted": False,
        },
    }

    evidence_root.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_root / "e5-codex-read-only-scribe-proof.v1.json"
    if evidence_path.exists():
        raise E5ProofError(
            f"evidence path already exists; refusing overwrite: {evidence_path}"
        )
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"evidence": evidence, "evidence_path": str(evidence_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Orchestra E5 read-only Codex/Scribe proof")
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", default=None)
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=Path.home() / "Downloads" / "ORCHESTRA_E5_CODEX_SCRIBE_20260829",
    )
    args = parser.parse_args(argv)

    print("ORCHESTRA_E5_CODEX_SCRIBE_READ_ONLY=START")
    try:
        result = run(args.model, args.reasoning_effort, args.evidence_root.resolve())
    except Exception as exc:
        print("ORCHESTRA_E5_CODEX_SCRIBE_READ_ONLY=FAIL_CLOSED")
        print(f"REASON={type(exc).__name__}:{exc}")
        print("E6=NOT_RUN")
        print("PROMOTION=PENDING")
        return 2

    evidence = result["evidence"]
    print("ORCHESTRA_E5_CODEX_SCRIBE_READ_ONLY=PASS")
    print(f"HOST={evidence['scope']['host']}")
    print(f"MODEL={evidence['scope']['model']}")
    print(f"COMMAND={evidence['runtime']['command_name']}")
    print(f"SPECIALIST={evidence['runtime']['specialist']}")
    print(f"REQUEST_ID={evidence['runtime']['request_id']}")
    print(f"RECEIPT_ID={evidence['host_receipt']['receipt_id']}")
    print("WORKTREE_UNCHANGED=TRUE")
    print("HOST_BRIDGE_E2E=VERIFIED_FOR_CODEX_READ_ONLY_SCRIBE_FIXTURE")
    print("SUBSTANTIVE_SPECIALIST_EXECUTION_E2E=VERIFIED_FOR_CODEX_READ_ONLY_SCRIBE_FIXTURE")
    print("E6=AUTHORIZED_NOT_RUN_BY_E5_PROOF")
    print("PROMOTION=PENDING")
    print(f"EVIDENCE={result['evidence_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
