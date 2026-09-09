"""Pure AQ-6 gate-coverage truthfulness contracts.

AQ-6 compares changed behavior and required assurance with gates that declare
coverage and evidence that proves those gates executed. It evaluates supplied
evidence only; it does not read files, run tests, or grant authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping

from ...shared.canonicalization import normalize_git_sha, normalize_timestamp, receipt_digest
from .risk_profiler import ASSURANCE_ORDER, RISK_CHARACTERISTICS


AQ6_CONTRACT_SCHEMA_VERSION = "orchestra.aq6-gate-coverage.v1"
AQ6_DECISION_SCHEMA_VERSION = "orchestra.aq6-gate-coverage-decision.v1"
AQ6_AUTHORITY_MODEL = "EVIDENCE_ONLY_NON_AUTHORIZING"
AQ6_PHASE = "AQ6_GATE_COVERAGE_TRUTHFULNESS"

AQ6_REQUIRED_NEGATIVE_FIXTURES = (
    "DECLARED_GATE_DID_NOT_EXECUTE",
    "WORKFLOW_COMMAND_NOT_DECLARED",
    "UNKNOWN_TEST_REFERENCE",
    "TEST_DOES_NOT_REACH_CHANGED_CODE",
    "STALE_GATE_EVIDENCE",
    "LEGACY_GATE_COVERAGE_INSUFFICIENT",
    "TENANT_SECURITY_COVERAGE_INSUFFICIENT",
    "INCOMPLETE_INTEGRATION_WITH_GREEN_TESTS",
)

AQ6_FAILURE_CODES = (
    "AQ6_CURRENT_IDENTITY_REQUIRED",
    "AQ6_SOURCE_BINDING_MISMATCH",
    "AQ6_CANDIDATE_BINDING_MISMATCH",
    "AQ6_TREE_BINDING_MISMATCH",
    "AQ6_INVALID_MANIFEST",
    "AQ6_DUPLICATE_GATE_DECLARATION",
    "AQ6_GATE_NOT_EXECUTED",
    "AQ6_GATE_EXECUTION_FAILED",
    "AQ6_STALE_GATE_EVIDENCE",
    "AQ6_WORKFLOW_NOT_FOUND",
    "AQ6_WORKFLOW_COMMAND_MISSING",
    "AQ6_UNKNOWN_TEST_REFERENCE",
    "AQ6_TEST_NOT_EXECUTED",
    "AQ6_TEST_DOES_NOT_REACH_CHANGED_CODE",
    "AQ6_CHANGED_PATH_UNCOVERED",
    "AQ6_REQUIRED_ASSURANCE_UNCOVERED",
    "AQ6_REQUIRED_RISK_UNCOVERED",
    "AQ6_EXECUTION_SCOPE_EXCEEDED",
    "AQ6_DUPLICATE_GATE_EXECUTION",
    "AQ6_INVALID_INPUT",
)

AQ6_MANIFEST_FIELDS = (
    "schema_version", "manifest_id", "repository", "source_ref",
    "candidate_sha", "tree_sha", "work_item_ref", "changed_paths",
    "required_assurance", "required_risks", "declarations", "generated_at",
    "manifest_digest",
)
AQ6_DECLARATION_FIELDS = (
    "gate_id", "assurance_classes", "covered_paths", "covered_risks",
    "test_ids", "workflow_path", "commands", "does_not_cover",
)
AQ6_EXECUTION_FIELDS = (
    "execution_id", "gate_id", "result", "candidate_sha", "tree_sha",
    "command", "executed_test_ids", "observed_at",
)
AQ6_DECISION_FIELDS = (
    "schema_version", "decision_id", "repository", "source_ref",
    "candidate_sha", "tree_sha", "work_item_ref", "manifest_id", "result",
    "compliant", "failure_codes", "changed_paths", "required_assurance",
    "required_risks", "declared_assurance", "declared_risks", "covered_paths",
    "uncovered_paths", "missing_assurance", "missing_risks",
    "executed_gate_ids", "missing_gate_ids", "executed_test_ids",
    "evidence_receipt_ids", "generated_at", "decision_digest",
)

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_TEST_IDENTIFIER = re.compile(r"^[A-Za-z0-9_./:-]+$")


class GateCoverageContractError(ValueError):
    """A fail-closed AQ-6 contract violation."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        message = code if not detail else f"{code}: {detail}"
        super().__init__(message)


def _fail(code: str, detail: str = "") -> None:
    raise GateCoverageContractError(code, detail)


def _text(value: object, field_name: str, *, maximum: int = 512) -> str:
    if not isinstance(value, str):
        _fail("AQ6_INVALID_INPUT", f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned or len(cleaned) > maximum or any(ord(char) < 32 for char in cleaned):
        _fail("AQ6_INVALID_INPUT", f"{field_name} is invalid")
    return cleaned


def _identifier(value: object, field_name: str) -> str:
    cleaned = _text(value, field_name, maximum=256)
    if not _IDENTIFIER.fullmatch(cleaned):
        _fail("AQ6_INVALID_INPUT", f"{field_name} must be an identifier")
    return cleaned


def _items(value: object, field_name: str, *, maximum: int = 256) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        _fail("AQ6_INVALID_INPUT", f"{field_name} must be an array")
    values = tuple(value)
    if len(values) > maximum:
        _fail("AQ6_INVALID_INPUT", f"{field_name} is too large")
    return values


def _strings(value: object, field_name: str, *, maximum: int = 256) -> tuple[str, ...]:
    return tuple(sorted({_text(item, field_name) for item in _items(value, field_name, maximum=maximum)}))


def _identifiers(value: object, field_name: str, *, maximum: int = 256) -> tuple[str, ...]:
    return tuple(sorted({_identifier(item, field_name) for item in _items(value, field_name, maximum=maximum)}))


def _test_identifiers(value: object, field_name: str, *, maximum: int = 256) -> tuple[str, ...]:
    values = []
    for item in _items(value, field_name, maximum=maximum):
        cleaned = _text(item, field_name, maximum=512).replace(chr(92), "/")
        path = cleaned.split("::", 1)[0]
        if (
            not _TEST_IDENTIFIER.fullmatch(cleaned)
            or cleaned.startswith("/")
            or any(part in {"", ".", ".."} for part in path.split("/"))
        ):
            _fail("AQ6_INVALID_INPUT", f"{field_name} must be a test reference")
        values.append(cleaned)
    return tuple(sorted(set(values)))


def _paths(value: object, field_name: str) -> tuple[str, ...]:
    paths = []
    for item in _items(value, field_name):
        path = _text(item, field_name, maximum=1024).replace(chr(92), "/")
        if path.startswith("/") or ":" in path or any(part in {"", ".", ".."} for part in path.split("/")):
            _fail("AQ6_INVALID_INPUT", f"{field_name} contains a non-relative path")
        paths.append(path)
    return tuple(sorted(set(paths)))


def _assurance(value: object, field_name: str) -> tuple[str, ...]:
    values = _identifiers(value, field_name)
    if set(values) - set(ASSURANCE_ORDER):
        _fail("AQ6_INVALID_INPUT", f"{field_name} contains an unknown assurance class")
    return tuple(item for item in ASSURANCE_ORDER if item in values)


def _risks(value: object, field_name: str) -> tuple[str, ...]:
    values = _identifiers(value, field_name)
    if set(values) - set(RISK_CHARACTERISTICS):
        _fail("AQ6_INVALID_INPUT", f"{field_name} contains an unknown risk")
    return tuple(item for item in RISK_CHARACTERISTICS if item in values)


def _payload_digest(payload: Mapping[str, Any]) -> str:
    return receipt_digest(payload)


@dataclass(frozen=True, slots=True)
class GateCoverageDeclaration:
    gate_id: str
    assurance_classes: tuple[str, ...]
    covered_paths: tuple[str, ...]
    covered_risks: tuple[str, ...]
    test_ids: tuple[str, ...]
    workflow_path: str
    commands: tuple[str, ...]
    does_not_cover: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", _identifier(self.gate_id, "gate_id"))
        object.__setattr__(self, "assurance_classes", _assurance(self.assurance_classes, "assurance_classes"))
        object.__setattr__(self, "covered_paths", _paths(self.covered_paths, "covered_paths"))
        object.__setattr__(self, "covered_risks", _risks(self.covered_risks, "covered_risks"))
        object.__setattr__(self, "test_ids", _test_identifiers(self.test_ids, "test_ids"))
        object.__setattr__(self, "workflow_path", _text(self.workflow_path, "workflow_path", maximum=1024).replace(chr(92), "/"))
        object.__setattr__(self, "commands", _strings(self.commands, "commands", maximum=32))
        object.__setattr__(self, "does_not_cover", _strings(self.does_not_cover, "does_not_cover", maximum=128))
        if not self.assurance_classes or not self.covered_paths or not self.test_ids or not self.commands:
            _fail("AQ6_INVALID_INPUT", "a gate declaration needs assurance, paths, tests, and commands")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "GateCoverageDeclaration":
        if not isinstance(data, Mapping):
            raise TypeError("AQ6 gate declaration must be a mapping")
        unknown = set(data) - set(AQ6_DECLARATION_FIELDS)
        if unknown:
            _fail("AQ6_INVALID_INPUT", "unsupported declaration fields: " + ", ".join(sorted(unknown)))
        return cls(
            gate_id=data.get("gate_id", ""),
            assurance_classes=tuple(data.get("assurance_classes", ())),
            covered_paths=tuple(data.get("covered_paths", ())),
            covered_risks=tuple(data.get("covered_risks", ())),
            test_ids=tuple(data.get("test_ids", ())),
            workflow_path=data.get("workflow_path", ""),
            commands=tuple(data.get("commands", ())),
            does_not_cover=tuple(data.get("does_not_cover", ())),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "assurance_classes": list(self.assurance_classes),
            "covered_paths": list(self.covered_paths),
            "covered_risks": list(self.covered_risks),
            "test_ids": list(self.test_ids),
            "workflow_path": self.workflow_path,
            "commands": list(self.commands),
            "does_not_cover": list(self.does_not_cover),
        }


@dataclass(frozen=True, slots=True)
class GateCoverageManifest:
    schema_version: str
    manifest_id: str
    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    work_item_ref: str
    changed_paths: tuple[str, ...]
    required_assurance: tuple[str, ...]
    required_risks: tuple[str, ...]
    declarations: tuple[GateCoverageDeclaration, ...]
    generated_at: str
    manifest_digest: str

    def __post_init__(self) -> None:
        if self.schema_version != AQ6_CONTRACT_SCHEMA_VERSION:
            _fail("AQ6_INVALID_MANIFEST", "unsupported AQ6 manifest schema")
        for field_name in ("manifest_id", "repository", "source_ref", "work_item_ref"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "changed_paths", _paths(self.changed_paths, "changed_paths"))
        object.__setattr__(self, "required_assurance", _assurance(self.required_assurance, "required_assurance"))
        object.__setattr__(self, "required_risks", _risks(self.required_risks, "required_risks"))
        declarations = tuple(self.declarations)
        if not declarations or len({item.gate_id for item in declarations}) != len(declarations):
            _fail("AQ6_DUPLICATE_GATE_DECLARATION", "gate declaration ids must be unique")
        object.__setattr__(self, "declarations", declarations)
        object.__setattr__(self, "generated_at", normalize_timestamp(self.generated_at, "generated_at"))
        digest = _text(self.manifest_digest, "manifest_digest", maximum=64).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            _fail("AQ6_INVALID_MANIFEST", "manifest_digest must be SHA-256")
        object.__setattr__(self, "manifest_digest", digest)
        if self.manifest_digest != _payload_digest(self._payload()):
            _fail("AQ6_INVALID_MANIFEST", "manifest_digest does not match canonical manifest")

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "manifest_id": self.manifest_id,
            "repository": self.repository,
            "source_ref": self.source_ref,
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "work_item_ref": self.work_item_ref,
            "changed_paths": list(self.changed_paths),
            "required_assurance": list(self.required_assurance),
            "required_risks": list(self.required_risks),
            "declarations": [item.to_dict() for item in self.declarations],
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "GateCoverageManifest":
        if not isinstance(data, Mapping):
            raise TypeError("AQ6 manifest must be a mapping")
        missing = set(AQ6_MANIFEST_FIELDS) - set(data)
        unknown = set(data) - set(AQ6_MANIFEST_FIELDS)
        if missing or unknown:
            _fail("AQ6_INVALID_MANIFEST", "manifest fields do not match the contract")
        declarations = tuple(
            GateCoverageDeclaration.from_mapping(item)
            for item in _items(data["declarations"], "declarations")
        )
        return cls(
            schema_version=data["schema_version"],
            manifest_id=data["manifest_id"],
            repository=data["repository"],
            source_ref=data["source_ref"],
            candidate_sha=data["candidate_sha"],
            tree_sha=data["tree_sha"],
            work_item_ref=data["work_item_ref"],
            changed_paths=tuple(data["changed_paths"]),
            required_assurance=tuple(data["required_assurance"]),
            required_risks=tuple(data["required_risks"]),
            declarations=declarations,
            generated_at=data["generated_at"],
            manifest_digest=data["manifest_digest"],
        )

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload()
        payload["manifest_digest"] = self.manifest_digest
        return payload


@dataclass(frozen=True, slots=True)
class GateExecutionReceipt:
    execution_id: str
    gate_id: str
    result: str
    candidate_sha: str
    tree_sha: str
    command: str
    executed_test_ids: tuple[str, ...]
    observed_at: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "execution_id", _identifier(self.execution_id, "execution_id"))
        object.__setattr__(self, "gate_id", _identifier(self.gate_id, "gate_id"))
        if self.result not in {"PASS", "FAIL", "BLOCKED"}:
            _fail("AQ6_INVALID_INPUT", "execution result is invalid")
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "command", _text(self.command, "command", maximum=1024))
        object.__setattr__(self, "executed_test_ids", _test_identifiers(self.executed_test_ids, "executed_test_ids"))
        object.__setattr__(self, "observed_at", normalize_timestamp(self.observed_at, "observed_at"))

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "GateExecutionReceipt":
        if not isinstance(data, Mapping):
            raise TypeError("AQ6 execution receipt must be a mapping")
        unknown = set(data) - set(AQ6_EXECUTION_FIELDS)
        if unknown:
            _fail("AQ6_INVALID_INPUT", "unsupported execution fields: " + ", ".join(sorted(unknown)))
        return cls(
            execution_id=data.get("execution_id", ""),
            gate_id=data.get("gate_id", ""),
            result=data.get("result", ""),
            candidate_sha=data.get("candidate_sha", ""),
            tree_sha=data.get("tree_sha", ""),
            command=data.get("command", ""),
            executed_test_ids=tuple(data.get("executed_test_ids", ())),
            observed_at=data.get("observed_at", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "gate_id": self.gate_id,
            "result": self.result,
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "command": self.command,
            "executed_test_ids": list(self.executed_test_ids),
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True, slots=True)
class GateCoverageDecision:
    schema_version: str
    decision_id: str
    repository: str
    source_ref: str
    candidate_sha: str
    tree_sha: str
    work_item_ref: str
    manifest_id: str
    result: str
    failure_codes: tuple[str, ...]
    changed_paths: tuple[str, ...]
    required_assurance: tuple[str, ...]
    required_risks: tuple[str, ...]
    declared_assurance: tuple[str, ...]
    declared_risks: tuple[str, ...]
    covered_paths: tuple[str, ...]
    uncovered_paths: tuple[str, ...]
    missing_assurance: tuple[str, ...]
    missing_risks: tuple[str, ...]
    executed_gate_ids: tuple[str, ...]
    missing_gate_ids: tuple[str, ...]
    executed_test_ids: tuple[str, ...]
    evidence_receipt_ids: tuple[str, ...]
    generated_at: str
    decision_digest: str

    def __post_init__(self) -> None:
        if self.schema_version != AQ6_DECISION_SCHEMA_VERSION or self.result not in {"PASS", "FAIL"}:
            _fail("AQ6_INVALID_INPUT", "invalid AQ6 decision header")
        for field_name in ("decision_id", "repository", "source_ref", "work_item_ref", "manifest_id"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))
        object.__setattr__(self, "candidate_sha", normalize_git_sha(self.candidate_sha, "candidate_sha"))
        object.__setattr__(self, "tree_sha", normalize_git_sha(self.tree_sha, "tree_sha"))
        object.__setattr__(self, "failure_codes", _identifiers(self.failure_codes, "failure_codes"))
        for field_name in ("changed_paths", "covered_paths", "uncovered_paths"):
            object.__setattr__(self, field_name, _paths(getattr(self, field_name), field_name))
        for field_name in ("required_assurance", "declared_assurance", "missing_assurance"):
            object.__setattr__(self, field_name, _assurance(getattr(self, field_name), field_name))
        for field_name in ("required_risks", "declared_risks", "missing_risks"):
            object.__setattr__(self, field_name, _risks(getattr(self, field_name), field_name))
        for field_name in ("executed_gate_ids", "missing_gate_ids", "evidence_receipt_ids"):
            object.__setattr__(self, field_name, _identifiers(getattr(self, field_name), field_name))
        object.__setattr__(self, "executed_test_ids", _test_identifiers(self.executed_test_ids, "executed_test_ids"))
        object.__setattr__(self, "generated_at", normalize_timestamp(self.generated_at, "generated_at"))
        digest = _text(self.decision_digest, "decision_digest", maximum=64).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            _fail("AQ6_INVALID_INPUT", "decision_digest must be SHA-256")
        object.__setattr__(self, "decision_digest", digest)
        if self.result == "PASS" and self.failure_codes:
            _fail("AQ6_INVALID_INPUT", "PASS decision cannot contain failures")
        if self.decision_digest != _payload_digest(self._payload()):
            _fail("AQ6_INVALID_INPUT", "decision_digest does not match canonical decision")

    @property
    def compliant(self) -> bool:
        return self.result == "PASS" and not self.failure_codes

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "repository": self.repository,
            "source_ref": self.source_ref,
            "candidate_sha": self.candidate_sha,
            "tree_sha": self.tree_sha,
            "work_item_ref": self.work_item_ref,
            "manifest_id": self.manifest_id,
            "result": self.result,
            "compliant": self.compliant,
            "failure_codes": list(self.failure_codes),
            "changed_paths": list(self.changed_paths),
            "required_assurance": list(self.required_assurance),
            "required_risks": list(self.required_risks),
            "declared_assurance": list(self.declared_assurance),
            "declared_risks": list(self.declared_risks),
            "covered_paths": list(self.covered_paths),
            "uncovered_paths": list(self.uncovered_paths),
            "missing_assurance": list(self.missing_assurance),
            "missing_risks": list(self.missing_risks),
            "executed_gate_ids": list(self.executed_gate_ids),
            "missing_gate_ids": list(self.missing_gate_ids),
            "executed_test_ids": list(self.executed_test_ids),
            "evidence_receipt_ids": list(self.evidence_receipt_ids),
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "GateCoverageDecision":
        if not isinstance(data, Mapping):
            raise TypeError("AQ6 decision must be a mapping")
        missing = set(AQ6_DECISION_FIELDS) - set(data)
        unknown = set(data) - set(AQ6_DECISION_FIELDS)
        if missing or unknown:
            _fail("AQ6_INVALID_INPUT", "decision fields do not match the contract")
        if data.get("compliant") is not (data.get("result") == "PASS"):
            _fail("AQ6_INVALID_INPUT", "compliant must match result")
        return cls(
            schema_version=data["schema_version"],
            decision_id=data["decision_id"],
            repository=data["repository"],
            source_ref=data["source_ref"],
            candidate_sha=data["candidate_sha"],
            tree_sha=data["tree_sha"],
            work_item_ref=data["work_item_ref"],
            manifest_id=data["manifest_id"],
            result=data["result"],
            failure_codes=tuple(data["failure_codes"]),
            changed_paths=tuple(data["changed_paths"]),
            required_assurance=tuple(data["required_assurance"]),
            required_risks=tuple(data["required_risks"]),
            declared_assurance=tuple(data["declared_assurance"]),
            declared_risks=tuple(data["declared_risks"]),
            covered_paths=tuple(data["covered_paths"]),
            uncovered_paths=tuple(data["uncovered_paths"]),
            missing_assurance=tuple(data["missing_assurance"]),
            missing_risks=tuple(data["missing_risks"]),
            executed_gate_ids=tuple(data["executed_gate_ids"]),
            missing_gate_ids=tuple(data["missing_gate_ids"]),
            executed_test_ids=tuple(data["executed_test_ids"]),
            evidence_receipt_ids=tuple(data["evidence_receipt_ids"]),
            generated_at=data["generated_at"],
            decision_digest=data["decision_digest"],
        )

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload()
        payload["decision_digest"] = self.decision_digest
        return payload


def _coerce_manifest(value: GateCoverageManifest | Mapping[str, Any]) -> GateCoverageManifest:
    return value if isinstance(value, GateCoverageManifest) else GateCoverageManifest.from_mapping(value)


def _coerce_receipts(
    value: Iterable[GateExecutionReceipt | Mapping[str, Any]] | Mapping[str, Any],
) -> tuple[GateExecutionReceipt, ...]:
    if isinstance(value, Mapping):
        value = value.get("executions", value.get("receipts", ()))
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError("AQ6 executions must be an iterable")
    return tuple(
        item if isinstance(item, GateExecutionReceipt) else GateExecutionReceipt.from_mapping(item)
        for item in value
    )


def _add(failures: list[str], *codes: str) -> None:
    for code in codes:
        if code and code not in failures:
            failures.append(code)


def _decision(
    manifest: GateCoverageManifest,
    *,
    result: str,
    failures: Iterable[str],
    declared_assurance: tuple[str, ...],
    declared_risks: tuple[str, ...],
    covered_paths: tuple[str, ...],
    uncovered_paths: tuple[str, ...],
    missing_assurance: tuple[str, ...],
    missing_risks: tuple[str, ...],
    executed_gate_ids: tuple[str, ...],
    missing_gate_ids: tuple[str, ...],
    executed_test_ids: tuple[str, ...],
    evidence_receipt_ids: tuple[str, ...],
    generated_at: str,
) -> GateCoverageDecision:
    failure_codes = tuple(sorted(set(failures)))
    seed = {
        "schema_version": AQ6_DECISION_SCHEMA_VERSION,
        "decision_id": "pending",
        "repository": manifest.repository,
        "source_ref": manifest.source_ref,
        "candidate_sha": manifest.candidate_sha,
        "tree_sha": manifest.tree_sha,
        "work_item_ref": manifest.work_item_ref,
        "manifest_id": manifest.manifest_id,
        "result": result,
        "compliant": result == "PASS",
        "failure_codes": list(failure_codes),
        "changed_paths": list(manifest.changed_paths),
        "required_assurance": list(manifest.required_assurance),
        "required_risks": list(manifest.required_risks),
        "declared_assurance": list(declared_assurance),
        "declared_risks": list(declared_risks),
        "covered_paths": list(covered_paths),
        "uncovered_paths": list(uncovered_paths),
        "missing_assurance": list(missing_assurance),
        "missing_risks": list(missing_risks),
        "executed_gate_ids": list(executed_gate_ids),
        "missing_gate_ids": list(missing_gate_ids),
        "executed_test_ids": list(executed_test_ids),
        "evidence_receipt_ids": list(evidence_receipt_ids),
        "generated_at": generated_at,
    }
    decision_id = "aq6-" + _payload_digest(seed)[:20]
    seed["decision_id"] = decision_id
    decision_digest = _payload_digest(seed)
    seed.pop("compliant")
    return GateCoverageDecision(**seed, decision_digest=decision_digest)


def evaluate_gate_coverage(
    manifest: GateCoverageManifest | Mapping[str, Any],
    executions: Iterable[GateExecutionReceipt | Mapping[str, Any]] | Mapping[str, Any],
    *,
    current_repository: str | None = None,
    current_source_ref: str | None = None,
    current_candidate_sha: str | None = None,
    current_tree_sha: str | None = None,
    current_work_item_ref: str | None = None,
    available_test_ids: Iterable[str] = (),
    workflow_texts: Mapping[str, str] | None = None,
    test_coverage: Mapping[str, Iterable[str]] | None = None,
    evaluated_at: str | None = None,
) -> GateCoverageDecision:
    """Compare changed behavior, declarations, and execution evidence."""

    manifest_obj = _coerce_manifest(manifest)
    failures: list[str] = []
    identity = (
        current_repository,
        current_source_ref,
        current_candidate_sha,
        current_tree_sha,
        current_work_item_ref,
    )
    if any(value is None for value in identity):
        _add(failures, "AQ6_CURRENT_IDENTITY_REQUIRED")
    repository = manifest_obj.repository if current_repository is None else _text(current_repository, "current_repository")
    source_ref = manifest_obj.source_ref if current_source_ref is None else _text(current_source_ref, "current_source_ref")
    candidate_sha = (
        manifest_obj.candidate_sha
        if current_candidate_sha is None
        else normalize_git_sha(current_candidate_sha, "current_candidate_sha")
    )
    tree_sha = manifest_obj.tree_sha if current_tree_sha is None else normalize_git_sha(current_tree_sha, "current_tree_sha")
    work_item_ref = manifest_obj.work_item_ref if current_work_item_ref is None else _text(current_work_item_ref, "current_work_item_ref")
    if current_repository is not None and repository != manifest_obj.repository:
        _add(failures, "AQ6_SOURCE_BINDING_MISMATCH")
    if current_source_ref is not None and source_ref != manifest_obj.source_ref:
        _add(failures, "AQ6_SOURCE_BINDING_MISMATCH")
    if current_candidate_sha is not None and candidate_sha != manifest_obj.candidate_sha:
        _add(failures, "AQ6_CANDIDATE_BINDING_MISMATCH")
    if current_tree_sha is not None and tree_sha != manifest_obj.tree_sha:
        _add(failures, "AQ6_TREE_BINDING_MISMATCH")
    if current_work_item_ref is not None and work_item_ref != manifest_obj.work_item_ref:
        _add(failures, "AQ6_INVALID_INPUT")

    declarations = {item.gate_id: item for item in manifest_obj.declarations}
    declared_assurance = tuple(
        item for item in ASSURANCE_ORDER
        if any(item in declaration.assurance_classes for declaration in declarations.values())
    )
    declared_risks = tuple(
        item for item in RISK_CHARACTERISTICS
        if any(item in declaration.covered_risks for declaration in declarations.values())
    )
    covered_paths = tuple(sorted({path for declaration in declarations.values() for path in declaration.covered_paths}))
    uncovered_paths = tuple(sorted(set(manifest_obj.changed_paths) - set(covered_paths)))
    missing_assurance = tuple(item for item in manifest_obj.required_assurance if item not in declared_assurance)
    missing_risks = tuple(item for item in manifest_obj.required_risks if item not in declared_risks)
    if uncovered_paths:
        _add(failures, "AQ6_CHANGED_PATH_UNCOVERED", "AQ6_INCOMPLETE_INTEGRATION_WITH_GREEN_TESTS")
    if missing_assurance:
        _add(failures, "AQ6_REQUIRED_ASSURANCE_UNCOVERED")
        if "TENANT_ISOLATION_ASSURANCE" in missing_assurance:
            _add(failures, "AQ6_TENANT_SECURITY_COVERAGE_INSUFFICIENT")
        if "ADVERSARIAL_ASSURANCE" in missing_assurance and manifest_obj.required_risks:
            _add(failures, "AQ6_LEGACY_GATE_COVERAGE_INSUFFICIENT")
    if missing_risks:
        _add(failures, "AQ6_REQUIRED_RISK_UNCOVERED")

    known_tests = _test_identifiers(available_test_ids, "available_test_ids")
    normalized_coverage: dict[str, tuple[str, ...]] = {}
    for test_id, paths in (test_coverage or {}).items():
        normalized_coverage[_test_identifiers((test_id,), "test_coverage test id")[0]] = _paths(
            paths, f"test_coverage[{test_id}]"
        )
    all_executed_tests: set[str] = set()
    receipt_map: dict[str, GateExecutionReceipt] = {}
    for receipt in _coerce_receipts(executions):
        if receipt.gate_id in receipt_map:
            _add(failures, "AQ6_DUPLICATE_GATE_EXECUTION")
        receipt_map[receipt.gate_id] = receipt
        all_executed_tests.update(receipt.executed_test_ids)
        if receipt.candidate_sha != candidate_sha or receipt.tree_sha != tree_sha:
            _add(failures, "AQ6_STALE_GATE_EVIDENCE")
        if receipt.result != "PASS":
            _add(failures, "AQ6_GATE_EXECUTION_FAILED")
        declaration = declarations.get(receipt.gate_id)
        if declaration is None:
            _add(failures, "AQ6_EXECUTION_SCOPE_EXCEEDED")
        elif not set(receipt.executed_test_ids).issubset(set(declaration.test_ids)):
            _add(failures, "AQ6_EXECUTION_SCOPE_EXCEEDED")

    workflow_map = {key.replace(chr(92), "/"): value for key, value in (workflow_texts or {}).items()}
    executed_gate_ids = tuple(
        sorted(gate_id for gate_id, receipt in receipt_map.items() if receipt.result == "PASS")
    )
    missing_gate_ids = tuple(sorted(set(declarations) - set(executed_gate_ids)))
    if missing_gate_ids:
        _add(failures, "AQ6_GATE_NOT_EXECUTED")
    for declaration in declarations.values():
        workflow = workflow_map.get(declaration.workflow_path)
        if workflow is None:
            _add(failures, "AQ6_WORKFLOW_NOT_FOUND")
        else:
            for command in declaration.commands:
                if command not in workflow:
                    _add(failures, "AQ6_WORKFLOW_COMMAND_MISSING")
        receipt = receipt_map.get(declaration.gate_id)
        if receipt is not None and receipt.result == "PASS":
            if receipt.command not in declaration.commands:
                _add(failures, "AQ6_WORKFLOW_COMMAND_MISSING")
            if set(declaration.test_ids) - set(receipt.executed_test_ids):
                _add(failures, "AQ6_TEST_NOT_EXECUTED")
    if known_tests:
        declared_tests = {
            test_id for declaration in declarations.values() for test_id in declaration.test_ids
        }
        if not declared_tests.issubset(set(known_tests)):
            _add(failures, "AQ6_UNKNOWN_TEST_REFERENCE")
    else:
        _add(failures, "AQ6_UNKNOWN_TEST_REFERENCE")
    covered_by_tests = {
        path
        for test_id in all_executed_tests
        for path in normalized_coverage.get(test_id, ())
    }
    if set(manifest_obj.changed_paths) - covered_by_tests:
        _add(failures, "AQ6_TEST_DOES_NOT_REACH_CHANGED_CODE")

    generated_at = (
        manifest_obj.generated_at
        if evaluated_at is None
        else normalize_timestamp(evaluated_at, "evaluated_at")
    )
    return _decision(
        manifest_obj,
        result="PASS" if not failures else "FAIL",
        failures=failures,
        declared_assurance=declared_assurance,
        declared_risks=declared_risks,
        covered_paths=covered_paths,
        uncovered_paths=uncovered_paths,
        missing_assurance=missing_assurance,
        missing_risks=missing_risks,
        executed_gate_ids=executed_gate_ids,
        missing_gate_ids=missing_gate_ids,
        executed_test_ids=tuple(sorted(all_executed_tests)),
        evidence_receipt_ids=tuple(sorted(receipt.execution_id for receipt in receipt_map.values())),
        generated_at=generated_at,
    )


def validate_gate_coverage_contract(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate the machine AQ-6 contract against runtime constants."""

    expected = {
        "schema_version": AQ6_CONTRACT_SCHEMA_VERSION,
        "phase": AQ6_PHASE,
        "owner": "overseer",
        "authority_model": AQ6_AUTHORITY_MODEL,
        "decision_schema_version": AQ6_DECISION_SCHEMA_VERSION,
        "manifest_fields": list(AQ6_MANIFEST_FIELDS),
        "declaration_fields": list(AQ6_DECLARATION_FIELDS),
        "execution_fields": list(AQ6_EXECUTION_FIELDS),
        "decision_fields": list(AQ6_DECISION_FIELDS),
        "required_negative_fixtures": list(AQ6_REQUIRED_NEGATIVE_FIXTURES),
        "failure_codes": list(AQ6_FAILURE_CODES),
        "assurance_classes": list(ASSURANCE_ORDER),
        "risk_characteristics": list(RISK_CHARACTERISTICS),
        "authority": {
            "decision_authorizes_execution": False,
            "decision_authorizes_transition": False,
            "decision_expands_authority": False,
            "production_action": False,
            "provider_activation": False,
        },
        "constraints": {
            "network_access": False,
            "repository_mutation": False,
            "test_execution": False,
            "promotion_or_transition": False,
        },
    }
    if not isinstance(contract, Mapping):
        raise TypeError("AQ6 machine contract must be a mapping")
    if set(contract) != set(expected) or any(
        contract.get(key) != value for key, value in expected.items()
    ):
        _fail("AQ6_INVALID_INPUT", "machine contract drift")
    return contract


validate_machine_contract = validate_gate_coverage_contract
validate_schema_runtime_parity = validate_gate_coverage_contract


__all__ = [
    "AQ6_AUTHORITY_MODEL",
    "AQ6_CONTRACT_SCHEMA_VERSION",
    "AQ6_DECISION_FIELDS",
    "AQ6_DECISION_SCHEMA_VERSION",
    "AQ6_FAILURE_CODES",
    "AQ6_MANIFEST_FIELDS",
    "AQ6_PHASE",
    "AQ6_REQUIRED_NEGATIVE_FIXTURES",
    "GateCoverageContractError",
    "GateCoverageDeclaration",
    "GateCoverageDecision",
    "GateCoverageManifest",
    "GateExecutionReceipt",
    "evaluate_gate_coverage",
    "validate_gate_coverage_contract",
    "validate_machine_contract",
    "validate_schema_runtime_parity",
]
