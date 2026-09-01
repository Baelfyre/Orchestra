from orchestra_runtime import preexecution as legacy_preexecution
from orchestra_runtime.application.use_cases import preexecution as application_preexecution


def test_legacy_preexecution_facade_preserves_public_identity():
    names = [
        "ExecutionAction",
        "ExecutionIntent",
        "PreExecutionArbiterEvaluation",
        "PreExecutionConstraint",
        "PreExecutionGateResult",
        "PreExecutionPolicy",
        "PreExecutionReason",
        "evaluate_preexecution",
        "evaluate_preexecution_with_arbiter",
    ]
    mismatched = [
        name
        for name in names
        if getattr(legacy_preexecution, name) is not getattr(application_preexecution, name)
    ]
    assert not mismatched, f"Legacy preexecution facade changed object identity: {mismatched}"


def test_preexecution_schema_version_is_preserved():
    assert legacy_preexecution.PREEXECUTION_SCHEMA_VERSION == application_preexecution.PREEXECUTION_SCHEMA_VERSION
