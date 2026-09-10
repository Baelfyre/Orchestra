# @codebase_provenance_JEO
# @codebase_rights_JEO
# @codebase_verified_JEO
"""AQ9 mutation/property/metamorphic/bounded-fuzz assurance regressions."""

from __future__ import annotations

import json
from pathlib import Path
import random
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validation.classify_adaptive_assurance_scope import (  # noqa: E402
    APPLICABLE,
    AQ9_IMPLEMENTATION_PATHS,
    AQ9_SCOPE_ANCHOR_PATHS,
    NOT_APPLICABLE,
    classify_paths,
)

CONTRACT_PATH = ROOT / "machine/adaptive/aq9-deep-assurance.v1.json"
SCHEMA_PATH = ROOT / "machine/schemas/aq9-deep-assurance.v1.schema.json"
HISTORICAL_GATES = ("prai", "aq5", "aq7")
UNKNOWN_PATHS = (
    "docs/architecture/AQ9_FUZZ_UNKNOWN.md",
    "machine/adaptive/aq10-unregistered.v1.json",
    "orchestra_runtime/domain/adaptive/aq9_parallel_engine.py",
)


def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_aq9_contract_is_schema_valid_and_non_authorizing() -> None:
    contract = _contract()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(contract, schema)
    assert contract["assurance_families"] == ["MUTATION", "PROPERTY", "METAMORPHIC", "BOUNDED_FUZZ"]
    assert all(value is False for value in contract["authority"].values())
    assert set(contract["implementation_inventory"]) == set(AQ9_IMPLEMENTATION_PATHS)


def test_property_exact_aq9_scope_is_order_invariant() -> None:
    contract = _contract()
    rng = random.Random(contract["bounded_fuzz"]["seed"])
    paths = list(AQ9_IMPLEMENTATION_PATHS)
    for _ in range(contract["property"]["cases"]):
        rng.shuffle(paths)
        for gate in HISTORICAL_GATES:
            assert classify_paths(tuple(paths), gate) == NOT_APPLICABLE


def test_property_removing_any_exact_aq9_path_revokes_exemption() -> None:
    exact = tuple(sorted(AQ9_IMPLEMENTATION_PATHS))
    for omitted in exact:
        candidate = tuple(path for path in exact if path != omitted)
        assert set(candidate) & set(AQ9_SCOPE_ANCHOR_PATHS)
        for gate in HISTORICAL_GATES:
            assert classify_paths(candidate, gate) == APPLICABLE


def test_metamorphic_equivalent_path_normalization_preserves_exact_result() -> None:
    exact = tuple(sorted(AQ9_IMPLEMENTATION_PATHS))
    windows_style = tuple(path.replace("/", "\\") for path in exact)
    for gate in HISTORICAL_GATES:
        assert classify_paths(exact, gate) == NOT_APPLICABLE
        assert classify_paths(windows_style, gate) == NOT_APPLICABLE


def test_metamorphic_scope_perturbation_fails_closed_and_restoration_recovers() -> None:
    contract = _contract()
    rng = random.Random(contract["bounded_fuzz"]["seed"] + 1)
    exact = list(AQ9_IMPLEMENTATION_PATHS)
    for _ in range(contract["metamorphic"]["cases"]):
        rng.shuffle(exact)
        removed = exact[:-1]
        expanded = [*exact, rng.choice(UNKNOWN_PATHS)]
        for gate in HISTORICAL_GATES:
            assert classify_paths(exact, gate) == NOT_APPLICABLE
            assert classify_paths(removed, gate) == APPLICABLE
            assert classify_paths(expanded, gate) == APPLICABLE
            assert classify_paths(exact, gate) == NOT_APPLICABLE


def test_bounded_fuzz_anchor_bearing_nonexact_scopes_never_gain_exemption() -> None:
    contract = _contract()
    rng = random.Random(contract["bounded_fuzz"]["seed"])
    exact = tuple(sorted(AQ9_IMPLEMENTATION_PATHS))
    anchors = tuple(sorted(AQ9_SCOPE_ANCHOR_PATHS))
    for index in range(contract["bounded_fuzz"]["cases"]):
        size = rng.randint(1, len(exact) - 1)
        candidate = list(rng.sample(exact, size))
        if not set(candidate).intersection(anchors):
            candidate.append(rng.choice(anchors))
        if rng.random() < 0.5 and len(candidate) < contract["bounded_fuzz"]["max_generated_paths"]:
            candidate.append(f"docs/architecture/AQ9_FUZZ_{index}.md")
        assert len(candidate) == len(set(candidate))
        assert set(candidate) != set(exact)
        for gate in HISTORICAL_GATES:
            assert classify_paths(candidate, gate) == APPLICABLE


def test_bounded_fuzz_duplicate_normalized_paths_are_rejected() -> None:
    anchor = "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md"
    duplicate = (anchor, anchor.replace("/", "\\"))
    for gate in HISTORICAL_GATES:
        with pytest.raises(ValueError):
            classify_paths(duplicate, gate)


def test_unregistered_future_aq_phase_stays_fail_closed() -> None:
    future = ("CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ10.md")
    for gate in HISTORICAL_GATES:
        assert classify_paths(future, gate) == APPLICABLE
