from __future__ import annotations

import secrets
import time
import uuid
from pathlib import Path

import pytest

from orchestra_runtime import (
    AntigravityAdapter,
    ClaudeCodeAdapter,
    CodexAdapter,
    CursorAdapter,
    EnvelopeMessageType,
    InMemoryAuditSink,
    JetBrainsAdapter,
    NeovimAdapter,
    OrchestraRuntimeEnvelope,
    RunIdentity,
    RuntimeEnvelopeAdapterMixin,
    SkillRegistry,
    VSCodeAdapter,
    WindsurfAdapter,
    ZedAdapter,
    build_compatibility_composition,
    deserialize_runtime_envelope,
    generate_correlation_id,
    is_valid_correlation_id,
    serialize_runtime_envelope,
    validate_correlation_id,
)
from orchestra_runtime.capabilities import CapabilityResolver
from orchestra_runtime.correlation import _generate_correlation_id
from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository


def test_public_generator_signature_and_conformance() -> None:
    # Public zero-arg signature
    cid = generate_correlation_id()
    assert isinstance(cid, str)
    assert len(cid) == 36
    assert cid == cid.lower()

    parsed = uuid.UUID(cid)
    assert parsed.version == 7
    assert parsed.variant == uuid.RFC_4122


def test_internal_generator_timestamp_and_clock_injection() -> None:
    fixed_ms = 1_700_000_000_000
    cid = _generate_correlation_id(clock=lambda: fixed_ms)

    parsed = uuid.UUID(cid)
    extracted_ms = parsed.int >> 80
    assert extracted_ms == fixed_ms


def test_generator_boundary_conditions() -> None:
    # Timestamp min (0)
    cid_min = _generate_correlation_id(clock=lambda: 0)
    assert uuid.UUID(cid_min).int >> 80 == 0

    # Timestamp max (2^48 - 1 = 0xFFFFFFFFFFFF)
    cid_max = _generate_correlation_id(clock=lambda: 0xFFFFFFFFFFFF)
    assert uuid.UUID(cid_max).int >> 80 == 0xFFFFFFFFFFFF

    # Negative timestamp rejected
    with pytest.raises(ValueError, match="timestamp must be an integer"):
        _generate_correlation_id(clock=lambda: -1)

    # Overflow timestamp rejected
    with pytest.raises(ValueError, match="timestamp must be an integer"):
        _generate_correlation_id(clock=lambda: 0x1000000000000)

    # Non-integer timestamp rejected
    with pytest.raises(ValueError, match="timestamp must be an integer"):
        _generate_correlation_id(clock=lambda: 1700000000.5)  # type: ignore[arg-type]

    # Entropy byte count tests
    # Exactly 10 bytes accepted
    cid_10 = _generate_correlation_id(rand_bytes=lambda _n: b"1234567890")
    assert is_valid_correlation_id(cid_10)

    # Short entropy (9 bytes) rejected
    with pytest.raises(ValueError, match="exactly 10 random bytes"):
        _generate_correlation_id(rand_bytes=lambda _n: b"123456789")

    # Long entropy (11 bytes) rejected
    with pytest.raises(ValueError, match="exactly 10 random bytes"):
        _generate_correlation_id(rand_bytes=lambda _n: b"12345678901")

    # Non-bytes entropy rejected
    with pytest.raises(TypeError, match="must return bytes"):
        _generate_correlation_id(rand_bytes=lambda _n: "1234567890")  # type: ignore[arg-type]


def test_generator_uniqueness_sample() -> None:
    sample_size = 10_000
    generated = {generate_correlation_id() for _ in range(sample_size)}
    assert len(generated) == sample_size


def test_generator_same_millisecond_uniqueness() -> None:
    fixed_ms = 1_710_000_000_000
    same_ms_sample = [_generate_correlation_id(clock=lambda: fixed_ms) for _ in range(100)]
    assert len(set(same_ms_sample)) == 100
    for cid in same_ms_sample:
        assert validate_correlation_id(cid) == cid


def test_generator_clock_rollback_resilience() -> None:
    times = [1_720_000_000_100, 1_720_000_000_000, 1_719_999_999_900]
    clock_idx = 0

    def rollback_clock() -> int:
        nonlocal clock_idx
        t = times[clock_idx % len(times)]
        clock_idx += 1
        return t

    results = [_generate_correlation_id(clock=rollback_clock) for _ in range(5)]
    assert len(results) == 5
    for cid in results:
        assert is_valid_correlation_id(cid) is True


def test_validate_correlation_id_positive() -> None:
    cid = generate_correlation_id()
    assert validate_correlation_id(cid) == cid

    # Uppercase input accepts and normalizes to lowercase
    upper_cid = cid.upper()
    assert validate_correlation_id(upper_cid) == cid


def test_validate_correlation_id_negative() -> None:
    # Non-string input
    with pytest.raises(TypeError, match="correlation_id must be a string"):
        validate_correlation_id(12345)  # type: ignore[arg-type]

    # Empty string
    with pytest.raises(ValueError, match="non-empty, unpadded"):
        validate_correlation_id("")

    # Whitespace padded
    cid = generate_correlation_id()
    with pytest.raises(ValueError, match="non-empty, unpadded"):
        validate_correlation_id(f" {cid} ")

    # Malformed string
    with pytest.raises(ValueError, match="malformed correlation_id"):
        validate_correlation_id("not-a-uuid-string")

    # UUIDv4 rejected
    v4_str = str(uuid.uuid4())
    with pytest.raises(ValueError, match="version must be 7"):
        validate_correlation_id(v4_str)

    # UUIDv1 rejected
    v1_str = str(uuid.uuid1())
    with pytest.raises(ValueError, match="version must be 7"):
        validate_correlation_id(v1_str)

    # Invalid variant (0b00 instead of 0b10)
    now_ms = 1_700_000_000_000
    ver_rand_a = 0x7000
    invalid_var = 0x0000  # Variant 0b00 (NCS reserved)
    bad_var_int = (now_ms << 80) | (ver_rand_a << 64) | (invalid_var << 48)
    bad_var_str = str(uuid.UUID(int=bad_var_int))
    with pytest.raises(ValueError, match="variant must be RFC 4122 / RFC 9562 compatible"):
        validate_correlation_id(bad_var_str)

    # Non-hyphenated UUID string rejected
    unhyphenated = cid.replace("-", "")
    with pytest.raises(ValueError, match="canonical hyphenated"):
        validate_correlation_id(unhyphenated)


def test_is_valid_correlation_id_helper() -> None:
    cid = generate_correlation_id()
    assert is_valid_correlation_id(cid) is True
    assert is_valid_correlation_id(cid.upper()) is True
    assert is_valid_correlation_id("invalid") is False
    assert is_valid_correlation_id(str(uuid.uuid4())) is False
    assert is_valid_correlation_id(None) is False
    assert is_valid_correlation_id(123) is False


def test_run_identity_correlation_integration_no_auto_generation() -> None:
    cid = generate_correlation_id()
    run = RunIdentity("run-1", "parent-1", correlation_id=cid)
    assert run.correlation_id == cid
    assert run.to_dict() == {"run_id": "run-1", "parent_run_id": "parent-1", "correlation_id": cid}

    # Absent correlation_id defaults to None and does NOT auto-generate
    legacy_run = RunIdentity("run-2", "parent-2")
    assert legacy_run.correlation_id is None
    assert legacy_run.to_dict() == {"run_id": "run-2", "parent_run_id": "parent-2"}

    # Invalid correlation_id raises ValueError
    with pytest.raises(ValueError, match="version must be 7"):
        RunIdentity("run-3", correlation_id=str(uuid.uuid4()))


def test_trusted_root_generation_in_runtime_services(tmp_path: Path) -> None:
    manifest_repo = ManifestRepository(tmp_path)
    skill_repo = SkillSourceRepository(tmp_path)
    skill_registry = SkillRegistry(manifest_repo, skill_repo)
    audit_sink = InMemoryAuditSink()

    # Initializing composition generates exactly one trusted root correlation ID internally
    comp = build_compatibility_composition(skill_registry, audit_sink, run_id="root-run-1")
    assert comp.run_identity.correlation_id is not None
    assert is_valid_correlation_id(comp.run_identity.correlation_id) is True
    assert comp.capability_manifest.run_identity.correlation_id == comp.run_identity.correlation_id

    # Public caller cannot pass or override correlation_id on build_compatibility_composition
    with pytest.raises(TypeError):
        build_compatibility_composition(skill_registry, audit_sink, run_id="root-run-2", correlation_id="custom-cid")  # type: ignore[call-arg]


def test_material_scope_change_new_root_semantics(tmp_path: Path) -> None:
    manifest_repo = ManifestRepository(tmp_path)
    skill_repo = SkillSourceRepository(tmp_path)
    skill_registry = SkillRegistry(manifest_repo, skill_repo)
    audit_sink = InMemoryAuditSink()

    comp1 = build_compatibility_composition(skill_registry, audit_sink, run_id="root-run-1")
    comp2 = build_compatibility_composition(skill_registry, audit_sink, run_id="root-run-2")

    assert comp1.run_identity.correlation_id != comp2.run_identity.correlation_id
    assert is_valid_correlation_id(comp1.run_identity.correlation_id) is True
    assert is_valid_correlation_id(comp2.run_identity.correlation_id) is True


def test_child_delegation_propagation_in_capability_resolver() -> None:
    from orchestra_runtime.authority import AuthorityProvenance, ProvenanceSource
    from orchestra_runtime.capabilities import RuntimeCapability, RuntimeCapabilityGrant

    resolver = CapabilityResolver()
    cid = generate_correlation_id()

    provenance = AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "policy",
        "1",
        "test",
    )
    grant = RuntimeCapabilityGrant(
        RuntimeCapability("cap.test", "test", ("execute",), "test grant"),
        ("execute",),
        provenance,
    )
    parent_manifest = resolver.build_manifest(
        "parent-run",
        (grant,),
        provenance,
        manifest_id="parent.manifest",
        policy_version="1",
        correlation_id=cid,
    )
    assert parent_manifest.run_identity.correlation_id == cid

    child_provenance = AuthorityProvenance(
        ProvenanceSource.ACCEPTED_DELEGATION,
        "policy",
        "1",
        "test",
        parent_run_id="parent-run",
        parent_decision_id="decision-1",
    )
    child_manifest = resolver.intersect(
        parent_manifest,
        (grant,),
        "child-run",
        manifest_id="child.manifest",
        provenance=child_provenance,
    )
    assert child_manifest.run_identity.correlation_id == cid


def test_untrusted_overwrite_protection() -> None:
    trusted_cid = generate_correlation_id()
    untrusted_host_cid = generate_correlation_id()

    # Trusted parent run identity
    trusted_parent = RunIdentity("parent-run", correlation_id=trusted_cid)

    # Host attempts to inject a different correlation_id during child creation
    # Propagation rule dictates trusted parent correlation_id must be preserved
    child = RunIdentity("child-run", parent_run_id=trusted_parent.run_id, correlation_id=trusted_parent.correlation_id)
    assert child.correlation_id == trusted_cid
    assert child.correlation_id != untrusted_host_cid


def test_runtime_envelope_correlation_roundtrip() -> None:
    cid = generate_correlation_id()
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-04T00:00:00Z",
        run_id="run-root-1",
        specialist="conductor",
        operation="execute",
        status="success",
        reason_code="EXECUTION_OK",
        correlation_id=cid,
    )
    assert envelope.correlation_id == cid

    payload = serialize_runtime_envelope(envelope)
    deserialized = deserialize_runtime_envelope(payload)
    assert deserialized.correlation_id == cid
    assert deserialized == envelope


def test_runtime_envelope_correlation_validation_failures() -> None:
    v4_cid = str(uuid.uuid4())
    with pytest.raises(ValueError, match="version must be 7"):
        OrchestraRuntimeEnvelope(
            schema_version="1.0.0",
            message_type=EnvelopeMessageType.EXECUTION_RESULT,
            timestamp="2026-08-04T00:00:00Z",
            run_id="run-root-1",
            specialist="conductor",
            operation="execute",
            status="success",
            reason_code="EXECUTION_OK",
            correlation_id=v4_cid,
        )


def test_adapter_correlation_preservation() -> None:
    cid = generate_correlation_id()
    envelope = OrchestraRuntimeEnvelope(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.EXECUTION_RESULT,
        timestamp="2026-08-04T00:00:00Z",
        run_id="run-root-1",
        specialist="conductor",
        operation="execute",
        status="success",
        reason_code="EXECUTION_OK",
        correlation_id=cid,
    )

    class DummyRepo:
        repo_root = "."
        def load_manifest(self) -> None: return None

    codex = CodexAdapter(DummyRepo())  # type: ignore[arg-type]
    antigravity = AntigravityAdapter(DummyRepo())  # type: ignore[arg-type]

    formatted_codex = codex.format_envelope(envelope)
    parsed_codex = codex.parse_envelope(formatted_codex)
    assert parsed_codex.correlation_id == cid

    formatted_ag = antigravity.format_envelope(envelope)
    parsed_ag = antigravity.parse_envelope(formatted_ag)
    assert parsed_ag.correlation_id == cid

    # Verify scaffold-only adapters do not expose envelope methods
    scaffolds = [
        ClaudeCodeAdapter,
        CursorAdapter,
        WindsurfAdapter,
        VSCodeAdapter,
        JetBrainsAdapter,
        ZedAdapter,
        NeovimAdapter,
    ]
    for cls in scaffolds:
        adapter = cls(DummyRepo())  # type: ignore[arg-type]
        assert not hasattr(adapter, "format_envelope")
        assert not hasattr(adapter, "parse_envelope")
