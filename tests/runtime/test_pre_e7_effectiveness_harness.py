from __future__ import annotations

import json

import pytest

from internal import e5_codex_scribe_live_proof as e5
from internal import e6_codex_ponytail_mutation_proof as e6
from internal.codex_user_model_selection import VALIDATION_MODEL_SELECTION_SOURCE


def _snapshot(*, branch: str = "validation/pre-e7") -> dict[str, object]:
    return {
        "branch": branch,
        "head": "a" * 40,
        "tree": "b" * 40,
        "clean": True,
        "status_sha256": "c" * 64,
    }


def test_e5_current_head_validation_does_not_require_historical_branch():
    e5._validate_before_snapshot(_snapshot(branch="main"))
    e5._validate_before_snapshot(_snapshot(branch=""))


def test_e5_dirty_worktree_is_rejected():
    snapshot = _snapshot()
    snapshot["clean"] = False

    with pytest.raises(e5.E5ProofError, match="clean worktree"):
        e5._validate_before_snapshot(snapshot)


@pytest.mark.parametrize("field", ["head", "tree"])
def test_e5_head_or_tree_drift_is_rejected(field):
    before = _snapshot()
    after = dict(before)
    after[field] = "d" * 40

    with pytest.raises(e5.E5ProofError, match="repository (HEAD|tree) changed"):
        e5._validate_after_snapshot(before, after)


def test_e5_task_markers_validate_exact_revision_values():
    output = json.dumps(
        {
            "non_mutating": True,
            "finding": (
                "E5-SCRIBE-20260829 ALDER-47 "
                "REVISION_DECLARED = 3 REVISION_FOOTER = 4"
            ),
        }
    )

    assert e5._validate_output(output)["non_mutating"] is True


def test_e5_entrypoint_requires_explicit_model():
    with pytest.raises(SystemExit) as exc_info:
        e5.main([])

    assert exc_info.value.code == 2


def test_new_validation_records_explicit_model_input_source():
    assert VALIDATION_MODEL_SELECTION_SOURCE == "EXPLICIT_VALIDATION_INPUT"


def test_e6_entrypoint_requires_explicit_model():
    with pytest.raises(SystemExit) as exc_info:
        e6.main([])

    assert exc_info.value.code == 2


def test_e6_preexisting_sandbox_is_rejected(tmp_path):
    sandbox = tmp_path / "workspace"
    sandbox.mkdir()

    with pytest.raises(e6.E6ProofError, match="already exists"):
        e6._prepare_sandbox(sandbox)
