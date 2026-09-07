"""Pure domain rules for the AQ-1 adaptive assurance doctrine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

AQ1_DOCTRINE_SCHEMA_VERSION = "orchestra.adaptive-assurance-doctrine.v1"

DEVELOPMENT_MODES = (
    "SPEC_FIRST",
    "DISCOVERY_FIRST",
    "AS_BUILT",
    "RECONCILIATION",
    "DEFECT_DRIVEN",
    "MAINTENANCE",
)

SOURCE_TRUTH_LABELS = ("OBSERVED", "INFERRED", "DECIDED", "UNVERIFIED")

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

PROVENANCE_QUALIFICATIONS = ("AUTHORITATIVE", "SELF_ASSERTED", "UNQUALIFIED")

COMPLETION_STATES = (
    "IDEATED",
    "PROTOTYPED",
    "DOMAIN_IMPLEMENTED",
    "APPLICATION_INTEGRATED",
    "API_INTEGRATED",
    "UI_INTEGRATED",
    "UNIT_VERIFIED",
    "CONTRACT_VERIFIED",
    "INTEGRATION_VERIFIED",
    "RUNTIME_VERIFIED",
    "SECURITY_VERIFIED",
    "ADVERSARIALLY_VERIFIED",
    "CANONICAL_VERIFIED",
    "PRODUCT_COMPLETE",
)

CLAIM_SCOPE_BY_STATE = {
    "IDEATED": "COMPLETION",
    "PROTOTYPED": "COMPLETION",
    "DOMAIN_IMPLEMENTED": "DOMAIN",
    "APPLICATION_INTEGRATED": "APPLICATION",
    "API_INTEGRATED": "API",
    "UI_INTEGRATED": "UI",
    "UNIT_VERIFIED": "UNIT",
    "CONTRACT_VERIFIED": "CONTRACT",
    "INTEGRATION_VERIFIED": "INTEGRATION",
    "RUNTIME_VERIFIED": "RUNTIME",
    "SECURITY_VERIFIED": "SECURITY",
    "ADVERSARIALLY_VERIFIED": "ADVERSARIAL",
    "CANONICAL_VERIFIED": "CANONICAL",
    "PRODUCT_COMPLETE": "PRODUCT",
}

REQUIRED_EVIDENCE_LAYERS = {
    "IDEATED": ("COMPLETION_STATE",),
    "PROTOTYPED": ("COMPLETION_STATE",),
    "DOMAIN_IMPLEMENTED": ("DOMAIN",),
    "APPLICATION_INTEGRATED": ("INTEGRATION",),
    "API_INTEGRATED": ("INTEGRATION",),
    "UI_INTEGRATED": ("INTEGRATION",),
    "UNIT_VERIFIED": ("UNIT",),
    "CONTRACT_VERIFIED": ("CONTRACT",),
    "INTEGRATION_VERIFIED": ("INTEGRATION",),
    "RUNTIME_VERIFIED": ("HTTP", "RUNTIME"),
    "SECURITY_VERIFIED": ("SECURITY",),
    "ADVERSARIALLY_VERIFIED": ("ADVERSARIAL", "MUTATION"),
    "CANONICAL_VERIFIED": ("PROVENANCE",),
    "PRODUCT_COMPLETE": ("COMPLETION_STATE",),
}

REQUIRED_EVIDENCE_METADATA = (
    "originating_source",
    "authoritative_source_ref",
    "producer",
    "validator",
    "source_ref",
    "candidate_ref",
    "work_item_ref",
    "freshness_ref",
    "version_ref",
    "provenance_qualification",
    "evidence_layer",
    "evidence_scope",
    "claim_scope",
    "authority_ref",
)

REQUIRED_VERIFIER_CONTEXT = (
    "source_ref",
    "candidate_ref",
    "work_item_ref",
    "freshness_ref",
    "version_ref",
    "verified_authority_ref",
)

# A scope relation is explicit coverage, not an assumption that one layer proves another.
_SCOPE_COVERAGE = {
    "SOURCE": {"SOURCE"},
    "COMPLETION": {"COMPLETION"},
    "DOMAIN": {"DOMAIN"},
    "APPLICATION": {"DOMAIN", "APPLICATION"},
    "API": {"API", "APPLICATION", "DOMAIN"},
    "UI": {"UI", "APPLICATION", "DOMAIN"},
    "UNIT": {"UNIT"},
    "CONTRACT": {"CONTRACT"},
    "INTEGRATION": {"INTEGRATION", "APPLICATION", "API", "UI", "DOMAIN"},
    "RUNTIME": {"RUNTIME", "INTEGRATION", "APPLICATION", "API", "UI", "DOMAIN"},
    "PERSISTENCE": {"PERSISTENCE"},
    "CONCURRENCY": {"CONCURRENCY"},
    "SECURITY": {"SECURITY"},
    "ADVERSARIAL": {"ADVERSARIAL"},
    "CANONICAL": {"CANONICAL"},
    "PRODUCT": {"PRODUCT"},
    "EMPIRICAL_EFFECTIVENESS": {"EMPIRICAL_EFFECTIVENESS"},
}


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _one_of(value: object, choices: tuple[str, ...], field_name: str) -> str:
    normalized = _text(value, field_name)
    if normalized not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return normalized


def _states(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("states must be an iterable of state strings")
    normalized = tuple(_one_of(value, COMPLETION_STATES, "completion state") for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError("completion states must not contain duplicates")
    return normalized


@dataclass(frozen=True, slots=True)
class AssuranceEvidence:
    evidence_id: str
    claimed_state: str
    source_truth: str
    authority_ref: str | None = None
    originating_source: str | None = None
    authoritative_source_ref: str | None = None
    producer: str | None = None
    validator: str | None = None
    source_ref: str | None = None
    candidate_ref: str | None = None
    work_item_ref: str | None = None
    freshness_ref: str | None = None
    version_ref: str | None = None
    provenance_qualification: str = "UNQUALIFIED"
    evidence_type: str | None = None
    evidence_layer: str | None = None
    evidence_scope: str | None = None
    claim_scope: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))
        object.__setattr__(
            self,
            "claimed_state",
            _one_of(self.claimed_state, COMPLETION_STATES, "claimed_state"),
        )
        object.__setattr__(
            self,
            "source_truth",
            _one_of(self.source_truth, SOURCE_TRUTH_LABELS, "source_truth"),
        )
        if self.authority_ref is not None:
            object.__setattr__(self, "authority_ref", _text(self.authority_ref, "authority_ref"))
        for field_name in (
            "originating_source",
            "authoritative_source_ref",
            "producer",
            "validator",
            "source_ref",
            "candidate_ref",
            "work_item_ref",
            "freshness_ref",
            "version_ref",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _text(value, field_name))
        object.__setattr__(
            self,
            "provenance_qualification",
            _one_of(
                self.provenance_qualification,
                PROVENANCE_QUALIFICATIONS,
                "provenance_qualification",
            ),
        )
        evidence_type = self.evidence_type
        evidence_layer = self.evidence_layer
        if evidence_type is not None:
            evidence_type = _one_of(evidence_type, EVIDENCE_LAYERS, "evidence_type")
        if evidence_layer is not None:
            evidence_layer = _one_of(evidence_layer, EVIDENCE_LAYERS, "evidence_layer")
        if evidence_type is not None and evidence_layer is not None and evidence_type != evidence_layer:
            raise ValueError("evidence_type and evidence_layer must match")
        if evidence_layer is None:
            evidence_layer = evidence_type
        object.__setattr__(self, "evidence_type", evidence_layer)
        object.__setattr__(self, "evidence_layer", evidence_layer)
        for field_name in ("evidence_scope", "claim_scope"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _one_of(value, EVIDENCE_SCOPES, field_name),
                )


@dataclass(frozen=True, slots=True)
class CompletionAssessment:
    explicit_states: tuple[str, ...]
    target_state: str
    canonical_proves_empirical_effectiveness: bool = False
    product_complete: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "explicit_states", _states(self.explicit_states))
        object.__setattr__(
            self,
            "target_state",
            _one_of(self.target_state, COMPLETION_STATES, "target_state"),
        )
        if self.canonical_proves_empirical_effectiveness:
            raise ValueError("CANONICAL_VERIFIED cannot prove empirical effectiveness")


def validate_development_mode(mode: str) -> str:
    """Return a declared mode or fail closed on an unknown mode."""

    return _one_of(mode, DEVELOPMENT_MODES, "development mode")


def transition_mode(current_mode: str, target_mode: str) -> str:
    """Support explicit transitions among all declared AQ-1 modes."""

    validate_development_mode(current_mode)
    return validate_development_mode(target_mode)


def select_mode_for_evidence(current_mode: str, *, conflicting_sources: bool = False) -> str:
    """Select reconciliation when authoritative sources conflict."""

    current = validate_development_mode(current_mode)
    if not isinstance(conflicting_sources, bool):
        raise TypeError("conflicting_sources must be a bool")
    return "RECONCILIATION" if conflicting_sources else current


def validate_completion_escalation(
    current_states: Iterable[str],
    target_state: str,
    evidence: Iterable[AssuranceEvidence],
    *,
    claim_source_truth: str = "OBSERVED",
    authority_ref: str | None = None,
    source_ref: str | None = None,
    candidate_ref: str | None = None,
    work_item_ref: str | None = None,
    freshness_ref: str | None = None,
    version_ref: str | None = None,
    verified_authority_ref: str | None = None,
) -> CompletionAssessment:
    """Validate one explicit state claim without inferring higher states."""

    current = _states(current_states)
    target = _one_of(target_state, COMPLETION_STATES, "target_state")
    claim_truth = _one_of(claim_source_truth, SOURCE_TRUTH_LABELS, "claim_source_truth")
    records = tuple(evidence)
    if any(not isinstance(record, AssuranceEvidence) for record in records):
        raise TypeError("evidence must contain AssuranceEvidence values")
    if not records:
        raise ValueError("completion-state qualification requires evidence")
    evidence_ids = tuple(record.evidence_id for record in records)
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("evidence_id values must be unique within one completion assessment")
    if claim_truth == "UNVERIFIED" or any(record.source_truth == "UNVERIFIED" for record in records):
        raise ValueError("UNVERIFIED evidence cannot qualify a completion claim")
    if any(record.claimed_state != target for record in records):
        raise ValueError("completion evidence must claim the target state")
    if verified_authority_ref is None:
        raise ValueError("verifier-owned authority reference is required")
    verified_authority = _text(verified_authority_ref, "verified_authority_ref")
    required_scope = CLAIM_SCOPE_BY_STATE[target]
    required_layers = REQUIRED_EVIDENCE_LAYERS[target]
    for record in records:
        if record.provenance_qualification != "AUTHORITATIVE":
            raise ValueError("completion evidence requires authoritative provenance")
        missing = [field for field in REQUIRED_EVIDENCE_METADATA if getattr(record, field) is None]
        if missing:
            raise ValueError("completion evidence metadata is incomplete: " + ", ".join(missing))
        if record.authority_ref != verified_authority:
            raise ValueError("evidence authority does not match verifier-owned authority")
        if record.authoritative_source_ref != record.source_ref:
            raise ValueError("authoritative source reference must match bound source")
        if record.claim_scope != required_scope:
            raise ValueError("evidence claim scope does not match target state")
        if record.evidence_layer not in required_layers:
            raise ValueError("evidence layer is insufficient for target state")
        if required_scope not in _SCOPE_COVERAGE[record.evidence_scope]:
            raise ValueError("evidence scope is insufficient for claim scope")

    present_layers = {record.evidence_layer for record in records}
    missing_layers = tuple(layer for layer in required_layers if layer not in present_layers)
    if missing_layers:
        raise ValueError("evidence layers are incomplete: " + ", ".join(missing_layers))

    def _check_binding(field_name: str, expected: str | None) -> None:
        if expected is None:
            raise ValueError(f"verifier context requires {field_name}")
        expected_value = _text(expected, field_name)
        values = tuple(getattr(record, field_name) for record in records)
        if any(value is None for value in values) or len(set(values)) != 1:
            raise ValueError(f"evidence {field_name} is not consistently bound")
        if values[0] != expected_value:
            raise ValueError(f"evidence {field_name} does not match requested subject")

    for field_name, expected in (
        ("source_ref", source_ref),
        ("candidate_ref", candidate_ref),
        ("work_item_ref", work_item_ref),
        ("freshness_ref", freshness_ref),
        ("version_ref", version_ref),
    ):
        _check_binding(field_name, expected)

    authority = None if authority_ref is None else _text(authority_ref, "authority_ref")
    has_inferred_support = any(record.source_truth == "INFERRED" for record in records)
    if has_inferred_support and claim_truth == "OBSERVED":
        raise ValueError("INFERRED evidence cannot qualify an OBSERVED claim")
    if claim_truth == "DECIDED" and authority is None:
        raise ValueError("DECIDED completion claims require authority")
    if claim_truth == "DECIDED" and has_inferred_support:
        if any(record.authority_ref != authority for record in records if record.source_truth == "INFERRED"):
            raise ValueError("INFERRED evidence cannot become DECIDED without authority")
    if claim_truth == "INFERRED" and target not in {"IDEATED", "PROTOTYPED"} and authority is None:
        raise ValueError("inferred completion claims require authority beyond prototype states")
    if any(record.source_truth == "DECIDED" for record in records) and (
        authority is None or any(record.authority_ref != authority for record in records if record.source_truth == "DECIDED")
    ):
        raise ValueError("DECIDED evidence requires authority")

    explicit = tuple(dict.fromkeys((*current, target)))
    return CompletionAssessment(
        explicit_states=explicit,
        target_state=target,
        product_complete=target == "PRODUCT_COMPLETE",
    )


def validate_product_complete(
    mode: str,
    current_states: Iterable[str],
    evidence: Iterable[AssuranceEvidence],
    *,
    claim_source_truth: str = "OBSERVED",
    authority_ref: str | None = None,
    reconciled: bool = False,
    source_ref: str | None = None,
    candidate_ref: str | None = None,
    work_item_ref: str | None = None,
    freshness_ref: str | None = None,
    version_ref: str | None = None,
    verified_authority_ref: str | None = None,
) -> CompletionAssessment:
    """Apply the product-complete gates that AQ-1 makes explicit."""

    selected_mode = validate_development_mode(mode)
    if not isinstance(reconciled, bool):
        raise TypeError("reconciled must be a bool")
    assessment = validate_completion_escalation(
        current_states,
        "PRODUCT_COMPLETE",
        evidence,
        claim_source_truth=claim_source_truth,
        authority_ref=authority_ref,
        source_ref=source_ref,
        candidate_ref=candidate_ref,
        work_item_ref=work_item_ref,
        freshness_ref=freshness_ref,
        version_ref=version_ref,
        verified_authority_ref=verified_authority_ref,
    )
    state_set = set(assessment.explicit_states)
    if selected_mode == "DISCOVERY_FIRST" and not reconciled:
        raise ValueError("DISCOVERY_FIRST requires RECONCILIATION before PRODUCT_COMPLETE")
    if "DOMAIN_IMPLEMENTED" in state_set and "APPLICATION_INTEGRATED" not in state_set:
        raise ValueError("domain-only implementation cannot be represented as product integration")
    return assessment


__all__ = [
    "AQ1_DOCTRINE_SCHEMA_VERSION",
    "AssuranceEvidence",
    "CLAIM_SCOPE_BY_STATE",
    "COMPLETION_STATES",
    "CompletionAssessment",
    "DEVELOPMENT_MODES",
    "EVIDENCE_LAYERS",
    "EVIDENCE_SCOPES",
    "PROVENANCE_QUALIFICATIONS",
    "REQUIRED_EVIDENCE_METADATA",
    "REQUIRED_EVIDENCE_LAYERS",
    "REQUIRED_VERIFIER_CONTEXT",
    "SOURCE_TRUTH_LABELS",
    "select_mode_for_evidence",
    "transition_mode",
    "validate_completion_escalation",
    "validate_development_mode",
    "validate_product_complete",
]
