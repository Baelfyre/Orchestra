"""Offline adapter for the V6-R2 Cloak and Impeccable evidence packet."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from ...domain.adaptive.jev_adjudication import (
    JEV_ADJUDICATION_CONTRACT,
    OrchestraJevAdjudicationState,
)
from ...shared.canonicalization import canonical_json_bytes, normalize_git_sha, normalize_sha256


JEV_V6_R2_HANDOFF_CONTRACT = "orchestra.jev.v6_r2_evidence_handoff.v1"
_V6_R2_TASK_ID = "ORCHESTRA-V1.12-V6-R2-IMPECCABLE-COMPLETION"
_V6_PACKET_KEYS = {
    "task_id",
    "purpose",
    "candidate",
    "shared_evidence",
    "specialist_inputs",
    "normalized_findings",
    "comparison_status",
    "readiness",
    "restrictions",
}
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_STABLE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
# shortcut: maps only the pinned V6-R2 finding IDs; add a new adapter version for another packet schema.
_FINDING_SOURCES = {
    "C1-I1": (
        "Cloak",
        ("CLOAK-HOST-NATIVE", "IMPECCABLE-V6-R2", "V4-BROWSER-OBSERVATIONS"),
    ),
    "C2-I3": (
        "Cloak",
        ("CLOAK-HOST-NATIVE", "IMPECCABLE-V6-R2", "V5-REVIEW-PACKET"),
    ),
    "I2": (
        "Impeccable",
        ("IMPECCABLE-V6-R2", "CLOAK-HOST-NATIVE", "V4-BROWSER-OBSERVATIONS"),
    ),
    "I4": ("Impeccable", ("IMPECCABLE-V6-R2", "V5-REVIEW-PACKET")),
    "I-DETECTOR": ("Impeccable", ("IMPECCABLE-V6-R2",)),
}
_ERROR_CODES = frozenset(
    {
        "INVALID_CANDIDATE_BINDING",
        "INVALID_EXPECTED_PACKET_HASH",
        "INVALID_PACKET",
        "INVALID_PACKET_SCHEMA",
        "PACKET_HASH_MISMATCH",
        "CANDIDATE_REPOSITORY_MISMATCH",
        "CANDIDATE_COMMIT_MISMATCH",
        "CANDIDATE_TREE_MISMATCH",
        "UNMAPPED_FINDING_SOURCE",
        "INVALID_EVIDENCE_REFERENCE",
        "INVALID_FINDING_RECORD",
        "INVALID_CONSTRAINT_SOURCE",
        "INVALID_NORMALIZED_EVIDENCE",
    }
)


class JevV6HandoffError(ValueError):
    """Sanitized, stable error for malformed or untrusted V6 handoff input."""

    def __init__(self, code: str) -> None:
        self.code = code if code in _ERROR_CODES else "INVALID_PACKET"
        super().__init__(self.code)


@dataclass(frozen=True, slots=True)
class JevEvidenceGap:
    field_path: str
    reason: str
    source_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "field_path": self.field_path,
            "reason": self.reason,
            "source_refs": list(self.source_refs),
        }


@dataclass(frozen=True, slots=True)
class JevV6EvidenceHandoff:
    packet_sha256: str
    sections: Mapping[str, Any]
    section_sources: Mapping[str, tuple[str, ...]]
    missing_evidence: tuple[JevEvidenceGap, ...]
    source_restrictions: Mapping[str, bool]
    state: OrchestraJevAdjudicationState | None

    @property
    def state_created(self) -> bool:
        return self.state is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_contract": JEV_V6_R2_HANDOFF_CONTRACT,
            "packet_sha256": self.packet_sha256,
            "state_created": self.state_created,
            "sections": json.loads(canonical_json_bytes(dict(self.sections)).decode("utf-8")),
            "section_sources": {
                name: list(refs) for name, refs in self.section_sources.items()
            },
            "source_restrictions": dict(self.source_restrictions),
            "missing_evidence": [item.to_dict() for item in self.missing_evidence],
            "state": None if self.state is None else self.state.to_payload(),
        }


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _required_text(value: object, code: str = "INVALID_PACKET") -> str:
    if not isinstance(value, str) or not value.strip():
        raise JevV6HandoffError(code)
    return value


def _candidate_identity(candidate: object) -> dict[str, str]:
    if not isinstance(candidate, Mapping) or set(candidate) != {"repository", "commit", "tree"}:
        raise JevV6HandoffError("INVALID_CANDIDATE_BINDING")
    repository = candidate["repository"]
    if not isinstance(repository, str) or not _REPOSITORY_RE.fullmatch(repository):
        raise JevV6HandoffError("INVALID_CANDIDATE_BINDING")
    try:
        return {
            "repository": repository,
            "commit": normalize_git_sha(candidate["commit"], "candidate.commit"),
            "tree": normalize_git_sha(candidate["tree"], "candidate.tree"),
        }
    except (TypeError, ValueError) as exc:
        raise JevV6HandoffError("INVALID_CANDIDATE_BINDING") from exc


def _locator(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JevV6HandoffError("CANDIDATE_REPOSITORY_MISMATCH")
    return value.replace("\\", "/").rstrip("/").casefold()


def _source_index(packet: Mapping[str, Any]) -> dict[str, tuple[str, int, str | None]]:
    index: dict[str, tuple[str, int, str | None]] = {}
    for section in ("shared_evidence", "specialist_inputs"):
        rows = packet[section]
        if not isinstance(rows, list):
            raise JevV6HandoffError("INVALID_EVIDENCE_REFERENCE")
        for row_index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise JevV6HandoffError("INVALID_EVIDENCE_REFERENCE")
            identifier = _required_text(row.get("id"), "INVALID_EVIDENCE_REFERENCE")
            if identifier in index:
                raise JevV6HandoffError("INVALID_EVIDENCE_REFERENCE")
            raw_digest = row.get("sha256")
            if raw_digest is None:
                index[identifier] = (section, row_index, None)
                continue
            try:
                digest = normalize_sha256(raw_digest, f"{section}.{identifier}.sha256")
            except (TypeError, ValueError) as exc:
                raise JevV6HandoffError("INVALID_EVIDENCE_REFERENCE") from exc
            index[identifier] = (section, row_index, digest)
    return index


def _packet_ref(packet_sha256: str, pointer: str) -> str:
    return f"packet:sha256:{packet_sha256}#{pointer}"


def _artifact_ref(
    packet_sha256: str,
    source_index: Mapping[str, tuple[str, int, str | None]],
    identifier: str,
) -> str:
    source = source_index.get(identifier)
    if source is None:
        raise JevV6HandoffError("INVALID_EVIDENCE_REFERENCE")
    section, row_index, digest = source
    if digest is None:
        return _packet_ref(packet_sha256, f"/{section}/{row_index}")
    return f"artifact:{identifier}:sha256:{digest}"


def _finding_sources(
    identifier: str,
    finding_index: int,
    packet_sha256: str,
    source_index: Mapping[str, tuple[str, int, str | None]],
) -> tuple[str, tuple[str, ...]]:
    producer, source_ids = _FINDING_SOURCES.get(identifier, ("", ()))
    if not producer:
        raise JevV6HandoffError("UNMAPPED_FINDING_SOURCE")
    refs = [_packet_ref(packet_sha256, f"/normalized_findings/{finding_index}")]
    refs.extend(_artifact_ref(packet_sha256, source_index, source_id) for source_id in source_ids)
    return producer, tuple(dict.fromkeys(refs))


def _validate_packet(packet_bytes: bytes) -> dict[str, Any]:
    try:
        packet = json.loads(packet_bytes.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise JevV6HandoffError("INVALID_PACKET") from exc
    if (
        not isinstance(packet, dict)
        or set(packet) != _V6_PACKET_KEYS
        or packet.get("task_id") != _V6_R2_TASK_ID
    ):
        raise JevV6HandoffError("INVALID_PACKET_SCHEMA")
    candidate = packet.get("candidate")
    if not isinstance(candidate, Mapping):
        raise JevV6HandoffError("INVALID_PACKET_SCHEMA")
    candidate_keys = {"repository", "branch", "head", "worktree_status_at_preflight"}
    if set(candidate) not in (candidate_keys, candidate_keys | {"tree"}):
        raise JevV6HandoffError("INVALID_PACKET_SCHEMA")
    _required_text(candidate.get("repository"))
    _required_text(candidate.get("branch"))
    _required_text(candidate.get("worktree_status_at_preflight"))
    try:
        normalize_git_sha(candidate.get("head"), "candidate.head")
        if "tree" in candidate:
            normalize_git_sha(candidate["tree"], "candidate.tree")
    except (TypeError, ValueError) as exc:
        raise JevV6HandoffError("INVALID_PACKET_SCHEMA") from exc
    if not isinstance(packet.get("normalized_findings"), list):
        raise JevV6HandoffError("INVALID_PACKET_SCHEMA")
    _required_text(packet.get("purpose"))
    _required_text(packet.get("comparison_status"))
    _required_text(packet.get("readiness"))
    if not isinstance(packet.get("restrictions"), Mapping):
        raise JevV6HandoffError("INVALID_PACKET_SCHEMA")
    return packet


def adapt_v6_r2_evidence_packet(
    packet_bytes: bytes,
    *,
    trusted_packet_sha256: str,
    trusted_candidate_binding: Mapping[str, object],
) -> JevV6EvidenceHandoff:
    """Map V6-R2 only against separately trusted packet and Git identities."""
    if not isinstance(packet_bytes, bytes):
        raise JevV6HandoffError("INVALID_PACKET")
    try:
        expected_digest = normalize_sha256(trusted_packet_sha256, "trusted_packet_sha256")
    except (TypeError, ValueError) as exc:
        raise JevV6HandoffError("INVALID_EXPECTED_PACKET_HASH") from exc
    actual_digest = hashlib.sha256(packet_bytes).hexdigest()
    if actual_digest != expected_digest:
        raise JevV6HandoffError("PACKET_HASH_MISMATCH")

    packet = _validate_packet(packet_bytes)
    trusted_candidate = _candidate_identity(trusted_candidate_binding)
    source_candidate = packet["candidate"]
    trusted_locator = f"candidate://{trusted_candidate['repository'].rsplit('/', 1)[-1]}"
    if _locator(source_candidate["repository"]) != _locator(trusted_locator):
        raise JevV6HandoffError("CANDIDATE_REPOSITORY_MISMATCH")
    if normalize_git_sha(source_candidate["head"], "candidate.head") != trusted_candidate["commit"]:
        raise JevV6HandoffError("CANDIDATE_COMMIT_MISMATCH")
    if "tree" in source_candidate and normalize_git_sha(
        source_candidate["tree"], "candidate.tree"
    ) != trusted_candidate["tree"]:
        raise JevV6HandoffError("CANDIDATE_TREE_MISMATCH")

    source_index = _source_index(packet)
    missing: list[JevEvidenceGap] = []
    for identifier, (section, row_index, digest) in source_index.items():
        if digest is None:
            missing.append(
                JevEvidenceGap(
                    f"{section}.{identifier}.sha256",
                    "V6-R2 names this source but omits its content digest; only the packet row can be referenced.",
                    (_packet_ref(actual_digest, f"/{section}/{row_index}"),),
                )
            )
    section_sources: dict[str, tuple[str, ...]] = {
        "contract": (JEV_ADJUDICATION_CONTRACT,),
        "candidate": (
            _packet_ref(actual_digest, "/candidate/head"),
            f"git:{trusted_candidate['repository']}@{trusted_candidate['commit']}^{{tree}}:{trusted_candidate['tree']}",
        ),
    }
    findings: list[dict[str, Any]] = []
    finding_ids: set[str] = set()
    finding_indexes: dict[str, int] = {}
    for finding_index, item in enumerate(packet["normalized_findings"]):
        if not isinstance(item, Mapping) or set(item) != {
            "id",
            "classification",
            "severity",
            "confidence",
            "claim",
            "acceptance",
        }:
            raise JevV6HandoffError("INVALID_FINDING_RECORD")
        identifier = _required_text(item.get("id"), "INVALID_FINDING_RECORD")
        if not _STABLE_ID_RE.fullmatch(identifier) or identifier in finding_ids:
            raise JevV6HandoffError("INVALID_FINDING_RECORD")
        finding_ids.add(identifier)
        finding_indexes[identifier] = finding_index
        producer, refs = _finding_sources(identifier, finding_index, actual_digest, source_index)
        classification = _required_text(item.get("classification"), "INVALID_FINDING_RECORD")
        severity = _required_text(item.get("severity"), "INVALID_FINDING_RECORD")
        confidence = _required_text(item.get("confidence"), "INVALID_FINDING_RECORD")
        claim = _required_text(item.get("claim"), "INVALID_FINDING_RECORD")
        acceptance = _required_text(item.get("acceptance"), "INVALID_FINDING_RECORD")
        findings.append(
            {
                "id": identifier,
                "producer": producer,
                "status": "UNVERIFIED",
                "summary": (
                    f"{classification}; severity={severity}; confidence={confidence}; "
                    f"claim={claim}; acceptance target (not completed verification)={acceptance}"
                ),
                "evidence_refs": list(refs),
            }
        )
    if not findings:
        missing.append(
            JevEvidenceGap(
                "findings",
                "V6-R2 supplies no normalized finding records.",
                (_packet_ref(actual_digest, "/normalized_findings"),),
            )
        )
    else:
        section_sources["findings"] = tuple(
            ref for finding in findings for ref in finding["evidence_refs"]
        )
        missing.append(
            JevEvidenceGap(
                "findings",
                "V6-R2 does not provide VERIFIED statuses; mapped findings remain UNVERIFIED.",
                tuple(ref for finding in findings for ref in finding["evidence_refs"]),
            )
        )

    task_refs = tuple(
        _packet_ref(actual_digest, f"/normalized_findings/{finding_indexes[item['id']]}")
        for item in findings
    )
    task: dict[str, Any] = {"domain": "user_interface"}
    section_sources["task"] = task_refs or (_packet_ref(actual_digest, "/purpose"),)
    for field, reason in (
        ("risk_level", "V6-R2 severity labels are finding severity, not task risk."),
        ("assurance_depth", "V6-R2 contains no task assurance-depth evidence."),
    ):
        missing.append(JevEvidenceGap(f"task.{field}", reason, section_sources["task"]))

    verification_refs = (
        _packet_ref(actual_digest, "/normalized_findings"),
        _artifact_ref(actual_digest, source_index, "IMPECCABLE-V6-R2"),
    )
    section_sources["verification"] = verification_refs
    missing.append(
        JevEvidenceGap(
            "verification",
            "Acceptance text is not a completed check; the detector's empty result is not empirical verification of a UI finding.",
            verification_refs,
        )
    )

    overseer_refs = tuple(
        _artifact_ref(actual_digest, source_index, source_id)
        for source_id in ("CLOAK-HOST-NATIVE", "IMPECCABLE-V6-R2")
    )
    section_sources["overseer_assessment"] = overseer_refs
    missing.append(
        JevEvidenceGap(
            "overseer_assessment",
            "V6-R2 contains Cloak and Impeccable inputs, not an Overseer assessment.",
            overseer_refs,
        )
    )

    c1_i1_pointer = (
        f"/normalized_findings/{finding_indexes['C1-I1']}/acceptance"
        if "C1-I1" in finding_indexes
        else "/normalized_findings"
    )
    mitigation_refs = (
        _packet_ref(actual_digest, c1_i1_pointer),
        _artifact_ref(actual_digest, source_index, "IMPECCABLE-V6-R2"),
    )
    section_sources["mitigation_options"] = mitigation_refs
    missing.append(
        JevEvidenceGap(
            "mitigation_options",
            "The normalized packet has acceptance criteria but no structured alternatives with evidence-backed tradeoffs.",
            mitigation_refs,
        )
    )

    dissent: list[dict[str, Any]] = []
    finding_by_id = {item["id"]: item for item in findings}
    if "I2" in finding_by_id:
        finding = finding_by_id["I2"]
        dissent.append(
            {
                "id": "I2",
                "producer": "Impeccable",
                "summary": finding["summary"],
                "evidence_refs": finding["evidence_refs"],
            }
        )
    section_sources["dissent"] = tuple(
        ref for item in dissent for ref in item["evidence_refs"]
    )

    restrictions = packet["restrictions"]
    required_restrictions = {
        "offline_only",
        "no_provider_calls",
        "no_source_or_repository_writes",
        "no_release_or_implementation_authority",
    }
    if set(restrictions) != required_restrictions or any(
        type(value) is not bool for value in restrictions.values()
    ):
        raise JevV6HandoffError("INVALID_CONSTRAINT_SOURCE")
    if any(value is not True for value in restrictions.values()):
        raise JevV6HandoffError("INVALID_CONSTRAINT_SOURCE")
    constraints = {
        "protected_policy_change_allowed": False,
        "authority_change_allowed": False,
        "scope_expansion_allowed": False,
    }
    section_sources["constraints"] = (_packet_ref(actual_digest, "/restrictions"),)

    sections: dict[str, Any] = {
        "contract": JEV_ADJUDICATION_CONTRACT,
        "candidate": {
            key: trusted_candidate[key] for key in ("repository", "commit", "tree")
        },
        "task": task,
        "findings": findings,
        "verification": [],
        "overseer_assessment": None,
        "mitigation_options": [],
        "dissent": dissent,
        "constraints": constraints,
    }
    state: OrchestraJevAdjudicationState | None = None
    if not missing:
        try:
            state = OrchestraJevAdjudicationState.create(
                candidate=sections["candidate"],
                task=sections["task"],
                findings=sections["findings"],
                verification=sections["verification"],
                overseer_assessment=sections["overseer_assessment"],
                mitigation_options=sections["mitigation_options"],
                dissent=sections["dissent"],
                constraints=sections["constraints"],
            )
        except (TypeError, ValueError) as exc:
            raise JevV6HandoffError("INVALID_NORMALIZED_EVIDENCE") from exc
    return JevV6EvidenceHandoff(
        packet_sha256=actual_digest,
        sections=sections,
        section_sources=section_sources,
        missing_evidence=tuple(missing),
        source_restrictions=dict(restrictions),
        state=state,
    )
