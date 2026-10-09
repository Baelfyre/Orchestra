#!/usr/bin/env python3
"""Behavior checks for the AQ-5 CLI boundary."""

from __future__ import annotations

import json
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.domain.adaptive import (
    EvidenceSlot,
    build_assurance_manifest,
    build_evidence_receipt,
    build_routing_receipt,
    profile_risk,
)

spec = importlib.util.spec_from_file_location("validate_qa_compliance", ROOT / "scripts" / "validation" / "validate_qa_compliance.py")
validation = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(validation)


SCRIPT = ROOT / "scripts" / "validation" / "validate_qa_compliance.py"
SOURCE = "orchestra:2fb6a0a8b1d4a207742c9daaa1f5cbf0e87305de"
CANDIDATE = "a" * 40
TREE = "b" * 40
GENERATED = "2026-09-08T14:00:00+08:00"
OBSERVED = "2026-09-08T14:01:00+08:00"


def _sample():
    profile = profile_risk(
        development_mode="SPEC_FIRST",
        material_behavior="AQ5 CLI behavior validation",
        authority_boundary=("IMPLEMENTATION",),
        changed_domains=(),
        changed_paths=(),
        quality_dimensions=(),
        risk_characteristics=(),
        invariants=(),
        protected_gates=(),
    )
    routing = build_routing_receipt(profile, source_identities=(SOURCE,))
    slot = EvidenceSlot(
        slot_id="gate-independent-qa",
        assurance_class="INDEPENDENT_QA",
        required_layer="CONTRACT",
        required_scope="CONTRACT",
        required_validator="overseer",
        required_source_truth="OBSERVED",
        required_provenance="AUTHORITATIVE",
        covered_risks=(),
        covered_invariants=(),
        independence_required=True,
    )
    manifest = build_assurance_manifest(
        profile=profile,
        receipt=routing,
        manifest_id="manifest-aq5-behavior",
        repository="Baelfyre/Orchestra",
        source_ref=SOURCE,
        candidate_sha=CANDIDATE,
        tree_sha=TREE,
        work_item_ref="AQ5",
        change_class="AQ5_IMPLEMENTATION",
        completion_target="AQ5_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW",
        required_evidence_slots=(slot,),
        selected_specialists=tuple(routing.selected_specialists),
        required_assurance=tuple(routing.required_assurance),
        generated_at=GENERATED,
    )
    receipt = build_evidence_receipt(
        manifest,
        receipt_id="receipt-gate-independent-qa",
        gate_id=slot.slot_id,
        gate_type="TEST",
        command_or_workflow="python -B -m pytest",
        result="PASS",
        observed_at=OBSERVED,
        producer="ponytail",
        exit_code=0,
        logical_identity="logical-gate-independent-qa",
    )
    return manifest, receipt


def _run_cli_checks():
    manifest, receipt = _sample()
    original_load = validation._load

    def fake_load(path: Path):
        return manifest.to_dict() if path.name == "manifest.json" else [receipt.to_dict()]

    validation._load = fake_load
    common = [
        "--manifest",
        "manifest.json",
        "--receipts",
        "receipts.json",
        "--repository",
        "Baelfyre/Orchestra",
        "--source-ref",
        SOURCE,
        "--candidate-sha",
        CANDIDATE,
        "--tree-sha",
        TREE,
        "--evaluated-at",
        OBSERVED,
    ]
    try:
        passed_output = io.StringIO()
        with contextlib.redirect_stdout(passed_output):
            passed = validation.main(
                common
                + [
                    "--changed-path",
                    "orchestra_runtime/domain/adaptive/qa_compliance.py",
                    "--declared-path",
                    "orchestra_runtime/domain/adaptive/qa_compliance.py",
                ]
            )
        assert passed == 0
        assert "QA_COMPLIANCE=PASS" in passed_output.getvalue()

        failed_output = io.StringIO()
        with contextlib.redirect_stdout(failed_output):
            failed = validation.main(
                common + ["--changed-path", "orchestra_runtime/domain/adaptive/qa_compliance.py"]
            )
        assert failed == 1
        assert "AQ5-F9_CHANGED_PATH_OMITTED" in failed_output.getvalue()

        missing_identity_stderr = io.StringIO()
        missing_identity = [
            item
            for index, item in enumerate(common)
            if index not in (6, 7)
        ]
        try:
            with contextlib.redirect_stderr(missing_identity_stderr):
                validation.main(missing_identity)
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("CLI accepted missing --source-ref identity")
        assert "--source-ref" in missing_identity_stderr.getvalue()
    finally:
        validation._load = original_load


def test_cli_pass_and_fail():
    _run_cli_checks()


def main() -> int:
    test_cli_pass_and_fail()
    help_result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0, help_result.stderr
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
