# @codebase_provenance_JEO
# @codebase_rights_JEO
"""Deterministic cross-governance reconciliation for The Covenant.

The Covenant synthesizes Steward and Governor judgments with system evidence.
It is evidence-only and never creates execution or transition authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


GOVERNANCE_DECISIONS = (
    "APPROVED",
    "ADVISORY_ONLY",
    "REVISION_REQUIRED",
    "BLOCKED",
    "NOT_APPLICABLE",
)
ALIGNMENT_STATES = ("ALIGNED", "CONFLICT", "UNKNOWN", "NOT_APPLICABLE")
COVENANT_DISPOSITIONS = (
    "PASS",
    "RECONCILED_WITH_CONSTRAINTS",
    "REVISION_REQUIRED",
    "WAIT_FOR_EVIDENCE",
    "ESCALATE_HUMAN",
    "BLOCKED",
)
ASSURANCE_RESULTS = ("PASS", "BLOCKED", "NOT_APPLICABLE", "MISSING")


def _text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def _strings(values: Iterable[str], field: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field} must be an iterable of strings")
    result = tuple(_text(value, field) for value in values)
    if len(result) != len(set(result)):
        raise ValueError(f"{field} must not contain duplicates")
    return result


@dataclass(frozen=True, slots=True)
class CovenantBasis:
    project_ref: str
    prime_directive_ref: str
    project_goal_refs: tuple[str, ...]
    critical_flows: tuple[str, ...]
    system_invariants: tuple[str, ...]
    prohibited_outcomes: tuple[str, ...] = ()
    authority_boundaries: tuple[str, ...] = ()
    assurance_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_ref", _text(self.project_ref, "project_ref"))
        object.__setattr__(
            self,
            "prime_directive_ref",
            _text(self.prime_directive_ref, "prime_directive_ref"),
        )
        object.__setattr__(
            self, "project_goal_refs", _strings(self.project_goal_refs, "project_goal_refs")
        )
        object.__setattr__(
            self, "critical_flows", _strings(self.critical_flows, "critical_flows")
        )
        object.__setattr__(
            self,
            "system_invariants",
            _strings(self.system_invariants, "system_invariants"),
        )
        object.__setattr__(
            self,
            "prohibited_outcomes",
            _strings(self.prohibited_outcomes, "prohibited_outcomes"),
        )
        object.__setattr__(
            self,
            "authority_boundaries",
            _strings(self.authority_boundaries, "authority_boundaries"),
        )
        if not self.project_goal_refs:
            raise ValueError("project_goal_refs must not be empty")
        if not isinstance(self.assurance_required, bool):
            raise TypeError("assurance_required must be bool")


@dataclass(frozen=True, slots=True)
class GovernanceJudgment:
    reviewer: str
    decision: str
    prime_directive_alignment: str
    project_goal_alignment: str
    constraints: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    human_review_required: bool = False

    def __post_init__(self) -> None:
        reviewer = _text(self.reviewer, "reviewer").upper()
        if reviewer not in ("STEWARD", "GOVERNOR"):
            raise ValueError("reviewer must be STEWARD or GOVERNOR")
        object.__setattr__(self, "reviewer", reviewer)
        decision = _text(self.decision, "decision").upper()
        if decision not in GOVERNANCE_DECISIONS:
            raise ValueError("unsupported governance decision")
        object.__setattr__(self, "decision", decision)
        for field in ("prime_directive_alignment", "project_goal_alignment"):
            value = _text(getattr(self, field), field).upper()
            if value not in ALIGNMENT_STATES:
                raise ValueError(f"unsupported {field}")
            object.__setattr__(self, field, value)
        object.__setattr__(self, "constraints", _strings(self.constraints, "constraints"))
        object.__setattr__(self, "findings", _strings(self.findings, "findings"))
        object.__setattr__(
            self, "evidence_refs", _strings(self.evidence_refs, "evidence_refs")
        )
        if not isinstance(self.human_review_required, bool):
            raise TypeError("human_review_required must be bool")


@dataclass(frozen=True, slots=True)
class ReconciliationProposal:
    summary: str
    preserves_prime_directive: bool
    preserves_project_goals: bool
    steward_accepts: bool
    governor_accepts: bool
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "summary", _text(self.summary, "summary"))
        object.__setattr__(
            self, "evidence_refs", _strings(self.evidence_refs, "evidence_refs")
        )
        for field in (
            "preserves_prime_directive",
            "preserves_project_goals",
            "steward_accepts",
            "governor_accepts",
        ):
            if not isinstance(getattr(self, field), bool):
                raise TypeError(f"{field} must be bool")

    @property
    def verified(self) -> bool:
        return (
            self.preserves_prime_directive
            and self.preserves_project_goals
            and self.steward_accepts
            and self.governor_accepts
            and bool(self.evidence_refs)
        )


@dataclass(frozen=True, slots=True)
class CovenantDecision:
    disposition: str
    reason_codes: tuple[str, ...]
    constraints: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        if self.disposition not in COVENANT_DISPOSITIONS:
            raise ValueError("unsupported Covenant disposition")


def evaluate_covenant(
    basis: CovenantBasis,
    steward: GovernanceJudgment,
    governor: GovernanceJudgment,
    *,
    assurance_result: str = "MISSING",
    cross_judgment_conflicts: Iterable[str] = (),
    system_contradictions: Iterable[str] = (),
    reconciliation: ReconciliationProposal | None = None,
) -> CovenantDecision:
    """Synthesize governance judgments without overriding their ownership."""

    if steward.reviewer != "STEWARD" or governor.reviewer != "GOVERNOR":
        raise ValueError("Steward and Governor judgments are required")

    assurance = _text(assurance_result, "assurance_result").upper()
    if assurance not in ASSURANCE_RESULTS:
        raise ValueError("unsupported assurance_result")

    conflicts = _strings(cross_judgment_conflicts, "cross_judgment_conflicts")
    contradictions = _strings(system_contradictions, "system_contradictions")
    constraints = tuple(dict.fromkeys((*steward.constraints, *governor.constraints)))
    evidence = tuple(dict.fromkeys((*steward.evidence_refs, *governor.evidence_refs)))

    prime_states = {
        steward.prime_directive_alignment,
        governor.prime_directive_alignment,
    }
    goal_states = {steward.project_goal_alignment, governor.project_goal_alignment}

    if "CONFLICT" in prime_states:
        return CovenantDecision(
            "BLOCKED",
            ("PRIME_DIRECTIVE_CONFLICT",),
            constraints,
            evidence,
            True,
        )

    if steward.human_review_required or governor.human_review_required:
        return CovenantDecision(
            "ESCALATE_HUMAN",
            ("GOVERNANCE_HUMAN_REVIEW_REQUIRED",),
            constraints,
            evidence,
            True,
        )

    if "UNKNOWN" in prime_states or "UNKNOWN" in goal_states:
        return CovenantDecision(
            "WAIT_FOR_EVIDENCE",
            ("GOVERNING_ALIGNMENT_UNKNOWN",),
            constraints,
            evidence,
            False,
        )

    if steward.decision == "BLOCKED" or governor.decision == "BLOCKED":
        return CovenantDecision(
            "BLOCKED",
            ("OWNING_GOVERNANCE_BLOCK",),
            constraints,
            evidence,
            False,
        )

    if basis.assurance_required and assurance == "MISSING":
        return CovenantDecision(
            "WAIT_FOR_EVIDENCE",
            ("REQUIRED_ASSURANCE_MISSING",),
            constraints,
            evidence,
            False,
        )

    if assurance == "BLOCKED":
        return CovenantDecision(
            "BLOCKED",
            ("ASSURANCE_ENGINE_BLOCKED",),
            constraints,
            evidence,
            False,
        )

    if contradictions:
        return CovenantDecision(
            "REVISION_REQUIRED",
            ("SYSTEM_CONTRADICTION",),
            constraints,
            evidence,
            False,
        )

    if "CONFLICT" in goal_states:
        return CovenantDecision(
            "REVISION_REQUIRED",
            ("PROJECT_GOAL_MISALIGNMENT",),
            constraints,
            evidence,
            False,
        )

    if (
        steward.decision == "REVISION_REQUIRED"
        or governor.decision == "REVISION_REQUIRED"
    ):
        return CovenantDecision(
            "REVISION_REQUIRED",
            ("OWNING_GOVERNANCE_REVISION_REQUIRED",),
            constraints,
            evidence,
            False,
        )

    if conflicts:
        if reconciliation is not None and reconciliation.verified:
            reconciled_evidence = tuple(
                dict.fromkeys((*evidence, *reconciliation.evidence_refs))
            )
            return CovenantDecision(
                "RECONCILED_WITH_CONSTRAINTS",
                ("VERIFIED_NARROW_RECONCILIATION",),
                constraints,
                reconciled_evidence,
                False,
            )
        return CovenantDecision(
            "REVISION_REQUIRED",
            ("UNRESOLVED_CROSS_GOVERNANCE_CONFLICT",),
            constraints,
            evidence,
            False,
        )

    return CovenantDecision(
        "PASS",
        ("COHERENT_GOVERNANCE_AND_SYSTEM_EVIDENCE",),
        constraints,
        evidence,
        False,
    )


__all__ = [
    "ALIGNMENT_STATES",
    "ASSURANCE_RESULTS",
    "COVENANT_DISPOSITIONS",
    "CovenantBasis",
    "CovenantDecision",
    "GOVERNANCE_DECISIONS",
    "GovernanceJudgment",
    "ReconciliationProposal",
    "evaluate_covenant",
]
