from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from orchestra_runtime.domain.adaptive import prai


REPOSITORY = "Baelfyre/Orchestra"
SOURCE_REF = "5454e643745cb1b1ab16b233dd6ad36d08bcb9f2"
CANDIDATE_SHA = "a" * 40
TREE_SHA = "b" * 40
WORK_ITEM = "prai-cli-behavior"
FRESHNESS = "2026-09-09T00:00:00Z"
VERSION = "orchestra-prai-plan-20260908-v1"
PATHS = (
    "tests/behavior/test_prai.py",
)


def unit() -> prai.PraiWorkUnit:
    roles = prai.BASELINE_REVIEWERS
    refs = tuple(f"evidence://{role.lower()}" for role in roles)
    receipts = tuple(
        prai.PraiReviewReceipt(
            receipt_id=f"{role.lower()}-cli",
            role=role,
            reviewer=f"{role.lower()}-reviewer",
            result="PASS",
            repository=REPOSITORY,
            source_ref=SOURCE_REF,
            candidate_sha=CANDIDATE_SHA,
            tree_sha=TREE_SHA,
            work_item_ref=WORK_ITEM,
            audit_depth="STANDARD",
            evidence_refs=(ref,),
            audited_paths=PATHS,
            evidence_layer="PROVENANCE",
            evidence_scope="UNIT",
            covered_risks=(),
            covered_invariants=(),
            freshness_ref=FRESHNESS,
            version_ref=VERSION,
            provenance="AUTHORITATIVE",
            independent=True,
            producer="independent-review",
            validator=f"{role.lower()}-validator",
            claim_scope="UNIT",
            limitations=("fixture",),
            examined_changed_code=True,
        )
        for role, ref in zip(roles, refs)
    )
    return prai.PraiWorkUnit(
        work_item_ref=WORK_ITEM,
        repository=REPOSITORY,
        source_ref=SOURCE_REF,
        candidate_sha=CANDIDATE_SHA,
        tree_sha=TREE_SHA,
        freshness_ref=FRESHNESS,
        version_ref=VERSION,
        changed_paths=PATHS,
        implementer="ponytail",
        logical_impact="LOW",
        security_impact="LOW",
        audit_depth="STANDARD",
        required_reviewers=roles,
        required_additional_assurance=prai.BASELINE_ASSURANCE,
        logical_result="PASS",
        security_result="PASS",
        evidence_refs=refs,
        limitations=("fixture",),
        overseer_sufficiency=True,
        arbiter_disposition="AUTO_CONTINUE",
        review_receipts=receipts,
        green_tests=True,
    )


def run_validator(
    root: Path, work_path: Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "validation" / "validate_prai.py"),
            "--work-unit",
            str(work_path),
            "--repository",
            REPOSITORY,
            "--source-ref",
            SOURCE_REF,
            "--candidate-sha",
            CANDIDATE_SHA,
            "--tree-sha",
            TREE_SHA,
            "--work-item-ref",
            WORK_ITEM,
            "--freshness-ref",
            FRESHNESS,
            "--version-ref",
            VERSION,
            *extra,
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_passes_and_writes_decision() -> None:
    root = Path(__file__).resolve().parents[2]
    with TemporaryDirectory() as directory:
        directory_path = Path(directory)
        work_path = directory_path / "work.json"
        output_path = directory_path / "decision.json"
        work_path.write_text(json.dumps(unit().to_dict()), encoding="utf-8")
        result = run_validator(root, work_path, "--output", str(output_path))
        assert result.returncode == 0, result.stderr
        assert "PRAI_RESULT=PASS" in result.stdout
        decision = json.loads(output_path.read_text(encoding="utf-8"))
        assert decision["result"] == "PASS"
        assert decision["authority_expansion"] is False


def test_cli_blocks_stale_candidate() -> None:
    root = Path(__file__).resolve().parents[2]
    with TemporaryDirectory() as directory:
        work_path = Path(directory) / "work.json"
        work_path.write_text(json.dumps(unit().to_dict()), encoding="utf-8")
        result = run_validator(root, work_path, "--candidate-sha", "c" * 40)
        assert result.returncode == 1
        assert "PRAI_RESULT=BLOCKED" in result.stdout
        assert "FAIL_STALE_CANDIDATE" in result.stdout


def test_cli_blocks_stale_version() -> None:
    root = Path(__file__).resolve().parents[2]
    with TemporaryDirectory() as directory:
        work_path = Path(directory) / "work.json"
        work_path.write_text(json.dumps(unit().to_dict()), encoding="utf-8")
        result = run_validator(root, work_path, "--version-ref", "orchestra-prai-plan-20260907-v1")
        assert result.returncode == 1
        assert "PRAI_RESULT=BLOCKED" in result.stdout
        assert prai.FAIL_STALE_VERSION in result.stdout


def test_cli_reads_configured_schema() -> None:
    root = Path(__file__).resolve().parents[2]
    with TemporaryDirectory() as directory:
        directory_path = Path(directory)
        work_path = directory_path / "work.json"
        schema_path = directory_path / "schema.json"
        work_path.write_text(json.dumps(unit().to_dict()), encoding="utf-8")
        schema_path.write_text(json.dumps({"type": "not-a-schema-type"}), encoding="utf-8")
        result = run_validator(root, work_path, "--schema", str(schema_path))
        assert result.returncode == 2
        assert "PRAI_RESULT=INVALID" in result.stderr
        assert prai.FAIL_SCHEMA_RUNTIME_PARITY in result.stderr


def test_cli_fails_closed_for_malformed_work_unit() -> None:
    root = Path(__file__).resolve().parents[2]
    with TemporaryDirectory() as directory:
        work_path = Path(directory) / "work.json"
        work_path.write_text("{}", encoding="utf-8")
        result = run_validator(root, work_path)
        assert result.returncode == 2
        assert "PRAI_RESULT=INVALID" in result.stderr
