from pathlib import Path

import pytest

from orchestra_runtime.models import (
    ApprovedUnitPlan,
    AuditEventType,
    EnvelopeMessageType,
    ExecutionResult,
    OrchestraRuntimeEnvelope,
    RouteDecision,
    RunIdentity,
    RuntimeAuditEvent,
    ValidationResult,
    validate_approved_unit_plan_context,
)
from orchestra_runtime.protocol.adapter_protocol import (
    PRAP_V1,
    AdapterCapabilities,
    AdapterError,
    AdapterProtocol,
    ProtocolValidator,
)


ROOT = Path(__file__).resolve().parents[2]


def _plan(**overrides):
    values = dict(
        unit_id="unit-1",
        unit_revision=1,
        unit_name="Fixture Unit",
        phase_id="P9",
        execution_envelope_ref="run-1",
        scope_ref="scope-1",
        responsible_specialist="conductor",
        objective="exercise validation boundaries",
        expected_outputs=("output",),
        validation_requirements=("pytest",),
    )
    values.update(overrides)
    return ApprovedUnitPlan(**values)


def _route():
    return RouteDecision("review-architecture", "clockwork", False, "fixture")


def _validation():
    return ValidationResult(True, "APPROVED")


def _transition_envelope(**overrides):
    values = dict(
        schema_version="1.0.0",
        message_type=EnvelopeMessageType.TRANSITION_DECISION,
        timestamp="2026-08-15T12:00:00Z",
        run_id="run-1",
        specialist="conductor",
        operation="P9",
        disposition="AUTO_CONTINUE",
        reason_code="READY",
        phase_id="P9",
    )
    values.update(overrides)
    return OrchestraRuntimeEnvelope(**values)


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"schema_version": "bad"}, "unsupported schema_version"),
        ({"unit_id": " "}, "unit_id"),
        ({"unit_revision": True}, "unit_revision integer"),
        ({"unit_revision": " "}, "unit_revision"),
        ({"unit_name": ""}, "unit_name"),
        ({"phase_id": ""}, "phase_id"),
        ({"execution_envelope_ref": ""}, "execution_envelope_ref"),
        ({"scope_ref": ""}, "scope_ref"),
        ({"responsible_specialist": ""}, "responsible_specialist"),
        ({"objective": ""}, "objective"),
        ({"expected_outputs": []}, "expected_outputs"),
        ({"expected_outputs": (" ",)}, "at least one"),
        ({"validation_requirements": []}, "validation_requirements"),
        ({"validation_requirements": (" ",)}, "at least one"),
        ({"allowed_paths": ["src"]}, "allowed_paths must be a tuple"),
        ({"prohibited_paths": ["secrets"]}, "prohibited_paths must be a tuple"),
        ({"dependency_unit_ids": ["u2"]}, "dependency_unit_ids must be a tuple"),
        ({"dependency_unit_ids": ("",)}, "entry must be a non-empty"),
        ({"dependency_unit_ids": ("unit-1",)}, "self dependency"),
        ({"governance_decision_ref": " "}, "governance_decision_ref"),
    ],
)
def test_approved_unit_plan_rejects_invalid_structural_fields(overrides, match):
    with pytest.raises(ValueError, match=match):
        _plan(**overrides)


@pytest.mark.parametrize("path", ["", "file://secret", "/etc/passwd", "\\server", "C:/secret", "src/../secret", "src/./file", ".agents/state", "src/.agents/state"])
def test_approved_unit_plan_rejects_unsafe_repository_paths(path):
    with pytest.raises(ValueError):
        _plan(allowed_paths=(path,))


def test_approved_unit_plan_deduplicates_paths_dependencies_and_normalizes_specialist():
    plan = _plan(
        responsible_specialist=" Conductor ",
        allowed_paths=("src\\core", "src/core"),
        prohibited_paths=("docs/private", "docs/private"),
        dependency_unit_ids=("u2", "u2", "u3"),
        governance_decision_ref=" gov:1 ",
    )
    assert plan.responsible_specialist == "conductor"
    assert plan.allowed_paths == ("src/core",)
    assert plan.prohibited_paths == ("docs/private",)
    assert plan.dependency_unit_ids == ("u2", "u3")
    assert plan.governance_decision_ref == "gov:1"


def test_approved_unit_plan_rejects_allowed_prohibited_overlap():
    with pytest.raises(ValueError, match="overlaps"):
        _plan(allowed_paths=("src",), prohibited_paths=("src/secrets",))


def test_context_validator_rejects_wrong_type_and_file_mutation_without_scope():
    wrong = validate_approved_unit_plan_context("bad")  # type: ignore[arg-type]
    assert wrong.allowed is False
    assert wrong.status == "REJECTED"

    result = validate_approved_unit_plan_context(_plan(), operation_context="FILE_MUTATION")
    assert result.allowed is False
    assert any("MISSING_ALLOWED_PATHS" in reason for reason in result.reasons)


def test_context_validator_reports_envelope_binding_mismatches():
    envelope = _transition_envelope(run_id="other-run", specialist="clockwork", phase_id="OTHER")
    result = validate_approved_unit_plan_context(_plan(allowed_paths=("src",)), envelope=envelope)
    assert result.allowed is False
    assert any(reason.startswith("ENVELOPE_MISMATCH") for reason in result.reasons)
    assert any(reason.startswith("PHASE_MISMATCH") for reason in result.reasons)
    assert any(reason.startswith("SPECIALIST_MISMATCH") for reason in result.reasons)


def test_context_validator_dependency_evidence_failure_shapes():
    plan = _plan(dependency_unit_ids=("missing", "bad-status", "bad-shape"))
    result = validate_approved_unit_plan_context(
        plan,
        predecessor_evidence={
            "bad-status": {"status": "RUNNING"},
            "bad-shape": "completed",
        },
    )
    assert result.allowed is False
    assert len([reason for reason in result.reasons if reason.startswith("UNACCEPTED_DEPENDENCY")]) == 3


def test_context_validator_accepts_complete_dependencies_and_envelope():
    plan = _plan(allowed_paths=("src",), dependency_unit_ids=("u2",))
    envelope = _transition_envelope()
    result = validate_approved_unit_plan_context(
        plan,
        operation_context="FILE_MUTATION",
        envelope=envelope,
        predecessor_evidence={"u2": {"status": "COMPLETED"}},
    )
    assert result.allowed is True
    assert result.status == "ACCEPTED"


def test_execution_result_requires_run_identity_for_runtime_evidence():
    with pytest.raises(ValueError, match="run identity"):
        ExecutionResult(
            True, "codex", "x", _route(), _validation(), "ok", "audit",
            authority_mode="ACTIVE",
        )


def test_execution_result_rejects_bad_event_ids_mode_and_state():
    identity = RunIdentity("run-1")
    with pytest.raises(ValueError, match="non-empty and unique"):
        ExecutionResult(True, "codex", "x", _route(), _validation(), "ok", "audit", runtime_audit_event_ids=("",))
    with pytest.raises(ValueError, match="valid authority mode"):
        ExecutionResult(True, "codex", "x", _route(), _validation(), "ok", "audit", run_identity=identity, authority_mode="BAD", lifecycle_state="ACTIVE")
    with pytest.raises(ValueError, match="valid lifecycle state"):
        ExecutionResult(True, "codex", "x", _route(), _validation(), "ok", "audit", run_identity=identity, authority_mode="ACTIVE", lifecycle_state="UNKNOWN")


def test_run_identity_and_audit_event_validation_and_serialization():
    with pytest.raises(ValueError, match="run_id must be non-empty"):
        RunIdentity(" ")
    with pytest.raises(ValueError, match="must differ"):
        RunIdentity("run", parent_run_id="run")
    identity = RunIdentity(" run ", parent_run_id=" parent ")
    assert identity.to_dict() == {"run_id": "run", "parent_run_id": "parent"}

    with pytest.raises(ValueError, match="must be non-empty"):
        RuntimeAuditEvent("", AuditEventType.AUTHORITY_DECIDED, "run", "rel", "reason")
    with pytest.raises(ValueError, match="non-empty and unique"):
        RuntimeAuditEvent("e", AuditEventType.AUTHORITY_DECIDED, "run", "rel", "reason", details=(("k", "1"), ("k", "2")))
    event = RuntimeAuditEvent(
        " e ", AuditEventType.AUTHORITY_DECIDED, " run ", " rel ", " reason ",
        provenance_ids=("b", "a", "a", ""), details=(("z", "2"), ("a", "1")), parent_run_id=" parent ",
    )
    payload = event.to_dict()
    assert payload["provenance_ids"] == ["a", "b"]
    assert payload["details"] == {"a": "1", "z": "2"}
    assert payload["parent_run_id"] == "parent"


@pytest.mark.parametrize(
    "overrides",
    [
        {"schema_version": ""},
        {"message_type": "unknown"},
        {"timestamp": ""},
        {"run_id": ""},
        {"specialist": ""},
    ],
)
def test_runtime_envelope_rejects_missing_core_identity(overrides):
    with pytest.raises(ValueError):
        _transition_envelope(**overrides)


def test_runtime_envelope_variant_requirements_and_prohibited_fields():
    with pytest.raises(ValueError, match="execution_result variant requires"):
        OrchestraRuntimeEnvelope("1", EnvelopeMessageType.EXECUTION_RESULT, "t", "r", "s")
    with pytest.raises(ValueError, match="execution_result variant prohibits"):
        OrchestraRuntimeEnvelope("1", EnvelopeMessageType.EXECUTION_RESULT, "t", "r", "s", operation="op", status="OK", reason_code="R", disposition="STOP")
    with pytest.raises(ValueError, match="transition_decision variant requires"):
        OrchestraRuntimeEnvelope("1", EnvelopeMessageType.TRANSITION_DECISION, "t", "r", "s")
    with pytest.raises(ValueError, match="transition_decision variant prohibits"):
        OrchestraRuntimeEnvelope("1", EnvelopeMessageType.TRANSITION_DECISION, "t", "r", "s", operation="op", disposition="STOP", reason_code="R", status="BAD")
    with pytest.raises(ValueError, match="audit_event variant requires non-empty"):
        OrchestraRuntimeEnvelope("1", EnvelopeMessageType.AUDIT_EVENT, "t", "r", "s", details={})
    with pytest.raises(ValueError, match="requires details mapping"):
        OrchestraRuntimeEnvelope("1", EnvelopeMessageType.AUDIT_EVENT, "t", "r", "s", event_type="E")
    with pytest.raises(ValueError, match="audit_event variant prohibits"):
        OrchestraRuntimeEnvelope("1", EnvelopeMessageType.AUDIT_EVENT, "t", "r", "s", event_type="E", details={}, operation="bad")


def test_runtime_envelope_optional_fields_serialize_only_when_present():
    envelope = _transition_envelope(summary="ready", data={"x": 1}, governance_decision_ref="gov:1")
    payload = envelope.to_dict()
    assert payload["summary"] == "ready"
    assert payload["data"] == {"x": 1}
    assert payload["governance_decision_ref"] == "gov:1"
    assert "status" not in payload


# PRAP adapter protocol validation

def _capabilities(**overrides):
    values = dict(
        supports_commands=True,
        supports_context=True,
        supports_file_handoff=True,
        supports_workspace=True,
        supports_audit_trace=True,
        supports_streaming=True,
        supports_governance=True,
        worktree_supported=False,
        worktree_isolation_mode="NONE",
    )
    values.update(overrides)
    return AdapterCapabilities(**values)


def _protocol(**overrides):
    values = dict(
        adapter_id="fixture",
        display_name="Fixture",
        runtime_adapter="fixture",
        host_type="ide",
        protocol_version=PRAP_V1,
        packaging_status="scaffold-only",
        marketplace_status="deferred",
        capabilities=_capabilities(),
    )
    values.update(overrides)
    return AdapterProtocol(**values)


def test_adapter_protocol_metadata_includes_optional_aliases_and_metadata():
    payload = _protocol(aliases=("alias",), metadata={"extra": "value"}).to_metadata()
    assert payload["aliases"] == ("alias",)
    assert payload["metadata"] == {"extra": "value"}


def test_protocol_validator_exercises_invalid_metadata_capability_and_case_edges():
    capabilities = _capabilities(worktree_supported=False, worktree_isolation_mode="OPTIONAL")
    object.__setattr__(capabilities, "supports_commands", "yes")
    protocol = _protocol(
        adapter_id="UPPER",
        runtime_adapter="UPPER",
        protocol_version="unsupported",
        display_name="",
        capabilities=capabilities,
    )
    errors = ProtocolValidator.validate_protocol(protocol)
    joined = "\n".join(errors)
    assert "Missing protocol metadata field" in joined
    assert "Unsupported protocol version" in joined
    assert "Capability metadata must be boolean" in joined
    assert "worktree_isolation_mode must be NONE" in joined
    assert "worktree_supported must be True" in joined
    assert "runtime_adapter must be lowercase" in joined
    assert "adapter_id must be lowercase" in joined


def test_protocol_validator_rejects_invalid_worktree_mode():
    errors = ProtocolValidator.validate_protocol(_protocol(capabilities=_capabilities(worktree_isolation_mode="MAGIC")))
    assert any("Invalid worktree_isolation_mode" in item for item in errors)


def test_validate_adapter_requires_protocol_metadata_method():
    assert ProtocolValidator.validate_adapter(object()) == ["Adapter does not implement protocol_metadata()."]


class _Adapter:
    def protocol_metadata(self):
        return _protocol()


def test_validate_adapter_accepts_valid_protocol():
    assert ProtocolValidator.validate_adapter(_Adapter()) == []


def test_packaging_manifest_unknown_adapter_and_mismatch_paths():
    errors = ProtocolValidator.validate_packaging_manifest("definitely-unknown", {}, ROOT)
    assert any("AdapterFactory cannot build" in item for item in errors)

    mismatch = ProtocolValidator.validate_packaging_manifest(
        "codex", {"runtime_adapter": "wrong", "host": "wrong"}, ROOT
    )
    assert any("runtime_adapter mismatch" in item for item in mismatch)
    assert any("host mismatch" in item for item in mismatch)


def test_compatibility_lookup_is_case_insensitive_and_rejects_unknown_or_rejected():
    assert ProtocolValidator.compatibility_for("CODEX").adapter_id == "codex"
    with pytest.raises(AdapterError, match="Unknown adapter"):
        ProtocolValidator.compatibility_for("missing")
    with pytest.raises(AdapterError, match="not PRAP-compatible"):
        ProtocolValidator.ensure_supported("unknown")
    assert ProtocolValidator.ensure_supported("vscode").compatibility_status == "supported"
