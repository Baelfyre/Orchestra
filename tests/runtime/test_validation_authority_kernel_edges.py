from __future__ import annotations

import pytest

import orchestra_runtime.governance_kernel as kernel


def test_machine_precedence_without_any_registered_disposition_fails_closed(monkeypatch):
    candidate = kernel.ArbiterKernelInput(
        project_id="validation-authority",
        unit_id="precedence-empty",
        governance_decisions=(
            kernel.GovernanceDecisionRecord(
                reviewer="arbiter",
                project_context="validation-authority",
                decision="APPROVED",
                reason="fixture",
            ),
        ),
    )
    monkeypatch.setattr(kernel, "transition_precedence", lambda: ())
    with pytest.raises(RuntimeError, match="did not select an Arbiter disposition"):
        kernel.evaluate_arbiter(candidate)
