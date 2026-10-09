from pathlib import Path

import pytest

from orchestra_runtime.adapters import (
    AntigravityAdapter,
    ClaudeCodeAdapter,
    CodexAdapter,
    CursorAdapter,
    JetBrainsAdapter,
    NeovimAdapter,
    VSCodeAdapter,
    WindsurfAdapter,
    ZedAdapter,
)
from orchestra_runtime.presentation import PresentationDisposition, PresentationEvent, PresentationEventKind
from orchestra_runtime.repositories import ManifestRepository


ROOT = Path(__file__).resolve().parents[2]
ADAPTERS = (
    CodexAdapter,
    AntigravityAdapter,
    ClaudeCodeAdapter,
    CursorAdapter,
    WindsurfAdapter,
    VSCodeAdapter,
    JetBrainsAdapter,
    ZedAdapter,
    NeovimAdapter,
)


@pytest.mark.parametrize("adapter_type", ADAPTERS)
def test_adapters_default_to_normal_explanation(adapter_type):
    adapter = adapter_type(ManifestRepository(ROOT))
    event = PresentationEvent("run-normal", PresentationEventKind.EXECUTION_HEARTBEAT, 1)
    decision = adapter.presentation_decision(event)
    assert decision.disposition is PresentationDisposition.EXPLAIN
    assert decision.reason_code == "MODE_NORMAL"


def test_all_adapters_delegate_murmurs_to_same_machine_policy():
    event = PresentationEvent("run-parity", PresentationEventKind.TOOL_COMPLETED, 11)
    decisions = []
    for adapter_type in ADAPTERS:
        adapter = adapter_type(ManifestRepository(ROOT))
        decisions.append(
            adapter.presentation_decision(
                event,
                metadata={"orchestra.presentation_mode": "MURMURS"},
            )
        )
    assert all(item == decisions[0] for item in decisions)
    assert decisions[0].disposition is PresentationDisposition.MURMUR


def test_invalid_adapter_mode_fails_closed_without_host_reinterpretation():
    event = PresentationEvent("run-invalid", PresentationEventKind.EXECUTION_HEARTBEAT, 1)
    decisions = []
    for adapter_type in ADAPTERS:
        adapter = adapter_type(ManifestRepository(ROOT))
        decisions.append(
            adapter.presentation_decision(
                event,
                metadata={"orchestra.presentation_mode": "UNSUPPORTED"},
            )
        )
    assert all(item == decisions[0] for item in decisions)
    assert decisions[0].disposition is PresentationDisposition.EXPLAIN
    assert decisions[0].reason_code == "PRESENTATION_MODE_INVALID"
