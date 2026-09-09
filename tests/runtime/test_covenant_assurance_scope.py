# @codebase_provenance_JEO
# @codebase_rights_JEO
from __future__ import annotations

from scripts.validation.classify_adaptive_assurance_scope import (
    APPLICABLE,
    COVENANT_IMPLEMENTATION_PATHS,
    NOT_APPLICABLE,
    classify_paths,
)


def full_paths():
    return tuple(sorted((*COVENANT_IMPLEMENTATION_PATHS, "CHANGELOG.md", "README.json")))


def test_complete_covenant_slice_is_outside_historical_assurance_inventories():
    paths = full_paths()
    assert classify_paths(paths, "aq5") == NOT_APPLICABLE
    assert classify_paths(paths, "aq7") == NOT_APPLICABLE
    assert classify_paths(paths, "prai") == NOT_APPLICABLE


def test_partial_covenant_slice_remains_fail_closed_applicable():
    partial = tuple(path for path in full_paths() if path != "orchestra_runtime/domain/governance/covenant.py")
    assert classify_paths(partial, "aq5") == APPLICABLE
    assert classify_paths(partial, "aq7") == APPLICABLE
    assert classify_paths(partial, "prai") == APPLICABLE


def test_covenant_slice_with_unknown_path_remains_fail_closed_applicable():
    mixed = (*full_paths(), "unexpected-covenant-path.txt")
    assert classify_paths(mixed, "aq5") == APPLICABLE
    assert classify_paths(mixed, "aq7") == APPLICABLE
    assert classify_paths(mixed, "prai") == APPLICABLE
