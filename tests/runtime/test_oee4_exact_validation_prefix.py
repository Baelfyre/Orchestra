from __future__ import annotations

import pytest

from orchestra_runtime.domain.orchestration.execution_efficiency import (
    authorize_validation_stage,
)


def test_oee4_rejects_future_stage_in_completed_history() -> None:
    with pytest.raises(ValueError, match="exact ordered prior stages"):
        authorize_validation_stage(
            "DIRECT_TESTS",
            ("SYNTAX_SCHEMA", "PROTECTED_GATES"),
            candidate_stable=True,
        )


def test_oee4_rejects_reordered_completed_history() -> None:
    with pytest.raises(ValueError, match="exact ordered prior stages"):
        authorize_validation_stage(
            "SUBSYSTEM",
            ("DIRECT_TESTS", "SYNTAX_SCHEMA"),
            candidate_stable=False,
        )
