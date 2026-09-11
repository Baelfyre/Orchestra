"""Deterministic, evidence-only AQ14 final ADAPT-QA effectiveness qualification."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any

AQ14_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
TARGET_REPOSITORY = "Baelfyre/Orchestra"
CANONICAL_START_SHA = "34eb2a38a97f6d1acef6bbd206da8795393457de"
QUALIFICATION_MODE = "CONTROLLED_NON_PRODUCTION_FINAL_EFFECTIVENESS_QUALIFICATION"
CUD10_HOLD_STATE = "READY_NOT_STARTED_HELD_BY_CURRENT_USER"
REQUIRED_PHASES = ("AQ9", "AQ10", "AQ11", "AQ12", "AQ13")
PHASE_DISPOSITIONS = ("PASS", "WAIT_FOR_EVIDENCE", "REVISION_REQUIRED", "HOLD")
EXPECTED_PHASE_IDENTITIES = {
    "AQ9": {
        "canonical_pr": 907,
        "canonical_sha": "b5b6e1761e9ebf265e3e2b3ffbfc17a52c6c99b3",
        "canonical_tree": "ac90102a77339baff72b5ca52e512885e47f2819",
    },
    "AQ10": {
        "canonical_pr": 913,
        "canonical_sha": "2fa5d648b5b19d483ecbe2342f5a28927a85d28f",
        "canonical_tree": "e9199f374d5c6b1f32b3c52f826e0141d021b4d3",
    },
    "AQ11": {
        "canonical_pr": 916,
        "canonical_sha": "34c7fcf45ee42db92289479c1ec8e0b425af29e7",
        "canonical_tree": "6832c5050a5319876cded35e4a206dc44c10b050",
    },
    "AQ12": {
        "canonical_pr": 919,
        "canonical_sha": "2fc2d9ce9fc263813981e4dc8c88d1e4f604f036",
        "canonical_tree": "85681748eb895898d8c941c69b0ddd5da1da754c",
    },
    "AQ13": {
        "canonical_pr": 922,
        "canonical_sha": "34eb2a38a97f6d1acef6bbd206da8795393457de",
        "canonical_tree": "60e8410e0031f2977c920f429afccad5f983ce2a",
    },
}
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be non-empty")
    if any(ord(char) < 32 for char in cleaned):
        raise ValueError(f"{field_name} must not contain control characters")
    return cleaned


def _sha(value: Any, field_name: str) -> str:
    cleaned = _text(value, field_name).lower()
    if not _SHA_RE.fullmatch(cleaned):
        raise ValueError(f"{field_name} must be an exact 40-character lowercase Git SHA")
    return cleaned


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _nonnegative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _boolean(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be boolean")
    return value


@dataclass(frozen=True, slots=True)
class QualificationContext:
    repository: str
    canonical_sha: str
    mode: str
    cud10_state: str
    protected_policy_mutation_performed: bool = False
    production_mutation_performed: bool = False
    provider_activation_performed: bool = False
    telemetry_activation_performed: bool = False
    release_or_deploy_performed: bool = False
    aq15_authorized: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository", _text(self.repository, "repository"))
        object.__setattr__(self, "canonical_sha", _sha(self.canonical_sha, "canonical_sha"))
        object.__setattr__(self, "mode", _text(self.mode, "mode").upper())
        object.__setattr__(self, "cud10_state", _text(self.cud10_state, "cud10_state").upper())
        if self.repository != TARGET_REPOSITORY:
            raise ValueError("AQ14 target repository must remain Orchestra")
        if self.canonical_sha != CANONICAL_START_SHA:
            raise ValueError("AQ14 baseline must match canonical AQ13 closeout")
        if self.mode != QUALIFICATION_MODE:
            raise ValueError("AQ14 must remain a controlled non-production final qualification")
        if self.cud10_state != CUD10_HOLD_STATE:
            raise ValueError("AQ14 cannot alter the CritiQual CUD10 hold state")
        flags = {
            "protected_policy_mutation_performed": self.protected_policy_mutation_performed,
            "production_mutation_performed": self.production_mutation_performed,
            "provider_activation_performed": self.provider_activation_performed,
            "telemetry_activation_performed": self.telemetry_activation_performed,
            "release_or_deploy_performed": self.release_or_deploy_performed,
            "aq15_authorized": self.aq15_authorized,
        }
        for name, value in flags.items():
            _boolean(value, name)
            if value:
                raise ValueError(f"AQ14 boundary violation: {name}")


@dataclass(frozen=True, slots=True)
class PhaseEvidence:
    phase_id: str
    canonical_pr: int
    canonical_sha: str
    canonical_tree: str
    disposition: str
    canonical_verified: bool
    source_assurance_pass: bool
    promotion_assurance_pass: bool
    post_merge_assurance_pass: bool
    independent_evidence: bool
    deterministic_evidence: bool
    unresolved_critical_findings: int = 0

    def __post_init__(self) -> None:
        phase_id = _text(self.phase_id, "phase_id").upper()
        if phase_id not in REQUIRED_PHASES:
            raise ValueError(f"unsupported AQ14 phase_id: {phase_id}")
        object.__setattr__(self, "phase_id", phase_id)
        object.__setattr__(self, "canonical_pr", _positive_int(self.canonical_pr, "canonical_pr"))
        object.__setattr__(self, "canonical_sha", _sha(self.canonical_sha, "canonical_sha"))
        object.__setattr__(self, "canonical_tree", _sha(self.canonical_tree, "canonical_tree"))
        disposition = _text(self.disposition, "disposition").upper()
        if disposition not in PHASE_DISPOSITIONS:
            raise ValueError(f"disposition must be one of {PHASE_DISPOSITIONS}")
        object.__setattr__(self, "disposition", disposition)
        for name in (
            "canonical_verified", "source_assurance_pass", "promotion_assurance_pass",
            "post_merge_assurance_pass", "independent_evidence", "deterministic_evidence",
        ):
            _boolean(getattr(self, name), name)
        object.__setattr__(
            self,
            "unresolved_critical_findings",
            _nonnegative_int(self.unresolved_critical_findings, "unresolved_critical_findings"),
        )
        expected = EXPECTED_PHASE_IDENTITIES[phase_id]
        if self.canonical_pr != expected["canonical_pr"]:
            raise ValueError(f"{phase_id} canonical PR identity drift")
        if self.canonical_sha != expected["canonical_sha"]:
            raise ValueError(f"{phase_id} canonical SHA identity drift")
        if self.canonical_tree != expected["canonical_tree"]:
            raise ValueError(f"{phase_id} canonical tree identity drift")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PhaseEvidence":
        if not isinstance(value, Mapping):
            raise TypeError("phase evidence must be a mapping")
        required = {
            "phase_id", "canonical_pr", "canonical_sha", "canonical_tree", "disposition",
            "canonical_verified", "source_assurance_pass", "promotion_assurance_pass",
            "post_merge_assurance_pass", "independent_evidence", "deterministic_evidence",
            "unresolved_critical_findings",
        }
        if set(value) != required:
            raise ValueError("phase evidence fields must match the AQ14 contract")
        return cls(**{key: value[key] for key in required})


@dataclass(frozen=True, slots=True)
class PhaseQualificationFinding:
    phase_id: str
    qualified: bool
    disposition: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FinalEffectivenessQualification:
    disposition: str
    findings: tuple[PhaseQualificationFinding, ...]
    phase_count: int
    qualified_count: int
    unresolved_count: int
    reason_codes: tuple[str, ...]
    authority_granted: bool = False
    transition_authorized: bool = False
    release_authorized: bool = False
    production_authorized: bool = False
    aq15_authorized: bool = False
    cud10_admission_authorized: bool = False
    organic_effectiveness_claimed: bool = False
    production_readiness_claimed: bool = False


def _evaluate_phase(evidence: PhaseEvidence) -> PhaseQualificationFinding:
    reasons: list[str] = []
    if evidence.disposition in {"REVISION_REQUIRED", "HOLD"}:
        reasons.append("AQ14_PRIOR_PHASE_BLOCKING_DISPOSITION")
    elif evidence.disposition == "WAIT_FOR_EVIDENCE":
        reasons.append("AQ14_PRIOR_PHASE_EVIDENCE_INCOMPLETE")
    if evidence.unresolved_critical_findings:
        reasons.append("AQ14_UNRESOLVED_CRITICAL_FINDING")
    if not evidence.canonical_verified:
        reasons.append("AQ14_CANONICAL_VERIFICATION_REQUIRED")
    if not evidence.source_assurance_pass:
        reasons.append("AQ14_SOURCE_ASSURANCE_REQUIRED")
    if not evidence.promotion_assurance_pass:
        reasons.append("AQ14_PROMOTION_ASSURANCE_REQUIRED")
    if not evidence.post_merge_assurance_pass:
        reasons.append("AQ14_POST_MERGE_ASSURANCE_REQUIRED")
    if not evidence.independent_evidence:
        reasons.append("AQ14_INDEPENDENT_EVIDENCE_REQUIRED")
    if not evidence.deterministic_evidence:
        reasons.append("AQ14_DETERMINISTIC_EVIDENCE_REQUIRED")
    qualified = not reasons and evidence.disposition == "PASS"
    if qualified:
        reasons.append("AQ14_PHASE_EVIDENCE_QUALIFIED")
    return PhaseQualificationFinding(
        phase_id=evidence.phase_id,
        qualified=qualified,
        disposition=evidence.disposition,
        reason_codes=tuple(reasons),
    )


def evaluate_final_effectiveness(
    context: QualificationContext,
    evidence: Iterable[PhaseEvidence],
) -> FinalEffectivenessQualification:
    if not isinstance(context, QualificationContext):
        raise TypeError("context must be QualificationContext")
    if isinstance(evidence, (str, bytes)):
        raise TypeError("evidence must be an iterable of PhaseEvidence")
    materialized = tuple(evidence)
    if any(not isinstance(item, PhaseEvidence) for item in materialized):
        raise TypeError("evidence must contain only PhaseEvidence values")
    phases = tuple(item.phase_id for item in materialized)
    if phases != REQUIRED_PHASES:
        raise ValueError("AQ14 requires exactly AQ9 through AQ13 in canonical phase order")

    findings = tuple(_evaluate_phase(item) for item in materialized)
    qualified_count = sum(item.qualified for item in findings)
    unresolved_count = len(findings) - qualified_count

    if any(
        item.disposition in {"REVISION_REQUIRED", "HOLD"}
        or item.unresolved_critical_findings > 0
        for item in materialized
    ):
        disposition = "REVISION_REQUIRED"
        reasons = (
            "AQ14_BLOCKING_EVIDENCE_PRESENT",
            "AQ14_FINAL_QUALIFICATION_NON_AUTHORIZING",
        )
    elif any(
        item.disposition == "WAIT_FOR_EVIDENCE"
        or not item.canonical_verified
        or not item.source_assurance_pass
        or not item.promotion_assurance_pass
        or not item.post_merge_assurance_pass
        or not item.independent_evidence
        or not item.deterministic_evidence
        for item in materialized
    ):
        disposition = "WAIT_FOR_EVIDENCE"
        reasons = (
            "AQ14_EVIDENCE_CHAIN_INCOMPLETE",
            "AQ14_FINAL_QUALIFICATION_NON_AUTHORIZING",
        )
    else:
        disposition = "PASS"
        reasons = (
            "AQ14_CONTROLLED_EFFECTIVENESS_CHAIN_QUALIFIED",
            "AQ14_PASS_IS_EVIDENCE_ONLY_NON_AUTHORIZING",
            "AQ14_NO_ORGANIC_OR_PRODUCTION_READINESS_CLAIM",
            "AQ14_AQ15_NOT_AUTHORIZED",
            "AQ14_CUD10_HOLD_PRESERVED",
        )

    return FinalEffectivenessQualification(
        disposition=disposition,
        findings=findings,
        phase_count=len(findings),
        qualified_count=qualified_count,
        unresolved_count=unresolved_count,
        reason_codes=reasons,
    )
