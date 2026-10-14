# @codebase_provenance_JEO
# @codebase_rights_JEO

from dataclasses import replace
import json
from pathlib import Path

import pytest

from orchestra_runtime.application.ports.capability_memory import CapabilityMemoryStore
from orchestra_runtime.domain.adaptive.capability_inventory import (
    CapabilityDiscoveryDisposition,
    CapabilityDiscoveryTrigger,
    CapabilityInventoryClaim,
    CapabilityInventoryDescriptor,
    CapabilityInventoryIdentity,
    CapabilityResourceKind,
    InventoryCompatibilityStatus,
    InventoryObservationStatus,
)
from orchestra_runtime.domain.adaptive.capability_memory import (
    CapabilityMemoryRecord,
    CapabilityMemoryRecordKind,
    CapabilityMemoryRecordStatus,
    CapabilityMemoryScope,
)
from orchestra_runtime.domain.adaptive.capability_inventory import plan_capability_discovery
from orchestra_runtime.infrastructure.persistence.adaptive_capability_memory import (
    JsonCapabilityMemoryStore,
)
from orchestra_runtime.shared import receipt_digest
import orchestra_runtime.infrastructure.persistence.adaptive_capability_memory as memory_module


NOW = "2026-10-14T08:00:00Z"
FUTURE = "2026-10-15T08:00:00Z"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def scope(user: str = "user.one", workspace: str = "workspace.one") -> CapabilityMemoryScope:
    return CapabilityMemoryScope("host.desktop", user, workspace)


def descriptor(
    memory_scope: CapabilityMemoryScope | None = None,
    *,
    resource_id: str = "plugin.one",
    capability_id: str = "ui.accessibility",
    observation: InventoryObservationStatus | str = InventoryObservationStatus.PRESENT,
    compatibility: InventoryCompatibilityStatus | str = InventoryCompatibilityStatus.COMPATIBLE,
    observed_at: str | None = "2026-10-14T07:00:00Z",
    valid_until: str | None = FUTURE,
    resource_kind: CapabilityResourceKind | str = CapabilityResourceKind.EXTERNAL_PLUGIN,
    output_refs: tuple[str, ...] = (),
) -> CapabilityInventoryDescriptor:
    current_scope = memory_scope or scope()
    return CapabilityInventoryDescriptor(
        identity=CapabilityInventoryIdentity(
            resource_id,
            f"source.{resource_id}",
            host_id=current_scope.host_id,
            user_scope_id=current_scope.user_scope_id,
            workspace_scope_id=current_scope.workspace_scope_id,
            permission_scope_id="permissions.read.v1",
        ),
        resource_kind=resource_kind,
        observation=observation,
        compatibility=compatibility,
        capability_claims=(CapabilityInventoryClaim(capability_id, "SUPPORTS", ("evidence:capability",)),),
        observation_evidence_refs=("evidence:inventory",) if observation == InventoryObservationStatus.PRESENT else (),
        compatibility_evidence_refs=("evidence:compatibility",)
        if compatibility == InventoryCompatibilityStatus.COMPATIBLE
        else (),
        independent_output_refs=output_refs,
        review_refs=("evidence:review",),
        observed_at=observed_at,
        valid_until=valid_until,
    )


def record(
    record_id: str = "record.one",
    memory_scope: CapabilityMemoryScope | None = None,
    *,
    observation: CapabilityInventoryDescriptor | None = None,
    kind: CapabilityMemoryRecordKind | str = CapabilityMemoryRecordKind.CAPABILITY_OBSERVATION,
) -> CapabilityMemoryRecord:
    selected_scope = memory_scope or scope()
    return CapabilityMemoryRecord(
        record_id,
        selected_scope,
        kind,
        observation or descriptor(selected_scope),
        NOW,
    )


def store(tmp_path: Path) -> JsonCapabilityMemoryStore:
    return JsonCapabilityMemoryStore(tmp_path / "private-memory", repository_root=REPOSITORY_ROOT)


def rewrite_envelope(path: Path, envelope: dict[str, object]) -> None:
    body = {key: envelope[key] for key in ("schema_version", "scope", "records")}
    envelope["content_sha256"] = receipt_digest(body)
    path.write_text(json.dumps(envelope), encoding="utf-8")


def test_store_round_trips_scoped_records_and_partitions_user_workspaces(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    first_scope = scope()
    second_scope = scope("user.two", "workspace.two")
    first = record("record.a", first_scope)
    second = record("record.b", second_scope)

    assert isinstance(memory_store, CapabilityMemoryStore)
    memory_store.save(first)
    memory_store.save(second)

    assert memory_store.load(first_scope) == (first,)
    assert memory_store.load(second_scope) == (second,)
    assert memory_store.load(scope("user.three", "workspace.one")) == ()
    assert len(tuple((tmp_path / "private-memory" / "v1").glob("*.json"))) == 2


def test_scope_ids_must_be_canonical_and_records_require_complete_matching_identity() -> None:
    descriptor_value = descriptor()
    assert CapabilityMemoryScope.from_identity(descriptor_value.identity) == scope()

    with pytest.raises(TypeError, match="must be a string"):
        CapabilityMemoryScope(1, "user.one", "workspace.one")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="canonical identifier"):
        CapabilityMemoryScope("host", "../user", "workspace")

    with pytest.raises(ValueError, match="complete host, user, and workspace"):
        CapabilityMemoryScope.from_identity(CapabilityInventoryIdentity("plugin.one", "source.one"))

    with pytest.raises(ValueError, match="complete inventory identity scope"):
        record(observation=replace(descriptor(), identity=CapabilityInventoryIdentity("plugin.one", "source.one")))

    with pytest.raises(ValueError, match="does not match memory scope"):
        record(observation=descriptor(scope("user.other", "workspace.one")))


def test_memory_record_rejects_malformed_fields_and_lifecycle_states() -> None:
    valid = record()
    assert record("record.string-kind", kind="CAPABILITY_OBSERVATION").kind is CapabilityMemoryRecordKind.CAPABILITY_OBSERVATION

    with pytest.raises(TypeError, match="record_id must be a string"):
        record(1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="scope must be CapabilityMemoryScope"):
        replace(valid, scope=object())
    with pytest.raises(TypeError, match="descriptor must be CapabilityInventoryDescriptor"):
        replace(valid, descriptor=object())
    with pytest.raises(ValueError, match="schema_version is unsupported"):
        replace(valid, schema_version="orchestra.capability-memory.v2")
    with pytest.raises(TypeError, match="kind must be a string"):
        replace(valid, kind=1)
    with pytest.raises(ValueError, match="kind is unsupported"):
        replace(valid, kind="UNKNOWN")
    with pytest.raises(TypeError, match="status must be a string"):
        replace(valid, status=1)
    with pytest.raises(ValueError, match="status is unsupported"):
        replace(valid, status="UNKNOWN")
    with pytest.raises(ValueError, match="superseded records require"):
        replace(valid, status=CapabilityMemoryRecordStatus.SUPERSEDED)
    with pytest.raises(ValueError, match="different superseded_by"):
        replace(valid, status=CapabilityMemoryRecordStatus.SUPERSEDED, superseded_by=valid.record_id)
    with pytest.raises(ValueError, match="only superseded records"):
        replace(valid, superseded_by="record.other")
    with pytest.raises(ValueError, match="recorded_at"):
        replace(valid, recorded_at="not-a-timestamp")


def test_stale_records_remain_available_to_the_existing_selective_planner(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    fresh = descriptor(current_scope, resource_id="plugin.fresh", capability_id="ui.accessibility")
    stale = descriptor(
        current_scope,
        resource_id="plugin.stale",
        capability_id="ui.accessibility",
        valid_until="2026-10-14T07:59:59Z",
    )
    unrelated = descriptor(current_scope, resource_id="plugin.other", capability_id="code.formatting")
    for item in (
        record("record.fresh", current_scope, observation=fresh),
        record("record.stale", current_scope, observation=stale),
        record("record.other", current_scope, observation=unrelated),
    ):
        memory_store.save(item)

    cached = memory_store.load(current_scope)
    current_identities = tuple(item.descriptor.identity for item in cached)
    plan = plan_capability_discovery(
        CapabilityDiscoveryTrigger("CAPABILITY_GAP", ("ui.accessibility",), ()),
        tuple(item.descriptor for item in cached),
        current_identities,
        evaluated_at=NOW,
    )

    assert {item.identity.resource_id for item in plan.relevant_observations} == {"plugin.fresh", "plugin.stale"}
    assert plan.reuse_hint_identities == (fresh.identity,)
    assert plan.revalidate_identities == (stale.identity,)
    assert plan.target_capability_ids == ()
    assert plan.target_resource_ids == ("plugin.stale",)
    assert plan.disposition is CapabilityDiscoveryDisposition.TARGETED_DISCOVERY


def test_reusable_pattern_records_are_evidence_references_not_free_text(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    pattern = descriptor(
        current_scope,
        resource_id="pattern.accessibility",
        resource_kind=CapabilityResourceKind.PRIVATE_REFERENCE,
        output_refs=("evidence:pattern-review",),
    )
    pattern_record = record(
        "pattern.one",
        current_scope,
        observation=pattern,
        kind=CapabilityMemoryRecordKind.REUSABLE_PATTERN,
    )

    memory_store.save(pattern_record)

    assert memory_store.load(current_scope) == (pattern_record,)
    assert "raw_conversation" not in pattern_record.__dataclass_fields__
    with pytest.raises(ValueError, match="PRIVATE_REFERENCE"):
        record("pattern.bad", current_scope, kind="REUSABLE_PATTERN")
    with pytest.raises(ValueError, match="evidence references"):
        no_evidence = descriptor(
            current_scope,
            resource_id="pattern.no_evidence",
            resource_kind=CapabilityResourceKind.PRIVATE_REFERENCE,
        )
        record("pattern.no_evidence", current_scope, observation=no_evidence, kind="REUSABLE_PATTERN")


def test_invalidation_and_supersession_keep_inactive_records_out_of_cache_reads(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    original = record("record.original", current_scope)
    unrelated = record(
        "record.unrelated",
        current_scope,
        observation=descriptor(current_scope, resource_id="plugin.unrelated"),
    )
    memory_store.save(original)
    memory_store.save(unrelated)
    replacement_descriptor = replace(original.descriptor, observed_at="2026-10-14T07:30:00Z")
    replacement = record("record.replacement", current_scope, observation=replacement_descriptor)

    memory_store.supersede(current_scope, original.record_id, replacement)

    active = memory_store.load(current_scope)
    all_records = memory_store.load(current_scope, include_inactive=True)
    assert active == (replacement, unrelated)
    records_by_id = {item.record_id: item for item in all_records}
    assert len(all_records) == 3
    assert records_by_id[original.record_id].status is CapabilityMemoryRecordStatus.SUPERSEDED
    assert records_by_id[original.record_id].superseded_by == replacement.record_id
    assert memory_store.invalidate(current_scope, replacement.record_id)
    assert memory_store.load(current_scope) == (unrelated,)
    assert {item.record_id: item for item in memory_store.load(current_scope, include_inactive=True)}[
        replacement.record_id
    ].status is CapabilityMemoryRecordStatus.INVALIDATED
    assert not memory_store.invalidate(current_scope, replacement.record_id)


def test_save_rejects_duplicate_ids_and_active_identity_without_supersession(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    first = record("record.first", current_scope)
    memory_store.save(first)

    with pytest.raises(ValueError, match="record id already exists"):
        memory_store.save(first)
    with pytest.raises(ValueError, match="active capability memory identity already exists"):
        memory_store.save(record("record.second", current_scope))

    with pytest.raises(KeyError, match="not found"):
        memory_store.supersede(current_scope, "record.missing", record("record.third", current_scope))
    with pytest.raises(ValueError, match="same scope"):
        memory_store.supersede(
            current_scope,
            "record.first",
            record("record.other", scope("user.other", "workspace.other")),
        )


def test_delete_record_and_scope_remove_only_the_selected_partition(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    first_scope = scope()
    second_scope = scope("user.two", "workspace.two")
    first = record("record.first", first_scope)
    second = record("record.second", second_scope)
    memory_store.save(first)
    memory_store.save(second)

    assert memory_store.delete_record(first_scope, first.record_id)
    assert not memory_store.delete_record(first_scope, first.record_id)
    assert memory_store.load(first_scope) == ()
    assert memory_store.load(second_scope) == (second,)
    assert memory_store.delete_scope(second_scope) == 1
    assert memory_store.delete_scope(second_scope) == 0


def test_delete_record_rewrites_when_other_records_remain(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    first = record("record.first", current_scope)
    second = record(
        "record.second",
        current_scope,
        observation=descriptor(current_scope, resource_id="plugin.two"),
    )
    memory_store.save(first)
    memory_store.save(second)

    assert memory_store.delete_record(current_scope, first.record_id)
    assert memory_store.load(current_scope) == (second,)


def test_store_methods_reject_invalid_scope_and_record_ids(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    replacement = record("record.replacement", current_scope)

    with pytest.raises(TypeError, match="scope must be CapabilityMemoryScope"):
        memory_store.load(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="include_inactive must be a boolean"):
        memory_store.load(current_scope, include_inactive="false")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="record must be CapabilityMemoryRecord"):
        memory_store.save(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="only active records can be saved"):
        memory_store.save(replace(replacement, status=CapabilityMemoryRecordStatus.INVALIDATED))
    with pytest.raises(TypeError, match="record_id must be a string"):
        memory_store.invalidate(current_scope, 1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="canonical identifier"):
        memory_store.delete_record(current_scope, "../record")
    with pytest.raises(TypeError, match="scope must be CapabilityMemoryScope"):
        memory_store.delete_scope(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="replacement must be CapabilityMemoryRecord"):
        memory_store.supersede(current_scope, "record.one", object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="replacement must be active"):
        memory_store.supersede(
            current_scope,
            "record.one",
            replace(replacement, status=CapabilityMemoryRecordStatus.INVALIDATED),
        )
    with pytest.raises(ValueError, match="replacement record id already exists"):
        memory_store.save(replacement)
        memory_store.supersede(current_scope, replacement.record_id, replacement)
    assert not memory_store.invalidate(current_scope, "record.not_found")


def test_supersede_rejects_inactive_previous_record(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    original = record("record.original", current_scope)
    memory_store.save(original)
    memory_store.invalidate(current_scope, original.record_id)

    with pytest.raises(ValueError, match="only active records can be superseded"):
        memory_store.supersede(current_scope, original.record_id, record("record.next", current_scope))


def test_supersede_rejects_identity_owned_by_another_active_record(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    first = record("record.first", current_scope)
    other = record(
        "record.other",
        current_scope,
        observation=descriptor(current_scope, resource_id="plugin.other"),
    )
    memory_store.save(first)
    memory_store.save(other)

    with pytest.raises(ValueError, match="another active record"):
        memory_store.supersede(
            current_scope,
            first.record_id,
            record("record.next", current_scope, observation=other.descriptor),
        )


def test_store_rejects_repository_local_storage_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside the repository"):
        JsonCapabilityMemoryStore(REPOSITORY_ROOT / "private-memory", repository_root=REPOSITORY_ROOT)


def test_corrupt_or_unknown_store_data_fails_closed(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    memory_store.save(record(memory_scope=current_scope))
    path = memory_store._path(current_scope)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["records"][0]["record_id"] = "record.changed"
    path.write_text(json.dumps(envelope), encoding="utf-8")

    with pytest.raises(ValueError, match="integrity check failed"):
        memory_store.load(current_scope)

    envelope["schema_version"] = "orchestra.capability-memory.v2"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    with pytest.raises(ValueError, match="schema version is unsupported"):
        memory_store.load(current_scope)


def test_read_rejects_unreadable_json_and_invalid_collection_shapes(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    memory_store.save(record(memory_scope=current_scope))
    path = memory_store._path(current_scope)

    path.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="data is unreadable"):
        memory_store.load(current_scope)
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="data is unreadable"):
        memory_store.load(current_scope)

    shape_store = JsonCapabilityMemoryStore(
        tmp_path / "shape-memory",
        repository_root=REPOSITORY_ROOT,
    )
    shape_store.save(record("record.shape", current_scope))
    shape_path = shape_store._path(current_scope)
    envelope = json.loads(shape_path.read_text(encoding="utf-8"))
    envelope["records"][0]["descriptor"]["capability_claims"] = "not-a-list"
    rewrite_envelope(shape_path, envelope)
    with pytest.raises(ValueError, match="capability_claims must be a list"):
        shape_store.load(current_scope)


def test_read_rejects_scope_mismatch_and_duplicate_records(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    memory_store.save(record(memory_scope=current_scope))
    path = memory_store._path(current_scope)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["scope"]["user_scope_id"] = "user.other"
    rewrite_envelope(path, envelope)
    with pytest.raises(ValueError, match="scope does not match storage partition"):
        memory_store.load(current_scope)

    second_store = JsonCapabilityMemoryStore(
        tmp_path / "duplicate-memory",
        repository_root=REPOSITORY_ROOT,
    )
    second_store.save(record("record.duplicate", current_scope))
    duplicate_path = second_store._path(current_scope)
    duplicate_envelope = json.loads(duplicate_path.read_text(encoding="utf-8"))
    duplicate_envelope["records"].append(duplicate_envelope["records"][0])
    rewrite_envelope(duplicate_path, duplicate_envelope)
    with pytest.raises(ValueError, match="duplicate record ids"):
        second_store.load(current_scope)


def test_read_rejects_cross_scope_records_and_duplicate_active_identities(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    memory_store.save(record(memory_scope=current_scope))
    path = memory_store._path(current_scope)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["records"][0]["scope"]["user_scope_id"] = "user.other"
    envelope["records"][0]["descriptor"]["identity"]["user_scope_id"] = "user.other"
    rewrite_envelope(path, envelope)
    with pytest.raises(ValueError, match="record scope mismatch"):
        memory_store.load(current_scope)

    second_store = JsonCapabilityMemoryStore(
        tmp_path / "identity-memory",
        repository_root=REPOSITORY_ROOT,
    )
    second_store.save(record("record.first", current_scope))
    duplicate_path = second_store._path(current_scope)
    duplicate_envelope = json.loads(duplicate_path.read_text(encoding="utf-8"))
    duplicate_record = dict(duplicate_envelope["records"][0])
    duplicate_record["record_id"] = "record.second"
    duplicate_envelope["records"].append(duplicate_record)
    rewrite_envelope(duplicate_path, duplicate_envelope)
    with pytest.raises(ValueError, match="duplicate active identities"):
        second_store.load(current_scope)


def test_write_failure_cleans_temporary_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()

    def fail_replace(*args: object, **kwargs: object) -> None:
        raise OSError("synthetic replace failure")

    monkeypatch.setattr(memory_module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="synthetic replace failure"):
        memory_store.save(record(memory_scope=current_scope))

    scope_directory = tmp_path / "private-memory" / "v1"
    assert list(scope_directory.iterdir()) == []


def test_temporary_file_creation_failure_leaves_no_scope_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()

    def fail_create(*args: object, **kwargs: object) -> None:
        raise OSError("synthetic temporary file failure")

    monkeypatch.setattr(memory_module.tempfile, "NamedTemporaryFile", fail_create)
    with pytest.raises(OSError, match="synthetic temporary file failure"):
        memory_store.save(record(memory_scope=current_scope))

    scope_directory = tmp_path / "private-memory" / "v1"
    assert list(scope_directory.iterdir()) == []


def test_schema_rejects_unsupported_record_shape_even_with_recomputed_digest(tmp_path: Path) -> None:
    memory_store = store(tmp_path)
    current_scope = scope()
    memory_store.save(record(memory_scope=current_scope))
    path = memory_store._path(current_scope)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["records"][0]["unexpected"] = "value"
    body = {key: envelope[key] for key in ("schema_version", "scope", "records")}
    envelope["content_sha256"] = receipt_digest(body)
    path.write_text(json.dumps(envelope), encoding="utf-8")

    with pytest.raises(ValueError, match="record has an unsupported shape"):
        memory_store.load(current_scope)
