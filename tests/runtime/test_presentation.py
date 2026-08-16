from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra_runtime.authority import AuthorityProvenance, ProvenanceSource
from orchestra_runtime.lifecycle import (
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleState,
    StructuredTerminalResult,
    lifecycle_signal_fingerprint,
)
from orchestra_runtime.presentation import (
    FORCED_EXPLAIN_EVENTS,
    MURMURS_VOCABULARY_SCHEMA_VERSION,
    PRESENTATION_POLICY_SCHEMA_VERSION,
    PresentationDecision,
    PresentationDisposition,
    PresentationEvent,
    PresentationEventKind,
    decide_lifecycle_presentation,
    decide_presentation,
    lifecycle_presentation_event,
    load_murmurs_vocabulary,
    load_presentation_policy,
    presentation_decision_digest,
    render_presentation,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "machine" / "presentation" / "murmurs-policy.v1.json"
VOCABULARY_PATH = ROOT / "machine" / "presentation" / "murmurs-vocabulary.v1.json"
POLICY_SCHEMA_PATH = ROOT / "machine" / "schemas" / "presentation-policy.schema.json"
VOCABULARY_SCHEMA_PATH = ROOT / "machine" / "schemas" / "murmurs-vocabulary.schema.json"


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_contracts(tmp_path: Path, policy: dict | None = None, vocabulary: dict | None = None) -> None:
    destination = tmp_path / "machine" / "presentation"
    destination.mkdir(parents=True)
    (destination / "murmurs-policy.v1.json").write_text(
        json.dumps(policy or _load(POLICY_PATH)),
        encoding="utf-8",
    )
    (destination / "murmurs-vocabulary.v1.json").write_text(
        json.dumps(vocabulary or _load(VOCABULARY_PATH)),
        encoding="utf-8",
    )


def _provenance() -> AuthorityProvenance:
    return AuthorityProvenance(
        ProvenanceSource.TRUSTED_COMPOSITION,
        "runtime.root",
        "v1",
        "runtime",
    )


def _activate_signal() -> LifecycleSignal:
    return LifecycleSignal(
        signal_id="signal.activate",
        run_id="run-1",
        signal_type=LifecycleSignalType.ACTIVATE,
        expected_state=LifecycleState.INITIALIZING,
        requested_state=LifecycleState.ACTIVE,
        reason_code="START",
        source_component="runtime",
        provenance=_provenance(),
        evidence_refs=("evidence-2", "evidence-1"),
    )


def _complete_signal() -> LifecycleSignal:
    return LifecycleSignal(
        signal_id="signal.complete",
        run_id="run-1",
        signal_type=LifecycleSignalType.COMPLETE,
        expected_state=LifecycleState.ACTIVE,
        requested_state=LifecycleState.COMPLETED,
        reason_code="COMPLETE",
        source_component="runtime",
        provenance=_provenance(),
        evidence_refs=("evidence-final",),
        terminal_result=StructuredTerminalResult(
            "run-1",
            LifecycleState.COMPLETED,
            "COMPLETE",
            evidence_refs=("evidence-final",),
        ),
    )


def test_machine_presentation_contracts_are_valid_and_bounded():
    policy = load_presentation_policy()
    vocabulary = load_murmurs_vocabulary()

    assert policy["schema_version"] == PRESENTATION_POLICY_SCHEMA_VERSION
    assert policy["default_disposition"] == "EXPLAIN"
    assert policy["explain_required"] == [item.value for item in FORCED_EXPLAIN_EVENTS]
    assert policy["authority_effect"] == {
        "presentation_may_change_machine_state": False,
        "presentation_may_override_governance": False,
        "presentation_may_suppress_required_explanation": False,
    }
    assert vocabulary["schema_version"] == MURMURS_VOCABULARY_SCHEMA_VERSION
    assert vocabulary["selection"] == "SHA256_MODULO"
    assert vocabulary["entries"]
    assert all(len(item) <= 12 and "\n" not in item and "\r" not in item for item in vocabulary["entries"])


def test_schema_documents_match_runtime_contract_versions_and_required_events():
    policy_schema = _load(POLICY_SCHEMA_PATH)
    vocabulary_schema = _load(VOCABULARY_SCHEMA_PATH)
    assert policy_schema["properties"]["schema_version"]["const"] == PRESENTATION_POLICY_SCHEMA_VERSION
    assert vocabulary_schema["properties"]["schema_version"]["const"] == MURMURS_VOCABULARY_SCHEMA_VERSION
    assert set(policy_schema["properties"]["events"]["required"]) == {
        item.value for item in PresentationEventKind
    }
    assert policy_schema["properties"]["default_disposition"]["const"] == "EXPLAIN"
    assert vocabulary_schema["properties"]["selection"]["const"] == "SHA256_MODULO"


def test_routine_events_use_local_murmurs_or_silence():
    heartbeat = PresentationEvent("run-1", PresentationEventKind.EXECUTION_HEARTBEAT, 3)
    heartbeat_decision = decide_presentation(heartbeat)
    assert heartbeat_decision.disposition is PresentationDisposition.MURMUR
    assert heartbeat_decision.murmur_text in load_murmurs_vocabulary()["entries"]
    assert render_presentation(heartbeat_decision) == heartbeat_decision.murmur_text
    assert heartbeat_decision.requires_explanation is False

    tool_started = PresentationEvent("run-1", PresentationEventKind.TOOL_STARTED, 4)
    tool_decision = decide_presentation(tool_started)
    assert tool_decision.disposition is PresentationDisposition.SILENT
    assert tool_decision.murmur_text is None
    assert render_presentation(tool_decision) == ""


@pytest.mark.parametrize("event_kind", FORCED_EXPLAIN_EVENTS)
def test_required_explanation_events_can_never_be_murmured(event_kind: PresentationEventKind):
    decision = decide_presentation(PresentationEvent("run-required", event_kind, 1))
    assert decision.disposition is PresentationDisposition.EXPLAIN
    assert decision.requires_explanation is True
    assert decision.murmur_text is None
    assert render_presentation(decision) is None


def test_murmur_selection_and_decision_digest_are_deterministic():
    event = PresentationEvent(
        "run-deterministic",
        PresentationEventKind.TOOL_COMPLETED,
        17,
        evidence_refs=("receipt-b", "receipt-a", "receipt-a"),
    )
    first = decide_presentation(event)
    second = decide_presentation(event)
    assert first == second
    assert first.event.evidence_refs == ("receipt-a", "receipt-b")
    assert presentation_decision_digest(first) == presentation_decision_digest(second)
    assert len(presentation_decision_digest(first)) == 64


def test_lifecycle_adapter_does_not_mutate_signal_identity_and_terminal_events_explain():
    activate = _activate_signal()
    activate_fingerprint = lifecycle_signal_fingerprint(activate)
    presentation_event = lifecycle_presentation_event(activate, 8)
    activate_decision = decide_lifecycle_presentation(activate, 8)

    assert presentation_event.event_kind is PresentationEventKind.EXECUTION_HEARTBEAT
    assert presentation_event.evidence_refs == activate.evidence_refs
    assert activate_decision.disposition is PresentationDisposition.MURMUR
    assert lifecycle_signal_fingerprint(activate) == activate_fingerprint

    complete = _complete_signal()
    complete_fingerprint = lifecycle_signal_fingerprint(complete)
    complete_decision = decide_lifecycle_presentation(complete, 9)
    assert complete_decision.event.event_kind is PresentationEventKind.TASK_COMPLETED
    assert complete_decision.disposition is PresentationDisposition.EXPLAIN
    assert render_presentation(complete_decision) is None
    assert lifecycle_signal_fingerprint(complete) == complete_fingerprint


def test_invalid_policy_fails_closed_to_explain(tmp_path: Path):
    policy = _load(POLICY_PATH)
    policy["events"]["TASK_COMPLETED"] = "MURMUR"
    _write_contracts(tmp_path, policy=policy)

    with pytest.raises(ValueError, match="must require EXPLAIN"):
        load_presentation_policy(tmp_path)

    decision = decide_presentation(
        PresentationEvent("run-invalid-policy", PresentationEventKind.EXECUTION_HEARTBEAT, 1),
        tmp_path,
    )
    assert decision.disposition is PresentationDisposition.EXPLAIN
    assert decision.reason_code == "PRESENTATION_CONTRACT_INVALID"
    assert render_presentation(decision) is None


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("schema_version", "schema_version"),
        ("default_disposition", "default disposition"),
        ("events_type", "events must be an object"),
        ("event_set", "event set"),
        ("event_disposition", "invalid disposition"),
        ("explain_type", "explain_required must be a list"),
        ("explain_values", "explain_required does not match"),
        ("authority_effect", "cannot create authority"),
    ],
)
def test_policy_contract_rejects_every_fail_closed_boundary(tmp_path: Path, case: str, message: str):
    policy = _load(POLICY_PATH)
    if case == "schema_version":
        policy["schema_version"] = "orchestra.presentation-policy.v0"
    elif case == "default_disposition":
        policy["default_disposition"] = "MURMUR"
    elif case == "events_type":
        policy["events"] = []
    elif case == "event_set":
        del policy["events"]["TOOL_STARTED"]
    elif case == "event_disposition":
        policy["events"]["TOOL_STARTED"] = "UNKNOWN"
    elif case == "explain_type":
        policy["explain_required"] = "TASK_COMPLETED"
    elif case == "explain_values":
        policy["explain_required"] = policy["explain_required"][:-1]
    elif case == "authority_effect":
        policy["authority_effect"]["presentation_may_change_machine_state"] = True
    else:  # pragma: no cover - parametrization owns the finite cases
        raise AssertionError(case)
    _write_contracts(tmp_path, policy=policy)
    with pytest.raises(ValueError, match=message):
        load_presentation_policy(tmp_path)


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("schema_version", "schema_version"),
        ("selection", "selection strategy"),
        ("constraints", "constraints"),
        ("entries_type", "non-empty list"),
        ("entries_empty", "non-empty list"),
        ("duplicate", "unique"),
        ("untrimmed", "trimmed"),
        ("too_long", "length/newline"),
        ("newline", "length/newline"),
    ],
)
def test_vocabulary_contract_rejects_nonsemantic_boundary_violations(tmp_path: Path, case: str, message: str):
    vocabulary = _load(VOCABULARY_PATH)
    if case == "schema_version":
        vocabulary["schema_version"] = "orchestra.murmurs-vocabulary.v0"
    elif case == "selection":
        vocabulary["selection"] = "RANDOM"
    elif case == "constraints":
        vocabulary["constraints"]["allow_status_claims"] = True
    elif case == "entries_type":
        vocabulary["entries"] = "hm..."
    elif case == "entries_empty":
        vocabulary["entries"] = []
    elif case == "duplicate":
        vocabulary["entries"] = ["hm...", "hm..."]
    elif case == "untrimmed":
        vocabulary["entries"] = [" hm..."]
    elif case == "too_long":
        vocabulary["entries"] = ["abcdefghijklmnop"]
    elif case == "newline":
        vocabulary["entries"] = ["hm...\n"]
    else:  # pragma: no cover - parametrization owns the finite cases
        raise AssertionError(case)
    _write_contracts(tmp_path, vocabulary=vocabulary)
    with pytest.raises(ValueError, match=message):
        load_murmurs_vocabulary(tmp_path)


def test_status_claim_in_vocabulary_fails_closed_to_explain(tmp_path: Path):
    vocabulary = _load(VOCABULARY_PATH)
    vocabulary["entries"] = ["done"]
    _write_contracts(tmp_path, vocabulary=vocabulary)

    with pytest.raises(ValueError, match="status or completion claims"):
        load_murmurs_vocabulary(tmp_path)

    decision = decide_presentation(
        PresentationEvent("run-invalid-vocabulary", PresentationEventKind.EXECUTION_HEARTBEAT, 2),
        tmp_path,
    )
    assert decision.disposition is PresentationDisposition.EXPLAIN
    assert decision.reason_code == "PRESENTATION_CONTRACT_INVALID"


def test_missing_or_invalid_contract_fails_closed_to_explain(tmp_path: Path):
    decision = decide_presentation(
        PresentationEvent("run-missing", PresentationEventKind.EXECUTION_HEARTBEAT, 1),
        tmp_path,
    )
    assert decision.disposition is PresentationDisposition.EXPLAIN

    destination = tmp_path / "machine" / "presentation"
    destination.mkdir(parents=True)
    (destination / "murmurs-policy.v1.json").write_text("[]", encoding="utf-8")
    second = decide_presentation(
        PresentationEvent("run-invalid-json-shape", PresentationEventKind.EXECUTION_HEARTBEAT, 2),
        tmp_path,
    )
    assert second.disposition is PresentationDisposition.EXPLAIN


@pytest.mark.parametrize("bad_sequence", [-1, True, 1.5])
def test_presentation_event_rejects_invalid_sequence(bad_sequence):
    with pytest.raises(ValueError, match="non-negative integer"):
        PresentationEvent("run-1", PresentationEventKind.EXECUTION_HEARTBEAT, bad_sequence)


def test_presentation_event_requires_identity_and_source_component():
    with pytest.raises(ValueError, match="run_id"):
        PresentationEvent(" ", PresentationEventKind.EXECUTION_HEARTBEAT, 0)
    with pytest.raises(ValueError, match="source_component"):
        PresentationEvent("run-1", PresentationEventKind.EXECUTION_HEARTBEAT, 0, source_component=" ")


def test_presentation_decision_rejects_semantically_invalid_murmur_payloads():
    event = PresentationEvent("run-1", PresentationEventKind.EXECUTION_HEARTBEAT, 0)
    with pytest.raises(ValueError, match="requires local murmur_text"):
        PresentationDecision(event, PresentationDisposition.MURMUR, "TEST")
    with pytest.raises(ValueError, match="only MURMUR"):
        PresentationDecision(event, PresentationDisposition.EXPLAIN, "TEST", "hm...")


def test_lifecycle_adapter_rejects_unstructured_input():
    with pytest.raises(ValueError, match="LifecycleSignal"):
        lifecycle_presentation_event(object(), 1)
