"""Explicit-root JSON store for scoped synthetic/advisory capability records."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from ...application.ports.capability_memory import CapabilityMemoryStore
from ...domain.adaptive.capability_inventory import (
    CapabilityInventoryClaim,
    CapabilityInventoryDescriptor,
    CapabilityInventoryIdentity,
    OperationPermissionObservation,
    SideEffectObservation,
)
from ...domain.adaptive.capability_memory import (
    CAPABILITY_MEMORY_SCHEMA_VERSION,
    CapabilityMemoryRecord,
    CapabilityMemoryRecordStatus,
    CapabilityMemoryScope,
)
from ...shared import canonical_json_bytes, receipt_digest


_IDENTITY_FIELDS = {
    "resource_id",
    "source_id",
    "host_id",
    "adapter_id",
    "publisher_id",
    "user_scope_id",
    "workspace_scope_id",
    "distribution_id",
    "distribution_version",
    "permission_scope_id",
    "source_revision",
    "distribution_digest",
    "inventory_scope_revision",
    "recheck_token",
    "identity_evidence_refs",
}
_DESCRIPTOR_FIELDS = {
    "identity",
    "resource_kind",
    "observation",
    "compatibility",
    "capability_claims",
    "permissions",
    "side_effects",
    "observation_evidence_refs",
    "compatibility_evidence_refs",
    "independent_output_refs",
    "review_refs",
    "observed_at",
    "valid_until",
    "limitations",
    "schema_version",
}
_RECORD_FIELDS = {
    "record_id",
    "scope",
    "kind",
    "descriptor",
    "recorded_at",
    "status",
    "superseded_by",
    "schema_version",
}
_RECORD_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")


def _mapping(value: object, fields: set[str], field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{field_name} has an unsupported shape")
    return value


def _items(value: object, field_name: str) -> tuple[Any, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return tuple(value)


def _record_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("record_id must be a string")
    normalized = value.strip().casefold()
    if not _RECORD_ID_RE.fullmatch(normalized):
        raise ValueError("record_id must be a canonical identifier")
    return normalized


def _scope(value: object) -> CapabilityMemoryScope:
    if not isinstance(value, CapabilityMemoryScope):
        raise TypeError("scope must be CapabilityMemoryScope")
    return value


def _scope_to_dict(scope: CapabilityMemoryScope) -> dict[str, str]:
    return {
        "host_id": scope.host_id,
        "user_scope_id": scope.user_scope_id,
        "workspace_scope_id": scope.workspace_scope_id,
    }


def _scope_from_dict(value: object) -> CapabilityMemoryScope:
    raw = _mapping(value, {"host_id", "user_scope_id", "workspace_scope_id"}, "scope")
    return CapabilityMemoryScope(**raw)


def _descriptor_to_dict(descriptor: CapabilityInventoryDescriptor) -> dict[str, Any]:
    identity = descriptor.identity
    return {
        "identity": {
            "resource_id": identity.resource_id,
            "source_id": identity.source_id,
            "host_id": identity.host_id,
            "adapter_id": identity.adapter_id,
            "publisher_id": identity.publisher_id,
            "user_scope_id": identity.user_scope_id,
            "workspace_scope_id": identity.workspace_scope_id,
            "distribution_id": identity.distribution_id,
            "distribution_version": identity.distribution_version,
            "permission_scope_id": identity.permission_scope_id,
            "source_revision": identity.source_revision,
            "distribution_digest": identity.distribution_digest,
            "inventory_scope_revision": identity.inventory_scope_revision,
            "recheck_token": identity.recheck_token,
            "identity_evidence_refs": list(identity.identity_evidence_refs),
        },
        "resource_kind": descriptor.resource_kind.value,
        "observation": descriptor.observation.value,
        "compatibility": descriptor.compatibility.value,
        "capability_claims": [
            {
                "capability_id": item.capability_id,
                "claim": item.claim.value,
                "evidence_refs": list(item.evidence_refs),
            }
            for item in descriptor.capability_claims
        ],
        "permissions": [
            {
                "operation_id": item.operation_id,
                "status": item.status.value,
                "evidence_refs": list(item.evidence_refs),
            }
            for item in descriptor.permissions
        ],
        "side_effects": [
            {
                "kind": item.kind.value,
                "status": item.status.value,
                "evidence_refs": list(item.evidence_refs),
            }
            for item in descriptor.side_effects
        ],
        "observation_evidence_refs": list(descriptor.observation_evidence_refs),
        "compatibility_evidence_refs": list(descriptor.compatibility_evidence_refs),
        "independent_output_refs": list(descriptor.independent_output_refs),
        "review_refs": list(descriptor.review_refs),
        "observed_at": descriptor.observed_at,
        "valid_until": descriptor.valid_until,
        "limitations": list(descriptor.limitations),
        "schema_version": descriptor.schema_version,
    }


def _descriptor_from_dict(value: object) -> CapabilityInventoryDescriptor:
    raw = _mapping(value, _DESCRIPTOR_FIELDS, "descriptor")
    identity_data = _mapping(raw["identity"], _IDENTITY_FIELDS, "identity")
    identity_args = dict(identity_data)
    identity_args["identity_evidence_refs"] = _items(
        identity_args["identity_evidence_refs"], "identity_evidence_refs"
    )
    claims = tuple(
        CapabilityInventoryClaim(
            **{
                **_mapping(item, {"capability_id", "claim", "evidence_refs"}, "capability_claim"),
                "evidence_refs": _items(item["evidence_refs"], "evidence_refs"),
            }
        )
        for item in _items(raw["capability_claims"], "capability_claims")
    )
    permissions = tuple(
        OperationPermissionObservation(
            **{
                **_mapping(item, {"operation_id", "status", "evidence_refs"}, "permission"),
                "evidence_refs": _items(item["evidence_refs"], "evidence_refs"),
            }
        )
        for item in _items(raw["permissions"], "permissions")
    )
    side_effects = tuple(
        SideEffectObservation(
            **{
                **_mapping(item, {"kind", "status", "evidence_refs"}, "side_effect"),
                "evidence_refs": _items(item["evidence_refs"], "evidence_refs"),
            }
        )
        for item in _items(raw["side_effects"], "side_effects")
    )
    return CapabilityInventoryDescriptor(
        identity=CapabilityInventoryIdentity(**identity_args),
        resource_kind=raw["resource_kind"],
        observation=raw["observation"],
        compatibility=raw["compatibility"],
        capability_claims=claims,
        permissions=permissions,
        side_effects=side_effects,
        observation_evidence_refs=_items(raw["observation_evidence_refs"], "observation_evidence_refs"),
        compatibility_evidence_refs=_items(raw["compatibility_evidence_refs"], "compatibility_evidence_refs"),
        independent_output_refs=_items(raw["independent_output_refs"], "independent_output_refs"),
        review_refs=_items(raw["review_refs"], "review_refs"),
        observed_at=raw["observed_at"],
        valid_until=raw["valid_until"],
        limitations=_items(raw["limitations"], "limitations"),
        schema_version=raw["schema_version"],
    )


def _record_to_dict(record: CapabilityMemoryRecord) -> dict[str, Any]:
    return {
        "record_id": record.record_id,
        "scope": _scope_to_dict(record.scope),
        "kind": record.kind.value,
        "descriptor": _descriptor_to_dict(record.descriptor),
        "recorded_at": record.recorded_at,
        "status": record.status.value,
        "superseded_by": record.superseded_by,
        "schema_version": record.schema_version,
    }


def _record_from_dict(value: object) -> CapabilityMemoryRecord:
    raw = _mapping(value, _RECORD_FIELDS, "record")
    return CapabilityMemoryRecord(
        record_id=raw["record_id"],
        scope=_scope_from_dict(raw["scope"]),
        kind=raw["kind"],
        descriptor=_descriptor_from_dict(raw["descriptor"]),
        recorded_at=raw["recorded_at"],
        status=raw["status"],
        superseded_by=raw["superseded_by"],
        schema_version=raw["schema_version"],
    )


class JsonCapabilityMemoryStore(CapabilityMemoryStore):
    """Scoped JSON persistence with no default location or production wiring."""

    def __init__(self, root: Path, *, repository_root: Path) -> None:
        self.root = Path(root).expanduser().resolve()
        repository = Path(repository_root).expanduser().resolve()
        if self.root == repository or repository in self.root.parents:
            raise ValueError("capability memory store must be outside the repository")

    def _path(self, scope: CapabilityMemoryScope) -> Path:
        _scope(scope)
        return self.root / "v1" / f"{receipt_digest(_scope_to_dict(scope))}.json"

    def _read(self, scope: CapabilityMemoryScope) -> tuple[CapabilityMemoryRecord, ...]:
        path = self._path(scope)
        if not path.exists():
            return ()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("capability memory data is unreadable") from exc
        envelope = _mapping(
            raw,
            {"schema_version", "scope", "records", "content_sha256"},
            "envelope",
        )
        if envelope["schema_version"] != CAPABILITY_MEMORY_SCHEMA_VERSION:
            raise ValueError("capability memory schema version is unsupported")
        stored_scope = _scope_from_dict(envelope["scope"])
        if stored_scope != scope:
            raise ValueError("capability memory scope does not match storage partition")
        records_data = _items(envelope["records"], "records")
        body = {
            "schema_version": envelope["schema_version"],
            "scope": envelope["scope"],
            "records": list(records_data),
        }
        if envelope["content_sha256"] != receipt_digest(body):
            raise ValueError("capability memory integrity check failed")
        records = tuple(_record_from_dict(item) for item in records_data)
        if any(record.scope != scope for record in records):
            raise ValueError("capability memory record scope mismatch")
        if len({record.record_id for record in records}) != len(records):
            raise ValueError("capability memory contains duplicate record ids")
        active_identities = [
            record.descriptor.identity
            for record in records
            if record.status is CapabilityMemoryRecordStatus.ACTIVE
        ]
        if len(set(active_identities)) != len(active_identities):
            raise ValueError("capability memory contains duplicate active identities")
        return tuple(sorted(records, key=lambda record: record.record_id))

    def _write(self, scope: CapabilityMemoryScope, records: tuple[CapabilityMemoryRecord, ...]) -> None:
        path = self._path(scope)
        path.parent.mkdir(parents=True, exist_ok=True)
        record_data = [_record_to_dict(item) for item in sorted(records, key=lambda record: record.record_id)]
        body = {
            "schema_version": CAPABILITY_MEMORY_SCHEMA_VERSION,
            "scope": _scope_to_dict(scope),
            "records": record_data,
        }
        envelope = {**body, "content_sha256": receipt_digest(body)}
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".capability-memory-", delete=False) as handle:
                temporary_path = Path(handle.name)
                handle.write(canonical_json_bytes(envelope) + b"\n")
            os.replace(temporary_path, path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def load(
        self,
        scope: CapabilityMemoryScope,
        *,
        include_inactive: bool = False,
    ) -> tuple[CapabilityMemoryRecord, ...]:
        _scope(scope)
        if not isinstance(include_inactive, bool):
            raise TypeError("include_inactive must be a boolean")
        records = self._read(scope)
        return records if include_inactive else tuple(
            record for record in records if record.status is CapabilityMemoryRecordStatus.ACTIVE
        )

    def save(self, record: CapabilityMemoryRecord) -> None:
        if not isinstance(record, CapabilityMemoryRecord):
            raise TypeError("record must be CapabilityMemoryRecord")
        if record.status is not CapabilityMemoryRecordStatus.ACTIVE:
            raise ValueError("only active records can be saved")
        records = self._read(record.scope)
        if any(item.record_id == record.record_id for item in records):
            raise ValueError("capability memory record id already exists")
        if any(
            item.status is CapabilityMemoryRecordStatus.ACTIVE
            and item.descriptor.identity == record.descriptor.identity
            for item in records
        ):
            raise ValueError("active capability memory identity already exists; supersede it")
        self._write(record.scope, (*records, record))

    def invalidate(self, scope: CapabilityMemoryScope, record_id: str) -> bool:
        _scope(scope)
        record_id = _record_id(record_id)
        records = self._read(scope)
        found = False
        updated: list[CapabilityMemoryRecord] = []
        for record in records:
            if record.record_id == record_id:
                if record.status is not CapabilityMemoryRecordStatus.ACTIVE:
                    return False
                record = CapabilityMemoryRecord(
                    record_id=record.record_id,
                    scope=record.scope,
                    kind=record.kind,
                    descriptor=record.descriptor,
                    recorded_at=record.recorded_at,
                    status=CapabilityMemoryRecordStatus.INVALIDATED,
                )
                found = True
            updated.append(record)
        if found:
            self._write(scope, tuple(updated))
        return found

    def supersede(
        self,
        scope: CapabilityMemoryScope,
        record_id: str,
        replacement: CapabilityMemoryRecord,
    ) -> None:
        _scope(scope)
        record_id = _record_id(record_id)
        if not isinstance(replacement, CapabilityMemoryRecord):
            raise TypeError("replacement must be CapabilityMemoryRecord")
        if replacement.scope != scope:
            raise ValueError("replacement must be a record in the same scope")
        if replacement.status is not CapabilityMemoryRecordStatus.ACTIVE:
            raise ValueError("replacement must be active")
        records = self._read(scope)
        previous = next((item for item in records if item.record_id == record_id), None)
        if previous is None:
            raise KeyError("capability memory record was not found")
        if previous.status is not CapabilityMemoryRecordStatus.ACTIVE:
            raise ValueError("only active records can be superseded")
        if any(item.record_id == replacement.record_id for item in records):
            raise ValueError("replacement record id already exists")
        if any(
            item.record_id != record_id
            and item.status is CapabilityMemoryRecordStatus.ACTIVE
            and item.descriptor.identity == replacement.descriptor.identity
            for item in records
        ):
            raise ValueError("replacement identity already exists as another active record")
        updated: list[CapabilityMemoryRecord] = []
        for record in records:
            if record.record_id == record_id:
                record = CapabilityMemoryRecord(
                    record_id=record.record_id,
                    scope=record.scope,
                    kind=record.kind,
                    descriptor=record.descriptor,
                    recorded_at=record.recorded_at,
                    status=CapabilityMemoryRecordStatus.SUPERSEDED,
                    superseded_by=replacement.record_id,
                )
            updated.append(record)
        self._write(scope, (*updated, replacement))

    def delete_record(self, scope: CapabilityMemoryScope, record_id: str) -> bool:
        _scope(scope)
        record_id = _record_id(record_id)
        records = self._read(scope)
        remaining = tuple(record for record in records if record.record_id != record_id)
        if len(remaining) == len(records):
            return False
        if remaining:
            self._write(scope, remaining)
        else:
            self._path(scope).unlink(missing_ok=True)
        return True

    def delete_scope(self, scope: CapabilityMemoryScope) -> int:
        _scope(scope)
        records = self._read(scope)
        if not records:
            return 0
        self._path(scope).unlink(missing_ok=True)
        return len(records)


__all__ = ["JsonCapabilityMemoryStore"]
