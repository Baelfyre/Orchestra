from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "orchestra.unified-testing-packet.v1"
STAGE_IDS = tuple(f"T{i}" for i in range(10))
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

STAGE_NAMES = {
    "T0": "Applicability & Evidence Plan",
    "T1": "Smoke / Sanity",
    "T2": "Functional",
    "T3": "Integration / Contract",
    "T4": "UI / UX / Accessibility / User Validation",
    "T5": "Load / Capacity / Performance",
    "T6": "Stress / Resilience / Recovery",
    "T7": "Security / Privacy / Abuse Resistance",
    "T8": "Regression / Compatibility / Portability",
    "T9": "Readiness Aggregation / Independent Verification",
}

STAGE_OWNERS = {
    "T0": ("conductor", "overseer"),
    "T1": ("overseer",),
    "T2": ("overseer",),
    "T3": ("overseer",),
    "T4": ("cloak", "overseer"),
    "T5": ("overseer", "dagger"),
    "T6": ("dagger", "overseer"),
    "T7": ("cipher", "overseer"),
    "T8": ("overseer",),
    "T9": ("overseer",),
}


@dataclass(frozen=True, slots=True)
class UnifiedTestingVerdict:
    disposition: str
    subject_sha: str
    release_intent: str
    required_stages: tuple[str, ...]
    passed_stages: tuple[str, ...]
    failed_stages: tuple[str, ...]
    pending_stages: tuple[str, ...]
    missing_stages: tuple[str, ...]
    human_signoff_status: str
    release_authorized: bool = False
    merge_authorized: bool = False
    deployment_authorized: bool = False
    policy_activation_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "subject_sha": self.subject_sha,
            "release_intent": self.release_intent,
            "required_stages": list(self.required_stages),
            "passed_stages": list(self.passed_stages),
            "failed_stages": list(self.failed_stages),
            "pending_stages": list(self.pending_stages),
            "missing_stages": list(self.missing_stages),
            "human_signoff_status": self.human_signoff_status,
            "release_authorized": self.release_authorized,
            "merge_authorized": self.merge_authorized,
            "deployment_authorized": self.deployment_authorized,
            "policy_activation_authorized": self.policy_activation_authorized,
        }


def _sha(value: object, field: str) -> str:
    cleaned = str(value or "").strip().lower()
    if _GIT_SHA_RE.fullmatch(cleaned) is None:
        raise ValueError(f"{field} must be an exact lowercase 40-character Git SHA")
    return cleaned


def _nonempty_strings(values: object, field: str) -> tuple[str, ...]:
    if not isinstance(values, list):
        raise ValueError(f"{field} must be an array")
    cleaned = tuple(str(item).strip() for item in values)
    if any(not item for item in cleaned):
        raise ValueError(f"{field} cannot contain blank values")
    if len(set(cleaned)) != len(cleaned):
        raise ValueError(f"{field} cannot contain duplicates")
    return cleaned


def validate_packet(packet: Mapping[str, Any]) -> None:
    if packet.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must equal {SCHEMA_VERSION}")

    subject = packet.get("subject")
    if not isinstance(subject, Mapping):
        raise ValueError("subject must be an object")
    subject_sha = _sha(subject.get("revision_sha"), "subject.revision_sha")
    repository = str(subject.get("repository") or "").strip()
    if "/" not in repository or repository.startswith("/") or repository.endswith("/"):
        raise ValueError("subject.repository must use owner/repository form")

    release_intent = packet.get("release_intent")
    if release_intent not in {"NON_RELEASE", "RELEASE_CANDIDATE"}:
        raise ValueError("release_intent must be NON_RELEASE or RELEASE_CANDIDATE")

    stages = packet.get("stages")
    if not isinstance(stages, list) or len(stages) != len(STAGE_IDS):
        raise ValueError("stages must contain exactly T0-T9")

    seen: set[str] = set()
    applicability: dict[str, str] = {}
    for index, item in enumerate(stages):
        if not isinstance(item, Mapping):
            raise ValueError(f"stages[{index}] must be an object")
        stage_id = str(item.get("stage_id") or "")
        if stage_id not in STAGE_IDS or stage_id in seen:
            raise ValueError("stages must contain each T0-T9 stage exactly once")
        seen.add(stage_id)
        if item.get("name") != STAGE_NAMES[stage_id]:
            raise ValueError(f"{stage_id} name must match the canonical stage name")
        owners = _nonempty_strings(item.get("owners"), f"{stage_id}.owners")
        if owners != STAGE_OWNERS[stage_id]:
            raise ValueError(f"{stage_id} owners must match the canonical ownership mapping")
        value = item.get("applicability")
        if value not in {"REQUIRED", "NOT_APPLICABLE"}:
            raise ValueError(f"{stage_id} has invalid applicability")
        rationale = str(item.get("rationale") or "").strip()
        if not rationale:
            raise ValueError(f"{stage_id} requires an applicability rationale")
        requirements = _nonempty_strings(item.get("evidence_requirements"), f"{stage_id}.evidence_requirements")
        if value == "REQUIRED" and not requirements:
            raise ValueError(f"{stage_id} requires at least one evidence requirement")
        if value == "NOT_APPLICABLE" and requirements:
            raise ValueError(f"{stage_id} NOT_APPLICABLE must not declare evidence requirements")
        applicability[stage_id] = value

    if applicability["T0"] != "REQUIRED" or applicability["T9"] != "REQUIRED":
        raise ValueError("T0 and T9 are always REQUIRED")

    evidence = packet.get("evidence")
    if not isinstance(evidence, list):
        raise ValueError("evidence must be an array")
    evidence_seen: set[str] = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, Mapping):
            raise ValueError(f"evidence[{index}] must be an object")
        stage_id = str(item.get("stage_id") or "")
        if stage_id not in STAGE_IDS or stage_id in evidence_seen:
            raise ValueError("evidence may contain each T0-T9 stage at most once")
        evidence_seen.add(stage_id)
        if applicability[stage_id] == "NOT_APPLICABLE":
            raise ValueError(f"{stage_id} is NOT_APPLICABLE and must not have evidence")
        if _sha(item.get("revision_sha"), f"{stage_id}.revision_sha") != subject_sha:
            raise ValueError(f"{stage_id} evidence is stale for the packet subject")
        result = item.get("result")
        if result not in {"PASS", "FAIL", "PENDING"}:
            raise ValueError(f"{stage_id} has invalid evidence result")
        refs = _nonempty_strings(item.get("evidence_refs"), f"{stage_id}.evidence_refs")
        if result in {"PASS", "FAIL"} and not refs:
            raise ValueError(f"{stage_id} terminal evidence requires evidence_refs")
        _nonempty_strings(item.get("limitations"), f"{stage_id}.limitations")

    signoff = packet.get("human_signoff")
    if not isinstance(signoff, Mapping):
        raise ValueError("human_signoff must be an object")
    status = signoff.get("status")
    if status not in {"NOT_REQUESTED", "PENDING", "APPROVED", "REJECTED"}:
        raise ValueError("human_signoff.status is invalid")
    owner = signoff.get("decision_owner")
    refs = _nonempty_strings(signoff.get("evidence_refs"), "human_signoff.evidence_refs")
    if status in {"APPROVED", "REJECTED"}:
        if not str(owner or "").strip() or not refs:
            raise ValueError("terminal human signoff requires decision_owner and evidence_refs")
    elif owner is not None or refs:
        raise ValueError("non-terminal human signoff must not claim decision evidence")


def aggregate_packet(packet: Mapping[str, Any]) -> UnifiedTestingVerdict:
    validate_packet(packet)
    subject_sha = str(packet["subject"]["revision_sha"])
    required = tuple(item["stage_id"] for item in packet["stages"] if item["applicability"] == "REQUIRED")
    by_stage = {item["stage_id"]: item for item in packet["evidence"]}

    passed = tuple(stage for stage in required if by_stage.get(stage, {}).get("result") == "PASS")
    failed = tuple(stage for stage in required if by_stage.get(stage, {}).get("result") == "FAIL")
    pending = tuple(stage for stage in required if by_stage.get(stage, {}).get("result") == "PENDING")
    missing = tuple(stage for stage in required if stage not in by_stage)

    if failed:
        disposition = "BLOCKED"
    elif pending or missing:
        disposition = "WAIT_FOR_EVIDENCE"
    else:
        disposition = "READINESS_EVIDENCE_COMPLETE"

    return UnifiedTestingVerdict(
        disposition=disposition,
        subject_sha=subject_sha,
        release_intent=str(packet["release_intent"]),
        required_stages=required,
        passed_stages=passed,
        failed_stages=failed,
        pending_stages=pending,
        missing_stages=missing,
        human_signoff_status=str(packet["human_signoff"]["status"]),
    )


def load_packet(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("packet root must be an object")
    return payload


def write_verdict(packet_path: Path, output_path: Path) -> UnifiedTestingVerdict:
    verdict = aggregate_packet(load_packet(packet_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(verdict.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return verdict
