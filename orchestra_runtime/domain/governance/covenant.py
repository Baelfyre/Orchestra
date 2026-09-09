"""Fail-closed cross-governance synthesis for an exact candidate state."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from ...shared.canonicalization import normalize_git_sha, receipt_digest


COVENANT_SCHEMA_VERSION = "orchestra.covenant.v1"

GOVERNANCE_DECISIONS = (
    "APPROVED",
    "ADVISORY_ONLY",
    "REVISION_REQUIRED",
    "BLOCKED",
    "NOT_APPLICABLE",
)
ALIGNMENT_STATES = ("ALIGNED", "CONFLICT", "UNKNOWN", "NOT_APPLICABLE")
FLOW_ALIGNMENT_STATES = ("ALIGNED", "CONTRADICTIONS", "UNKNOWN", "NOT_APPLICABLE")
OBLIGATION_STATES = ("SATISFIED", "GAPS", "UNKNOWN", "NOT_APPLICABLE")
COVENANT_DISPOSITIONS = (
    "PASS",
    "RECONCILED_WITH_CONSTRAINTS",
    "REVISION_REQUIRED",
    "WAIT_FOR_EVIDENCE",
    "ESCALATE_HUMAN",
    "BLOCKED",
)
ASSURANCE_RESULTS = ("PASS", "BLOCKED", "NOT_APPLICABLE", "MISSING")
SPECIALIST_RESULTS = ("PASS", "BLOCKED", "NOT_APPLICABLE", "MISSING")
SPECIALIST_REVIEWERS = (
    "CLOCKWORK",
    "CIPHER",
    "CHRONICLER",
    "OVERSEER",
    "DAGGER",
    "CLOAK",
)


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(character) < 32 for character in cleaned):
        raise ValueError(f"{field_name} must not contain control characters")
    return cleaned


def _strings(value: Iterable[str], field_name: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(_text(item, f"{field_name} item") for item in value)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be an iterable of strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must contain at least one item")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return items


def _choice(value: str, field_name: str, choices: tuple[str, ...]) -> str:
    normalized = _text(value, field_name).upper()
    if normalized not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return normalized


def _unique(*groups: Iterable[str]) -> tuple[str, ...]:
    values: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            if value not in seen:
                seen.add(value)
                values.append(value)
    return tuple(values)


@dataclass(frozen=True, slots=True)
class CovenantBasis:
    """The immutable project and candidate context a decision is allowed to assess."""

    repository: str
    candidate_sha: str
    tree_sha: str
    basis_revision: str
    project_context_ref: str | None = None
    prime_directive_ref: str = ""
    project_goal_refs: tuple[str, ...] = ()
    critical_flows: tuple[str, ...] = ()
    system_invariants: tuple[str, ...] = ()
    prohibited_outcomes: tuple[str, ...] = ()
    authority_boundaries: tuple[str, ...] = ()
    assurance_required: bool = True
    # Compatibility input for historical PR #868. It is never emitted as the
    # canonical machine field; project_context_ref remains the source of truth.
    project_ref: str | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(
            self,
            "candidate_sha",
            normalize_git_sha(self.candidate_sha, "candidate_sha"),
        )
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "basis_revision", _text(self.basis_revision, "basis_revision"))

        context_ref = self.project_context_ref
        legacy_ref = self.project_ref
        if context_ref is not None:
            context_ref = _text(context_ref, "project_context_ref")
        if legacy_ref is not None:
            legacy_ref = _text(legacy_ref, "project_ref")
        if context_ref and legacy_ref and context_ref != legacy_ref:
            raise ValueError("project_context_ref and project_ref must identify the same context")
        context_ref = context_ref or legacy_ref
        if context_ref is None:
            raise ValueError("project_context_ref is required")
        object.__setattr__(self, "project_context_ref", context_ref)
        object.__setattr__(self, "project_ref", context_ref)

        object.__setattr__(
            self,
            "prime_directive_ref",
            _text(self.prime_directive_ref, "prime_directive_ref"),
        )
        object.__setattr__(
            self,
            "project_goal_refs",
            _strings(self.project_goal_refs, "project_goal_refs", allow_empty=False),
        )
        object.__setattr__(
            self,
            "critical_flows",
            _strings(self.critical_flows, "critical_flows", allow_empty=False),
        )
        object.__setattr__(
            self,
            "system_invariants",
            _strings(self.system_invariants, "system_invariants", allow_empty=False),
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
        if not isinstance(self.assurance_required, bool):
            raise TypeError("assurance_required must be a boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "basis_revision": self.basis_revision,
            "project_context_ref": self.project_context_ref,
            "prime_directive_ref": self.prime_directive_ref,
            "project_goal_refs": list(self.project_goal_refs),
            "critical_flows": list(self.critical_flows),
            "system_invariants": list(self.system_invariants),
            "prohibited_outcomes": list(self.prohibited_outcomes),
            "authority_boundaries": list(self.authority_boundaries),
            "assurance_required": self.assurance_required,
        }

    @property
    def basis_digest(self) -> str:
        return receipt_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class GovernanceJudgment:
    """A single owner judgment, kept separate so synthesis cannot become voting."""

    reviewer: str
    decision: str = "APPROVED"
    prime_directive_alignment: str = "ALIGNED"
    project_goal_alignment: str = "ALIGNED"
    critical_flow_alignment: str = "ALIGNED"
    system_invariant_alignment: str = "ALIGNED"
    protected_obligations: tuple[str, ...] = ()
    obligation_satisfaction: str = "SATISFIED"
    prohibited_outcomes: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    human_review_required: bool = False
    claim_scope: str = "GOVERNANCE"

    def __post_init__(self) -> None:
        object.__setattr__(self, "reviewer", _choice(self.reviewer, "reviewer", ("STEWARD", "GOVERNOR")))
        object.__setattr__(self, "decision", _choice(self.decision, "decision", GOVERNANCE_DECISIONS))
        object.__setattr__(
            self,
            "prime_directive_alignment",
            _choice(self.prime_directive_alignment, "prime_directive_alignment", ALIGNMENT_STATES),
        )
        object.__setattr__(
            self,
            "project_goal_alignment",
            _choice(self.project_goal_alignment, "project_goal_alignment", ALIGNMENT_STATES),
        )
        object.__setattr__(
            self,
            "critical_flow_alignment",
            _choice(self.critical_flow_alignment, "critical_flow_alignment", FLOW_ALIGNMENT_STATES),
        )
        object.__setattr__(
            self,
            "system_invariant_alignment",
            _choice(self.system_invariant_alignment, "system_invariant_alignment", FLOW_ALIGNMENT_STATES),
        )
        object.__setattr__(
            self,
            "protected_obligations",
            _strings(self.protected_obligations, "protected_obligations"),
        )
        object.__setattr__(
            self,
            "obligation_satisfaction",
            _choice(self.obligation_satisfaction, "obligation_satisfaction", OBLIGATION_STATES),
        )
        object.__setattr__(
            self,
            "prohibited_outcomes",
            _strings(self.prohibited_outcomes, "prohibited_outcomes"),
        )
        object.__setattr__(self, "constraints", _strings(self.constraints, "constraints"))
        object.__setattr__(self, "findings", _strings(self.findings, "findings"))
        object.__setattr__(self, "evidence_refs", _strings(self.evidence_refs, "evidence_refs"))
        if not isinstance(self.human_review_required, bool):
            raise TypeError("human_review_required must be a boolean")
        object.__setattr__(self, "claim_scope", _text(self.claim_scope, "claim_scope"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviewer": self.reviewer,
            "decision": self.decision,
            "prime_directive_alignment": self.prime_directive_alignment,
            "project_goal_alignment": self.project_goal_alignment,
            "critical_flow_alignment": self.critical_flow_alignment,
            "system_invariant_alignment": self.system_invariant_alignment,
            "protected_obligations": list(self.protected_obligations),
            "obligation_satisfaction": self.obligation_satisfaction,
            "prohibited_outcomes": list(self.prohibited_outcomes),
            "constraints": list(self.constraints),
            "findings": list(self.findings),
            "evidence_refs": list(self.evidence_refs),
            "human_review_required": self.human_review_required,
            "claim_scope": self.claim_scope,
        }


@dataclass(frozen=True, slots=True)
class SpecialistEvidence:
    """Technical evidence, bound to the same candidate and tree as the basis."""

    reviewer: str
    result: str
    claim_scope: str
    evidence_refs: tuple[str, ...]
    candidate_sha: str
    tree_sha: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "reviewer", _choice(self.reviewer, "reviewer", SPECIALIST_REVIEWERS))
        object.__setattr__(self, "result", _choice(self.result, "result", SPECIALIST_RESULTS))
        object.__setattr__(self, "claim_scope", _text(self.claim_scope, "claim_scope"))
        object.__setattr__(self, "evidence_refs", _strings(self.evidence_refs, "evidence_refs"))
        object.__setattr__(
            self,
            "candidate_sha",
            normalize_git_sha(self.candidate_sha, "candidate_sha"),
        )
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "limitations", _strings(self.limitations, "limitations"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviewer": self.reviewer,
            "result": self.result,
            "claim_scope": self.claim_scope,
            "evidence_refs": list(self.evidence_refs),
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationProposal:
    """An evidence-backed narrower design accepted by both governance owners."""

    summary: str
    preserves_prime_directive: bool
    preserves_project_goals: bool
    steward_accepts: bool
    governor_accepts: bool
    evidence_refs: tuple[str, ...]
    constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "summary", _text(self.summary, "summary"))
        for field_name in (
            "preserves_prime_directive",
            "preserves_project_goals",
            "steward_accepts",
            "governor_accepts",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a boolean")
        object.__setattr__(
            self,
            "evidence_refs",
            _strings(self.evidence_refs, "evidence_refs", allow_empty=False),
        )
        object.__setattr__(self, "constraints", _strings(self.constraints, "constraints"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "preserves_prime_directive": self.preserves_prime_directive,
            "preserves_project_goals": self.preserves_project_goals,
            "steward_accepts": self.steward_accepts,
            "governor_accepts": self.governor_accepts,
            "evidence_refs": list(self.evidence_refs),
            "constraints": list(self.constraints),
        }


@dataclass(frozen=True, slots=True)
class CovenantDecision:
    """Evidence-only synthesis. It grants no transition, merge, or runtime authority."""

    basis: CovenantBasis
    disposition: str
    reason_codes: tuple[str, ...]
    constraints: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    human_review_required: bool

    def __post_init__(self) -> None:
        if not isinstance(self.basis, CovenantBasis):
            raise TypeError("basis must be a CovenantBasis")
        object.__setattr__(
            self,
            "disposition",
            _choice(self.disposition, "disposition", COVENANT_DISPOSITIONS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _strings(self.reason_codes, "reason_codes", allow_empty=False),
        )
        object.__setattr__(self, "constraints", _strings(self.constraints, "constraints"))
        object.__setattr__(
            self,
            "evidence_refs",
            _strings(self.evidence_refs, "evidence_refs", allow_empty=False),
        )
        if not isinstance(self.human_review_required, bool):
            raise TypeError("human_review_required must be a boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": COVENANT_SCHEMA_VERSION,
            "basis": self.basis.to_dict(),
            "disposition": self.disposition,
            "reason_codes": list(self.reason_codes),
            "constraints": list(self.constraints),
            "evidence_refs": list(self.evidence_refs),
            "human_review_required": self.human_review_required,
            "authority_granted": False,
        }

    @property
    def decision_digest(self) -> str:
        return receipt_digest(self.to_dict())

    @property
    def basis_digest(self) -> str:
        return self.basis.basis_digest


def _basis_evidence(basis: CovenantBasis) -> tuple[str, ...]:
    return _unique(
        (basis.project_context_ref,),
        (basis.prime_directive_ref,),
        basis.project_goal_refs,
        basis.critical_flows,
        basis.system_invariants,
        basis.prohibited_outcomes,
        basis.authority_boundaries,
    )


def _make_decision(
    basis: CovenantBasis,
    disposition: str,
    reason_codes: Iterable[str],
    *,
    constraints: Iterable[str] = (),
    evidence_groups: Iterable[Iterable[str]] = (),
    human_review_required: bool = False,
) -> CovenantDecision:
    evidence = [_basis_evidence(basis)]
    evidence.extend(evidence_groups)
    return CovenantDecision(
        basis=basis,
        disposition=disposition,
        reason_codes=_strings(reason_codes, "reason_codes"),
        constraints=_strings(constraints, "constraints"),
        evidence_refs=_unique(*evidence),
        human_review_required=human_review_required,
    )


def _invalid_input_decision(
    basis: CovenantBasis,
    reason_code: str,
    *,
    evidence_groups: Iterable[Iterable[str]] = (),
) -> CovenantDecision:
    return _make_decision(
        basis,
        "WAIT_FOR_EVIDENCE",
        (reason_code,),
        evidence_groups=evidence_groups,
    )


def _claim_scope_is_valid(value: bool | str) -> bool | None:
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    if normalized in {"VERIFIED", "SUFFICIENT", "ALIGNED", "COMPLETE", "PASS"}:
        return True
    if normalized in {"UNKNOWN", "MISSING", "INSUFFICIENT", "UNVERIFIED", "CONFLICT"}:
        return False
    return None


def _claim_scope_is_unknown(value: str) -> bool:
    return value.strip().upper() in {
        "UNKNOWN",
        "MISSING",
        "INSUFFICIENT",
        "UNVERIFIED",
        "CONFLICT",
    }


def evaluate_covenant(
    basis: CovenantBasis,
    steward: GovernanceJudgment | None = None,
    governor: GovernanceJudgment | None = None,
    *,
    assurance_result: str = "PASS",
    cross_judgment_conflicts: Iterable[str] = (),
    cross_specialist_contradictions: Iterable[str] = (),
    system_contradictions: Iterable[str] = (),
    reconciliation: ReconciliationProposal | None = None,
    current_candidate_sha: str | None = None,
    current_tree_sha: str | None = None,
    claim_to_evidence_scope: bool | str = True,
    assurance_evidence_durable: bool = True,
    assurance_evidence_retrievable: bool | None = None,
    assurance_evidence_refs: Iterable[str] = (),
    specialist_evidence: Iterable[SpecialistEvidence] = (),
    prohibited_outcome_avoidance: str = "AVOIDED",
) -> CovenantDecision:
    """Synthesize two owner judgments without voting or creating authority.

    Omitting current identity means the immutable basis is the asserted
    evaluation identity. Callers that have a separate live readback must pass
    both current SHA values; a partial or mismatched readback fails closed.
    """

    if not isinstance(basis, CovenantBasis):
        raise TypeError("basis must be a CovenantBasis")

    if (current_candidate_sha is None) != (current_tree_sha is None):
        return _invalid_input_decision(basis, "STATE_IDENTITY_INCOMPLETE")
    if current_candidate_sha is not None and current_tree_sha is not None:
        try:
            current_candidate = normalize_git_sha(current_candidate_sha, "current_candidate_sha")
            current_tree = normalize_git_sha(current_tree_sha, "current_tree_sha")
        except (TypeError, ValueError):
            return _invalid_input_decision(basis, "INVALID_STATE_IDENTITY")
        if current_candidate != basis.candidate_sha:
            return _invalid_input_decision(basis, "STALE_CANDIDATE_SHA")
        if current_tree != basis.tree_sha:
            return _invalid_input_decision(basis, "STALE_TREE_SHA")

    if not isinstance(steward, GovernanceJudgment) or not isinstance(governor, GovernanceJudgment):
        missing = []
        if steward is None:
            missing.append("STEWARD_JUDGMENT_MISSING")
        if governor is None:
            missing.append("GOVERNOR_JUDGMENT_MISSING")
        if not missing:
            missing.append("INVALID_GOVERNANCE_JUDGMENT")
        return _make_decision(basis, "WAIT_FOR_EVIDENCE", tuple(missing))
    if steward.reviewer != "STEWARD" or governor.reviewer != "GOVERNOR":
        return _invalid_input_decision(basis, "WRONG_GOVERNANCE_REVIEWER")
    if not steward.evidence_refs or not governor.evidence_refs:
        return _invalid_input_decision(basis, "GOVERNANCE_EVIDENCE_MISSING")

    try:
        assurance = _choice(assurance_result, "assurance_result", ASSURANCE_RESULTS)
        conflicts = _strings(cross_judgment_conflicts, "cross_judgment_conflicts")
        specialist_contradictions = _strings(
            cross_specialist_contradictions,
            "cross_specialist_contradictions",
        )
        contradictions = _unique(
            _strings(system_contradictions, "system_contradictions"),
            specialist_contradictions,
        )
        assurance_refs = _strings(assurance_evidence_refs, "assurance_evidence_refs")
        specialists = tuple(specialist_evidence)
        if not isinstance(assurance_evidence_durable, bool):
            raise TypeError("assurance_evidence_durable must be a boolean")
        if assurance_evidence_retrievable is not None and not isinstance(assurance_evidence_retrievable, bool):
            raise TypeError("assurance_evidence_retrievable must be a boolean")
        claim_scope_valid = _claim_scope_is_valid(claim_to_evidence_scope)
        if claim_scope_valid is None:
            raise ValueError("claim_to_evidence_scope is unknown")
        prohibited_state = _choice(
            prohibited_outcome_avoidance,
            "prohibited_outcome_avoidance",
            ("AVOIDED", "PRESENT", "UNKNOWN"),
        )
    except (TypeError, ValueError):
        return _invalid_input_decision(basis, "MALFORMED_COVENANT_INPUT")

    if reconciliation is not None and not isinstance(reconciliation, ReconciliationProposal):
        return _invalid_input_decision(basis, "INVALID_RECONCILIATION")

    specialist_refs: list[str] = []
    for specialist in specialists:
        if not isinstance(specialist, SpecialistEvidence):
            return _invalid_input_decision(basis, "INVALID_SPECIALIST_EVIDENCE")
        specialist_refs.extend(specialist.evidence_refs)
        if specialist.candidate_sha != basis.candidate_sha or specialist.tree_sha != basis.tree_sha:
            return _invalid_input_decision(
                basis,
                "STALE_SPECIALIST_EVIDENCE",
                evidence_groups=(specialist.evidence_refs,),
            )
        if not specialist.evidence_refs:
            return _invalid_input_decision(basis, "SPECIALIST_EVIDENCE_MISSING")

    judgment_refs = steward.evidence_refs + governor.evidence_refs
    evidence_groups = (judgment_refs, tuple(specialist_refs), assurance_refs)
    owner_human_review = steward.human_review_required or governor.human_review_required

    if any(
        _claim_scope_is_unknown(judgment.claim_scope)
        for judgment in (steward, governor)
    ) or any(_claim_scope_is_unknown(specialist.claim_scope) for specialist in specialists):
        return _make_decision(
            basis,
            "WAIT_FOR_EVIDENCE",
            ("CLAIM_TO_EVIDENCE_SCOPE_UNVERIFIED",),
            evidence_groups=evidence_groups,
        )

    # Constitutional conflict is not a negotiable reviewer disagreement.
    if "CONFLICT" in (steward.prime_directive_alignment, governor.prime_directive_alignment):
        return _make_decision(
            basis,
            "BLOCKED",
            ("PRIME_DIRECTIVE_CONFLICT",),
            evidence_groups=evidence_groups,
            human_review_required=True,
        )

    # An owning governance block remains a block even when technical evidence
    # or PRAI is green.
    if steward.decision == "BLOCKED" or governor.decision == "BLOCKED":
        return _make_decision(
            basis,
            "BLOCKED",
            ("GOVERNANCE_OWNER_BLOCKED",),
            evidence_groups=evidence_groups,
            human_review_required=owner_human_review,
        )
    if governor.obligation_satisfaction == "GAPS":
        return _make_decision(
            basis,
            "BLOCKED",
            ("PROTECTED_OBLIGATION_UNSATISFIED",),
            evidence_groups=evidence_groups,
            human_review_required=owner_human_review,
        )

    if owner_human_review:
        return _make_decision(
            basis,
            "ESCALATE_HUMAN",
            ("HUMAN_REVIEW_REQUIRED",),
            evidence_groups=evidence_groups,
            human_review_required=True,
        )

    # Evidence and state uncertainty outrank delivery convenience and a green
    # local test run.
    if assurance == "MISSING" or (basis.assurance_required and assurance == "NOT_APPLICABLE"):
        return _make_decision(
            basis,
            "WAIT_FOR_EVIDENCE",
            ("ASSURANCE_EVIDENCE_MISSING",),
            evidence_groups=evidence_groups,
        )
    if not assurance_evidence_durable or assurance_evidence_retrievable is False:
        return _make_decision(
            basis,
            "WAIT_FOR_EVIDENCE",
            ("ASSURANCE_EVIDENCE_NOT_DURABLE",),
            evidence_groups=evidence_groups,
        )
    if not claim_scope_valid:
        return _make_decision(
            basis,
            "WAIT_FOR_EVIDENCE",
            ("CLAIM_TO_EVIDENCE_SCOPE_UNVERIFIED",),
            evidence_groups=evidence_groups,
        )
    if assurance == "BLOCKED":
        return _make_decision(
            basis,
            "BLOCKED",
            ("ASSURANCE_BLOCKED",),
            evidence_groups=evidence_groups,
        )

    if prohibited_state == "PRESENT":
        return _make_decision(
            basis,
            "BLOCKED",
            ("PROHIBITED_OUTCOME_PRESENT",),
            evidence_groups=evidence_groups,
        )
    if prohibited_state == "UNKNOWN":
        return _make_decision(
            basis,
            "WAIT_FOR_EVIDENCE",
            ("PROHIBITED_OUTCOME_AVOIDANCE_UNKNOWN",),
            evidence_groups=evidence_groups,
        )

    if "UNKNOWN" in (
        steward.prime_directive_alignment,
        governor.prime_directive_alignment,
        steward.project_goal_alignment,
        governor.project_goal_alignment,
        steward.critical_flow_alignment,
        governor.critical_flow_alignment,
        steward.system_invariant_alignment,
        governor.system_invariant_alignment,
        governor.obligation_satisfaction,
    ):
        return _make_decision(
            basis,
            "WAIT_FOR_EVIDENCE",
            ("GOVERNANCE_ALIGNMENT_UNKNOWN",),
            evidence_groups=evidence_groups,
        )
    if steward.decision in {"ADVISORY_ONLY", "NOT_APPLICABLE"} or governor.decision == "ADVISORY_ONLY":
        return _make_decision(
            basis,
            "WAIT_FOR_EVIDENCE",
            ("GOVERNANCE_DECISION_NOT_FINAL",),
            evidence_groups=evidence_groups,
        )
    if governor.decision == "NOT_APPLICABLE" and governor.obligation_satisfaction != "NOT_APPLICABLE":
        return _make_decision(
            basis,
            "WAIT_FOR_EVIDENCE",
            ("GOVERNOR_APPLICABILITY_UNVERIFIED",),
            evidence_groups=evidence_groups,
        )
    if any(
        state == "NOT_APPLICABLE"
        for state in (
            steward.critical_flow_alignment,
            governor.critical_flow_alignment,
            steward.system_invariant_alignment,
            governor.system_invariant_alignment,
        )
    ):
        return _make_decision(
            basis,
            "WAIT_FOR_EVIDENCE",
            ("REQUIRED_SYSTEM_COVERAGE_NOT_APPLICABLE",),
            evidence_groups=evidence_groups,
        )

    if "CONFLICT" in (steward.project_goal_alignment, governor.project_goal_alignment):
        return _make_decision(
            basis,
            "REVISION_REQUIRED",
            ("PROJECT_GOAL_CONFLICT",),
            evidence_groups=evidence_groups,
        )
    if "CONTRADICTIONS" in (
        steward.critical_flow_alignment,
        governor.critical_flow_alignment,
        steward.system_invariant_alignment,
        governor.system_invariant_alignment,
    ):
        return _make_decision(
            basis,
            "REVISION_REQUIRED",
            ("SYSTEM_COHERENCE_CONTRADICTION",),
            evidence_groups=evidence_groups,
        )
    if steward.decision == "REVISION_REQUIRED" or governor.decision == "REVISION_REQUIRED":
        if not conflicts:
            return _make_decision(
                basis,
                "REVISION_REQUIRED",
                ("GOVERNANCE_REVISION_REQUIRED",),
                evidence_groups=evidence_groups,
            )

    # Specialist evidence can constrain a candidate, but it cannot authorize
    # one or override an owning governance decision.
    for specialist in specialists:
        if specialist.result == "MISSING":
            return _make_decision(
                basis,
                "WAIT_FOR_EVIDENCE",
                ("SPECIALIST_EVIDENCE_MISSING",),
                evidence_groups=evidence_groups,
            )
        if specialist.result == "BLOCKED":
            return _make_decision(
                basis,
                "REVISION_REQUIRED",
                ("SPECIALIST_CONSTRAINT_UNSATISFIED",),
                evidence_groups=evidence_groups,
            )

    # A concrete system contradiction is stronger than a PRAI PASS. It cannot
    # be reconciled with a reviewer-count or confidence calculation.
    if contradictions:
        return _make_decision(
            basis,
            "REVISION_REQUIRED",
            ("SYSTEM_CONTRADICTION",),
            evidence_groups=(*evidence_groups, contradictions),
        )

    if conflicts:
        if reconciliation is None:
            return _make_decision(
                basis,
                "REVISION_REQUIRED",
                ("UNRESOLVED_CROSS_GOVERNANCE_CONFLICT",),
                evidence_groups=(*evidence_groups, conflicts),
            )
        if not (
            reconciliation.preserves_prime_directive
            and reconciliation.preserves_project_goals
            and reconciliation.steward_accepts
            and reconciliation.governor_accepts
        ):
            return _make_decision(
                basis,
                "REVISION_REQUIRED",
                ("RECONCILIATION_INVALID",),
                constraints=reconciliation.constraints,
                evidence_groups=(*evidence_groups, reconciliation.evidence_refs),
            )
        return _make_decision(
            basis,
            "RECONCILED_WITH_CONSTRAINTS",
            ("RECONCILIATION_ACCEPTED",),
            constraints=reconciliation.constraints,
            evidence_groups=(*evidence_groups, reconciliation.evidence_refs, conflicts),
        )
    if reconciliation is not None:
        return _make_decision(
            basis,
            "REVISION_REQUIRED",
            ("UNEXPECTED_RECONCILIATION",),
            constraints=reconciliation.constraints,
            evidence_groups=(*evidence_groups, reconciliation.evidence_refs),
        )

    return _make_decision(
        basis,
        "PASS",
        ("COHERENT_GOVERNANCE_AND_SYSTEM_EVIDENCE",),
        evidence_groups=evidence_groups,
    )


__all__ = [
    "ALIGNMENT_STATES",
    "ASSURANCE_RESULTS",
    "COVENANT_DISPOSITIONS",
    "COVENANT_SCHEMA_VERSION",
    "CovenantBasis",
    "CovenantDecision",
    "FLOW_ALIGNMENT_STATES",
    "GOVERNANCE_DECISIONS",
    "GovernanceJudgment",
    "OBLIGATION_STATES",
    "ReconciliationProposal",
    "SPECIALIST_RESULTS",
    "SPECIALIST_REVIEWERS",
    "SpecialistEvidence",
    "evaluate_covenant",
]
