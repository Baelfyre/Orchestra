"""Pure post-run assurance rules for the PRAI completion invariant.

PRAI records independent evidence sufficiency and transition disposition. It
never grants execution, merge, release, provider, or production authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ...shared.canonicalization import (
    normalize_git_sha,
    normalize_sha256,
    normalize_timestamp,
    receipt_digest,
)


PRAI_CONTRACT_SCHEMA_VERSION = "orchestra.post-run-assurance.v1"
PRAI_DECISION_SCHEMA_VERSION = "orchestra.post-run-assurance-decision.v1"
PRAI_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
PRAI_AUTHORITY_BOUNDARY = "EVIDENCE_ONLY_NON_AUTHORIZING"
SECURITY_NO_MATERIAL_IMPACT = "SECURITY_REVIEWED_NO_MATERIAL_SECURITY_IMPACT"

AUDIT_DEPTHS = ("LIGHT", "STANDARD", "DEEP")
IMPACT_LEVELS = ("NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL")
REVIEW_RESULTS = ("PASS", "FAIL", "BLOCKED")
ARBITER_DISPOSITIONS = (
    "AUTO_CONTINUE",
    "AUTO_REMEDIATE_AND_REVALIDATE",
    "WAIT_FOR_EVIDENCE",
    "WAIT_FOR_CAPACITY",
    "ESCALATE_HUMAN",
    "STOP",
)
REVIEW_ROLES = (
    "CLOCKWORK",
    "CIPHER",
    "OVERSEER",
    "CHRONICLER",
    "DAGGER",
    "STEWARD",
    "GOVERNOR",
    "CLOAK",
    "CI",
    "GENERIC_CI",
)
BASELINE_REVIEWERS = ("CLOCKWORK", "CIPHER", "OVERSEER")
BASELINE_ASSURANCE = (
    "POST_RUN_LOGICAL_ASSURANCE",
    "POST_RUN_SECURITY_ASSURANCE",
    "EVIDENCE_SUFFICIENCY",
)
DEEP_RISK_CHARACTERISTICS = (
    "AUTHENTICATION",
    "AUTHORIZATION",
    "PRIVILEGE",
    "TENANT_ISOLATION",
    "EXTERNAL_INPUT",
    "CONCURRENCY",
    "AGGREGATE_INVARIANTS",
    "STATE_MACHINE",
    "DESTRUCTIVE_LIFECYCLE",
    "MIGRATION",
    "RECOVERY",
    "RETRY_IDEMPOTENCY",
    "PARTIAL_FAILURE",
    "SENSITIVE_PROVENANCE",
    "RESOURCE_PRESSURE",
    "PRODUCTION_CRITICAL",
)
TRIGGERED_SPECIALISTS = {
    "CHRONICLER": (
        "PERSISTENCE",
        "MIGRATION",
        "TRANSACTION",
        "CONCURRENCY",
        "DURABILITY",
        "DATA_OWNERSHIP",
        "AGGREGATE_INVARIANTS",
    ),
    "DAGGER": (
        "AUTHENTICATION",
        "AUTHORIZATION",
        "PRIVILEGE",
        "TENANT_ISOLATION",
        "EXTERNAL_INPUT",
        "CONCURRENCY",
        "AGGREGATE_INVARIANTS",
        "STATE_MACHINE",
        "DESTRUCTIVE_LIFECYCLE",
        "RECOVERY",
        "RETRY_IDEMPOTENCY",
        "PARTIAL_FAILURE",
        "SENSITIVE_PROVENANCE",
        "RESOURCE_PRESSURE",
    ),
    "STEWARD": ("SCOPE_EXPANSION", "PRODUCT", "CAPACITY", "RESOURCE_ALLOCATION"),
    "GOVERNOR": ("LEGAL", "PRIVACY", "COMPLIANCE", "IP", "POLICY"),
    "CLOAK": ("UI", "UX", "ACCESSIBILITY", "VISUAL"),
}
ALLOWED_RISK_CHARACTERISTICS = tuple(
    sorted(
        set(DEEP_RISK_CHARACTERISTICS).union(
            *(set(values) for values in TRIGGERED_SPECIALISTS.values())
        )
    )
)
EVIDENCE_LAYERS = (
    "STATIC",
    "UNIT",
    "DOMAIN",
    "CONTRACT",
    "INTEGRATION",
    "HTTP",
    "RUNTIME",
    "PERSISTENCE",
    "CONCURRENCY",
    "SECURITY",
    "PROVENANCE",
    "MUTATION",
    "ADVERSARIAL",
    "DOCUMENTATION",
    "COMPLETION_STATE",
)
EVIDENCE_SCOPES = (
    "SOURCE",
    "COMPLETION",
    "DOMAIN",
    "APPLICATION",
    "API",
    "UI",
    "UNIT",
    "CONTRACT",
    "INTEGRATION",
    "RUNTIME",
    "PERSISTENCE",
    "CONCURRENCY",
    "SECURITY",
    "ADVERSARIAL",
    "CANONICAL",
    "PRODUCT",
    "EMPIRICAL_EFFECTIVENESS",
)
EVIDENCE_SCOPE_COVERAGE = {
    "SOURCE": ("SOURCE",),
    "COMPLETION": ("COMPLETION",),
    "DOMAIN": ("DOMAIN",),
    "APPLICATION": ("DOMAIN", "APPLICATION"),
    "API": ("API", "APPLICATION", "DOMAIN"),
    "UI": ("UI", "APPLICATION", "DOMAIN"),
    "UNIT": ("UNIT",),
    "CONTRACT": ("CONTRACT",),
    "INTEGRATION": ("INTEGRATION", "APPLICATION", "API", "UI", "DOMAIN"),
    "RUNTIME": ("RUNTIME", "INTEGRATION", "APPLICATION", "API", "UI", "DOMAIN"),
    "PERSISTENCE": ("PERSISTENCE",),
    "CONCURRENCY": ("CONCURRENCY",),
    "SECURITY": ("SECURITY",),
    "ADVERSARIAL": ("ADVERSARIAL",),
    "CANONICAL": ("CANONICAL",),
    "PRODUCT": ("PRODUCT",),
    "EMPIRICAL_EFFECTIVENESS": ("EMPIRICAL_EFFECTIVENESS",),
}
PRAI_PROTECTED_PATHS = (
    ".github/workflows/prai.yml",
    "machine/adaptive/prai-post-run-assurance.v1.json",
    "machine/schemas/prai-post-run-assurance.v1.schema.json",
    "orchestra_runtime/domain/adaptive/prai.py",
    "scripts/validation/validate_prai.py",
)
_DOC_SUFFIXES = (".md", ".rst", ".txt")
_DEPTH_RANK = {"LIGHT": 0, "STANDARD": 1, "DEEP": 2}

FAIL_CURRENT_IDENTITY_REQUIRED = "FAIL_CURRENT_IDENTITY_REQUIRED"
FAIL_STALE_REPOSITORY = "FAIL_STALE_REPOSITORY"
FAIL_STALE_SOURCE = "FAIL_STALE_SOURCE"
FAIL_STALE_CANDIDATE = "FAIL_STALE_CANDIDATE"
FAIL_STALE_TREE = "FAIL_STALE_TREE"
FAIL_STALE_WORK_ITEM = "FAIL_STALE_WORK_ITEM"
FAIL_STALE_FRESHNESS = "FAIL_STALE_FRESHNESS"
FAIL_STALE_VERSION = "FAIL_STALE_VERSION"
FAIL_REQUIRED_LOGICAL_ASSURANCE = "FAIL_REQUIRED_LOGICAL_ASSURANCE"
FAIL_REQUIRED_SECURITY_ASSURANCE = "FAIL_REQUIRED_SECURITY_ASSURANCE"
FAIL_REQUIRED_OVERSEER_ASSURANCE = "FAIL_REQUIRED_OVERSEER_ASSURANCE"
FAIL_REQUIRED_REVIEWER = "FAIL_REQUIRED_REVIEWER"
FAIL_REQUIRED_ASSURANCE = "FAIL_REQUIRED_ASSURANCE"
FAIL_NON_INDEPENDENT_EVIDENCE = "FAIL_NON_INDEPENDENT_EVIDENCE"
FAIL_UNAUTHORITATIVE_EVIDENCE = "FAIL_UNAUTHORITATIVE_EVIDENCE"
FAIL_IMPLEMENTER_SELF_CERTIFICATION = "FAIL_IMPLEMENTER_SELF_CERTIFICATION"
FAIL_REQUIRED_AUDIT_DEPTH = "FAIL_REQUIRED_AUDIT_DEPTH"
FAIL_SECURITY_CLASSIFICATION = "FAIL_SECURITY_CLASSIFICATION"
FAIL_SECURITY_FINDING = "FAIL_SECURITY_FINDING"
FAIL_LOGICAL_CONTRADICTION = "FAIL_LOGICAL_CONTRADICTION"
FAIL_CALLER_CONTRACT = "FAIL_CALLER_CONTRACT"
FAIL_CHANGED_CODE_UNEXAMINED = "FAIL_CHANGED_CODE_UNEXAMINED"
FAIL_TRIGGERED_SPECIALIST = "FAIL_TRIGGERED_SPECIALIST"
FAIL_DUPLICATE_RECEIPT = "FAIL_DUPLICATE_RECEIPT"
FAIL_CONTRADICTORY_RECEIPT = "FAIL_CONTRADICTORY_RECEIPT"
FAIL_GENERIC_CI_SUBSTITUTION = "FAIL_GENERIC_CI_SUBSTITUTION"
FAIL_AUTHORITY_EXPANSION = "FAIL_AUTHORITY_EXPANSION"
FAIL_POLICY_SELF_MODIFICATION = "FAIL_POLICY_SELF_MODIFICATION"
FAIL_OVERSEER_INSUFFICIENT = "FAIL_OVERSEER_INSUFFICIENT"
FAIL_ARBITER_DISPOSITION = "FAIL_ARBITER_DISPOSITION"
FAIL_INVALID_RECEIPT_RESULT = "FAIL_INVALID_RECEIPT_RESULT"
FAIL_EVIDENCE_BINDING = "FAIL_EVIDENCE_BINDING"
FAIL_SCOPE_EXCEEDED = "FAIL_SCOPE_EXCEEDED"
FAIL_INVALID_FIELD = "FAIL_INVALID_FIELD"
FAIL_INVALID_DIGEST = "FAIL_INVALID_DIGEST"
FAIL_ASSURANCE_COVERAGE = "FAIL_ASSURANCE_COVERAGE"
FAIL_SCHEMA_RUNTIME_PARITY = "FAIL_SCHEMA_RUNTIME_PARITY"
FAIL_UNKNOWN_RISK_CHARACTERISTIC = "FAIL_UNKNOWN_RISK_CHARACTERISTIC"
FAIL_EVIDENCE_SCOPE = "FAIL_EVIDENCE_SCOPE"
FAIL_EVIDENCE_LAYER = "FAIL_EVIDENCE_LAYER"
FAIL_LOGICAL_IDENTITY = "FAIL_LOGICAL_IDENTITY"

REQUIRED_NEGATIVE_FIXTURES = (
    "green_tests_contradictory_logical_invariant",
    "security_sensitive_without_cipher",
    "harmless_docs_explicit_light",
    "implementer_self_certification",
    "stale_candidate_receipt",
    "stale_tree_receipt",
    "light_for_deep_trigger",
    "security_none_without_classification",
    "broken_caller_contract",
    "tenant_global_authority_expansion",
    "missing_chronicler_assurance",
    "missing_dagger_assurance",
    "contradictory_logical_receipts",
    "duplicate_pseudo_independent_receipts",
    "stale_audit_reuse_after_repair",
    "audit_does_not_examine_changed_code",
    "generic_green_ci_substitution",
    "self_modifying_prai_policy",
    "schema_runtime_divergence",
    "unknown_risk_characteristic",
    "partial_changed_path_coverage",
    "uncovered_risk_coverage",
    "uncovered_invariant_coverage",
    "noncanonical_risk_characteristic",
    "evidence_scope_claim_scope_mismatch",
    "spoofed_logical_identity",
    "stale_version_context",
    "mismatched_version_context",
    "missing_version_context",
    "unknown_evidence_layer",
    "noncanonical_evidence_layer",
    "undeclared_prai_policy_self_modification",
)
REQUIRED_PROPERTY_INVARIANTS = (
    "audit_is_mandatory",
    "adaptive_proportionality",
    "assurance_monotonicity",
    "authority_non_expansion",
    "candidate_binding",
    "repair_invalidation",
    "receipt_order_invariance",
    "duplicate_normalization",
)

RECEIPT_FIELDS = (
    "schema_version",
    "receipt_id",
    "role",
    "reviewer",
    "result",
    "repository",
    "source_ref",
    "candidate_sha",
    "tree_sha",
    "work_item_ref",
    "audit_depth",
    "evidence_refs",
    "audited_paths",
    "evidence_layer",
    "evidence_scope",
    "covered_risks",
    "covered_invariants",
    "freshness_ref",
    "version_ref",
    "provenance",
    "independent",
    "producer",
    "validator",
    "claim_scope",
    "limitations",
    "examined_changed_code",
    "security_classification",
    "logical_identity",
    "digest",
)
WORK_UNIT_FIELDS = (
    "schema_version",
    "work_item_ref",
    "repository",
    "source_ref",
    "candidate_sha",
    "tree_sha",
    "freshness_ref",
    "version_ref",
    "changed_paths",
    "implementer",
    "logical_impact",
    "security_impact",
    "audit_depth",
    "required_reviewers",
    "required_additional_assurance",
    "logical_result",
    "security_result",
    "evidence_refs",
    "limitations",
    "overseer_sufficiency",
    "arbiter_disposition",
    "review_receipts",
    "authority_boundary",
    "risk_characteristics",
    "invariants",
    "logical_findings",
    "security_findings",
    "caller_contract_issues",
    "policy_modified_paths",
    "policy_self_modification",
    "authority_expansion",
    "green_tests",
    "security_classification",
    "digest",
)
DECISION_FIELDS = (
    "schema_version",
    "decision_id",
    "repository",
    "source_ref",
    "candidate_sha",
    "tree_sha",
    "work_item_ref",
    "version_ref",
    "result",
    "compliant",
    "failure_codes",
    "required_reviewers",
    "satisfied_reviewers",
    "required_additional_assurance",
    "satisfied_additional_assurance",
    "audit_depth",
    "evidence_receipt_ids",
    "authority_model",
    "authority_expansion",
    "generated_at",
    "limitations",
    "decision_digest",
)
REQUIRED_WORK_UNIT_FIELDS = tuple(field for field in WORK_UNIT_FIELDS if field != "digest")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    value = value.strip()
    if not value or any(ord(char) < 32 for char in value):
        raise ValueError(f"{field_name} must be a non-empty text value")
    return value


def _choice(value: Any, choices: Iterable[str], field_name: str) -> str:
    value = _text(value, field_name)
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {tuple(choices)!r}")
    return value


def _evidence_layer(value: Any) -> str:
    try:
        return _choice(value, EVIDENCE_LAYERS, "evidence_layer")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{FAIL_EVIDENCE_LAYER}: {exc}") from exc


def _strings(
    values: Any, field_name: str, *, allow_empty: bool = True
) -> tuple[str, ...]:
    if values is None:
        if allow_empty:
            return ()
        raise ValueError(f"{field_name} must not be empty")
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError(f"{field_name} must be an iterable of strings")
    result = tuple(_text(value, field_name) for value in values)
    if not allow_empty and not result:
        raise ValueError(f"{field_name} must not be empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return result


def _canonical_risks(values: Any) -> tuple[str, ...]:
    result = _strings(values, "risk_characteristics")
    noncanonical = sorted(value for value in result if value != value.upper())
    unknown = sorted(set(result) - set(ALLOWED_RISK_CHARACTERISTICS))
    if noncanonical or unknown:
        invalid = sorted(set(noncanonical).union(unknown))
        raise ValueError(
            f"{FAIL_UNKNOWN_RISK_CHARACTERISTIC}: " + ", ".join(invalid)
        )
    return result


def _roles(
    values: Any, field_name: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
    result = tuple(
        value.upper()
        for value in _strings(values, field_name, allow_empty=allow_empty)
    )
    if any(value not in REVIEW_ROLES for value in result):
        raise ValueError(f"{field_name} contains an unknown reviewer role")
    return result


def _paths(
    values: Any, field_name: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
    result = _strings(values, field_name, allow_empty=allow_empty)
    for path in result:
        if path.startswith("/") or path.startswith("\\") or ".." in path.split("/"):
            raise ValueError(f"{field_name} contains an unsafe path")
    return result


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    return value


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    return receipt_digest(payload)


def _tuple_json(values: Iterable[str]) -> list[str]:
    return list(values)


@dataclass(frozen=True, slots=True)
class PraiReviewReceipt:
    receipt_id: str
    role: str
    reviewer: str
    result: str
    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    work_item_ref: str
    audit_depth: str
    evidence_refs: tuple[str, ...]
    audited_paths: tuple[str, ...]
    evidence_layer: str
    evidence_scope: str
    covered_risks: tuple[str, ...]
    covered_invariants: tuple[str, ...]
    freshness_ref: str
    version_ref: str
    provenance: str
    independent: bool
    producer: str
    validator: str
    claim_scope: str
    limitations: tuple[str, ...]
    examined_changed_code: bool
    security_classification: str | None = None
    logical_identity: str | None = None
    schema_version: str = PRAI_CONTRACT_SCHEMA_VERSION
    digest: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "reviewer",
            "repository",
            "source_ref",
            "work_item_ref",
            "producer",
            "validator",
            "claim_scope",
            "evidence_layer",
            "evidence_scope",
            "version_ref",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self,
            "evidence_layer",
            _evidence_layer(self.evidence_layer),
        )
        object.__setattr__(
            self,
            "evidence_scope",
            _choice(self.evidence_scope, EVIDENCE_SCOPES, "evidence_scope"),
        )
        object.__setattr__(
            self,
            "claim_scope",
            _choice(self.claim_scope, EVIDENCE_SCOPES, "claim_scope"),
        )
        if self.claim_scope not in EVIDENCE_SCOPE_COVERAGE[self.evidence_scope]:
            raise ValueError(
                f"{FAIL_EVIDENCE_SCOPE}: evidence scope {self.evidence_scope} "
                f"does not cover claim scope {self.claim_scope}"
            )
        object.__setattr__(self, "role", _choice(self.role, REVIEW_ROLES, "role"))
        object.__setattr__(self, "result", _choice(self.result, REVIEW_RESULTS, "result"))
        object.__setattr__(self, "audit_depth", _choice(self.audit_depth, AUDIT_DEPTHS, "audit_depth"))
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "evidence_refs", _strings(self.evidence_refs, "evidence_refs", allow_empty=False))
        object.__setattr__(self, "audited_paths", _paths(self.audited_paths, "audited_paths"))
        object.__setattr__(self, "covered_risks", _strings(self.covered_risks, "covered_risks"))
        object.__setattr__(self, "covered_invariants", _strings(self.covered_invariants, "covered_invariants"))
        object.__setattr__(self, "limitations", _strings(self.limitations, "limitations"))
        object.__setattr__(self, "freshness_ref", normalize_timestamp(self.freshness_ref, "freshness_ref"))
        object.__setattr__(
            self,
            "provenance",
            _choice(self.provenance, ("AUTHORITATIVE", "SELF_ASSERTED", "UNQUALIFIED"), "provenance"),
        )
        if not isinstance(self.independent, bool) or not isinstance(self.examined_changed_code, bool):
            raise TypeError("independent and examined_changed_code must be bool values")
        if self.security_classification is not None:
            object.__setattr__(self, "security_classification", _text(self.security_classification, "security_classification"))
        if self.schema_version != PRAI_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported PRAI receipt schema version")
        expected_identity = _canonical_digest(
            {
                "work_item_ref": self.work_item_ref,
                "candidate_sha": self.candidate_sha,
                "tree_sha": self.tree_sha,
                "evidence_refs": _tuple_json(self.evidence_refs),
                "evidence_layer": self.evidence_layer,
                "version_ref": self.version_ref,
                "evidence_scope": self.evidence_scope,
                "claim_scope": self.claim_scope,
            }
        )
        if self.logical_identity is None:
            logical_identity = expected_identity
        else:
            logical_identity = _text(self.logical_identity, "logical_identity")
            if logical_identity != expected_identity:
                raise ValueError(
                    f"{FAIL_LOGICAL_IDENTITY}: logical_identity does not match "
                    "derived identity"
                )
        object.__setattr__(self, "logical_identity", logical_identity)
        expected_digest = _canonical_digest(self.to_dict(include_digest=False))
        if self.digest is None:
            object.__setattr__(self, "digest", expected_digest)
        else:
            object.__setattr__(self, "digest", normalize_sha256(self.digest, "digest"))
            if self.digest != expected_digest:
                raise ValueError("receipt digest does not match canonical receipt content")

    @property
    def review_type(self) -> str:
        return self.role

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PraiReviewReceipt":
        data = dict(_mapping(value, "receipt"))
        unknown = set(data) - set(RECEIPT_FIELDS)
        if unknown:
            raise ValueError("unknown receipt fields: " + ", ".join(sorted(unknown)))
        required = set(RECEIPT_FIELDS) - {"digest"}
        missing = required - set(data)
        if missing:
            raise ValueError("missing receipt fields: " + ", ".join(sorted(missing)))
        return cls(**data)

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "role": self.role,
            "reviewer": self.reviewer,
            "result": self.result,
            "repository": self.repository,
            "source_ref": self.source_ref,
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "work_item_ref": self.work_item_ref,
            "audit_depth": self.audit_depth,
            "evidence_refs": _tuple_json(self.evidence_refs),
            "audited_paths": _tuple_json(self.audited_paths),
            "evidence_layer": self.evidence_layer,
            "evidence_scope": self.evidence_scope,
            "covered_risks": _tuple_json(self.covered_risks),
            "covered_invariants": _tuple_json(self.covered_invariants),
            "freshness_ref": self.freshness_ref,
            "version_ref": self.version_ref,
            "provenance": self.provenance,
            "independent": self.independent,
            "producer": self.producer,
            "validator": self.validator,
            "claim_scope": self.claim_scope,
            "limitations": _tuple_json(self.limitations),
            "examined_changed_code": self.examined_changed_code,
            "security_classification": self.security_classification,
            "logical_identity": self.logical_identity,
        }
        if include_digest:
            value["digest"] = self.digest
        return value


@dataclass(frozen=True, slots=True)
class PraiWorkUnit:
    work_item_ref: str
    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    freshness_ref: str
    version_ref: str
    changed_paths: tuple[str, ...]
    implementer: str
    logical_impact: str
    security_impact: str
    audit_depth: str
    required_reviewers: tuple[str, ...]
    required_additional_assurance: tuple[str, ...]
    logical_result: str
    security_result: str
    evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    overseer_sufficiency: bool | str
    arbiter_disposition: str
    review_receipts: tuple[PraiReviewReceipt, ...]
    authority_boundary: str = PRAI_AUTHORITY_BOUNDARY
    risk_characteristics: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    logical_findings: tuple[str, ...] = ()
    security_findings: tuple[str, ...] = ()
    caller_contract_issues: tuple[str, ...] = ()
    policy_modified_paths: tuple[str, ...] = ()
    policy_self_modification: bool = False
    authority_expansion: bool = False
    green_tests: bool = False
    security_classification: str | None = None
    schema_version: str = PRAI_CONTRACT_SCHEMA_VERSION
    digest: str | None = None

    def __post_init__(self) -> None:
        for name in ("work_item_ref", "repository", "source_ref", "implementer"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "freshness_ref", normalize_timestamp(self.freshness_ref, "freshness_ref"))
        object.__setattr__(self, "version_ref", _text(self.version_ref, "version_ref"))
        object.__setattr__(self, "changed_paths", _paths(self.changed_paths, "changed_paths", allow_empty=False))
        object.__setattr__(self, "logical_impact", _choice(self.logical_impact, IMPACT_LEVELS, "logical_impact"))
        object.__setattr__(self, "security_impact", _choice(self.security_impact, IMPACT_LEVELS, "security_impact"))
        object.__setattr__(self, "audit_depth", _choice(self.audit_depth, AUDIT_DEPTHS, "audit_depth"))
        object.__setattr__(self, "required_reviewers", _roles(self.required_reviewers, "required_reviewers"))
        object.__setattr__(
            self,
            "required_additional_assurance",
            _strings(self.required_additional_assurance, "required_additional_assurance", allow_empty=False),
        )
        object.__setattr__(self, "logical_result", _choice(self.logical_result, REVIEW_RESULTS, "logical_result"))
        object.__setattr__(self, "security_result", _choice(self.security_result, REVIEW_RESULTS, "security_result"))
        object.__setattr__(self, "evidence_refs", _strings(self.evidence_refs, "evidence_refs", allow_empty=False))
        object.__setattr__(self, "limitations", _strings(self.limitations, "limitations"))
        object.__setattr__(self, "arbiter_disposition", _choice(self.arbiter_disposition, ARBITER_DISPOSITIONS, "arbiter_disposition"))
        object.__setattr__(self, "authority_boundary", _text(self.authority_boundary, "authority_boundary"))
        object.__setattr__(
            self,
            "risk_characteristics",
            _canonical_risks(self.risk_characteristics),
        )
        object.__setattr__(self, "invariants", _strings(self.invariants, "invariants"))
        object.__setattr__(self, "logical_findings", _strings(self.logical_findings, "logical_findings"))
        object.__setattr__(self, "security_findings", _strings(self.security_findings, "security_findings"))
        object.__setattr__(self, "caller_contract_issues", _strings(self.caller_contract_issues, "caller_contract_issues"))
        object.__setattr__(self, "policy_modified_paths", _paths(self.policy_modified_paths, "policy_modified_paths", allow_empty=True))
        for name in ("policy_self_modification", "authority_expansion", "green_tests"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be bool")
        if not isinstance(self.overseer_sufficiency, (bool, str)):
            raise TypeError("overseer_sufficiency must be bool or string")
        if isinstance(self.overseer_sufficiency, str):
            object.__setattr__(self, "overseer_sufficiency", _text(self.overseer_sufficiency, "overseer_sufficiency"))
        if self.security_classification is not None:
            object.__setattr__(self, "security_classification", _text(self.security_classification, "security_classification"))
        receipts: list[PraiReviewReceipt] = []
        if isinstance(self.review_receipts, (str, bytes)) or not isinstance(self.review_receipts, Iterable):
            raise TypeError("review_receipts must be iterable")
        for value in self.review_receipts:
            if isinstance(value, PraiReviewReceipt):
                receipt = value
            else:
                receipt = PraiReviewReceipt.from_mapping(value)
            receipts.append(receipt)
        object.__setattr__(self, "review_receipts", tuple(receipts))
        if self.schema_version != PRAI_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported PRAI work-unit schema version")
        expected_digest = _canonical_digest(self.to_dict(include_digest=False))
        if self.digest is None:
            object.__setattr__(self, "digest", expected_digest)
        else:
            object.__setattr__(self, "digest", normalize_sha256(self.digest, "digest"))
            if self.digest != expected_digest:
                raise ValueError("work-unit digest does not match canonical work-unit content")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PraiWorkUnit":
        data = dict(_mapping(value, "work_unit"))
        unknown = set(data) - set(WORK_UNIT_FIELDS)
        if unknown:
            raise ValueError("unknown work-unit fields: " + ", ".join(sorted(unknown)))
        missing = set(REQUIRED_WORK_UNIT_FIELDS) - set(data)
        if missing:
            raise ValueError("missing work-unit fields: " + ", ".join(sorted(missing)))
        return cls(**data)

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": self.schema_version,
            "work_item_ref": self.work_item_ref,
            "repository": self.repository,
            "source_ref": self.source_ref,
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "freshness_ref": self.freshness_ref,
            "version_ref": self.version_ref,
            "changed_paths": _tuple_json(self.changed_paths),
            "implementer": self.implementer,
            "logical_impact": self.logical_impact,
            "security_impact": self.security_impact,
            "audit_depth": self.audit_depth,
            "required_reviewers": _tuple_json(self.required_reviewers),
            "required_additional_assurance": _tuple_json(self.required_additional_assurance),
            "logical_result": self.logical_result,
            "security_result": self.security_result,
            "evidence_refs": _tuple_json(self.evidence_refs),
            "limitations": _tuple_json(self.limitations),
            "overseer_sufficiency": self.overseer_sufficiency,
            "arbiter_disposition": self.arbiter_disposition,
            "review_receipts": [receipt.to_dict() for receipt in self.review_receipts],
            "authority_boundary": self.authority_boundary,
            "risk_characteristics": _tuple_json(self.risk_characteristics),
            "invariants": _tuple_json(self.invariants),
            "logical_findings": _tuple_json(self.logical_findings),
            "security_findings": _tuple_json(self.security_findings),
            "caller_contract_issues": _tuple_json(self.caller_contract_issues),
            "policy_modified_paths": _tuple_json(self.policy_modified_paths),
            "policy_self_modification": self.policy_self_modification,
            "authority_expansion": self.authority_expansion,
            "green_tests": self.green_tests,
            "security_classification": self.security_classification,
        }
        if include_digest:
            value["digest"] = self.digest
        return value


@dataclass(frozen=True, slots=True)
class PraiDecision:
    decision_id: str
    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    work_item_ref: str
    version_ref: str
    result: str
    compliant: bool
    failure_codes: tuple[str, ...]
    required_reviewers: tuple[str, ...]
    satisfied_reviewers: tuple[str, ...]
    required_additional_assurance: tuple[str, ...]
    satisfied_additional_assurance: tuple[str, ...]
    audit_depth: str
    evidence_receipt_ids: tuple[str, ...]
    authority_model: str
    authority_expansion: bool
    generated_at: str
    limitations: tuple[str, ...]
    schema_version: str = PRAI_DECISION_SCHEMA_VERSION
    decision_digest: str | None = None

    def __post_init__(self) -> None:
        for name in ("decision_id", "repository", "source_ref", "work_item_ref", "version_ref", "authority_model"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "result", _choice(self.result, ("PASS", "BLOCKED"), "result"))
        if not isinstance(self.compliant, bool) or not isinstance(self.authority_expansion, bool):
            raise TypeError("compliant and authority_expansion must be bool values")
        object.__setattr__(self, "failure_codes", _strings(self.failure_codes, "failure_codes"))
        object.__setattr__(self, "required_reviewers", _roles(self.required_reviewers, "required_reviewers"))
        object.__setattr__(
            self,
            "satisfied_reviewers",
            _roles(self.satisfied_reviewers, "satisfied_reviewers", allow_empty=True),
        )
        object.__setattr__(self, "required_additional_assurance", _strings(self.required_additional_assurance, "required_additional_assurance", allow_empty=False))
        object.__setattr__(self, "satisfied_additional_assurance", _strings(self.satisfied_additional_assurance, "satisfied_additional_assurance"))
        object.__setattr__(self, "audit_depth", _choice(self.audit_depth, AUDIT_DEPTHS, "audit_depth"))
        object.__setattr__(self, "evidence_receipt_ids", _strings(self.evidence_receipt_ids, "evidence_receipt_ids"))
        object.__setattr__(self, "generated_at", normalize_timestamp(self.generated_at, "generated_at"))
        object.__setattr__(self, "limitations", _strings(self.limitations, "limitations"))
        if self.schema_version != PRAI_DECISION_SCHEMA_VERSION:
            raise ValueError("unsupported PRAI decision schema version")
        if self.authority_model != PRAI_AUTHORITY_MODEL or self.authority_expansion:
            raise ValueError("PRAI decision authority model drift")
        expected_digest = _canonical_digest(self.to_dict(include_digest=False))
        if self.decision_digest is None:
            object.__setattr__(self, "decision_digest", expected_digest)
        else:
            object.__setattr__(self, "decision_digest", normalize_sha256(self.decision_digest, "decision_digest"))
            if self.decision_digest != expected_digest:
                raise ValueError("decision digest does not match canonical decision content")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PraiDecision":
        data = dict(_mapping(value, "decision"))
        unknown = set(data) - set(DECISION_FIELDS)
        if unknown:
            raise ValueError("unknown decision fields: " + ", ".join(sorted(unknown)))
        required = set(DECISION_FIELDS) - {"schema_version", "decision_digest"}
        missing = required - set(data)
        if missing:
            raise ValueError("missing decision fields: " + ", ".join(sorted(missing)))
        return cls(**data)

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "repository": self.repository,
            "source_ref": self.source_ref,
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "work_item_ref": self.work_item_ref,
            "version_ref": self.version_ref,
            "result": self.result,
            "compliant": self.compliant,
            "failure_codes": _tuple_json(self.failure_codes),
            "required_reviewers": _tuple_json(self.required_reviewers),
            "satisfied_reviewers": _tuple_json(self.satisfied_reviewers),
            "required_additional_assurance": _tuple_json(self.required_additional_assurance),
            "satisfied_additional_assurance": _tuple_json(self.satisfied_additional_assurance),
            "audit_depth": self.audit_depth,
            "evidence_receipt_ids": _tuple_json(self.evidence_receipt_ids),
            "authority_model": self.authority_model,
            "authority_expansion": self.authority_expansion,
            "generated_at": self.generated_at,
            "limitations": _tuple_json(self.limitations),
        }
        if include_digest:
            value["decision_digest"] = self.decision_digest
        return value


def _coerce_work_unit(value: PraiWorkUnit | Mapping[str, Any]) -> PraiWorkUnit:
    return value if isinstance(value, PraiWorkUnit) else PraiWorkUnit.from_mapping(value)


def required_audit_depth(unit: PraiWorkUnit | Mapping[str, Any]) -> str:
    work = _coerce_work_unit(unit)
    risks = set(work.risk_characteristics)
    if risks.intersection(DEEP_RISK_CHARACTERISTICS) or max(
        _DEPTH_RANK["STANDARD"] if work.logical_impact in {"MEDIUM", "HIGH", "CRITICAL"} else 0,
        _DEPTH_RANK["STANDARD"] if work.security_impact in {"MEDIUM", "HIGH", "CRITICAL"} else 0,
    ) >= _DEPTH_RANK["STANDARD"]:
        return "DEEP"
    if (
        work.logical_impact != "NONE"
        or work.security_impact != "NONE"
        or risks
        or any(not path.endswith(_DOC_SUFFIXES) for path in work.changed_paths)
    ):
        return "STANDARD"
    return "LIGHT"


def triggered_reviewers(risk_characteristics: Iterable[str]) -> tuple[str, ...]:
    risks = set(_canonical_risks(risk_characteristics))
    return tuple(
        role
        for role, triggers in TRIGGERED_SPECIALISTS.items()
        if risks.intersection(triggers)
    )


def _required_reviewers(work: PraiWorkUnit) -> tuple[str, ...]:
    roles = list(BASELINE_REVIEWERS)
    for role in triggered_reviewers(work.risk_characteristics):
        if role not in roles:
            roles.append(role)
    return tuple(roles)


def _required_assurance(work: PraiWorkUnit) -> tuple[str, ...]:
    values = list(BASELINE_ASSURANCE)
    for role in triggered_reviewers(work.risk_characteristics):
        values.append(f"{role}_ASSURANCE")
    return tuple(values)


def _add(failures: list[str], code: str) -> None:
    if code not in failures:
        failures.append(code)


def _compare_identity(
    failures: list[str],
    label: str,
    observed: str,
    current: str | None,
    code: str,
    *,
    normalize: bool = False,
) -> None:
    if current is None:
        _add(failures, FAIL_CURRENT_IDENTITY_REQUIRED)
        return
    try:
        expected = normalize_git_sha(current, f"current_{label}") if normalize else _text(current, f"current_{label}")
    except (TypeError, ValueError):
        _add(failures, code)
        return
    if observed != expected:
        _add(failures, code)


def _receipt_covers_claim(
    receipt: PraiReviewReceipt,
    work: PraiWorkUnit,
    changed_paths: set[str],
) -> bool:
    return (
        set(receipt.audited_paths) == changed_paths
        and {value.upper() for value in receipt.covered_risks}
        == set(work.risk_characteristics)
        and {value.casefold() for value in receipt.covered_invariants}
        == {value.casefold() for value in work.invariants}
    )


def evaluate_post_run_assurance(
    work_unit: PraiWorkUnit | Mapping[str, Any],
    *,
    current_repository: str | None = None,
    current_source_ref: str | None = None,
    current_candidate_sha: str | None = None,
    current_tree_sha: str | None = None,
    current_work_item_ref: str | None = None,
    current_freshness_ref: str | None = None,
    current_version_ref: str | None = None,
    generated_at: str | None = None,
    decision_id: str = "prai-post-run-assurance",
) -> PraiDecision:
    work = _coerce_work_unit(work_unit)
    failures: list[str] = []
    _compare_identity(failures, "repository", work.repository, current_repository, FAIL_STALE_REPOSITORY)
    _compare_identity(failures, "source_ref", work.source_ref, current_source_ref, FAIL_STALE_SOURCE)
    _compare_identity(failures, "candidate_sha", work.candidate_sha, current_candidate_sha, FAIL_STALE_CANDIDATE, normalize=True)
    _compare_identity(failures, "tree_sha", work.tree_sha, current_tree_sha, FAIL_STALE_TREE, normalize=True)
    _compare_identity(failures, "work_item_ref", work.work_item_ref, current_work_item_ref, FAIL_STALE_WORK_ITEM)
    _compare_identity(failures, "freshness_ref", work.freshness_ref, current_freshness_ref, FAIL_STALE_FRESHNESS)
    _compare_identity(failures, "version_ref", work.version_ref, current_version_ref, FAIL_STALE_VERSION)

    required_reviewers = _required_reviewers(work)
    required_assurance = _required_assurance(work)
    declared_reviewers = set(work.required_reviewers)
    declared_assurance = set(work.required_additional_assurance)
    for role in required_reviewers:
        if role not in declared_reviewers:
            _add(failures, FAIL_REQUIRED_REVIEWER)
    for assurance in required_assurance:
        if assurance not in declared_assurance:
            _add(failures, FAIL_REQUIRED_ASSURANCE)

    required_depth = required_audit_depth(work)
    if _DEPTH_RANK[work.audit_depth] < _DEPTH_RANK[required_depth]:
        _add(failures, FAIL_REQUIRED_AUDIT_DEPTH)
    if work.authority_boundary != PRAI_AUTHORITY_BOUNDARY or work.authority_expansion:
        _add(failures, FAIL_AUTHORITY_EXPANSION)
    if (
        set(work.changed_paths).intersection(PRAI_PROTECTED_PATHS)
        or work.policy_self_modification
        or work.policy_modified_paths
    ):
        _add(failures, FAIL_POLICY_SELF_MODIFICATION)
    if work.overseer_sufficiency not in (True, "SUFFICIENT"):
        _add(failures, FAIL_OVERSEER_INSUFFICIENT)
    if work.arbiter_disposition != "AUTO_CONTINUE":
        _add(failures, FAIL_ARBITER_DISPOSITION)
    if work.logical_result != "PASS" or work.logical_findings:
        _add(failures, FAIL_LOGICAL_CONTRADICTION)
    if work.caller_contract_issues:
        _add(failures, FAIL_CALLER_CONTRACT)
    if work.security_result != "PASS" or work.security_findings:
        _add(failures, FAIL_SECURITY_FINDING)
    if work.security_impact == "NONE" and work.security_classification != SECURITY_NO_MATERIAL_IMPACT:
        _add(failures, FAIL_SECURITY_CLASSIFICATION)
    if not work.evidence_refs:
        _add(failures, FAIL_REQUIRED_ASSURANCE)

    receipts = tuple(sorted(work.review_receipts, key=lambda item: (item.role, item.receipt_id)))
    receipt_ids = tuple(receipt.receipt_id for receipt in receipts)
    if len(receipt_ids) != len(set(receipt_ids)):
        _add(failures, FAIL_DUPLICATE_RECEIPT)
    logical_id_groups: dict[str, list[PraiReviewReceipt]] = {}
    role_groups: dict[str, list[PraiReviewReceipt]] = {}
    changed = set(work.changed_paths)
    for receipt in receipts:
        logical_id_groups.setdefault(receipt.logical_identity or "", []).append(receipt)
        role_groups.setdefault(receipt.role, []).append(receipt)
        _compare_identity(failures, "repository", receipt.repository, current_repository, FAIL_STALE_REPOSITORY)
        _compare_identity(failures, "source_ref", receipt.source_ref, current_source_ref, FAIL_STALE_SOURCE)
        _compare_identity(failures, "candidate_sha", receipt.candidate_sha, current_candidate_sha, FAIL_STALE_CANDIDATE, normalize=True)
        _compare_identity(failures, "tree_sha", receipt.tree_sha, current_tree_sha, FAIL_STALE_TREE, normalize=True)
        _compare_identity(failures, "work_item_ref", receipt.work_item_ref, current_work_item_ref, FAIL_STALE_WORK_ITEM)
        _compare_identity(failures, "freshness_ref", receipt.freshness_ref, current_freshness_ref, FAIL_STALE_FRESHNESS)
        _compare_identity(failures, "version_ref", receipt.version_ref, current_version_ref, FAIL_STALE_VERSION)
        if (
            receipt.repository != work.repository
            or receipt.source_ref != work.source_ref
            or receipt.candidate_sha != work.candidate_sha
            or receipt.tree_sha != work.tree_sha
            or receipt.work_item_ref != work.work_item_ref
            or receipt.freshness_ref != work.freshness_ref
            or receipt.version_ref != work.version_ref
        ):
            _add(failures, FAIL_EVIDENCE_BINDING)
        if receipt.result != "PASS":
            _add(failures, FAIL_INVALID_RECEIPT_RESULT)
        if receipt.provenance != "AUTHORITATIVE":
            _add(failures, FAIL_UNAUTHORITATIVE_EVIDENCE)
        if (
            not receipt.independent
            or receipt.reviewer.casefold() == work.implementer.casefold()
            or receipt.producer.casefold() == work.implementer.casefold()
        ):
            _add(failures, FAIL_NON_INDEPENDENT_EVIDENCE)
            if (
                receipt.reviewer.casefold() == work.implementer.casefold()
                or receipt.producer.casefold() == work.implementer.casefold()
            ):
                _add(failures, FAIL_IMPLEMENTER_SELF_CERTIFICATION)
        if not set(receipt.evidence_refs).issubset(set(work.evidence_refs)):
            _add(failures, FAIL_SCOPE_EXCEEDED)
        if (
            changed and set(receipt.audited_paths).isdisjoint(changed)
        ) or (
            any(not path.endswith(_DOC_SUFFIXES) for path in changed)
            and not receipt.examined_changed_code
        ):
            _add(failures, FAIL_CHANGED_CODE_UNEXAMINED)
        if receipt.result == "PASS" and not _receipt_covers_claim(receipt, work, changed):
            _add(failures, FAIL_ASSURANCE_COVERAGE)
        if _DEPTH_RANK[receipt.audit_depth] < _DEPTH_RANK[work.audit_depth]:
            _add(failures, FAIL_REQUIRED_AUDIT_DEPTH)
        if (
            receipt.role == "CIPHER"
            and work.security_impact == "NONE"
            and receipt.security_classification != SECURITY_NO_MATERIAL_IMPACT
        ):
            _add(failures, FAIL_SECURITY_CLASSIFICATION)
        if receipt.role == "CIPHER" and work.security_impact != "NONE" and not receipt.evidence_refs:
            _add(failures, FAIL_REQUIRED_SECURITY_ASSURANCE)

    for group in logical_id_groups.values():
        if len(group) > 1:
            if len({receipt.result for receipt in group}) > 1:
                _add(failures, FAIL_CONTRADICTORY_RECEIPT)
            else:
                _add(failures, FAIL_DUPLICATE_RECEIPT)
    for group in role_groups.values():
        if len({receipt.result for receipt in group}) > 1:
            _add(failures, FAIL_CONTRADICTORY_RECEIPT)

    by_role = {
        receipt.role: receipt
        for receipt in receipts
        if (
            receipt.result == "PASS"
            and receipt.provenance == "AUTHORITATIVE"
            and receipt.independent
            and receipt.reviewer.casefold() != work.implementer.casefold()
            and receipt.producer.casefold() != work.implementer.casefold()
            and receipt.repository == work.repository
            and receipt.source_ref == work.source_ref
            and receipt.candidate_sha == work.candidate_sha
            and receipt.tree_sha == work.tree_sha
            and receipt.work_item_ref == work.work_item_ref
            and receipt.freshness_ref == work.freshness_ref
            and receipt.version_ref == work.version_ref
            and current_version_ref is not None
            and receipt.version_ref == current_version_ref
            and set(receipt.evidence_refs).issubset(set(work.evidence_refs))
            and _receipt_covers_claim(receipt, work, changed)
            and _DEPTH_RANK[receipt.audit_depth] >= _DEPTH_RANK[work.audit_depth]
            and (
                not any(not path.endswith(_DOC_SUFFIXES) for path in changed)
                or receipt.examined_changed_code
            )
            and (
                receipt.role != "CIPHER"
                or work.security_impact != "NONE"
                or receipt.security_classification == SECURITY_NO_MATERIAL_IMPACT
            )
        )
    }
    for role in required_reviewers:
        receipt = by_role.get(role)
        if receipt is None:
            _add(failures, FAIL_REQUIRED_REVIEWER)
            if role == "CLOCKWORK":
                _add(failures, FAIL_REQUIRED_LOGICAL_ASSURANCE)
            elif role == "CIPHER":
                _add(failures, FAIL_REQUIRED_SECURITY_ASSURANCE)
            elif role == "OVERSEER":
                _add(failures, FAIL_REQUIRED_OVERSEER_ASSURANCE)
            else:
                _add(failures, FAIL_TRIGGERED_SPECIALIST)
    if work.green_tests and (work.logical_findings or work.caller_contract_issues):
        _add(failures, FAIL_LOGICAL_CONTRADICTION)
    if any(receipt.role in {"CI", "GENERIC_CI"} for receipt in receipts):
        _add(failures, FAIL_GENERIC_CI_SUBSTITUTION)

    satisfied_reviewers = tuple(role for role in required_reviewers if role in by_role)
    satisfied_assurance = tuple(
        assurance
        for assurance in required_assurance
        if (
            assurance == "POST_RUN_LOGICAL_ASSURANCE"
            and "CLOCKWORK" in by_role
        )
        or (
            assurance == "POST_RUN_SECURITY_ASSURANCE"
            and "CIPHER" in by_role
        )
        or (assurance == "EVIDENCE_SUFFICIENCY" and "OVERSEER" in by_role)
        or (assurance.removesuffix("_ASSURANCE") in by_role)
    )
    result = "PASS" if not failures else "BLOCKED"
    timestamp = generated_at or current_freshness_ref or work.freshness_ref
    return PraiDecision(
        decision_id=decision_id,
        repository=work.repository,
        source_ref=work.source_ref,
        candidate_sha=work.candidate_sha,
        tree_sha=work.tree_sha,
        work_item_ref=work.work_item_ref,
        version_ref=work.version_ref,
        result=result,
        compliant=result == "PASS",
        failure_codes=tuple(failures),
        required_reviewers=required_reviewers,
        satisfied_reviewers=satisfied_reviewers,
        required_additional_assurance=required_assurance,
        satisfied_additional_assurance=satisfied_assurance,
        audit_depth=work.audit_depth,
        evidence_receipt_ids=receipt_ids,
        authority_model=PRAI_AUTHORITY_MODEL,
        authority_expansion=False,
        generated_at=timestamp,
        limitations=work.limitations,
    )


def validate_prai_contract(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    data = _mapping(contract, "contract")
    expected = {
        "schema_version": PRAI_CONTRACT_SCHEMA_VERSION,
        "decision_schema_version": PRAI_DECISION_SCHEMA_VERSION,
        "authority_model": PRAI_AUTHORITY_MODEL,
        "audit_depths": list(AUDIT_DEPTHS),
        "impact_levels": list(IMPACT_LEVELS),
        "review_results": list(REVIEW_RESULTS),
        "arbiter_dispositions": list(ARBITER_DISPOSITIONS),
        "review_roles": list(REVIEW_ROLES),
        "baseline_reviewers": list(BASELINE_REVIEWERS),
        "baseline_assurance": list(BASELINE_ASSURANCE),
        "deep_risk_characteristics": list(DEEP_RISK_CHARACTERISTICS),
        "allowed_risk_characteristics": list(ALLOWED_RISK_CHARACTERISTICS),
        "evidence_layers": list(EVIDENCE_LAYERS),
        "evidence_scopes": list(EVIDENCE_SCOPES),
        "evidence_scope_coverage": {
            key: list(value) for key, value in EVIDENCE_SCOPE_COVERAGE.items()
        },
        "evidence_scope_rule": "EVIDENCE_SCOPE_MUST_COVER_CLAIM_SCOPE",
        "version_context": {
            "work_unit_field": "version_ref",
            "receipt_field": "version_ref",
            "decision_field": "version_ref",
            "current_identity_parameter": "current_version_ref",
            "failure_code": FAIL_STALE_VERSION,
        },
        "protected_prai_paths": list(PRAI_PROTECTED_PATHS),
        "triggered_specialists": {
            key: list(value) for key, value in TRIGGERED_SPECIALISTS.items()
        },
        "required_work_unit_fields": list(REQUIRED_WORK_UNIT_FIELDS),
        "work_unit_fields": list(WORK_UNIT_FIELDS),
        "receipt_fields": list(RECEIPT_FIELDS),
        "decision_fields": list(DECISION_FIELDS),
        "required_negative_fixtures": list(REQUIRED_NEGATIVE_FIXTURES),
        "required_property_invariants": list(REQUIRED_PROPERTY_INVARIANTS),
        "security_no_material_impact": SECURITY_NO_MATERIAL_IMPACT,
    }
    for key, expected_value in expected.items():
        if data.get(key) != expected_value:
            raise ValueError(f"PRAI machine contract drift: {key}")
    if data.get("authority") != {
        "execution": False,
        "merge": False,
        "release": False,
        "provider_routing": False,
        "production": False,
    }:
        raise ValueError("PRAI machine contract authority drift")
    return data


def validate_prai_schema(
    schema: Mapping[str, Any],
    work_unit: Mapping[str, Any],
) -> Mapping[str, Any]:
    schema_data = _mapping(schema, "schema")
    payload = _mapping(work_unit, "work_unit")
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: jsonschema is required") from exc
    try:
        Draft202012Validator.check_schema(schema_data)
        errors = sorted(
            Draft202012Validator(schema_data).iter_errors(payload),
            key=lambda item: tuple(str(value) for value in item.absolute_path),
        )
    except Exception as exc:
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: {exc}") from exc
    if errors:
        error = errors[0]
        location = ".".join(str(value) for value in error.absolute_path) or "<root>"
        raise ValueError(
            f"{FAIL_SCHEMA_RUNTIME_PARITY}: schema rejected work unit at "
            f"{location}: {error.message}"
        )
    return payload


def validate_schema_runtime_parity(
    contract: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> Mapping[str, Any]:
    data = validate_prai_contract(contract)
    schema_data = _mapping(schema, "schema")
    try:
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(schema_data)
    except ImportError as exc:
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: jsonschema is required") from exc
    except Exception as exc:
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: {exc}") from exc
    properties = schema_data.get("properties")
    if not isinstance(properties, Mapping):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: work-unit properties are missing")
    if set(properties) != set(WORK_UNIT_FIELDS):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: work-unit properties drift")
    if set(schema_data.get("required", ())) != set(REQUIRED_WORK_UNIT_FIELDS):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: work-unit required fields drift")
    if schema_data.get("additionalProperties") is not False:
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: work-unit openness drift")
    version_schema = properties.get("version_ref")
    if (
        not isinstance(version_schema, Mapping)
        or version_schema.get("type") != "string"
        or version_schema.get("minLength") != 1
    ):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: work-unit version context drift")
    risk_schema = properties.get("risk_characteristics")
    if not isinstance(risk_schema, Mapping):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: risk-characteristic schema is missing")
    risk_items = risk_schema.get("items")
    if not isinstance(risk_items, Mapping):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: risk-characteristic items are missing")
    if list(risk_items.get("enum", ())) != list(ALLOWED_RISK_CHARACTERISTICS):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: risk-characteristic allowlist drift")

    definitions = schema_data.get("$defs")
    if not isinstance(definitions, Mapping):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: receipt definitions are missing")
    receipt_schema = definitions.get("receipt")
    if not isinstance(receipt_schema, Mapping):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: receipt schema is missing")
    receipt_properties = receipt_schema.get("properties")
    if not isinstance(receipt_properties, Mapping):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: receipt properties are missing")
    if set(receipt_properties) != set(RECEIPT_FIELDS):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: receipt properties drift")
    if set(receipt_schema.get("required", ())) != set(RECEIPT_FIELDS) - {"digest"}:
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: receipt required fields drift")
    if receipt_schema.get("additionalProperties") is not False:
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: receipt openness drift")
    for field, vocabulary in (
        ("evidence_layer", EVIDENCE_LAYERS),
        ("evidence_scope", EVIDENCE_SCOPES),
        ("claim_scope", EVIDENCE_SCOPES),
    ):
        scope_schema = receipt_properties.get(field)
        if (
            not isinstance(scope_schema, Mapping)
            or list(scope_schema.get("enum", ())) != list(vocabulary)
        ):
            raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: {field} vocabulary drift")
    receipt_version_schema = receipt_properties.get("version_ref")
    if (
        not isinstance(receipt_version_schema, Mapping)
        or receipt_version_schema.get("type") != "string"
        or receipt_version_schema.get("minLength") != 1
    ):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: receipt version context drift")
    logical_schema = receipt_properties.get("logical_identity")
    if (
        not isinstance(logical_schema, Mapping)
        or logical_schema.get("pattern") != "^[a-f0-9]{64}$"
    ):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: logical identity drift")

    decision_schema = definitions.get("decision")
    if not isinstance(decision_schema, Mapping):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: decision schema is missing")
    decision_properties = decision_schema.get("properties")
    if not isinstance(decision_properties, Mapping):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: decision properties are missing")
    if set(decision_properties) != set(DECISION_FIELDS):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: decision properties drift")
    if set(decision_schema.get("required", ())) != set(DECISION_FIELDS) - {"decision_digest"}:
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: decision required fields drift")
    if decision_schema.get("additionalProperties") is not False:
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: decision openness drift")
    decision_version_schema = decision_properties.get("version_ref")
    if (
        not isinstance(decision_version_schema, Mapping)
        or decision_version_schema.get("type") != "string"
        or decision_version_schema.get("minLength") != 1
    ):
        raise ValueError(f"{FAIL_SCHEMA_RUNTIME_PARITY}: decision version context drift")
    return data


validate_prai_machine_contract = validate_prai_contract
evaluate_prai = evaluate_post_run_assurance
evaluate = evaluate_post_run_assurance

__all__ = [
    "ALLOWED_RISK_CHARACTERISTICS",
    "ARBITER_DISPOSITIONS",
    "EVIDENCE_LAYERS",
    "EVIDENCE_SCOPES",
    "EVIDENCE_SCOPE_COVERAGE",
    "AUDIT_DEPTHS",
    "BASELINE_ASSURANCE",
    "BASELINE_REVIEWERS",
    "DEEP_RISK_CHARACTERISTICS",
    "DECISION_FIELDS",
    "FAIL_ASSURANCE_COVERAGE",
    "FAIL_AUTHORITY_EXPANSION",
    "FAIL_CALLER_CONTRACT",
    "FAIL_SCHEMA_RUNTIME_PARITY",
    "FAIL_CHANGED_CODE_UNEXAMINED",
    "FAIL_CONTRADICTORY_RECEIPT",
    "FAIL_CURRENT_IDENTITY_REQUIRED",
    "FAIL_UNKNOWN_RISK_CHARACTERISTIC",
    "FAIL_DUPLICATE_RECEIPT",
    "FAIL_EVIDENCE_BINDING",
    "FAIL_EVIDENCE_LAYER",
    "FAIL_EVIDENCE_SCOPE",
    "FAIL_GENERIC_CI_SUBSTITUTION",
    "FAIL_IMPLEMENTER_SELF_CERTIFICATION",
    "FAIL_INVALID_RECEIPT_RESULT",
    "FAIL_LOGICAL_CONTRADICTION",
    "FAIL_LOGICAL_IDENTITY",
    "FAIL_NON_INDEPENDENT_EVIDENCE",
    "FAIL_OVERSEER_INSUFFICIENT",
    "FAIL_POLICY_SELF_MODIFICATION",
    "FAIL_REQUIRED_ASSURANCE",
    "FAIL_REQUIRED_AUDIT_DEPTH",
    "FAIL_REQUIRED_LOGICAL_ASSURANCE",
    "FAIL_REQUIRED_OVERSEER_ASSURANCE",
    "FAIL_REQUIRED_REVIEWER",
    "FAIL_REQUIRED_SECURITY_ASSURANCE",
    "FAIL_SCOPE_EXCEEDED",
    "FAIL_SECURITY_CLASSIFICATION",
    "FAIL_SECURITY_FINDING",
    "FAIL_STALE_CANDIDATE",
    "FAIL_STALE_FRESHNESS",
    "FAIL_STALE_VERSION",
    "FAIL_STALE_REPOSITORY",
    "FAIL_STALE_SOURCE",
    "FAIL_STALE_TREE",
    "FAIL_STALE_WORK_ITEM",
    "IMPACT_LEVELS",
    "PRAI_AUTHORITY_BOUNDARY",
    "PRAI_AUTHORITY_MODEL",
    "PRAI_CONTRACT_SCHEMA_VERSION",
    "PRAI_DECISION_SCHEMA_VERSION",
    "PRAI_PROTECTED_PATHS",
    "PraiDecision",
    "PraiReviewReceipt",
    "PraiWorkUnit",
    "RECEIPT_FIELDS",
    "REQUIRED_NEGATIVE_FIXTURES",
    "REQUIRED_PROPERTY_INVARIANTS",
    "REQUIRED_WORK_UNIT_FIELDS",
    "REVIEW_RESULTS",
    "REVIEW_ROLES",
    "SECURITY_NO_MATERIAL_IMPACT",
    "TRIGGERED_SPECIALISTS",
    "WORK_UNIT_FIELDS",
    "evaluate",
    "evaluate_prai",
    "evaluate_post_run_assurance",
    "required_audit_depth",
    "triggered_reviewers",
    "validate_prai_schema",
    "validate_prai_contract",
    "validate_prai_machine_contract",
    "validate_schema_runtime_parity",
]
