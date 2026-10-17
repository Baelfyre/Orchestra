"""Provider-independent contracts for optional JEV mitigation adjudication."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from typing import Any, Mapping

from ...shared.canonicalization import canonical_json_bytes, normalize_git_sha, normalize_sha256, receipt_digest


JEV_ADJUDICATION_CONTRACT = "orchestra.jev.adjudication.v1"
JEV_ADVISORY_RECOMMENDATION_AVAILABLE = "JEV_ADVISORY_RECOMMENDATION_AVAILABLE"
JEV_ADVISORY_INCONCLUSIVE = "JEV_ADVISORY_INCONCLUSIVE"
JEV_ADVISORY_STALE = "JEV_ADVISORY_STALE"
JEV_ADVISORY_UNBOUND = "JEV_ADVISORY_UNBOUND"
JEV_NOT_REQUIRED = "JEV_NOT_REQUIRED"
JEV_UNAVAILABLE = "JEV_UNAVAILABLE"
JEV_STATES = frozenset(
    {
        JEV_ADVISORY_RECOMMENDATION_AVAILABLE,
        JEV_ADVISORY_INCONCLUSIVE,
        JEV_ADVISORY_STALE,
        JEV_ADVISORY_UNBOUND,
        JEV_NOT_REQUIRED,
        JEV_UNAVAILABLE,
    }
)

TYPESAFE_SYSTEM_ONE_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
TYPESAFE_JEV_MODEL = "jev-latest"
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_STABLE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
_RESOLVED_MODEL_RE = re.compile(r"^jev-[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_RISK_LEVELS = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})
_ASSURANCE_DEPTHS = frozenset({"LIGHT", "STANDARD", "DEEP"})
JEV_VERIFICATION_RESULTS = frozenset(
    {"CONFIRMED", "INCOMPLETE", "NOT_STARTED", "PENDING", "RUNNING"}
)
_INCOMPLETE_VERIFICATION_RESULTS = JEV_VERIFICATION_RESULTS - {"CONFIRMED"}
_PROVIDER_FAILURE_CODES = frozenset(
    {
        "AUTHENTICATION_FAILED",
        "CREDENTIAL_UNAVAILABLE",
        "REQUEST_CONTRACT_REJECTED",
        "RESPONSE_CONTRACT_INCOMPATIBLE",
        "TRANSPORT_FAILURE",
        "PROVIDER_FAILURE",
    }
)
_PRIMARY_DECISION_FACTORS = (
    "EVIDENCE_FIT",
    "RISK_REDUCTION",
    "ARCHITECTURE_FIT",
    "SCOPE_CONTROL",
    "REVERSIBILITY",
    "COMPATIBILITY",
    "NO_DOMINANT_FACTOR",
)
_STRONGEST_RESIDUAL_RISKS = (
    "TECHNICAL_RISK",
    "SECURITY_RISK",
    "ARCHITECTURE_RISK",
    "SCOPE_RISK",
    "COMPATIBILITY_RISK",
    "EVIDENCE_GAP",
    "NO_MATERIAL_RESIDUAL_RISK",
)


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _as_json_mapping(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{field} must be a JSON object with string keys")
    try:
        copied = json.loads(canonical_json_bytes(dict(value)).decode("utf-8"))
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError(f"{field} must contain only finite JSON values") from exc
    if not isinstance(copied, dict):
        raise ValueError(f"{field} must be a JSON object")
    return copied


def _as_json_list(value: object, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a JSON array")
    try:
        copied = json.loads(canonical_json_bytes(value).decode("utf-8"))
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError(f"{field} must contain only finite JSON values") from exc
    if not isinstance(copied, list):
        raise ValueError(f"{field} must be a JSON array")
    return copied


def _require_keys(value: Mapping[str, object], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{field} must match the normalized Orchestra JEV contract")


def _validate_candidate(candidate: object) -> dict[str, str]:
    if not isinstance(candidate, Mapping) or set(candidate) != {
        "repository",
        "commit",
        "tree",
        "scope_hash",
    }:
        raise ValueError("candidate must bind repository, commit, tree, and scope_hash")
    repository = candidate["repository"]
    if not isinstance(repository, str) or not _REPOSITORY_RE.fullmatch(repository):
        raise ValueError("candidate repository identity is invalid")
    scope_hash = candidate["scope_hash"]
    if not isinstance(scope_hash, str) or not scope_hash.startswith("sha256:"):
        raise ValueError("candidate scope_hash must use the sha256 prefix")
    return {
        "repository": repository,
        "commit": normalize_git_sha(candidate["commit"], "candidate.commit"),
        "tree": normalize_git_sha(candidate["tree"], "candidate.tree"),
        "scope_hash": "sha256:" + normalize_sha256(scope_hash[7:], "candidate.scope_hash"),
    }


def _scope_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    candidate = payload["candidate"]
    return {
        "contract": payload["contract"],
        "candidate": {
            "repository": candidate["repository"],
            "commit": candidate["commit"],
            "tree": candidate["tree"],
        },
        "task": payload["task"],
        "findings": payload["findings"],
        "verification": payload["verification"],
        "overseer_assessment": payload["overseer_assessment"],
        "mitigation_options": payload["mitigation_options"],
        "dissent": payload["dissent"],
        "constraints": payload["constraints"],
    }


@dataclass(frozen=True, slots=True)
class JevCandidateBinding:
    repository: str
    commit: str
    tree: str
    scope_hash: str

    def __post_init__(self) -> None:
        normalized = _validate_candidate(
            {
                "repository": self.repository,
                "commit": self.commit,
                "tree": self.tree,
                "scope_hash": self.scope_hash,
            }
        )
        for key, value in normalized.items():
            object.__setattr__(self, key, value)

    @classmethod
    def from_mapping(cls, candidate: Mapping[str, object]) -> JevCandidateBinding:
        normalized = _validate_candidate(candidate)
        return cls(**normalized)

    def to_dict(self) -> dict[str, str]:
        return {
            "repository": self.repository,
            "commit": self.commit,
            "tree": self.tree,
            "scope_hash": self.scope_hash,
        }


@dataclass(frozen=True, slots=True, init=False)
class OrchestraJevAdjudicationState:
    """Immutable JSON handoff with a deterministic digest over its full adjudication scope."""

    _payload_bytes: bytes
    candidate_binding: JevCandidateBinding
    mitigation_ids: tuple[str, ...]

    def __init__(self, payload: Mapping[str, object]) -> None:
        normalized = self._normalize_payload(payload)
        expected_scope_hash = "sha256:" + receipt_digest(_scope_payload(normalized))
        if normalized["candidate"]["scope_hash"] != expected_scope_hash:
            raise ValueError("candidate scope_hash does not match the adjudication state")
        object.__setattr__(self, "_payload_bytes", canonical_json_bytes(normalized))
        object.__setattr__(
            self, "candidate_binding", JevCandidateBinding.from_mapping(normalized["candidate"])
        )
        object.__setattr__(
            self,
            "mitigation_ids",
            tuple(option["id"] for option in normalized["mitigation_options"]),
        )

    @classmethod
    def create(
        cls,
        *,
        candidate: Mapping[str, object],
        task: Mapping[str, object],
        findings: list[object],
        verification: list[object],
        overseer_assessment: Mapping[str, object] | None,
        mitigation_options: list[object],
        dissent: list[object],
        constraints: Mapping[str, object],
    ) -> OrchestraJevAdjudicationState:
        if not isinstance(candidate, Mapping) or set(candidate) != {"repository", "commit", "tree"}:
            raise ValueError("candidate input must contain repository, commit, and tree")
        base_candidate = {
            "repository": candidate["repository"],
            "commit": normalize_git_sha(candidate["commit"], "candidate.commit"),
            "tree": normalize_git_sha(candidate["tree"], "candidate.tree"),
        }
        sections = {
            "contract": JEV_ADJUDICATION_CONTRACT,
            "candidate": {**base_candidate, "scope_hash": ""},
            "task": _as_json_mapping(task, "task"),
            "findings": _as_json_list(findings, "findings"),
            "verification": _as_json_list(verification, "verification"),
            "overseer_assessment": (
                None
                if overseer_assessment is None
                else _as_json_mapping(overseer_assessment, "overseer_assessment")
            ),
            "mitigation_options": _as_json_list(mitigation_options, "mitigation_options"),
            "dissent": _as_json_list(dissent, "dissent"),
            "constraints": _as_json_mapping(constraints, "constraints"),
        }
        sections["candidate"]["scope_hash"] = "sha256:" + receipt_digest(
            _scope_payload(sections)
        )
        return cls(sections)

    @staticmethod
    def _normalize_payload(payload: Mapping[str, object]) -> dict[str, Any]:
        raw = _as_json_mapping(payload, "state")
        required = {
            "contract",
            "candidate",
            "task",
            "findings",
            "verification",
            "overseer_assessment",
            "mitigation_options",
            "dissent",
            "constraints",
        }
        if set(raw) != required or raw.get("contract") != JEV_ADJUDICATION_CONTRACT:
            raise ValueError("state must match orchestra.jev.adjudication.v1")
        candidate = _validate_candidate(raw["candidate"])
        task = _as_json_mapping(raw["task"], "task")
        _require_keys(task, {"domain", "risk_level", "assurance_depth"}, "task")
        if task["risk_level"] not in _RISK_LEVELS or task["assurance_depth"] not in _ASSURANCE_DEPTHS:
            raise ValueError("task risk_level or assurance_depth is invalid")
        _required_text(task["domain"], "task.domain")

        findings = _as_json_list(raw["findings"], "findings")
        finding_ids: set[str] = set()
        for finding in findings:
            if not isinstance(finding, dict) or not {
                "id",
                "producer",
                "status",
                "summary",
                "evidence_refs",
            }.issubset(finding):
                raise ValueError("finding records are malformed")
            finding_keys = {"id", "producer", "status", "summary", "evidence_refs"}
            if "verification_required" in finding:
                finding_keys.add("verification_required")
                if type(finding["verification_required"]) is not bool:
                    raise ValueError("finding.verification_required must be a boolean")
            _require_keys(
                finding,
                finding_keys,
                "finding",
            )
            identifier = _required_text(finding["id"], "finding.id")
            if not _STABLE_ID_RE.fullmatch(identifier) or identifier in finding_ids:
                raise ValueError("finding ids must be unique stable identifiers")
            finding_ids.add(identifier)
            _required_text(finding["producer"], "finding.producer")
            _required_text(finding["status"], "finding.status")
            _required_text(finding["summary"], "finding.summary")
            _validate_string_list(finding["evidence_refs"], "finding.evidence_refs")

        verification = _as_json_list(raw["verification"], "verification")
        verification_ids: set[str] = set()
        for item in verification:
            if not isinstance(item, dict) or not {
                "id",
                "producer",
                "finding_id",
                "result",
                "evidence_refs",
            }.issubset(item):
                raise ValueError("verification records are malformed")
            _require_keys(
                item,
                {"id", "producer", "finding_id", "result", "evidence_refs"},
                "verification",
            )
            identifier = _required_text(item["id"], "verification.id")
            if not _STABLE_ID_RE.fullmatch(identifier) or identifier in verification_ids:
                raise ValueError("verification ids must be unique stable identifiers")
            verification_ids.add(identifier)
            _required_text(item["producer"], "verification.producer")
            _required_text(item["finding_id"], "verification.finding_id")
            if item["finding_id"] not in finding_ids:
                raise ValueError("verification record refers to an unknown finding")
            result = _required_text(item["result"], "verification.result")
            if result not in JEV_VERIFICATION_RESULTS:
                raise ValueError("verification.result is unsupported")
            _validate_string_list(
                item["evidence_refs"],
                "verification.evidence_refs",
                nonempty=result == "CONFIRMED",
            )

        overseer = raw["overseer_assessment"]
        if overseer is not None:
            overseer = _as_json_mapping(overseer, "overseer_assessment")
            _require_keys(
                overseer,
                {"evidence_sufficiency", "impact", "residual_risk_context"},
                "overseer_assessment",
            )
            _required_text(overseer["evidence_sufficiency"], "overseer_assessment.evidence_sufficiency")
            _required_text(overseer["impact"], "overseer_assessment.impact")
            _required_text(
                overseer["residual_risk_context"], "overseer_assessment.residual_risk_context"
            )
        mitigation_options = _as_json_list(raw["mitigation_options"], "mitigation_options")
        mitigation_ids: set[str] = set()
        for option in mitigation_options:
            if not isinstance(option, dict) or not {
                "id",
                "producers",
                "summary",
                "addresses",
                "tradeoffs",
            }.issubset(option):
                raise ValueError("mitigation option records are malformed")
            _require_keys(
                option,
                {"id", "producers", "summary", "addresses", "tradeoffs"},
                "mitigation option",
            )
            identifier = _required_text(option["id"], "mitigation.id")
            if (
                not _STABLE_ID_RE.fullmatch(identifier)
                or identifier == "NO_CLEAR_PREFERENCE"
                or identifier in mitigation_ids
            ):
                raise ValueError("mitigation ids must be unique stable identifiers")
            mitigation_ids.add(identifier)
            _validate_string_list(option["producers"], "mitigation.producers", nonempty=True)
            _required_text(option["summary"], "mitigation.summary")
            addresses = _validate_string_list(option["addresses"], "mitigation.addresses", nonempty=True)
            if not set(addresses).issubset(finding_ids):
                raise ValueError("mitigation option refers to an unknown finding")
            _validate_string_list(option["tradeoffs"], "mitigation.tradeoffs", nonempty=True)

        dissent = _as_json_list(raw["dissent"], "dissent")
        for item in dissent:
            if not isinstance(item, dict):
                raise ValueError("dissent entries must be normalized specialist records")
            _require_keys(item, {"id", "producer", "summary", "evidence_refs"}, "dissent")
            identifier = _required_text(item["id"], "dissent.id")
            if not _STABLE_ID_RE.fullmatch(identifier):
                raise ValueError("dissent id must be a stable identifier")
            _required_text(item["producer"], "dissent.producer")
            _required_text(item["summary"], "dissent.summary")
            _validate_string_list(item["evidence_refs"], "dissent.evidence_refs")
        constraints = _as_json_mapping(raw["constraints"], "constraints")
        required_constraints = {
            "protected_policy_change_allowed",
            "authority_change_allowed",
            "scope_expansion_allowed",
        }
        if set(constraints) != required_constraints or any(
            type(value) is not bool for value in constraints.values()
        ):
            raise ValueError("constraints must contain the three explicit boolean boundaries")
        return {
            "contract": JEV_ADJUDICATION_CONTRACT,
            "candidate": candidate,
            "task": task,
            "findings": findings,
            "verification": verification,
            "overseer_assessment": overseer,
            "mitigation_options": mitigation_options,
            "dissent": dissent,
            "constraints": constraints,
        }

    def to_payload(self) -> dict[str, Any]:
        return json.loads(self._payload_bytes.decode("utf-8"))


def _validate_string_list(value: object, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(f"{field} must be {'a non-empty' if nonempty else 'a'} string array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field} must contain non-empty strings")
    return value


class JevAdjudicationEligibilityError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class JevProviderFailure(RuntimeError):
    """Sanitized provider failure; response bodies and request headers are never retained."""

    def __init__(self, code: str, http_status: int | None = None) -> None:
        self.code = code if code in _PROVIDER_FAILURE_CODES else "PROVIDER_FAILURE"
        self.http_status = http_status
        super().__init__(self.code)


def validate_jev_adjudication_eligibility(state: OrchestraJevAdjudicationState) -> None:
    payload = state.to_payload()
    verified = [finding for finding in payload["findings"] if finding["status"] == "VERIFIED"]
    if not verified:
        raise JevAdjudicationEligibilityError("VERIFIED_FINDINGS_REQUIRED")
    verification_by_finding: dict[str, list[dict[str, Any]]] = {}
    for item in payload["verification"]:
        if item["result"].upper() in _INCOMPLETE_VERIFICATION_RESULTS:
            raise JevAdjudicationEligibilityError("EMPIRICAL_VERIFICATION_INCOMPLETE")
        verification_by_finding.setdefault(item["finding_id"], []).append(item)
    if any(
        finding.get("verification_required") is True
        and not verification_by_finding.get(finding["id"])
        for finding in verified
    ):
        raise JevAdjudicationEligibilityError("EMPIRICAL_VERIFICATION_REQUIRED")
    overseer = payload["overseer_assessment"]
    if not isinstance(overseer, Mapping) or not {
        "evidence_sufficiency",
        "impact",
    }.issubset(overseer):
        raise JevAdjudicationEligibilityError("OVERSEER_ASSESSMENT_REQUIRED")


def _noul(instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": yes, "false": no},
    }


def _choice(instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    return {"type": "choice", "instructions": instructions, "criteria": dict(criteria)}


class OrchestraJevQuestionBuilder:
    """Build one complete, deterministic TypeSafe System One question object."""

    def build(self, state: OrchestraJevAdjudicationState) -> dict[str, dict[str, Any]]:
        if not isinstance(state, OrchestraJevAdjudicationState):
            raise TypeError("state must be OrchestraJevAdjudicationState")
        questions: dict[str, dict[str, Any]] = {
            "material_unresolved_uncertainty": _noul(
                "Could unresolved uncertainty in the supplied evidence, verification results, constraints, or mitigation tradeoffs reasonably change which mitigation option should be preferred?",
                "Unresolved uncertainty could reasonably change the preferred mitigation.",
                "Unresolved uncertainty would not reasonably change the preferred mitigation.",
            ),
            "material_specialist_dissent": _noul(
                "Does the supplied specialist dissent identify a material technical, architectural, security, privacy, reliability, compatibility, or scope consideration that could reasonably change the mitigation ranking?",
                "Specialist dissent identifies a material consideration that could reasonably change the mitigation ranking.",
                "Supplied specialist dissent does not identify a material consideration that could reasonably change the mitigation ranking.",
            ),
            "unsupported_assumption_dependency": _noul(
                "Would selecting a preferred mitigation require relying on a material assumption not supported by the supplied verified findings, verification evidence, Overseer assessment, constraints, or mitigation descriptions?",
                "Selecting the preferred mitigation would require an unsupported material assumption.",
                "Selecting the preferred mitigation would not require an unsupported material assumption.",
            ),
        }
        for option in state.to_payload()["mitigation_options"]:
            identifier = option["id"]
            questions[f"evidence_supports_{identifier}"] = _noul(
                f"Does the supplied verified evidence support mitigation {identifier} as described?",
                f"The supplied verified evidence supports mitigation {identifier}.",
                f"The supplied verified evidence does not support mitigation {identifier}.",
            )
            questions[f"{identifier}_introduces_scope_risk"] = _noul(
                f"Does mitigation {identifier} introduce material scope risk under the supplied constraints?",
                f"Mitigation {identifier} introduces material scope risk.",
                f"Mitigation {identifier} does not introduce material scope risk.",
            )
            questions[f"{identifier}_preserves_architecture"] = _noul(
                f"Does mitigation {identifier} preserve the existing architecture as described by the supplied tradeoffs?",
                f"Mitigation {identifier} preserves the existing architecture.",
                f"Mitigation {identifier} does not preserve the existing architecture.",
            )

        mitigation_criteria = {
            option["id"]: option["summary"]
            for option in state.to_payload()["mitigation_options"]
        }
        mitigation_criteria["NO_CLEAR_PREFERENCE"] = (
            "The supplied state does not support a defensible mitigation preference."
        )
        questions["recommended_mitigation"] = _choice(
            "Select the mitigation best supported by the verified findings, verification evidence, Overseer assessment, specialist input, tradeoffs, and constraints. This is advisory only. Select NO_CLEAR_PREFERENCE when the supplied state does not support a defensible preference.",
            mitigation_criteria,
        )
        questions["primary_decision_factor"] = _choice(
            "Which single factor most strongly explains the advisory mitigation preference?",
            {
                "EVIDENCE_FIT": "Fit to the supplied verified evidence.",
                "RISK_REDUCTION": "Expected reduction of the assessed risk.",
                "ARCHITECTURE_FIT": "Fit with the existing architecture.",
                "SCOPE_CONTROL": "Control of implementation scope.",
                "REVERSIBILITY": "Ease of reversing the mitigation if needed.",
                "COMPATIBILITY": "Compatibility with existing behavior and integrations.",
                "NO_DOMINANT_FACTOR": "No single factor dominates the decision.",
            },
        )
        questions["strongest_residual_risk"] = _choice(
            "Which residual risk is strongest after considering the supplied mitigation alternatives?",
            {
                "TECHNICAL_RISK": "Technical behavior or correctness risk.",
                "SECURITY_RISK": "Security risk.",
                "ARCHITECTURE_RISK": "Architecture or structural risk.",
                "SCOPE_RISK": "Scope growth or incomplete scope control.",
                "COMPATIBILITY_RISK": "Compatibility with existing behavior or integrations.",
                "EVIDENCE_GAP": "A material gap in the supplied evidence.",
                "NO_MATERIAL_RESIDUAL_RISK": "No material residual risk is supported by the supplied state.",
            },
        )
        expected_ids = {
            "material_unresolved_uncertainty",
            "material_specialist_dissent",
            "unsupported_assumption_dependency",
            "recommended_mitigation",
            "primary_decision_factor",
            "strongest_residual_risk",
            *(
                question_id
                for identifier in state.mitigation_ids
                for question_id in (
                    f"evidence_supports_{identifier}",
                    f"{identifier}_introduces_scope_risk",
                    f"{identifier}_preserves_architecture",
                )
            ),
        }
        if set(questions) != expected_ids:
            raise ValueError("mitigation ids produce colliding JEV question ids")
        return questions

    def serialize(self, state: OrchestraJevAdjudicationState) -> str:
        return canonical_json_bytes(self.build(state)).decode("utf-8")


def _probability(value: object, field: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{field} must be a finite probability")
    return value


@dataclass(frozen=True, slots=True)
class JevNoulAnswer:
    probability: int | float

    def __post_init__(self) -> None:
        _probability(self.probability, "noul probability")

    def to_dict(self) -> dict[str, int | float | str]:
        return {"type": "noul", "noul": self.probability}


@dataclass(frozen=True, slots=True)
class JevChoiceAnswer:
    selected: str
    confidence: int | float | None
    probabilities: tuple[tuple[str, int | float], ...]

    def __post_init__(self) -> None:
        _required_text(self.selected, "choice")
        if self.confidence is not None:
            _probability(self.confidence, "choice confidence")
        keys = [key for key, _ in self.probabilities]
        if not keys or len(keys) != len(set(keys)):
            raise ValueError("choice probabilities must have unique criteria")
        values = [_probability(value, "choice probability") for _, value in self.probabilities]
        if abs(math.fsum(values) - 1.0) > 0.001:
            raise ValueError("choice probabilities must form a complete distribution")
        if self.selected not in keys:
            raise ValueError("selected choice must be present in its distribution")

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": "choice",
            "choice": self.selected,
            "probabilities": {key: value for key, value in self.probabilities},
        }
        if self.confidence is not None:
            result["confidence"] = self.confidence
        return result


@dataclass(frozen=True, slots=True)
class JevProviderResponse:
    model: str
    candidate_binding: JevCandidateBinding
    answers: tuple[tuple[str, JevNoulAnswer | JevChoiceAnswer], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.model, str) or not _RESOLVED_MODEL_RE.fullmatch(self.model):
            raise ValueError("resolved JEV model is invalid")
        if not isinstance(self.candidate_binding, JevCandidateBinding):
            raise TypeError("JEV provider response must retain its request candidate binding")
        question_ids = [question_id for question_id, _ in self.answers]
        if len(question_ids) != len(set(question_ids)) or any(
            not isinstance(question_id, str) for question_id in question_ids
        ):
            raise ValueError("JEV answer ids must be unique strings")
        if any(not isinstance(answer, (JevNoulAnswer, JevChoiceAnswer)) for _, answer in self.answers):
            raise TypeError("JEV answers must be typed Noul or Choice answers")

    def answer_map(self) -> dict[str, JevNoulAnswer | JevChoiceAnswer]:
        return dict(self.answers)


@dataclass(frozen=True, slots=True)
class JevAdvisoryResult:
    candidate_binding: JevCandidateBinding
    advisory_state: str
    risk_level: str
    assurance_depth: str
    answers: tuple[tuple[str, JevNoulAnswer | JevChoiceAnswer], ...] = ()
    resolved_model: str | None = None
    failure_code: str | None = None
    recommendation: str | None = None
    current_candidate_binding: JevCandidateBinding | None = None

    def __post_init__(self) -> None:
        if self.advisory_state in (JEV_ADVISORY_STALE, JEV_ADVISORY_UNBOUND):
            object.__setattr__(self, "answers", ())
            object.__setattr__(self, "resolved_model", None)
            object.__setattr__(self, "recommendation", None)

        if self.advisory_state not in JEV_STATES:
            raise ValueError("unknown JEV advisory state")
        if self.risk_level not in _RISK_LEVELS or self.assurance_depth not in _ASSURANCE_DEPTHS:
            raise ValueError("JEV result risk or assurance depth is invalid")
        if self.advisory_state == JEV_ADVISORY_RECOMMENDATION_AVAILABLE and not self.recommendation:
            raise ValueError("available JEV advisory requires a mitigation recommendation")
        if self.recommendation == "NO_CLEAR_PREFERENCE" and self.advisory_state != JEV_ADVISORY_INCONCLUSIVE:
            raise ValueError("NO_CLEAR_PREFERENCE must be inconclusive")
        if self.resolved_model is not None and not _RESOLVED_MODEL_RE.fullmatch(self.resolved_model):
            raise ValueError("resolved JEV model is invalid")

    def to_dict(self) -> dict[str, Any]:
        answers = {question_id: answer.to_dict() for question_id, answer in self.answers}
        return {
            "contract": JEV_ADJUDICATION_CONTRACT,
            "candidate": self.candidate_binding.to_dict(),
            "current_candidate": (
                None if self.current_candidate_binding is None else self.current_candidate_binding.to_dict()
            ),
            "task": {"risk_level": self.risk_level, "assurance_depth": self.assurance_depth},
            "advisory_state": self.advisory_state,
            "recommendation": self.recommendation,
            "answers": answers,
            "model_provenance": {
                "provider": "TypeSafe System One",
                "endpoint": TYPESAFE_SYSTEM_ONE_ENDPOINT,
                "requested_model": TYPESAFE_JEV_MODEL,
                "resolved_model": self.resolved_model,
            },
            "failure_code": self.failure_code,
            "advisory_only": True,
            "may_authorize": False,
            "authority_effect": "NONE",
        }


class OrchestraJevInterpreter:
    """Interpret a typed provider response without granting authority or assurance credit."""

    def interpret(
        self,
        state: OrchestraJevAdjudicationState,
        response: JevProviderResponse,
        current_binding: JevCandidateBinding | None,
    ) -> JevAdvisoryResult:
        if not isinstance(state, OrchestraJevAdjudicationState):
            raise TypeError("state must be OrchestraJevAdjudicationState")
        if not isinstance(response, JevProviderResponse):
            raise TypeError("response must be JevProviderResponse")
        question_catalog = OrchestraJevQuestionBuilder().build(state)
        answers = response.answer_map()
        if set(answers) != set(question_catalog):
            raise ValueError("typed JEV response does not cover the complete question catalog")
        for question_id, question in question_catalog.items():
            answer = answers[question_id]
            criteria = set(question["criteria"])
            if question["type"] == "noul" and not isinstance(answer, JevNoulAnswer):
                raise ValueError("typed JEV Noul answer does not match its question")
            if question["type"] == "choice":
                if not isinstance(answer, JevChoiceAnswer) or set(dict(answer.probabilities)) != criteria:
                    raise ValueError("typed JEV Choice answer does not match its criteria")
                if answer.selected not in criteria:
                    raise ValueError("typed JEV Choice selection is outside its criteria")

        advisory_state = JEV_ADVISORY_RECOMMENDATION_AVAILABLE
        recommendation: str | None = answers["recommended_mitigation"].selected
        request_binding = response.candidate_binding
        current = state.candidate_binding if current_binding is not None else None
        if current_binding is None:
            advisory_state = JEV_ADVISORY_UNBOUND
            recommendation = None
        elif current_binding != state.candidate_binding or request_binding != state.candidate_binding:
            advisory_state = JEV_ADVISORY_STALE
            recommendation = None
            current = current_binding if current_binding != state.candidate_binding else state.candidate_binding
        elif recommendation == "NO_CLEAR_PREFERENCE":
            advisory_state = JEV_ADVISORY_INCONCLUSIVE
        return JevAdvisoryResult(
            candidate_binding=request_binding,
            advisory_state=advisory_state,
            risk_level=state.to_payload()["task"]["risk_level"],
            assurance_depth=state.to_payload()["task"]["assurance_depth"],
            answers=tuple((question_id, answer) for question_id, answer in response.answers),
            resolved_model=response.model,
            recommendation=recommendation,
            current_candidate_binding=current,
        )

    def unavailable(
        self, state: OrchestraJevAdjudicationState, failure_code: str
    ) -> JevAdvisoryResult:
        if not isinstance(state, OrchestraJevAdjudicationState):
            raise TypeError("state must be OrchestraJevAdjudicationState")
        safe_code = failure_code if failure_code in {
            "AUTHENTICATION_FAILED",
            "CREDENTIAL_UNAVAILABLE",
            "REQUEST_CONTRACT_REJECTED",
            "RESPONSE_CONTRACT_INCOMPATIBLE",
            "TRANSPORT_FAILURE",
        } else "PROVIDER_FAILURE"
        payload = state.to_payload()
        return JevAdvisoryResult(
            candidate_binding=state.candidate_binding,
            advisory_state=JEV_UNAVAILABLE,
            risk_level=payload["task"]["risk_level"],
            assurance_depth=payload["task"]["assurance_depth"],
            failure_code=safe_code,
        )

    def unbound(self, state: OrchestraJevAdjudicationState) -> JevAdvisoryResult:
        payload = state.to_payload()
        return JevAdvisoryResult(
            state.candidate_binding,
            JEV_ADVISORY_UNBOUND,
            payload["task"]["risk_level"],
            payload["task"]["assurance_depth"],
        )

    def stale(
        self,
        state: OrchestraJevAdjudicationState,
        current_binding: JevCandidateBinding | None = None,
    ) -> JevAdvisoryResult:
        payload = state.to_payload()
        return JevAdvisoryResult(
            state.candidate_binding,
            JEV_ADVISORY_STALE,
            payload["task"]["risk_level"],
            payload["task"]["assurance_depth"],
            current_candidate_binding=current_binding,
        )

    def not_required(self, state: OrchestraJevAdjudicationState) -> JevAdvisoryResult:
        payload = state.to_payload()
        return JevAdvisoryResult(
            state.candidate_binding,
            JEV_NOT_REQUIRED,
            payload["task"]["risk_level"],
            payload["task"]["assurance_depth"],
        )


__all__ = [
    "JEV_ADJUDICATION_CONTRACT",
    "JEV_ADVISORY_INCONCLUSIVE",
    "JEV_ADVISORY_RECOMMENDATION_AVAILABLE",
    "JEV_ADVISORY_STALE",
    "JEV_ADVISORY_UNBOUND",
    "JEV_NOT_REQUIRED",
    "JEV_STATES",
    "JEV_UNAVAILABLE",
    "JEV_VERIFICATION_RESULTS",
    "JevAdjudicationEligibilityError",
    "JevCandidateBinding",
    "JevChoiceAnswer",
    "JevAdvisoryResult",
    "JevNoulAnswer",
    "JevProviderFailure",
    "JevProviderResponse",
    "OrchestraJevAdjudicationState",
    "OrchestraJevInterpreter",
    "OrchestraJevQuestionBuilder",
    "TYPESAFE_JEV_MODEL",
    "TYPESAFE_SYSTEM_ONE_ENDPOINT",
    "validate_jev_adjudication_eligibility",
]
