"""Evidence-bound ArchitectureValidationContract evaluation.

This module evaluates already-observed evidence. It does not run tests,
benchmarks, migrations, or specialist workflows.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


ARCHITECTURE_VALIDATION_CONTRACT_SCHEMA_VERSION = (
    "orchestra.architecture-validation-contract.v1"
)
VALIDATION_DIMENSIONS = (
    "functional_validation",
    "capacity_validation",
    "performance_validation",
    "tenant_isolation_validation",
    "migration_validation",
    "failure_behavior_validation",
    "compatibility_validation",
)
VALIDATION_PROOF_STATES = frozenset({"PROVEN", "NOT_PROVEN", "FAILED"})
APPLICABILITY_STATES = frozenset({"REQUIRED", "NOT_REQUIRED"})
EVIDENCE_FRESHNESS_STATES = frozenset({"CURRENT", "STALE", "SUPERSEDED"})


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _strings(value: object, field_name: str, *, required: bool = True) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an array of strings")
    result = tuple(_text(item, field_name) for item in value)
    if required and not result:
        raise ValueError(f"{field_name} must not be empty")
    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} contains duplicate values")
    return tuple(sorted(result))


def _normalized_contract_refs(value: object) -> tuple[str, ...]:
    return _strings(value, "contract_refs")


def _validated_obligations(
    obligations: Mapping[str, Mapping[str, Any]],
) -> dict[str, tuple[str, ...] | None]:
    if not isinstance(obligations, Mapping):
        raise ValueError("obligations must be an object")
    unknown = sorted(set(obligations) - set(VALIDATION_DIMENSIONS))
    missing = sorted(set(VALIDATION_DIMENSIONS) - set(obligations))
    if unknown:
        raise ValueError(f"obligations contains unknown dimensions: {unknown}")
    if missing:
        raise ValueError(f"obligations must state applicability for: {missing}")

    normalized: dict[str, tuple[str, ...] | None] = {}
    for dimension in VALIDATION_DIMENSIONS:
        record = obligations[dimension]
        if not isinstance(record, Mapping):
            raise ValueError(f"obligation {dimension} must be an object")
        applicability = _text(record.get("applicability"), f"{dimension}.applicability")
        if applicability not in APPLICABILITY_STATES:
            raise ValueError(
                f"{dimension}.applicability must be REQUIRED or NOT_REQUIRED"
            )
        criteria = _strings(
            record.get("criteria", ()),
            f"{dimension}.criteria",
            required=applicability == "REQUIRED",
        )
        if applicability == "NOT_REQUIRED" and criteria:
            raise ValueError(f"{dimension} must not declare criteria when NOT_REQUIRED")
        normalized[dimension] = criteria if applicability == "REQUIRED" else None
    return normalized


def _evidence_record(
    record: Mapping[str, Any],
    *,
    contract_refs: tuple[str, ...],
    exact_revision: str,
    environment_identity: str,
    declared_criteria: tuple[str, ...] | None,
) -> tuple[str, str, tuple[str, ...], bool, str | None]:
    reference = _text(record.get("evidence_ref"), "evidence_ref")
    dimension = _text(record.get("dimension"), "dimension")
    if dimension not in VALIDATION_DIMENSIONS:
        raise ValueError(f"evidence {reference} has unknown dimension: {dimension}")
    proof_state = _text(record.get("proof_state"), f"{reference}.proof_state")
    if proof_state not in VALIDATION_PROOF_STATES:
        raise ValueError(
            f"{reference}.proof_state must be PROVEN, NOT_PROVEN, or FAILED"
        )
    evidence_refs = _normalized_contract_refs(record.get("contract_refs"))
    evidence_revision = _text(record.get("exact_revision"), f"{reference}.exact_revision")
    evidence_environment = _text(
        record.get("environment_identity"), f"{reference}.environment_identity"
    )
    criteria = _strings(record.get("criteria", ()), f"{reference}.criteria")
    if declared_criteria is None:
        raise ValueError(f"evidence {reference} targets a NOT_REQUIRED dimension")
    if not set(criteria).issubset(declared_criteria):
        raise ValueError(f"evidence {reference} cites undeclared criteria")

    freshness = _text(record.get("evidence_status", "CURRENT"), f"{reference}.evidence_status")
    if freshness not in EVIDENCE_FRESHNESS_STATES:
        raise ValueError(
            f"{reference}.evidence_status must be CURRENT, STALE, or SUPERSEDED"
        )
    identity_matches = (
        evidence_refs == contract_refs
        and evidence_revision == exact_revision
        and evidence_environment == environment_identity
        and freshness == "CURRENT"
    )
    limitation = record.get("limitation")
    if limitation is not None:
        limitation = _text(limitation, f"{reference}.limitation")
    return reference, dimension, criteria, identity_matches, limitation


def evaluate_architecture_validation(
    *,
    contract_refs: Sequence[str],
    exact_revision: str,
    environment_identity: str,
    obligations: Mapping[str, Mapping[str, Any]],
    evidence: Iterable[Mapping[str, Any]],
    limitations: Iterable[str] = (),
) -> dict[str, Any]:
    """Build a schema-shaped validation contract from accepted evidence.

    Every dimension must be explicitly marked REQUIRED or NOT_REQUIRED. A
    required dimension is PROVEN only when current, exact-bound evidence covers
    every declared criterion. A matching FAILED observation takes precedence;
    absent, stale, mismatched, skipped, or unreliable proof remains
    NOT_PROVEN. The caller supplies observed evidence and remains responsible
    for running the underlying validation.
    """
    normalized_refs = _normalized_contract_refs(contract_refs)
    revision = _text(exact_revision, "exact_revision")
    environment = _text(environment_identity, "environment_identity")
    normalized_obligations = _validated_obligations(obligations)
    if isinstance(evidence, (str, bytes)):
        raise ValueError("evidence must be an array of objects")

    evidence_refs: list[str] = []
    normalized_limitations = [_text(item, "limitations") for item in limitations]
    proven: dict[str, set[str]] = {dimension: set() for dimension in VALIDATION_DIMENSIONS}
    failed: dict[str, set[str]] = {dimension: set() for dimension in VALIDATION_DIMENSIONS}

    for record in evidence:
        if not isinstance(record, Mapping):
            raise ValueError("each evidence record must be an object")
        reference = _text(record.get("evidence_ref"), "evidence_ref")
        if reference in evidence_refs:
            raise ValueError(f"duplicate evidence_ref: {reference}")
        evidence_refs.append(reference)
        dimension_hint = _text(record.get("dimension"), f"{reference}.dimension")
        reference, dimension, criteria, identity_matches, limitation = _evidence_record(
            record,
            contract_refs=normalized_refs,
            exact_revision=revision,
            environment_identity=environment,
            declared_criteria=normalized_obligations.get(dimension_hint),
        )
        proof_state = _text(record.get("proof_state"), f"{reference}.proof_state")
        if limitation:
            normalized_limitations.append(f"{reference}: {limitation}")
        if not identity_matches:
            normalized_limitations.append(
                f"{reference}: evidence is stale or does not match the exact contract revision and environment"
            )
            continue
        if proof_state == "PROVEN":
            proven[dimension].update(criteria)
        elif proof_state == "FAILED":
            failed[dimension].update(criteria)
        else:
            normalized_limitations.append(
                f"{reference}: required criterion remains NOT_PROVEN"
            )

    result: dict[str, Any] = {
        "schema_version": ARCHITECTURE_VALIDATION_CONTRACT_SCHEMA_VERSION,
        "contract_name": "ArchitectureValidationContract",
        "owner": "overseer",
        "contract_refs": list(normalized_refs),
        "exact_revision": revision,
        "environment_identity": environment,
    }
    for dimension in VALIDATION_DIMENSIONS:
        criteria = normalized_obligations[dimension]
        if criteria is None:
            result[dimension] = "NOT_REQUIRED"
        elif failed[dimension]:
            result[dimension] = "FAILED"
        elif set(criteria).issubset(proven[dimension]):
            result[dimension] = "PROVEN"
        else:
            result[dimension] = "NOT_PROVEN"

    result["limitations"] = sorted(set(normalized_limitations))
    result["evidence_refs"] = sorted(evidence_refs)
    return result


__all__ = [
    "ARCHITECTURE_VALIDATION_CONTRACT_SCHEMA_VERSION",
    "VALIDATION_DIMENSIONS",
    "VALIDATION_PROOF_STATES",
    "evaluate_architecture_validation",
]
