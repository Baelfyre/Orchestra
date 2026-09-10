"""Deterministic, evidence-only assurance packs for AQ-8 high-risk behavior."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from ...shared.canonicalization import normalize_git_sha, normalize_timestamp, receipt_digest
from ..governance.covenant import (
    CovenantBasis,
    CovenantDecision,
    GovernanceJudgment,
    ReconciliationProposal,
    SpecialistEvidence,
    evaluate_covenant,
)


AQ8_CONTRACT_SCHEMA_VERSION = "orchestra.aq8-high-risk-assurance-packs.v1"
AQ8_DECISION_SCHEMA_VERSION = "orchestra.aq8-high-risk-assurance-decision.v1"
AQ8_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
AQ8_TRANSITION_OWNER = "ARBITER"
PACKS = ("SECURITY", "PROVENANCE", "CONCURRENCY", "STATE_MACHINE", "EVIDENCE_INTEGRITY")
DISPOSITIONS = ("PASS", "REVISION_REQUIRED", "WAIT_FOR_EVIDENCE", "BLOCKED", "ESCALATE_HUMAN")
EVIDENCE_RESULTS = ("PASS", "FAIL", "BLOCKED", "WAIT_FOR_EVIDENCE")
SUPPORTED_EVIDENCE_TYPES = (
    "CONTROLLED_FIXTURE", "UNIT_TEST", "INTEGRATION_TEST", "STATIC_ANALYSIS",
    "PRAI", "COVENANT", "GOVERNANCE", "WORKFLOW",
)

REQUIRED_SECURITY_CASES = (
    "SECURITY_UNKNOWN_CREDENTIAL", "SECURITY_INACTIVE_PRINCIPAL",
    "SECURITY_MISSING_GRANT", "SECURITY_GUESSED_OBJECT_ID",
    "SECURITY_CROSS_TENANT_ID", "SECURITY_CROSS_WORKSPACE_ID",
    "SECURITY_PRIVILEGE_ESCALATION",
    "SECURITY_TENANT_ADMIN_GLOBAL_AUTHORITY_SEPARATION",
    "SECURITY_REVOCATION_BEFORE_REQUEST", "SECURITY_REVOCATION_DURING_REQUEST",
    "SECURITY_STALE_AUTHORIZATION_STATE",
)
REQUIRED_PROVENANCE_CASES = (
    "PROVENANCE_CALLER_SUPPLIED_AUTHORITATIVE_VERSION",
    "PROVENANCE_FORGED_SOURCE_SHA", "PROVENANCE_REPORT_HASH_MISMATCH",
    "PROVENANCE_STALE_EVIDENCE", "PROVENANCE_WRONG_TENANT_WORKSPACE_EVIDENCE",
    "PROVENANCE_WRONG_CANDIDATE_EVIDENCE", "PROVENANCE_DUPLICATE_PROVENANCE_ID",
)
REQUIRED_CONCURRENCY_CASES = (
    "CONCURRENCY_SAME_ROW_RACE", "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE",
    "CONCURRENCY_LOST_UPDATE", "CONCURRENCY_DUPLICATE_SUBMIT",
    "CONCURRENCY_RETRY_AFTER_TIMEOUT", "CONCURRENCY_IDEMPOTENCY_COLLISION",
    "CONCURRENCY_PRIVILEGE_REVOCATION_DURING_OPERATION",
    "CONCURRENCY_PARTIAL_WRITE_ROLLBACK", "CONCURRENCY_MULTI_PROCESS_SERVICE_INSTANCE",
)
REQUIRED_STATE_MACHINE_CASES = (
    "STATE_MACHINE_LEGAL_TRANSITION", "STATE_MACHINE_ILLEGAL_TRANSITION",
    "STATE_MACHINE_TERMINAL_MUTATION", "STATE_MACHINE_STALE_TRANSITION",
    "STATE_MACHINE_DUPLICATE_TRANSITION",
    "STATE_MACHINE_FAILED_VALIDATION_BEFORE_TRANSITION",
    "STATE_MACHINE_ROLLBACK_SEMANTICS",
)
REQUIRED_EVIDENCE_INTEGRITY_CASES = (
    "EVIDENCE_SELF_ASSERTED_PASS", "EVIDENCE_NONZERO_EXIT_LABELED_PASS",
    "EVIDENCE_MISMATCHED_CANDIDATE_HASH", "EVIDENCE_MISSING_VALIDATOR_IDENTITY",
    "EVIDENCE_UNSUPPORTED_EVIDENCE_TYPE", "EVIDENCE_STALE_WORKFLOW_RUN",
)
REQUIRED_CASES = {
    "SECURITY": REQUIRED_SECURITY_CASES,
    "PROVENANCE": REQUIRED_PROVENANCE_CASES,
    "CONCURRENCY": REQUIRED_CONCURRENCY_CASES,
    "STATE_MACHINE": REQUIRED_STATE_MACHINE_CASES,
    "EVIDENCE_INTEGRITY": REQUIRED_EVIDENCE_INTEGRITY_CASES,
}
CASE_PACK = {case_id: pack for pack, cases in REQUIRED_CASES.items() for case_id in cases}

AQ8_REQUIRED_COVENANT_SCENARIOS = tuple(f"COV-{index:02d}" for index in range(1, 19))
AQ8_AQ7_REGRESSION_ANCHORS = (
    "CONCURRENT_LAST_ADMIN_AGGREGATE_INVARIANT",
    "PRIVILEGE_MUTATION_BEFORE_AUDIT_DURABILITY",
    "MISSING_DURABLE_ASSURANCE_EVIDENCE",
)
AQ8_ADVERSARIAL_PERMUTATIONS = (
    "MALFORMED_STATE", "STALE_CANDIDATE_STATE", "STALE_TREE_STATE",
    "MISSING_STATE_IDENTITY", "MISSING_EVIDENCE", "DUPLICATE_EVIDENCE_ID",
    "CALLER_ASSERTED_EVIDENCE", "NONZERO_EXIT_PASS", "UNKNOWN_CASE", "UNKNOWN_PACK",
    "SEQUENTIAL_CONCURRENCY_APPROXIMATION", "INVALID_RECONCILIATION",
    "PRAI_PASS_SYSTEM_CONTRADICTION", "AUTHORITY_EXPANSION_ATTEMPT",
)
AQ8_CONTEXT_FIELDS = (
    "repository", "source_ref", "candidate_sha", "tree_sha", "work_item_ref",
    "basis_revision", "project_context_ref", "prime_directive_ref",
    "project_goal_refs", "critical_flows", "system_invariants",
    "prohibited_outcomes", "authority_boundaries", "observed_at", "workflow_run_id",
)
AQ8_EVIDENCE_FIELDS = (
    "evidence_id", "evidence_type", "repository", "source_ref", "candidate_sha",
    "tree_sha", "validator_identity", "observed_at", "result", "exit_code",
    "workflow_run_id", "freshness_ref", "durable", "retrievable", "independent",
    "producer_role", "evidence_digest",
)
AQ8_OBSERVATION_FIELDS = ("facts", "evidence", "controlled_fixture")
AQ8_CASE_RESULT_FIELDS = (
    "schema_version", "pack", "case_id", "disposition", "compliant",
    "reason_codes", "evidence_ids", "controlled_fixture", "repository",
    "candidate_sha", "tree_sha", "authority_granted",
)
AQ8_PACK_RESULT_FIELDS = (
    "schema_version", "pack", "result", "compliant", "failure_codes",
    "evidence_ids", "cases", "controlled_case_count", "organic_case_count",
    "authority_granted",
)
AQ8_DECISION_FIELDS = (
    "schema_version", "repository", "source_ref", "candidate_sha", "tree_sha",
    "work_item_ref", "result", "compliant", "failure_codes", "packs",
    "transition_owner", "authority_granted", "decision_digest",
)
AQ8_FAILURE_CODES = (
    "AQ8_CURRENT_IDENTITY_REQUIRED", "AQ8_UNKNOWN_PACK", "AQ8_UNKNOWN_CASE",
    "AQ8_CASE_OBSERVATION_MISSING", "AQ8_INVALID_OBSERVATION",
    "AQ8_REQUIRED_FACT_MISSING", "AQ8_CONTROL_VIOLATION", "AQ8_UNKNOWN_STATE",
    "AQ8_CONTROLLED_INTERLEAVING_REQUIRED", "AQ8_AGGREGATE_PROOF_REQUIRED",
    "AQ8_EVIDENCE_MISSING", "AQ8_EVIDENCE_DUPLICATE_ID",
    "AQ8_EVIDENCE_REPOSITORY_MISMATCH", "AQ8_EVIDENCE_SOURCE_MISMATCH",
    "AQ8_EVIDENCE_CANDIDATE_MISMATCH", "AQ8_EVIDENCE_TREE_MISMATCH",
    "AQ8_EVIDENCE_VALIDATOR_MISSING", "AQ8_EVIDENCE_TYPE_UNSUPPORTED", "AQ8_EVIDENCE_RESULT_NOT_PASS",
    "AQ8_EVIDENCE_STALE_WORKFLOW_RUN", "AQ8_EVIDENCE_NOT_DURABLE",
    "AQ8_EVIDENCE_NOT_RETRIEVABLE", "AQ8_EVIDENCE_PASS_NONZERO_EXIT",
    "AQ8_EVIDENCE_CALLER_ASSERTED", "AQ8_EVIDENCE_NOT_INDEPENDENT",
    "AQ8_EVIDENCE_INVALID_DIGEST", "AQ8_PACK_STATE_MISMATCH", "AQ8_PACK_NOT_PASS",
    "AQ8_AUTHORITY_EXPANSION", "AQ8_SCHEMA_RUNTIME_DRIFT",
)


def _text(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = value.strip()
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    value = _text(value, field_name, allow_empty=True)
    return value or None


def _strings(value: Iterable[str], field_name: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings")
    try:
        result = tuple(_text(item, f"{field_name} item") for item in value)
    except TypeError as exc:
        raise TypeError(f"{field_name} must be an iterable of strings") from exc
    if not allow_empty and not result:
        raise ValueError(f"{field_name} must contain at least one item")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return result


def _choice(value: Any, choices: tuple[str, ...], field_name: str) -> str:
    value = _text(value, field_name).upper()
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return value


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class AssuranceContext:
    """Exact repository and governance state bound to every AQ-8 decision."""

    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    work_item_ref: str
    basis_revision: str
    project_context_ref: str
    prime_directive_ref: str
    project_goal_refs: tuple[str, ...]
    critical_flows: tuple[str, ...]
    system_invariants: tuple[str, ...]
    prohibited_outcomes: tuple[str, ...]
    authority_boundaries: tuple[str, ...]
    observed_at: str
    workflow_run_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        for name in ("work_item_ref", "basis_revision", "project_context_ref", "prime_directive_ref", "workflow_run_id"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        for name, required in (
            ("project_goal_refs", True), ("critical_flows", True), ("system_invariants", True),
            ("prohibited_outcomes", False), ("authority_boundaries", False),
        ):
            object.__setattr__(self, name, _strings(getattr(self, name), name, allow_empty=not required))
        object.__setattr__(self, "observed_at", normalize_timestamp(self.observed_at, "observed_at"))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AssuranceContext":
        if not isinstance(value, Mapping):
            raise TypeError("context must be a mapping")
        unknown = set(value) - set(AQ8_CONTEXT_FIELDS)
        missing = set(AQ8_CONTEXT_FIELDS) - set(value)
        if unknown:
            raise ValueError("unknown context fields: " + ", ".join(sorted(unknown)))
        if missing:
            raise ValueError("missing context fields: " + ", ".join(sorted(missing)))
        return cls(**dict(value))

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository, "source_ref": self.source_ref,
            "candidate_sha": self.candidate_sha, "tree_sha": self.tree_sha,
            "work_item_ref": self.work_item_ref, "basis_revision": self.basis_revision,
            "project_context_ref": self.project_context_ref,
            "prime_directive_ref": self.prime_directive_ref,
            "project_goal_refs": list(self.project_goal_refs),
            "critical_flows": list(self.critical_flows),
            "system_invariants": list(self.system_invariants),
            "prohibited_outcomes": list(self.prohibited_outcomes),
            "authority_boundaries": list(self.authority_boundaries),
            "observed_at": self.observed_at, "workflow_run_id": self.workflow_run_id,
        }

    def to_covenant_basis(self) -> CovenantBasis:
        return CovenantBasis(
            repository=self.repository, candidate_sha=self.candidate_sha,
            tree_sha=self.tree_sha, basis_revision=self.basis_revision,
            project_context_ref=self.project_context_ref,
            prime_directive_ref=self.prime_directive_ref,
            project_goal_refs=self.project_goal_refs, critical_flows=self.critical_flows,
            system_invariants=self.system_invariants,
            prohibited_outcomes=self.prohibited_outcomes,
            authority_boundaries=self.authority_boundaries,
        )


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """A durable test/validator receipt, never an authority grant."""

    evidence_id: str
    evidence_type: str
    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    validator_identity: str | None
    observed_at: str
    result: str
    exit_code: int | None
    workflow_run_id: str | None
    freshness_ref: str | None
    durable: bool
    retrievable: bool
    independent: bool
    producer_role: str
    evidence_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "evidence_type", _text(self.evidence_type, "evidence_type", allow_empty=True).upper())
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "source_ref", _text(self.source_ref, "source_ref"))
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "validator_identity", _optional_text(self.validator_identity, "validator_identity"))
        object.__setattr__(self, "observed_at", normalize_timestamp(self.observed_at, "observed_at"))
        object.__setattr__(self, "result", _choice(self.result, EVIDENCE_RESULTS, "result"))
        if self.exit_code is not None and (isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int)):
            raise TypeError("exit_code must be an integer or null")
        object.__setattr__(self, "workflow_run_id", _optional_text(self.workflow_run_id, "workflow_run_id"))
        object.__setattr__(self, "freshness_ref", _optional_text(self.freshness_ref, "freshness_ref"))
        object.__setattr__(self, "producer_role", _text(self.producer_role, "producer_role").upper())
        for name in ("durable", "retrievable", "independent"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean")
        expected = receipt_digest(self.to_dict(include_digest=False))
        if self.evidence_digest is None:
            object.__setattr__(self, "evidence_digest", expected)
        elif self.evidence_digest != expected:
            raise ValueError("evidence_digest does not match canonical evidence")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvidenceRecord":
        if not isinstance(value, Mapping):
            raise TypeError("evidence must be a mapping")
        unknown = set(value) - set(AQ8_EVIDENCE_FIELDS)
        required = set(AQ8_EVIDENCE_FIELDS) - {
            "validator_identity", "exit_code", "workflow_run_id", "freshness_ref", "evidence_digest",
        }
        missing = required - set(value)
        if unknown:
            raise ValueError("unknown evidence fields: " + ", ".join(sorted(unknown)))
        if missing:
            raise ValueError("missing evidence fields: " + ", ".join(sorted(missing)))
        return cls(**dict(value))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        value = {
            "evidence_id": self.evidence_id, "evidence_type": self.evidence_type,
            "repository": self.repository, "source_ref": self.source_ref,
            "candidate_sha": self.candidate_sha, "tree_sha": self.tree_sha,
            "validator_identity": self.validator_identity, "observed_at": self.observed_at,
            "result": self.result, "exit_code": self.exit_code,
            "workflow_run_id": self.workflow_run_id, "freshness_ref": self.freshness_ref,
            "durable": self.durable, "retrievable": self.retrievable,
            "independent": self.independent, "producer_role": self.producer_role,
        }
        if include_digest:
            value["evidence_digest"] = self.evidence_digest
        return value


@dataclass(frozen=True, slots=True)
class HighRiskCaseObservation:
    facts: Mapping[str, Any]
    evidence: tuple[EvidenceRecord, ...]
    controlled_fixture: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.facts, Mapping):
            raise TypeError("facts must be a mapping")
        object.__setattr__(self, "facts", dict(self.facts))
        if isinstance(self.evidence, (str, bytes)):
            raise TypeError("evidence must be an iterable")
        evidence = tuple(
            item if isinstance(item, EvidenceRecord) else EvidenceRecord.from_mapping(item)
            for item in self.evidence
        )
        object.__setattr__(self, "evidence", evidence)
        if not isinstance(self.controlled_fixture, bool):
            raise TypeError("controlled_fixture must be a boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "HighRiskCaseObservation":
        if not isinstance(value, Mapping):
            raise TypeError("observation must be a mapping")
        unknown = set(value) - set(AQ8_OBSERVATION_FIELDS)
        if unknown:
            raise ValueError("unknown observation fields: " + ", ".join(sorted(unknown)))
        if "facts" not in value:
            raise ValueError("observation facts are required")
        return cls(value["facts"], tuple(value.get("evidence", ())), value.get("controlled_fixture", True))

    def to_dict(self) -> dict[str, Any]:
        return {
            "facts": dict(self.facts),
            "evidence": [item.to_dict() for item in self.evidence],
            "controlled_fixture": self.controlled_fixture,
        }


@dataclass(frozen=True, slots=True)
class HighRiskCaseResult:
    pack: str
    case_id: str
    disposition: str
    compliant: bool
    reason_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    controlled_fixture: bool
    repository: str
    candidate_sha: str
    tree_sha: str
    authority_granted: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "pack", _choice(self.pack, PACKS, "pack"))
        case_id = _text(self.case_id, "case_id").upper()
        if CASE_PACK.get(case_id) != self.pack:
            raise ValueError("case_id is not declared by pack")
        object.__setattr__(self, "case_id", case_id)
        object.__setattr__(self, "disposition", _choice(self.disposition, DISPOSITIONS, "disposition"))
        object.__setattr__(self, "reason_codes", _strings(self.reason_codes, "reason_codes"))
        object.__setattr__(self, "evidence_ids", _strings(self.evidence_ids, "evidence_ids"))
        if not isinstance(self.compliant, bool) or self.compliant != (self.disposition == "PASS"):
            raise ValueError("compliant must reflect the PASS disposition")
        if not isinstance(self.controlled_fixture, bool):
            raise TypeError("controlled_fixture must be a boolean")
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        if self.authority_granted is not False:
            raise ValueError("AQ8 results cannot grant authority")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": AQ8_DECISION_SCHEMA_VERSION, "pack": self.pack,
            "case_id": self.case_id, "disposition": self.disposition,
            "compliant": self.compliant, "reason_codes": list(self.reason_codes),
            "evidence_ids": list(self.evidence_ids),
            "controlled_fixture": self.controlled_fixture,
            "repository": self.repository, "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha, "authority_granted": False,
        }


@dataclass(frozen=True, slots=True)
class HighRiskPackResult:
    pack: str
    result: str
    compliant: bool
    failure_codes: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    cases: tuple[HighRiskCaseResult, ...]
    authority_granted: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "pack", _choice(self.pack, PACKS, "pack"))
        object.__setattr__(self, "result", _choice(self.result, DISPOSITIONS, "result"))
        if not isinstance(self.compliant, bool) or self.compliant != (self.result == "PASS"):
            raise ValueError("compliant must reflect the PASS result")
        object.__setattr__(self, "failure_codes", _strings(self.failure_codes, "failure_codes"))
        object.__setattr__(self, "evidence_ids", _strings(self.evidence_ids, "evidence_ids"))
        object.__setattr__(self, "cases", tuple(self.cases))
        if any(item.pack != self.pack for item in self.cases):
            raise ValueError("pack result contains a case from another pack")
        if self.authority_granted is not False:
            raise ValueError("AQ8 pack results cannot grant authority")

    @property
    def controlled_case_count(self) -> int:
        return sum(item.controlled_fixture for item in self.cases)

    @property
    def organic_case_count(self) -> int:
        return len(self.cases) - self.controlled_case_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": AQ8_DECISION_SCHEMA_VERSION, "pack": self.pack,
            "result": self.result, "compliant": self.compliant,
            "failure_codes": list(self.failure_codes), "evidence_ids": list(self.evidence_ids),
            "cases": [item.to_dict() for item in self.cases],
            "controlled_case_count": self.controlled_case_count,
            "organic_case_count": self.organic_case_count, "authority_granted": False,
        }


@dataclass(frozen=True, slots=True)
class HighRiskAssuranceDecision:
    context: AssuranceContext
    result: str
    compliant: bool
    failure_codes: tuple[str, ...]
    packs: tuple[HighRiskPackResult, ...]
    authority_granted: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.context, AssuranceContext):
            raise TypeError("context must be an AssuranceContext")
        object.__setattr__(self, "result", _choice(self.result, DISPOSITIONS, "result"))
        if not isinstance(self.compliant, bool) or self.compliant != (self.result == "PASS"):
            raise ValueError("compliant must reflect the PASS result")
        object.__setattr__(self, "failure_codes", _strings(self.failure_codes, "failure_codes"))
        object.__setattr__(self, "packs", tuple(self.packs))
        if tuple(item.pack for item in self.packs) != PACKS:
            raise ValueError("decision must contain every pack in canonical order")
        if self.authority_granted is not False:
            raise ValueError("AQ8 decisions cannot grant authority")

    @property
    def transition_owner(self) -> str:
        return AQ8_TRANSITION_OWNER

    @property
    def decision_digest(self) -> str:
        return receipt_digest(self.to_dict(include_digest=False))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        value = {
            "schema_version": AQ8_DECISION_SCHEMA_VERSION,
            "repository": self.context.repository, "source_ref": self.context.source_ref,
            "candidate_sha": self.context.candidate_sha, "tree_sha": self.context.tree_sha,
            "work_item_ref": self.context.work_item_ref, "result": self.result,
            "compliant": self.compliant, "failure_codes": list(self.failure_codes),
            "packs": [item.to_dict() for item in self.packs],
            "transition_owner": AQ8_TRANSITION_OWNER, "authority_granted": False,
        }
        if include_digest:
            value["decision_digest"] = self.decision_digest
        return value


@dataclass(frozen=True, slots=True)
class StewardSystemIntentJudgment:
    candidate_sha: str
    tree_sha: str
    decision: str
    prime_directive_alignment: str
    project_goal_alignment: str
    critical_flow_alignment: str
    system_invariant_alignment: str
    scope_complete: bool
    evidence_refs: tuple[str, ...]
    constraints: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "decision", _choice(self.decision, ("APPROVED", "ADVISORY_ONLY", "REVISION_REQUIRED", "BLOCKED"), "decision"))
        object.__setattr__(self, "prime_directive_alignment", _choice(self.prime_directive_alignment, ("ALIGNED", "CONFLICT", "UNKNOWN"), "prime_directive_alignment"))
        for name in ("project_goal_alignment", "critical_flow_alignment", "system_invariant_alignment"):
            object.__setattr__(self, name, _choice(getattr(self, name), ("ALIGNED", "CONFLICT", "UNKNOWN", "CONTRADICTIONS"), name))
        if not isinstance(self.scope_complete, bool):
            raise TypeError("scope_complete must be a boolean")
        object.__setattr__(self, "evidence_refs", _strings(self.evidence_refs, "evidence_refs", allow_empty=False))
        object.__setattr__(self, "constraints", _strings(self.constraints, "constraints"))
        object.__setattr__(self, "findings", _strings(self.findings, "findings"))

    def to_governance_judgment(self) -> GovernanceJudgment:
        decision = self.decision
        if not self.scope_complete and decision == "APPROVED":
            decision = "REVISION_REQUIRED"
        return GovernanceJudgment(
            reviewer="STEWARD", decision=decision,
            prime_directive_alignment=self.prime_directive_alignment,
            project_goal_alignment=self.project_goal_alignment,
            critical_flow_alignment=self.critical_flow_alignment,
            system_invariant_alignment=self.system_invariant_alignment,
            constraints=self.constraints, findings=self.findings,
            evidence_refs=self.evidence_refs, claim_scope="AQ8_STEWARD_SYSTEM_INTENT",
        )


@dataclass(frozen=True, slots=True)
class GovernorProtectedObligationJudgment:
    candidate_sha: str
    tree_sha: str
    decision: str
    prime_directive_alignment: str
    project_goal_alignment: str
    critical_flow_alignment: str
    system_invariant_alignment: str
    obligation_satisfaction: str
    protected_obligations: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    human_review_required: bool = False
    constraints: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "decision", _choice(self.decision, ("APPROVED", "ADVISORY_ONLY", "REVISION_REQUIRED", "BLOCKED", "NOT_APPLICABLE"), "decision"))
        object.__setattr__(self, "prime_directive_alignment", _choice(self.prime_directive_alignment, ("ALIGNED", "CONFLICT", "UNKNOWN"), "prime_directive_alignment"))
        for name in ("project_goal_alignment", "critical_flow_alignment", "system_invariant_alignment"):
            object.__setattr__(self, name, _choice(getattr(self, name), ("ALIGNED", "CONFLICT", "UNKNOWN", "CONTRADICTIONS"), name))
        object.__setattr__(self, "obligation_satisfaction", _choice(self.obligation_satisfaction, ("SATISFIED", "GAPS", "UNKNOWN", "NOT_APPLICABLE"), "obligation_satisfaction"))
        object.__setattr__(self, "protected_obligations", _strings(self.protected_obligations, "protected_obligations"))
        object.__setattr__(self, "evidence_refs", _strings(self.evidence_refs, "evidence_refs", allow_empty=False))
        if not isinstance(self.human_review_required, bool):
            raise TypeError("human_review_required must be a boolean")
        object.__setattr__(self, "constraints", _strings(self.constraints, "constraints"))
        object.__setattr__(self, "findings", _strings(self.findings, "findings"))

    def to_governance_judgment(self) -> GovernanceJudgment:
        return GovernanceJudgment(
            reviewer="GOVERNOR", decision=self.decision,
            prime_directive_alignment=self.prime_directive_alignment,
            project_goal_alignment=self.project_goal_alignment,
            critical_flow_alignment=self.critical_flow_alignment,
            system_invariant_alignment=self.system_invariant_alignment,
            protected_obligations=self.protected_obligations,
            obligation_satisfaction=self.obligation_satisfaction,
            constraints=self.constraints, findings=self.findings,
            evidence_refs=self.evidence_refs, human_review_required=self.human_review_required,
            claim_scope="AQ8_GOVERNOR_PROTECTED_OBLIGATION",
        )


def _add_unique(values: list[str], code: str) -> None:
    if code not in values:
        values.append(code)


def validate_evidence_record(context: AssuranceContext, evidence: EvidenceRecord) -> tuple[str, ...]:
    if not isinstance(context, AssuranceContext) or not isinstance(evidence, EvidenceRecord):
        return ("AQ8_INVALID_OBSERVATION",)
    failures: list[str] = []
    checks = (
        (evidence.repository != context.repository, "AQ8_EVIDENCE_REPOSITORY_MISMATCH"),
        (evidence.source_ref != context.source_ref, "AQ8_EVIDENCE_SOURCE_MISMATCH"),
        (evidence.candidate_sha != context.candidate_sha, "AQ8_EVIDENCE_CANDIDATE_MISMATCH"),
        (evidence.tree_sha != context.tree_sha, "AQ8_EVIDENCE_TREE_MISMATCH"),
        (not evidence.validator_identity, "AQ8_EVIDENCE_VALIDATOR_MISSING"),
        (evidence.evidence_type not in SUPPORTED_EVIDENCE_TYPES, "AQ8_EVIDENCE_TYPE_UNSUPPORTED"),
        (evidence.result != "PASS", "AQ8_EVIDENCE_RESULT_NOT_PASS"),
        (
            evidence.workflow_run_id != context.workflow_run_id
            or evidence.freshness_ref != context.workflow_run_id,
            "AQ8_EVIDENCE_STALE_WORKFLOW_RUN",
        ),
        (not evidence.durable, "AQ8_EVIDENCE_NOT_DURABLE"),
        (not evidence.retrievable, "AQ8_EVIDENCE_NOT_RETRIEVABLE"),
        (evidence.result == "PASS" and evidence.exit_code != 0, "AQ8_EVIDENCE_PASS_NONZERO_EXIT"),
        (evidence.producer_role in {"CALLER", "CLIENT", "REQUESTER", "AUTHOR", "CONSUMER"}, "AQ8_EVIDENCE_CALLER_ASSERTED"),
        (not evidence.independent, "AQ8_EVIDENCE_NOT_INDEPENDENT"),
        (evidence.evidence_digest != receipt_digest(evidence.to_dict(include_digest=False)), "AQ8_EVIDENCE_INVALID_DIGEST"),
    )
    for condition, code in checks:
        if condition:
            _add_unique(failures, code)
    return tuple(failures)


def _validate_evidence_bundle(context: AssuranceContext, evidence: tuple[EvidenceRecord, ...]) -> tuple[str, ...]:
    if not evidence:
        return ("AQ8_EVIDENCE_MISSING",)
    failures: list[str] = []
    ids = [item.evidence_id for item in evidence]
    if len(ids) != len(set(ids)):
        _add_unique(failures, "AQ8_EVIDENCE_DUPLICATE_ID")
    for item in evidence:
        for code in validate_evidence_record(context, item):
            _add_unique(failures, code)
    return tuple(failures)


_CASE_REQUIREMENTS: dict[str, Mapping[str, Any]] = {
    "SECURITY_UNKNOWN_CREDENTIAL": {"control_verified": True, "credential_accepted": False, "decision": "DENY", "enumeration_safe": True},
    "SECURITY_INACTIVE_PRINCIPAL": {"control_verified": True, "principal_accepted": False, "decision": "DENY"},
    "SECURITY_MISSING_GRANT": {"control_verified": True, "grant_accepted": False, "decision": "DENY"},
    "SECURITY_GUESSED_OBJECT_ID": {"control_verified": True, "object_enumerated": False, "decision": "DENY"},
    "SECURITY_CROSS_TENANT_ID": {"control_verified": True, "tenant_scope_match": False, "object_enumerated": False, "decision": "DENY"},
    "SECURITY_CROSS_WORKSPACE_ID": {"control_verified": True, "workspace_scope_match": False, "object_enumerated": False, "decision": "DENY"},
    "SECURITY_PRIVILEGE_ESCALATION": {"control_verified": True, "escalation_accepted": False, "decision": "DENY"},
    "SECURITY_TENANT_ADMIN_GLOBAL_AUTHORITY_SEPARATION": {"control_verified": True, "global_authority_mutated": False, "tenant_authority_isolated": True},
    "SECURITY_REVOCATION_BEFORE_REQUEST": {"control_verified": True, "revocation_observed": True, "decision": "DENY"},
    "SECURITY_REVOCATION_DURING_REQUEST": {"control_verified": True, "revocation_rechecked": True, "commit_after_revocation": False, "decision": "DENY"},
    "SECURITY_STALE_AUTHORIZATION_STATE": {"control_verified": True, "authorization_refreshed": True, "stale_state_accepted": False, "decision": "DENY"},
    "PROVENANCE_CALLER_SUPPLIED_AUTHORITATIVE_VERSION": {"defect_detected": True, "authoritative_version_source": "REPOSITORY", "decision": "REJECT"},
    "PROVENANCE_FORGED_SOURCE_SHA": {"defect_detected": True, "source_sha_verified": False, "decision": "REJECT"},
    "PROVENANCE_REPORT_HASH_MISMATCH": {"defect_detected": True, "report_hash_matches": False, "decision": "REJECT"},
    "PROVENANCE_STALE_EVIDENCE": {"defect_detected": True, "evidence_fresh": False, "decision": "REJECT"},
    "PROVENANCE_WRONG_TENANT_WORKSPACE_EVIDENCE": {"defect_detected": True, "tenant_workspace_match": False, "decision": "REJECT"},
    "PROVENANCE_WRONG_CANDIDATE_EVIDENCE": {"defect_detected": True, "candidate_binding_match": False, "decision": "REJECT"},
    "PROVENANCE_DUPLICATE_PROVENANCE_ID": {"defect_detected": True, "duplicate_provenance_rejected": True, "decision": "REJECT"},
    "CONCURRENCY_SAME_ROW_RACE": {"controlled_interleaving_proof": True, "row_version_checked": True, "lost_update": False, "decision": "REJECT"},
    "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE": {"controlled_interleaving_proof": True, "aggregate_concurrency_proof": True, "aggregate_invariant_preserved": True, "row_versions_only": False},
    "CONCURRENCY_LOST_UPDATE": {"controlled_interleaving_proof": True, "lost_update_prevented": True, "decision": "REJECT"},
    "CONCURRENCY_DUPLICATE_SUBMIT": {"controlled_interleaving_proof": True, "idempotency_enforced": True, "logical_effect_count": 1},
    "CONCURRENCY_RETRY_AFTER_TIMEOUT": {"controlled_interleaving_proof": True, "retry_reconciled": True, "logical_effect_count": 1},
    "CONCURRENCY_IDEMPOTENCY_COLLISION": {"controlled_interleaving_proof": True, "collision_rejected": True, "logical_effect_count": 1},
    "CONCURRENCY_PRIVILEGE_REVOCATION_DURING_OPERATION": {"controlled_interleaving_proof": True, "authorization_rechecked_at_commit": True, "commit_after_revocation": False, "decision": "REJECT"},
    "CONCURRENCY_PARTIAL_WRITE_ROLLBACK": {"controlled_interleaving_proof": True, "rollback_complete": True, "partial_write_visible": False},
    "CONCURRENCY_MULTI_PROCESS_SERVICE_INSTANCE": {"controlled_interleaving_proof": True, "process_count": 2, "service_instance_count": 2, "shared_invariant_guard": True},
    "STATE_MACHINE_LEGAL_TRANSITION": {"transition_allowed": True, "validation_before_transition": True, "transition_applied": True, "decision": "APPLY"},
    "STATE_MACHINE_ILLEGAL_TRANSITION": {"transition_allowed": False, "transition_applied": False, "decision": "REJECT"},
    "STATE_MACHINE_TERMINAL_MUTATION": {"terminal_mutation_attempt": True, "transition_applied": False, "decision": "REJECT"},
    "STATE_MACHINE_STALE_TRANSITION": {"stale_transition": True, "transition_applied": False, "decision": "REJECT"},
    "STATE_MACHINE_DUPLICATE_TRANSITION": {"duplicate_transition": True, "duplicate_effect": False, "decision": "REJECT"},
    "STATE_MACHINE_FAILED_VALIDATION_BEFORE_TRANSITION": {"validation_before_transition": False, "transition_applied": False, "decision": "REJECT"},
    "STATE_MACHINE_ROLLBACK_SEMANTICS": {"rollback_complete": True, "partial_state_visible": False},
    "EVIDENCE_SELF_ASSERTED_PASS": {"defect_detected": True, "self_asserted_rejected": True, "decision": "REJECT"},
    "EVIDENCE_NONZERO_EXIT_LABELED_PASS": {"defect_detected": True, "nonzero_exit_rejected": True, "decision": "REJECT"},
    "EVIDENCE_MISMATCHED_CANDIDATE_HASH": {"defect_detected": True, "candidate_mismatch_rejected": True, "decision": "REJECT"},
    "EVIDENCE_MISSING_VALIDATOR_IDENTITY": {"defect_detected": True, "missing_validator_rejected": True, "decision": "REJECT"},
    "EVIDENCE_UNSUPPORTED_EVIDENCE_TYPE": {"defect_detected": True, "unsupported_type_rejected": True, "decision": "REJECT"},
    "EVIDENCE_STALE_WORKFLOW_RUN": {"defect_detected": True, "stale_workflow_rejected": True, "decision": "REJECT"},
}


def _fact_failures(case_id: str, facts: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    state = facts.get("state")
    decision = facts.get("decision")
    if isinstance(state, str) and state.upper() in {"UNKNOWN", "MALFORMED"}:
        return ((), ("AQ8_UNKNOWN_STATE",))
    if isinstance(decision, str) and decision.upper() == "UNKNOWN":
        return ((), ("AQ8_UNKNOWN_STATE",))
    missing: list[str] = []
    violations: list[str] = []
    for field_name, expected in _CASE_REQUIREMENTS[case_id].items():
        if field_name not in facts or facts[field_name] is None:
            missing.append(field_name)
        else:
            actual = facts[field_name]
            if isinstance(expected, str):
                actual = actual.upper() if isinstance(actual, str) else actual
            if actual != expected:
                violations.append(field_name)
    return tuple(missing), tuple(violations)


def _result(context: AssuranceContext, pack: str, case_id: str, disposition: str, reason_codes: Iterable[str], evidence: tuple[EvidenceRecord, ...], controlled_fixture: bool) -> HighRiskCaseResult:
    return HighRiskCaseResult(
        pack=pack, case_id=case_id, disposition=disposition,
        compliant=disposition == "PASS", reason_codes=_unique(reason_codes),
        evidence_ids=_unique(item.evidence_id for item in evidence),
        controlled_fixture=controlled_fixture, repository=context.repository,
        candidate_sha=context.candidate_sha, tree_sha=context.tree_sha,
    )


def _evaluate_facts_case(context: AssuranceContext, pack: str, case_id: str, observation: HighRiskCaseObservation) -> HighRiskCaseResult:
    evidence_failures = _validate_evidence_bundle(context, observation.evidence)
    if evidence_failures:
        return _result(context, pack, case_id, "WAIT_FOR_EVIDENCE", evidence_failures, observation.evidence, observation.controlled_fixture)
    if pack == "CONCURRENCY":
        if not observation.controlled_fixture:
            return _result(context, pack, case_id, "WAIT_FOR_EVIDENCE", ("AQ8_CONTROLLED_INTERLEAVING_REQUIRED",), observation.evidence, False)
        trace = observation.facts.get("interleaving_trace")
        if not isinstance(trace, (tuple, list)) or len(trace) < 2 or not any(
            isinstance(item, str) and item.upper().startswith(("SYNC:", "BARRIER:")) for item in trace
        ) or observation.facts.get("sequential_approximation") is True:
            return _result(context, pack, case_id, "WAIT_FOR_EVIDENCE", ("AQ8_CONTROLLED_INTERLEAVING_REQUIRED",), observation.evidence, True)
    missing, violations = _fact_failures(case_id, observation.facts)
    if "AQ8_UNKNOWN_STATE" in violations:
        return _result(context, pack, case_id, "WAIT_FOR_EVIDENCE", ("AQ8_UNKNOWN_STATE",), observation.evidence, observation.controlled_fixture)
    if missing:
        return _result(context, pack, case_id, "WAIT_FOR_EVIDENCE", ("AQ8_REQUIRED_FACT_MISSING",), observation.evidence, observation.controlled_fixture)
    if violations:
        codes = ["AQ8_CONTROL_VIOLATION"]
        if case_id == "CONCURRENCY_DIFFERENT_ROW_SHARED_AGGREGATE" and "aggregate_concurrency_proof" in violations:
            codes.append("AQ8_AGGREGATE_PROOF_REQUIRED")
        return _result(context, pack, case_id, "REVISION_REQUIRED", codes, observation.evidence, observation.controlled_fixture)
    return _result(context, pack, case_id, "PASS", (), observation.evidence, observation.controlled_fixture)


def _validate_case_id(case_id: str, pack: str) -> str:
    normalized = _text(case_id, "case_id").upper()
    if CASE_PACK.get(normalized) != pack:
        raise ValueError("AQ8_UNKNOWN_CASE")
    return normalized


def evaluate_security_case(context: AssuranceContext, case_id: str, observation: HighRiskCaseObservation) -> HighRiskCaseResult:
    return _evaluate_facts_case(context, "SECURITY", _validate_case_id(case_id, "SECURITY"), observation)


def evaluate_provenance_case(context: AssuranceContext, case_id: str, observation: HighRiskCaseObservation) -> HighRiskCaseResult:
    return _evaluate_facts_case(context, "PROVENANCE", _validate_case_id(case_id, "PROVENANCE"), observation)


def evaluate_concurrency_case(context: AssuranceContext, case_id: str, observation: HighRiskCaseObservation) -> HighRiskCaseResult:
    return _evaluate_facts_case(context, "CONCURRENCY", _validate_case_id(case_id, "CONCURRENCY"), observation)


def evaluate_state_machine_case(context: AssuranceContext, case_id: str, observation: HighRiskCaseObservation) -> HighRiskCaseResult:
    return _evaluate_facts_case(context, "STATE_MACHINE", _validate_case_id(case_id, "STATE_MACHINE"), observation)


def evaluate_evidence_integrity_case(context: AssuranceContext, case_id: str, observation: HighRiskCaseObservation) -> HighRiskCaseResult:
    return _evaluate_facts_case(context, "EVIDENCE_INTEGRITY", _validate_case_id(case_id, "EVIDENCE_INTEGRITY"), observation)


def evaluate_case(context: AssuranceContext, pack: str, case_id: str, observation: HighRiskCaseObservation) -> HighRiskCaseResult:
    normalized_pack = _choice(pack, PACKS, "pack")
    if normalized_pack == "SECURITY":
        return evaluate_security_case(context, case_id, observation)
    if normalized_pack == "PROVENANCE":
        return evaluate_provenance_case(context, case_id, observation)
    if normalized_pack == "CONCURRENCY":
        return evaluate_concurrency_case(context, case_id, observation)
    if normalized_pack == "STATE_MACHINE":
        return evaluate_state_machine_case(context, case_id, observation)
    return evaluate_evidence_integrity_case(context, case_id, observation)


def _aggregate_disposition(values: Iterable[str]) -> str:
    observed = set(values)
    for value in ("BLOCKED", "ESCALATE_HUMAN", "WAIT_FOR_EVIDENCE", "REVISION_REQUIRED", "PASS"):
        if value in observed:
            return value
    raise ValueError("AQ8_CURRENT_IDENTITY_REQUIRED")


def run_high_risk_pack(context: AssuranceContext, pack: str, observations: Mapping[str, HighRiskCaseObservation | Mapping[str, Any]]) -> HighRiskPackResult:
    normalized_pack = _choice(pack, PACKS, "pack")
    if not isinstance(observations, Mapping):
        raise TypeError("observations must be a mapping")
    parsed: dict[str, HighRiskCaseObservation] = {}
    failures: list[str] = []
    for raw_case_id, raw_observation in observations.items():
        case_id = _text(raw_case_id, "case_id").upper()
        if CASE_PACK.get(case_id) != normalized_pack:
            _add_unique(failures, "AQ8_UNKNOWN_CASE")
            continue
        try:
            parsed[case_id] = raw_observation if isinstance(raw_observation, HighRiskCaseObservation) else HighRiskCaseObservation.from_mapping(raw_observation)
        except (TypeError, ValueError):
            parsed[case_id] = HighRiskCaseObservation(facts={}, evidence=(), controlled_fixture=True)
            _add_unique(failures, "AQ8_INVALID_OBSERVATION")
    results = []
    for case_id in REQUIRED_CASES[normalized_pack]:
        observation = parsed.get(case_id)
        if observation is None:
            result = _result(context, normalized_pack, case_id, "WAIT_FOR_EVIDENCE", ("AQ8_CASE_OBSERVATION_MISSING",), (), False)
        else:
            result = evaluate_case(context, normalized_pack, case_id, observation)
        results.append(result)
    disposition = _aggregate_disposition(item.disposition for item in results)
    if "AQ8_UNKNOWN_CASE" in failures:
        disposition = "WAIT_FOR_EVIDENCE"
    for item in results:
        for code in item.reason_codes:
            _add_unique(failures, code)
    evidence_ids = _unique(evidence_id for item in results for evidence_id in item.evidence_ids)
    return HighRiskPackResult(normalized_pack, disposition, disposition == "PASS", tuple(failures), evidence_ids, tuple(results))


def run_all_high_risk_packs(context: AssuranceContext, observations: Mapping[str, Mapping[str, HighRiskCaseObservation | Mapping[str, Any]]]) -> HighRiskAssuranceDecision:
    if not isinstance(context, AssuranceContext):
        raise TypeError("context must be an AssuranceContext")
    if not isinstance(observations, Mapping):
        raise TypeError("observations must be a mapping")
    failures: list[str] = []
    for raw_pack in observations:
        if str(raw_pack).upper() not in PACKS:
            _add_unique(failures, "AQ8_UNKNOWN_PACK")
    packs = []
    for pack in PACKS:
        raw = observations.get(pack, {})
        if not isinstance(raw, Mapping):
            raw = {}
            _add_unique(failures, "AQ8_INVALID_OBSERVATION")
        result = run_high_risk_pack(context, pack, raw)
        packs.append(result)
        for code in result.failure_codes:
            _add_unique(failures, code)
    disposition = _aggregate_disposition(item.result for item in packs)
    if "AQ8_UNKNOWN_PACK" in failures:
        disposition = "WAIT_FOR_EVIDENCE"
    return HighRiskAssuranceDecision(context, disposition, disposition == "PASS", tuple(failures), tuple(packs))


def evaluate_state_bound_covenant(
    context: AssuranceContext,
    steward: StewardSystemIntentJudgment,
    governor: GovernorProtectedObligationJudgment,
    *,
    assurance_result: str,
    assurance_evidence_refs: Iterable[str],
    assurance_evidence_durable: bool,
    assurance_evidence_retrievable: bool,
    pack_decision: HighRiskAssuranceDecision | None = None,
    cross_judgment_conflicts: Iterable[str] = (),
    cross_specialist_contradictions: Iterable[str] = (),
    system_contradictions: Iterable[str] = (),
    reconciliation: ReconciliationProposal | None = None,
    specialist_evidence: Iterable[SpecialistEvidence] = (),
) -> CovenantDecision:
    if not isinstance(context, AssuranceContext):
        raise TypeError("context must be an AssuranceContext")
    if not isinstance(steward, StewardSystemIntentJudgment) or not isinstance(governor, GovernorProtectedObligationJudgment):
        raise TypeError("steward and governor judgments are required")
    contradictions = list(system_contradictions)
    if steward.candidate_sha != context.candidate_sha or steward.tree_sha != context.tree_sha:
        contradictions.append("AQ8_STEWARD_JUDGMENT_STATE_MISMATCH")
    if governor.candidate_sha != context.candidate_sha or governor.tree_sha != context.tree_sha:
        contradictions.append("AQ8_GOVERNOR_JUDGMENT_STATE_MISMATCH")
    if pack_decision is None:
        contradictions.append("AQ8_PACK_NOT_PASS")
    elif not isinstance(pack_decision, HighRiskAssuranceDecision):
        contradictions.append("AQ8_PACK_STATE_MISMATCH")
    elif (
        pack_decision.context.repository != context.repository
        or pack_decision.context.candidate_sha != context.candidate_sha
        or pack_decision.context.tree_sha != context.tree_sha
    ):
        contradictions.append("AQ8_PACK_STATE_MISMATCH")
    elif pack_decision.result != "PASS":
        contradictions.append("AQ8_PACK_NOT_PASS")
    return evaluate_covenant(
        context.to_covenant_basis(), steward.to_governance_judgment(), governor.to_governance_judgment(),
        assurance_result=assurance_result, assurance_evidence_refs=assurance_evidence_refs,
        assurance_evidence_durable=assurance_evidence_durable,
        assurance_evidence_retrievable=assurance_evidence_retrievable,
        cross_judgment_conflicts=cross_judgment_conflicts,
        cross_specialist_contradictions=cross_specialist_contradictions,
        system_contradictions=contradictions, reconciliation=reconciliation,
        current_candidate_sha=context.candidate_sha, current_tree_sha=context.tree_sha,
        specialist_evidence=specialist_evidence,
    )


def validate_aq8_contract(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(contract, Mapping):
        raise TypeError("AQ8 contract must be a mapping")
    expected = {
        "$schema": "../schemas/aq8-high-risk-assurance-packs.v1.schema.json",
        "schema_version": AQ8_CONTRACT_SCHEMA_VERSION,
        "contract_role": "machine_high_risk_assurance_packs_contract",
        "authority_model": AQ8_AUTHORITY_MODEL, "transition_owner": AQ8_TRANSITION_OWNER,
        "packs": list(PACKS), "required_cases": {p: list(c) for p, c in REQUIRED_CASES.items()},
        "required_covenant_scenarios": list(AQ8_REQUIRED_COVENANT_SCENARIOS),
        "required_aq7_regression_anchors": list(AQ8_AQ7_REGRESSION_ANCHORS),
        "adversarial_permutations": list(AQ8_ADVERSARIAL_PERMUTATIONS),
        "context_fields": list(AQ8_CONTEXT_FIELDS), "evidence_fields": list(AQ8_EVIDENCE_FIELDS),
        "observation_fields": list(AQ8_OBSERVATION_FIELDS), "case_result_fields": list(AQ8_CASE_RESULT_FIELDS),
        "pack_result_fields": list(AQ8_PACK_RESULT_FIELDS), "decision_fields": list(AQ8_DECISION_FIELDS),
        "dispositions": list(DISPOSITIONS), "evidence_results": list(EVIDENCE_RESULTS),
        "supported_evidence_types": list(SUPPORTED_EVIDENCE_TYPES), "failure_codes": list(AQ8_FAILURE_CODES),
        "governance_requirements": {
            "prai_mandatory": True, "covenant_mandatory": True,
            "covenant_pass_is_not_authority": True, "prai_pass_is_not_covenant_pass": True,
            "system_contradiction_overrides_prai_pass": True,
            "durable_retrievable_evidence_required": True,
            "unknown_state_fails_closed": True, "arbiter_transition_owner": True,
        },
        "concurrency_proof": {
            "controlled_interleaving_required": True,
            "sequential_approximation_is_not_proof": True,
            "aggregate_invariant_requires_aggregate_analysis": True,
        },
        "organic_effectiveness": {
            "enabled": True, "seeded_and_organic_must_remain_separate": True,
            "generalized_percentage_requires_clear_denominator": True,
        },
        "authority": {
            "case_result_grants_authority": False, "pack_result_grants_authority": False,
            "decision_grants_authority": False, "transition_owner": AQ8_TRANSITION_OWNER,
            "merge_authorized": False, "production_action": False, "provider_activation": False,
        },
    }
    if set(contract) != set(expected):
        raise ValueError("AQ8_SCHEMA_RUNTIME_DRIFT: contract fields differ from runtime")
    for field_name, expected_value in expected.items():
        if contract.get(field_name) != expected_value:
            raise ValueError(f"AQ8_SCHEMA_RUNTIME_DRIFT: {field_name}")
    return contract


validate_machine_contract = validate_aq8_contract
validate_schema_runtime_parity = validate_aq8_contract

__all__ = [
    "AQ8_ADVERSARIAL_PERMUTATIONS", "AQ8_AQ7_REGRESSION_ANCHORS", "AQ8_AUTHORITY_MODEL",
    "AQ8_CASE_RESULT_FIELDS", "AQ8_CONTRACT_SCHEMA_VERSION", "AQ8_CONTEXT_FIELDS",
    "AQ8_DECISION_FIELDS", "AQ8_DECISION_SCHEMA_VERSION", "AQ8_EVIDENCE_FIELDS",
    "AQ8_FAILURE_CODES", "AQ8_OBSERVATION_FIELDS", "AQ8_PACK_RESULT_FIELDS",
    "AQ8_REQUIRED_COVENANT_SCENARIOS", "AQ8_TRANSITION_OWNER", "AssuranceContext",
    "DISPOSITIONS", "EVIDENCE_RESULTS", "EvidenceRecord", "HighRiskAssuranceDecision",
    "HighRiskCaseObservation", "HighRiskCaseResult", "HighRiskPackResult",
    "GovernorProtectedObligationJudgment", "PACKS", "REQUIRED_CASES",
    "REQUIRED_CONCURRENCY_CASES", "REQUIRED_EVIDENCE_INTEGRITY_CASES",
    "REQUIRED_PROVENANCE_CASES", "REQUIRED_SECURITY_CASES", "REQUIRED_STATE_MACHINE_CASES",
    "StewardSystemIntentJudgment", "SUPPORTED_EVIDENCE_TYPES", "evaluate_case",
    "evaluate_concurrency_case", "evaluate_evidence_integrity_case",
    "evaluate_provenance_case", "evaluate_security_case", "evaluate_state_bound_covenant",
    "evaluate_state_machine_case", "run_all_high_risk_packs", "run_high_risk_pack",
    "validate_aq8_contract", "validate_evidence_record", "validate_machine_contract",
    "validate_schema_runtime_parity",
]
