from hypothesis import given, settings, strategies as st

from orchestra_runtime.compliance_protocol import (
    ComplianceConsumptionReceipt,
    ComplianceQueryReceipt,
    StewardTraceabilityReceipt,
    evaluate_compliance_set_equality,
)
from orchestra_runtime.context_state import CurrentProjectState
from orchestra_runtime.evidence import normalize_git_sha, receipt_digest
from orchestra_runtime.host_protocol import (
    HostCapability,
    HostCapabilityDeclaration,
    evaluate_host_capabilities,
)
from orchestra_runtime.preexecution import (
    ExecutionAction,
    ExecutionIntent,
    PreExecutionConstraint,
    PreExecutionPolicy,
    evaluate_preexecution,
)
from orchestra_runtime.remediation_circuit import (
    CircuitConstraint,
    RemediationCircuitState,
    request_remediation,
)


HEX = "0123456789abcdefABCDEF"
SAFE_ID = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_", min_size=1, max_size=16)
JSON_SCALAR = st.one_of(st.none(), st.booleans(), st.integers(min_value=-10_000, max_value=10_000), st.text(max_size=24))


@settings(max_examples=80, deadline=None)
@given(st.dictionaries(SAFE_ID, JSON_SCALAR, max_size=12))
def test_canonical_receipt_digest_is_independent_of_mapping_insertion_order(payload):
    forward = dict(payload.items())
    reverse = dict(reversed(tuple(payload.items())))
    assert receipt_digest(forward) == receipt_digest(reverse)


@settings(max_examples=80, deadline=None)
@given(st.text(alphabet=HEX, min_size=40, max_size=40))
def test_exact_git_sha_normalization_is_case_insensitive_and_length_preserving(value):
    normalized = normalize_git_sha(value)
    assert normalized == value.lower()
    assert len(normalized) == 40


@settings(max_examples=60, deadline=None)
@given(st.lists(SAFE_ID, min_size=1, max_size=10, unique=True))
def test_compliance_set_equality_is_independent_of_record_order(obligation_ids):
    ordered = tuple(obligation_ids)
    reversed_ids = tuple(reversed(ordered))
    query = ComplianceQueryReceipt(
        canonical_repository="x/y",
        registry_version="1",
        release_sequence=1,
        release_tag="v1",
        manifest_sha256="a" * 64,
        filters=(("jurisdiction", "PH"),),
        source_ids=("SRC",),
        obligation_ids=ordered,
    )
    consumption = ComplianceConsumptionReceipt(
        query_digest=query.digest,
        source_ids=("SRC",),
        obligation_ids=reversed_ids,
        classifications=tuple((item, "OK") for item in reversed_ids),
        verdict="APPROVED",
    )
    trace = StewardTraceabilityReceipt(
        query_digest=query.digest,
        source_ids=("SRC",),
        obligation_ids=ordered,
        evidence_refs=("receipt:trace",),
    )
    gate = evaluate_compliance_set_equality(query, consumption, trace)
    assert gate.ready is True
    assert gate.error_codes == ()


@settings(max_examples=60, deadline=None)
@given(st.lists(SAFE_ID, max_size=10, unique=True))
def test_current_state_digest_is_independent_of_set_like_field_order(values):
    first = CurrentProjectState(
        project_id="orchestra",
        repository="Baelfyre/Orchestra",
        canonical_sha="a" * 40,
        phase="P9",
        authority_mode="FULL_AUTONOMOUS_BOUNDED",
        current_task="property-test",
        blockers=tuple(values),
        critical_receipt_refs=tuple(values),
        evidence_index_refs=tuple(values),
        revision=1,
        updated_at="2026-08-15T11:00:00Z",
    )
    second = CurrentProjectState(
        project_id="orchestra",
        repository="Baelfyre/Orchestra",
        canonical_sha="a" * 40,
        phase="P9",
        authority_mode="FULL_AUTONOMOUS_BOUNDED",
        current_task="property-test",
        blockers=tuple(reversed(values)),
        critical_receipt_refs=tuple(reversed(values)),
        evidence_index_refs=tuple(reversed(values)),
        revision=1,
        updated_at="2026-08-15T11:00:00Z",
    )
    assert first.to_dict() == second.to_dict()
    assert first.digest == second.digest


CAPABILITIES = tuple(HostCapability)


@settings(max_examples=60, deadline=None)
@given(st.lists(st.sampled_from(CAPABILITIES), max_size=len(CAPABILITIES), unique=True))
def test_host_capability_gate_is_independent_of_capability_order(capabilities):
    declaration = HostCapabilityDeclaration(
        host_id="property-host",
        adapter_id="adapter:property",
        capabilities=tuple(capabilities),
        evidence_refs=("receipt:host",),
        observed_at="2026-08-15T11:00:00Z",
    )
    first = evaluate_host_capabilities(declaration, tuple(capabilities), alternate_host_allowed=True)
    second = evaluate_host_capabilities(declaration, tuple(reversed(capabilities)), alternate_host_allowed=True)
    assert first.to_dict() == second.to_dict()
    assert first.digest == second.digest
    assert first.ready is True


@settings(max_examples=60, deadline=None)
@given(SAFE_ID)
def test_prohibited_descendant_always_overrides_broader_allowed_root(segment):
    denied = f"src/{segment}"
    policy = PreExecutionPolicy(
        policy_id="property-path-policy",
        allowed_actions=(ExecutionAction.FILE_READ,),
        allowed_paths=("src",),
        prohibited_paths=(denied,),
    )
    host = HostCapabilityDeclaration(
        host_id="property-host",
        adapter_id="adapter:property",
        capabilities=(HostCapability.FILESYSTEM_READ,),
        evidence_refs=("receipt:host",),
        observed_at="2026-08-15T11:00:00Z",
    )
    blocked = evaluate_preexecution(
        ExecutionIntent("blocked", ExecutionAction.FILE_READ, requested_paths=(f"{denied}/value.txt",)),
        policy,
        host,
    )
    assert blocked.constraint is PreExecutionConstraint.STOP


@settings(max_examples=40, deadline=None)
@given(st.integers(min_value=0, max_value=2), st.text(alphabet="0123456789abcdef", min_size=64, max_size=64))
def test_remediation_attempt_count_is_monotonic_until_budget_exhaustion(attempts, failure_digest):
    state = RemediationCircuitState(
        project_id="orchestra",
        unit_id="property",
        envelope_id="property",
        total_remediation_attempts=attempts,
        maximum_remediation_attempts=3,
    )
    decision = request_remediation(state, failure_digest=failure_digest)
    assert decision.constraint is CircuitConstraint.ALLOW_REMEDIATION
    assert decision.state.total_remediation_attempts == attempts + 1
    assert decision.state.total_remediation_attempts > state.total_remediation_attempts
