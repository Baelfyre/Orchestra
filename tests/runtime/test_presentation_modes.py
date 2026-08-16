from orchestra_runtime.presentation import (
    PresentationDisposition,
    PresentationEvent,
    PresentationEventKind,
    PresentationMode,
    decide_presentation,
    render_presentation,
)


def test_normal_mode_preserves_explanatory_presentation():
    event = PresentationEvent("run-normal", PresentationEventKind.EXECUTION_HEARTBEAT, 1)
    decision = decide_presentation(event, mode=PresentationMode.NORMAL)
    assert decision.disposition is PresentationDisposition.EXPLAIN
    assert decision.reason_code == "MODE_NORMAL"
    assert decision.murmur_text is None
    assert render_presentation(decision) is None


def test_murmurs_mode_uses_local_policy():
    event = PresentationEvent("run-murmurs", PresentationEventKind.EXECUTION_HEARTBEAT, 1)
    decision = decide_presentation(event, mode=PresentationMode.MURMURS)
    assert decision.disposition is PresentationDisposition.MURMUR
    assert decision.murmur_text


def test_unknown_mode_fails_closed_to_explain():
    event = PresentationEvent("run-invalid-mode", PresentationEventKind.EXECUTION_HEARTBEAT, 1)
    decision = decide_presentation(event, mode="UNKNOWN")
    assert decision.disposition is PresentationDisposition.EXPLAIN
    assert decision.reason_code == "PRESENTATION_MODE_INVALID"
    assert render_presentation(decision) is None
