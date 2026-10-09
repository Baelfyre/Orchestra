from __future__ import annotations

import ast
from pathlib import Path

import pytest

import orchestra_runtime.lifecycle as legacy_lifecycle
from orchestra_runtime import (
    LifecycleSignal as public_lifecycle_signal,
    LifecycleSignalType as public_lifecycle_signal_type,
    LifecycleSnapshot as public_lifecycle_snapshot,
    LifecycleState as public_lifecycle_state,
    StructuredTerminalResult as public_terminal_result,
)
from orchestra_runtime.domain.execution import lifecycle as domain_lifecycle
from orchestra_runtime.domain.governance.authority import AuthorityProvenance, ProvenanceSource
from orchestra_runtime.shared.errors import (
    ConflictingTerminalSignalError,
    InvalidLifecycleSignalError,
    InvalidLifecycleTransitionError,
)


def _provenance() -> AuthorityProvenance:
    return AuthorityProvenance(ProvenanceSource.TRUSTED_COMPOSITION, "runtime.policy", "1", "runtime")


def _signal(
    signal_id: str,
    signal_type: domain_lifecycle.LifecycleSignalType,
    expected: domain_lifecycle.LifecycleState,
    requested: domain_lifecycle.LifecycleState,
    *,
    output: str = "",
) -> domain_lifecycle.LifecycleSignal:
    terminal = (
        domain_lifecycle.StructuredTerminalResult("run-1", requested, requested.value, output)
        if requested.terminal
        else None
    )
    return domain_lifecycle.LifecycleSignal(
        signal_id,
        "run-1",
        signal_type,
        expected,
        requested,
        requested.value,
        "runtime",
        _provenance(),
        terminal_result=terminal,
    )


def test_domain_lifecycle_exports_are_legacy_and_public_identity_compatible() -> None:
    assert legacy_lifecycle.LifecycleState is domain_lifecycle.LifecycleState
    assert legacy_lifecycle.LifecycleSignalType is domain_lifecycle.LifecycleSignalType
    assert legacy_lifecycle.LifecycleSignal is domain_lifecycle.LifecycleSignal
    assert legacy_lifecycle.LifecycleSnapshot is domain_lifecycle.LifecycleSnapshot
    assert legacy_lifecycle.StructuredTerminalResult is domain_lifecycle.StructuredTerminalResult
    assert legacy_lifecycle.LIFECYCLE_TRANSITIONS is domain_lifecycle.LIFECYCLE_TRANSITIONS
    assert legacy_lifecycle.lifecycle_signal_fingerprint is domain_lifecycle.lifecycle_signal_fingerprint
    assert public_lifecycle_state is domain_lifecycle.LifecycleState
    assert public_lifecycle_signal_type is domain_lifecycle.LifecycleSignalType
    assert public_lifecycle_signal is domain_lifecycle.LifecycleSignal
    assert public_lifecycle_snapshot is domain_lifecycle.LifecycleSnapshot
    assert public_terminal_result is domain_lifecycle.StructuredTerminalResult


def test_domain_lifecycle_initialization_wait_resume_and_terminal_transition() -> None:
    initial = domain_lifecycle.initialize_lifecycle_snapshot("  run-1  ")
    activate = _signal(
        "activate-1",
        domain_lifecycle.LifecycleSignalType.ACTIVATE,
        domain_lifecycle.LifecycleState.INITIALIZING,
        domain_lifecycle.LifecycleState.ACTIVE,
    )
    active = domain_lifecycle.apply_lifecycle_signal(initial, activate)
    waiting = domain_lifecycle.apply_lifecycle_signal(
        active,
        _signal(
            "wait-1",
            domain_lifecycle.LifecycleSignalType.WAIT,
            domain_lifecycle.LifecycleState.ACTIVE,
            domain_lifecycle.LifecycleState.WAITING,
        ),
    )
    resumed = domain_lifecycle.apply_lifecycle_signal(
        waiting,
        _signal(
            "resume-1",
            domain_lifecycle.LifecycleSignalType.RESUME,
            domain_lifecycle.LifecycleState.WAITING,
            domain_lifecycle.LifecycleState.ACTIVE,
        ),
    )
    complete = _signal(
        "complete-1",
        domain_lifecycle.LifecycleSignalType.COMPLETE,
        domain_lifecycle.LifecycleState.ACTIVE,
        domain_lifecycle.LifecycleState.COMPLETED,
        output="done",
    )
    completed = domain_lifecycle.apply_lifecycle_signal(resumed, complete)

    assert initial.run_identity.run_id == "run-1"
    assert active.state is domain_lifecycle.LifecycleState.ACTIVE
    assert waiting.state is domain_lifecycle.LifecycleState.WAITING
    assert resumed.state is domain_lifecycle.LifecycleState.ACTIVE
    assert completed.state is domain_lifecycle.LifecycleState.COMPLETED
    assert completed.terminal_result is not None
    assert completed.terminal_result.output == "done"
    assert completed.accepted_signal_fingerprint == domain_lifecycle.lifecycle_signal_fingerprint(complete)


def test_domain_lifecycle_preserves_fail_closed_transition_and_replay_semantics() -> None:
    initial = domain_lifecycle.initialize_lifecycle_snapshot("run-1")
    activate = _signal(
        "activate-1",
        domain_lifecycle.LifecycleSignalType.ACTIVATE,
        domain_lifecycle.LifecycleState.INITIALIZING,
        domain_lifecycle.LifecycleState.ACTIVE,
    )
    active = domain_lifecycle.apply_lifecycle_signal(initial, activate)
    complete = _signal(
        "complete-1",
        domain_lifecycle.LifecycleSignalType.COMPLETE,
        domain_lifecycle.LifecycleState.ACTIVE,
        domain_lifecycle.LifecycleState.COMPLETED,
        output="first",
    )
    completed = domain_lifecycle.apply_lifecycle_signal(active, complete)

    assert domain_lifecycle.apply_lifecycle_signal(completed, complete) is completed
    with pytest.raises(ConflictingTerminalSignalError):
        domain_lifecycle.apply_lifecycle_signal(
            completed,
            _signal(
                "complete-1",
                domain_lifecycle.LifecycleSignalType.COMPLETE,
                domain_lifecycle.LifecycleState.ACTIVE,
                domain_lifecycle.LifecycleState.COMPLETED,
                output="changed",
            ),
        )
    with pytest.raises(InvalidLifecycleTransitionError, match="terminal"):
        domain_lifecycle.apply_lifecycle_signal(
            completed,
            _signal(
                "wait-after",
                domain_lifecycle.LifecycleSignalType.WAIT,
                domain_lifecycle.LifecycleState.COMPLETED,
                domain_lifecycle.LifecycleState.WAITING,
            ),
        )
    with pytest.raises(InvalidLifecycleSignalError, match="structured"):
        domain_lifecycle.apply_lifecycle_signal(initial, "ACTIVE")
    with pytest.raises(InvalidLifecycleSignalError, match="expected state"):
        domain_lifecycle.apply_lifecycle_signal(
            initial,
            _signal(
                "complete-early",
                domain_lifecycle.LifecycleSignalType.COMPLETE,
                domain_lifecycle.LifecycleState.ACTIVE,
                domain_lifecycle.LifecycleState.COMPLETED,
            ),
        )


def test_legacy_controller_delegates_to_domain_lifecycle_functions(monkeypatch: pytest.MonkeyPatch) -> None:
    initialized = domain_lifecycle.initialize_lifecycle_snapshot("run-1")
    applied = domain_lifecycle.LifecycleSnapshot(initialized.run_identity, domain_lifecycle.LifecycleState.ACTIVE)
    calls: list[tuple[str, object]] = []

    def fake_initialize(run_id: str, correlation_id: str | None = None):
        calls.append(("initialize", (run_id, correlation_id)))
        return initialized

    def fake_apply(snapshot, signal):
        calls.append(("apply", (snapshot, signal)))
        return applied

    monkeypatch.setattr(legacy_lifecycle, "initialize_lifecycle_snapshot", fake_initialize)
    monkeypatch.setattr(legacy_lifecycle, "apply_lifecycle_signal", fake_apply)

    controller = legacy_lifecycle.LifecycleController()
    assert controller.initialize("run-1") is initialized
    assert controller.apply(initialized, object()) is applied
    assert calls[0] == ("initialize", ("run-1", None))
    assert calls[1][0] == "apply"


def test_domain_lifecycle_is_pure_and_legacy_free() -> None:
    source_path = Path(domain_lifecycle.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    forbidden = {
        "pathlib",
        "os",
        "subprocess",
        "socket",
        "sqlite3",
        "orchestra_runtime.lifecycle",
        "orchestra_runtime.interfaces",
        "orchestra_runtime.models",
        "orchestra_runtime.services",
        "orchestra_runtime.infrastructure",
        "orchestra_runtime.application",
        "orchestra_runtime.entrypoints",
    }
    assert not imports.intersection(forbidden)
    assert not any(isinstance(node, ast.Name) and node.id == "open" for node in ast.walk(tree))
