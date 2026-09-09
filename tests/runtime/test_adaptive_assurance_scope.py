from scripts.validation.classify_adaptive_assurance_scope import (
    AQ7_IMPLEMENTATION_PATHS,
    APPLICABLE,
    NOT_APPLICABLE,
    classify_paths,
)


def _complete_aq7_paths() -> list[str]:
    return [*sorted(AQ7_IMPLEMENTATION_PATHS), "README.json"]


def test_complete_aq7_slice_is_not_applicable_to_legacy_gates() -> None:
    paths = _complete_aq7_paths()
    assert classify_paths(paths, "prai") == NOT_APPLICABLE
    assert classify_paths(paths, "aq5") == NOT_APPLICABLE


def test_partial_aq7_slice_remains_applicable() -> None:
    paths = _complete_aq7_paths()
    paths.remove("tests/runtime/test_aq7_http_adapter_parity.py")
    assert classify_paths(paths, "prai") == APPLICABLE
    assert classify_paths(paths, "aq5") == APPLICABLE


def test_unknown_mixed_with_aq7_slice_remains_applicable() -> None:
    paths = [*_complete_aq7_paths(), "unexpected.txt"]
    assert classify_paths(paths, "prai") == APPLICABLE
    assert classify_paths(paths, "aq5") == APPLICABLE
