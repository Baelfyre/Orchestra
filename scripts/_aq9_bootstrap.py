#!/usr/bin/env python3
"""Temporary AQ9 branch materializer. Self-deleted before candidate commit."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "1e1a0f18ebb144bed76bc2ec617d3a3913b1c041"
INVENTORY = [
    "CHANGELOG.md",
    "README.json",
    "cosmic-ray.toml",
    "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md",
    "machine/adaptive/aq9-deep-assurance.v1.json",
    "machine/schemas/aq9-deep-assurance.v1.schema.json",
    "scripts/validation/validate_aq9.py",
    "tests/behavior/run_tests.py",
    "tests/runtime/test_adaptive_assurance_aq9.py",
]


def write_json(path: str, payload: object) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dedent(content).lstrip(), encoding="utf-8")


def build_contract() -> dict[str, object]:
    return {
        "schema_version": "orchestra.aq9-deep-assurance.v1",
        "phase": "AQ9_DEEP_ASSURANCE",
        "owner": "overseer",
        "authority_model": "EVIDENCE_ONLY_NON_AUTHORIZING",
        "purpose": (
            "Deepen deterministic assurance over existing Orchestra QA logic through mutation, "
            "property, metamorphic, and bounded fuzz evidence without creating a second QA engine "
            "or new authority."
        ),
        "implementation_inventory": INVENTORY,
        "assurance_families": ["MUTATION", "PROPERTY", "METAMORPHIC", "BOUNDED_FUZZ"],
        "mutation": {
            "tool": "cosmic-ray",
            "config": "cosmic-ray.toml",
            "required_existing_targets": [
                "orchestra_runtime/evidence.py",
                "orchestra_runtime/governance_kernel.py",
                "orchestra_runtime/preexecution.py",
            ],
            "aq9_added_targets": ["scripts/validation/classify_adaptive_assurance_scope.py"],
            "test_surfaces": [
                "tests/runtime/test_evidence_kernel.py",
                "tests/runtime/test_governance_kernel.py",
                "tests/runtime/test_preexecution.py",
                "tests/behavior/test_protected_aq8_assurance_scope_policy.py",
                "tests/runtime/test_adaptive_assurance_aq9.py",
            ],
            "score_policy": "PRESERVE_EXISTING_SCOREABLE_COMPATIBILITY_GATE",
        },
        "property": {
            "cases": 64,
            "invariants": [
                "EXACT_AQ9_SCOPE_IS_ORDER_INVARIANT",
                "EXACT_AQ9_SCOPE_IS_SEPARATOR_ONLY_FOR_HISTORICAL_GATES",
                "AQ9_PARTIAL_SCOPE_FAILS_CLOSED",
                "AQ9_UNKNOWN_SUPERSET_FAILS_CLOSED",
                "DUPLICATE_NORMALIZED_PATHS_ARE_REJECTED",
            ],
        },
        "metamorphic": {
            "cases": 32,
            "relations": [
                "PERMUTING_EQUIVALENT_PATHS_PRESERVES_CLASSIFICATION",
                "SLASH_NORMALIZATION_PRESERVES_EXACT_SCOPE_CLASSIFICATION",
                "REMOVING_ANY_EXACT_AQ9_PATH_REVOKES_EXEMPTION",
                "ADDING_UNKNOWN_PATH_TO_EXACT_AQ9_SCOPE_REVOKES_EXEMPTION",
                "RESTORING_EXACT_AQ9_SCOPE_RESTORES_ONLY_THE_PHASE_SEPARATOR_RESULT",
            ],
        },
        "bounded_fuzz": {
            "cases": 256,
            "seed": 20260911,
            "max_generated_paths": 12,
            "oracle": "ONLY_EXACT_COMPLETE_AQ9_INVENTORY_MAY_BE_NOT_APPLICABLE_FOR_HISTORICAL_GATES",
            "unsafe_input_policy": "REJECT",
        },
        "fail_closed_conditions": [
            "AQ9_PARTIAL_SCOPE",
            "AQ9_MIXED_SCOPE",
            "AQ9_UNKNOWN_SUPERSET",
            "DUPLICATE_NORMALIZED_PATH",
            "UNSAFE_PATH",
            "UNREGISTERED_FUTURE_AQ_PHASE",
            "SCHEMA_OR_SEMANTIC_DRIFT",
            "MUTATION_TARGET_OR_TEST_SURFACE_DRIFT",
        ],
        "authority": {
            "creates_execution_authority": False,
            "creates_transition_authority": False,
            "creates_whitelist_authority": False,
            "changes_protected_policy": False,
            "lowers_assurance_thresholds": False,
            "activates_provider": False,
            "activates_telemetry": False,
            "mutates_production": False,
            "authorizes_release": False,
        },
        "validation": {
            "validator": "scripts/validation/validate_aq9.py",
            "runtime_test": "tests/runtime/test_adaptive_assurance_aq9.py",
            "behavior_registration": "tests/behavior/run_tests.py",
            "architecture_reference": "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md",
            "schema": "machine/schemas/aq9-deep-assurance.v1.schema.json",
            "canonical_start_sha": BASE_SHA,
        },
    }


def build_schema() -> dict[str, object]:
    false_keys = [
        "creates_execution_authority",
        "creates_transition_authority",
        "creates_whitelist_authority",
        "changes_protected_policy",
        "lowers_assurance_thresholds",
        "activates_provider",
        "activates_telemetry",
        "mutates_production",
        "authorizes_release",
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/Baelfyre/Orchestra/blob/main/machine/schemas/aq9-deep-assurance.v1.schema.json",
        "title": "Orchestra AQ9 Deep Assurance Contract v1",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "phase",
            "owner",
            "authority_model",
            "purpose",
            "implementation_inventory",
            "assurance_families",
            "mutation",
            "property",
            "metamorphic",
            "bounded_fuzz",
            "fail_closed_conditions",
            "authority",
            "validation",
        ],
        "properties": {
            "schema_version": {"const": "orchestra.aq9-deep-assurance.v1"},
            "phase": {"const": "AQ9_DEEP_ASSURANCE"},
            "owner": {"const": "overseer"},
            "authority_model": {"const": "EVIDENCE_ONLY_NON_AUTHORIZING"},
            "purpose": {"type": "string", "minLength": 40, "maxLength": 1024},
            "implementation_inventory": {
                "type": "array",
                "minItems": 9,
                "maxItems": 9,
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1, "maxLength": 256},
            },
            "assurance_families": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "uniqueItems": True,
                "prefixItems": [
                    {"const": "MUTATION"},
                    {"const": "PROPERTY"},
                    {"const": "METAMORPHIC"},
                    {"const": "BOUNDED_FUZZ"},
                ],
                "items": False,
            },
            "mutation": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "tool",
                    "config",
                    "required_existing_targets",
                    "aq9_added_targets",
                    "test_surfaces",
                    "score_policy",
                ],
                "properties": {
                    "tool": {"const": "cosmic-ray"},
                    "config": {"const": "cosmic-ray.toml"},
                    "required_existing_targets": {
                        "type": "array",
                        "minItems": 3,
                        "uniqueItems": True,
                        "items": {"type": "string"},
                    },
                    "aq9_added_targets": {
                        "type": "array",
                        "minItems": 1,
                        "uniqueItems": True,
                        "items": {"type": "string"},
                    },
                    "test_surfaces": {
                        "type": "array",
                        "minItems": 5,
                        "uniqueItems": True,
                        "items": {"type": "string"},
                    },
                    "score_policy": {"const": "PRESERVE_EXISTING_SCOREABLE_COMPATIBILITY_GATE"},
                },
            },
            "property": {
                "type": "object",
                "additionalProperties": False,
                "required": ["cases", "invariants"],
                "properties": {
                    "cases": {"type": "integer", "minimum": 32, "maximum": 512},
                    "invariants": {
                        "type": "array",
                        "minItems": 5,
                        "uniqueItems": True,
                        "items": {"type": "string"},
                    },
                },
            },
            "metamorphic": {
                "type": "object",
                "additionalProperties": False,
                "required": ["cases", "relations"],
                "properties": {
                    "cases": {"type": "integer", "minimum": 16, "maximum": 256},
                    "relations": {
                        "type": "array",
                        "minItems": 5,
                        "uniqueItems": True,
                        "items": {"type": "string"},
                    },
                },
            },
            "bounded_fuzz": {
                "type": "object",
                "additionalProperties": False,
                "required": ["cases", "seed", "max_generated_paths", "oracle", "unsafe_input_policy"],
                "properties": {
                    "cases": {"type": "integer", "minimum": 128, "maximum": 4096},
                    "seed": {"const": 20260911},
                    "max_generated_paths": {"type": "integer", "minimum": 9, "maximum": 64},
                    "oracle": {"type": "string", "minLength": 20},
                    "unsafe_input_policy": {"const": "REJECT"},
                },
            },
            "fail_closed_conditions": {
                "type": "array",
                "minItems": 8,
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 3},
            },
            "authority": {
                "type": "object",
                "additionalProperties": False,
                "required": false_keys,
                "properties": {key: {"const": False} for key in false_keys},
            },
            "validation": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "validator",
                    "runtime_test",
                    "behavior_registration",
                    "architecture_reference",
                    "schema",
                    "canonical_start_sha",
                ],
                "properties": {
                    "validator": {"const": "scripts/validation/validate_aq9.py"},
                    "runtime_test": {"const": "tests/runtime/test_adaptive_assurance_aq9.py"},
                    "behavior_registration": {"const": "tests/behavior/run_tests.py"},
                    "architecture_reference": {"const": "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md"},
                    "schema": {"const": "machine/schemas/aq9-deep-assurance.v1.schema.json"},
                    "canonical_start_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                },
            },
        },
    }


def build_validator() -> str:
    return '''
    #!/usr/bin/env python3
    # @codebase_provenance_JEO
    # @codebase_rights_JEO
    # @codebase_verified_JEO
    """Validate AQ9 deep-assurance contract, configuration, and repository parity."""

    from __future__ import annotations

    import json
    from pathlib import Path
    import sys
    import tomllib

    import jsonschema

    ROOT = Path(__file__).resolve().parents[2]
    CONTRACT_PATH = ROOT / "machine/adaptive/aq9-deep-assurance.v1.json"
    SCHEMA_PATH = ROOT / "machine/schemas/aq9-deep-assurance.v1.schema.json"
    COSMIC_RAY_PATH = ROOT / "cosmic-ray.toml"
    RUN_TESTS_PATH = ROOT / "tests/behavior/run_tests.py"
    README_PATH = ROOT / "README.json"
    DOC_PATH = ROOT / "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md"

    EXACT_INVENTORY = (
        "CHANGELOG.md",
        "README.json",
        "cosmic-ray.toml",
        "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md",
        "machine/adaptive/aq9-deep-assurance.v1.json",
        "machine/schemas/aq9-deep-assurance.v1.schema.json",
        "scripts/validation/validate_aq9.py",
        "tests/behavior/run_tests.py",
        "tests/runtime/test_adaptive_assurance_aq9.py",
    )
    FAMILIES = ("MUTATION", "PROPERTY", "METAMORPHIC", "BOUNDED_FUZZ")
    BASE_MUTATION_TARGETS = {
        "orchestra_runtime/evidence.py",
        "orchestra_runtime/governance_kernel.py",
        "orchestra_runtime/preexecution.py",
    }
    AQ9_MUTATION_TARGET = "scripts/validation/classify_adaptive_assurance_scope.py"
    REQUIRED_TEST_SURFACES = {
        "tests/runtime/test_evidence_kernel.py",
        "tests/runtime/test_governance_kernel.py",
        "tests/runtime/test_preexecution.py",
        "tests/behavior/test_protected_aq8_assurance_scope_policy.py",
        "tests/runtime/test_adaptive_assurance_aq9.py",
    }


    def _require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)


    def validate() -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(contract, schema)

        _require(contract["schema_version"] == "orchestra.aq9-deep-assurance.v1", "AQ9 schema version drift")
        _require(contract["phase"] == "AQ9_DEEP_ASSURANCE", "AQ9 phase drift")
        _require(contract["owner"] == "overseer", "AQ9 owner drift")
        _require(contract["authority_model"] == "EVIDENCE_ONLY_NON_AUTHORIZING", "AQ9 authority model drift")
        _require(tuple(contract["implementation_inventory"]) == EXACT_INVENTORY, "AQ9 exact implementation inventory drift")
        _require(tuple(contract["assurance_families"]) == FAMILIES, "AQ9 assurance-family drift")
        _require(contract["property"]["cases"] == 64, "AQ9 property bound drift")
        _require(contract["metamorphic"]["cases"] == 32, "AQ9 metamorphic bound drift")
        _require(contract["bounded_fuzz"]["cases"] == 256, "AQ9 fuzz bound drift")
        _require(contract["bounded_fuzz"]["seed"] == 20260911, "AQ9 deterministic seed drift")
        _require(contract["bounded_fuzz"]["max_generated_paths"] == 12, "AQ9 fuzz path bound drift")
        _require(all(value is False for value in contract["authority"].values()), "AQ9 authority must remain non-authorizing")

        cosmic = tomllib.loads(COSMIC_RAY_PATH.read_text(encoding="utf-8"))["cosmic-ray"]
        module_paths = tuple(cosmic["module-path"])
        _require(len(module_paths) == len(set(module_paths)), "Cosmic Ray mutation targets contain duplicates")
        _require(BASE_MUTATION_TARGETS.issubset(module_paths), "AQ9 removed a pre-existing Cosmic Ray target")
        _require(AQ9_MUTATION_TARGET in module_paths, "AQ9 classifier is not an actual Cosmic Ray mutation target")
        _require(float(cosmic["timeout"]) >= 90.0, "AQ9 lowered the existing Cosmic Ray timeout")
        test_command = cosmic["test-command"]
        for path in REQUIRED_TEST_SURFACES:
            _require(path in test_command, f"Cosmic Ray test command is missing {path}")

        mutation = contract["mutation"]
        _require(set(mutation["required_existing_targets"]) == BASE_MUTATION_TARGETS, "AQ9 mutation baseline contract drift")
        _require(mutation["aq9_added_targets"] == [AQ9_MUTATION_TARGET], "AQ9 added mutation target drift")
        _require(set(mutation["test_surfaces"]) == REQUIRED_TEST_SURFACES, "AQ9 mutation test-surface drift")
        _require(mutation["score_policy"] == "PRESERVE_EXISTING_SCOREABLE_COMPATIBILITY_GATE", "AQ9 mutation score policy drift")

        run_tests = RUN_TESTS_PATH.read_text(encoding="utf-8")
        _require(
            '"Name": "validate_aq9.py", "Path": "scripts/validation/validate_aq9.py"' in run_tests,
            "AQ9 validator is not registered in behavior validation",
        )

        readme = json.loads(README_PATH.read_text(encoding="utf-8"))
        validation = readme["validation"]
        documentation = readme["documentation"]
        _require(validation["aq9_deep_assurance_contract"] == "machine/adaptive/aq9-deep-assurance.v1.json", "README AQ9 contract reference drift")
        _require(validation["aq9_deep_assurance_schema"] == "machine/schemas/aq9-deep-assurance.v1.schema.json", "README AQ9 schema reference drift")
        _require(validation["aq9_deep_assurance_validator"] == "scripts/validation/validate_aq9.py", "README AQ9 validator reference drift")
        _require(validation["aq9_deep_assurance_runtime_test"] == "tests/runtime/test_adaptive_assurance_aq9.py", "README AQ9 runtime-test reference drift")
        _require(documentation["adaptive_assurance_aq9_reference"] == "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md", "README AQ9 architecture reference drift")

        doc = DOC_PATH.read_text(encoding="utf-8")
        for marker in ("MUTATION", "PROPERTY", "METAMORPHIC", "BOUNDED_FUZZ", "EVIDENCE_ONLY_NON_AUTHORIZING"):
            _require(marker in doc, f"AQ9 architecture reference is missing {marker}")


    def main() -> int:
        try:
            validate()
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, jsonschema.ValidationError, tomllib.TOMLDecodeError) as exc:
            print(f"AQ9_DEEP_ASSURANCE_VALIDATION=FAIL: {exc}", file=sys.stderr)
            return 1
        print("AQ9_DEEP_ASSURANCE_VALIDATION=PASS")
        return 0


    if __name__ == "__main__":
        raise SystemExit(main())
    '''


def build_runtime_test() -> str:
    return '''
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
        windows_style = tuple(path.replace("/", "\\\\") for path in exact)
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
        duplicate = (anchor, anchor.replace("/", "\\\\"))
        for gate in HISTORICAL_GATES:
            with pytest.raises(ValueError):
                classify_paths(duplicate, gate)


    def test_unregistered_future_aq_phase_stays_fail_closed() -> None:
        future = ("CHANGELOG.md", "README.json", "docs/architecture/ADAPTIVE_ASSURANCE_AQ10.md")
        for gate in HISTORICAL_GATES:
            assert classify_paths(future, gate) == APPLICABLE
    '''


def build_doc() -> str:
    return '''
    # ADAPT-QA AQ9: Deep Assurance Expansion

    ## Status and purpose

    AQ9 deepens the existing deterministic assurance system after the AQ9 scope policy became canonical. It does not add a parallel QA engine, a new runtime authority, or any production behavior. The phase is evidence-only and uses the authority model `EVIDENCE_ONLY_NON_AUTHORIZING`.

    AQ9 adds four explicit assurance families:

    ```text
    MUTATION
    PROPERTY
    METAMORPHIC
    BOUNDED_FUZZ
    ```

    The goal is to challenge existing deterministic assurance logic from different directions while preserving the repository's current coverage, governance, provenance, signed-materialization, and fail-closed controls.

    ## Canonical input boundary

    AQ9 begins from canonical Orchestra commit `1e1a0f18ebb144bed76bc2ec617d3a3913b1c041`, where the human-approved AQ9 assurance-scope policy is already canonical and post-merge verified.

    The exact implementation inventory is fixed to nine paths:

    1. `CHANGELOG.md`
    2. `README.json`
    3. `cosmic-ray.toml`
    4. `docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md`
    5. `machine/adaptive/aq9-deep-assurance.v1.json`
    6. `machine/schemas/aq9-deep-assurance.v1.schema.json`
    7. `scripts/validation/validate_aq9.py`
    8. `tests/behavior/run_tests.py`
    9. `tests/runtime/test_adaptive_assurance_aq9.py`

    No production runtime module is added by AQ9.

    ## Mutation assurance

    AQ9 preserves every existing Cosmic Ray target and adds `scripts/validation/classify_adaptive_assurance_scope.py` as an actual mutation target. The mutation test command retains the evidence, governance-kernel, and preexecution suites and adds the protected scope-policy regression plus the AQ9 deep-assurance runtime suite.

    The existing scoreable-compatibility requirement is preserved. AQ9 does not lower or invent a mutation threshold merely to obtain PASS.

    ## Property assurance

    The PROPERTY layer executes 64 deterministic cases over the canonical AQ9 scope classifier. It proves that exact AQ9 classification is invariant to path order, only the complete exact inventory receives the historical phase-separation result, removing any required AQ9 path revokes that result, unknown supersets remain fail-closed, and duplicate normalized paths are rejected.

    ## Metamorphic assurance

    The METAMORPHIC layer executes 32 deterministic transformations. It checks that equivalent path permutations and slash normalization preserve the exact classification, while path removal or unknown-path addition revokes the exemption. Restoring the exact inventory restores only the approved phase-separation result.

    ## Bounded fuzz assurance

    The BOUNDED_FUZZ layer uses fixed seed `20260911` and 256 bounded cases. It generates AQ9 anchor-bearing non-exact subsets and controlled unknown-path supersets with at most 12 generated paths. The oracle is narrow: any AQ9-identifiable scope that is not exactly the complete nine-path inventory must remain fail-closed `APPLICABLE` for historical PRAI, AQ5, and AQ7 classifiers.

    The fixed seed makes failures reproducible. Unsafe or duplicate normalized path inputs remain rejection cases rather than being silently repaired.

    ## Machine contract and semantic parity

    `machine/adaptive/aq9-deep-assurance.v1.json` is the canonical machine description of AQ9. Its JSON Schema validates structural shape, while `scripts/validation/validate_aq9.py` additionally enforces semantic parity across the exact inventory, assurance families and bounds, Cosmic Ray mutation targets and test surfaces, behavior-suite registration, README references, and non-authorizing authority boundary.

    Schema validity alone is not sufficient. Semantic drift is fail-closed.

    ## Assurance truthfulness

    AQ9 does not reinterpret one evidence family as another. Cosmic Ray proves mutation behavior only for configured targets. Property tests prove stated invariants only over their deterministic case space. Metamorphic tests prove declared relations only over bounded transformations. Bounded fuzzing provides reproducible adversarial sampling, not exhaustive proof. Cross-platform CI remains portability evidence and CodeQL remains static-analysis evidence.

    No individual green check is treated as universal assurance.

    ## Authority boundary

    AQ9 creates no execution, transition, whitelist, provider, telemetry, production, credential, deployment, or release authority. It cannot amend a protected policy that blocks its own progression and cannot lower assurance thresholds. If progression requires a protected governance change, the autonomous run terminates at that boundary for human review.

    ## Completion gate

    AQ9 may be considered complete only after the exact source candidate is fully qualified, independently reviewed for scope and evidence truthfulness, protection-compliantly signed/materialized when required, promoted through a signed identical-tree carrier, and post-merge verified on canonical `main`.

    Required identity invariant:

    ```text
    QUALIFIED_SOURCE_TREE == SIGNED_MATERIALIZED_TREE == CANONICAL_TREE
    ```

    Until those steps complete, AQ9 remains an implementation candidate rather than a canonical completion claim.
    '''


def patch_existing_files() -> None:
    cosmic = '''
    [cosmic-ray]
    module-path = [
      "orchestra_runtime/evidence.py",
      "orchestra_runtime/governance_kernel.py",
      "orchestra_runtime/preexecution.py",
      "scripts/validation/classify_adaptive_assurance_scope.py",
    ]
    timeout = 90.0
    excluded-modules = []
    test-command = "python -m pytest -q tests/runtime/test_evidence_kernel.py tests/runtime/test_governance_kernel.py tests/runtime/test_preexecution.py tests/behavior/test_protected_aq8_assurance_scope_policy.py tests/runtime/test_adaptive_assurance_aq9.py"

    [cosmic-ray.distributor]
    name = "local"
    '''
    write_text("cosmic-ray.toml", cosmic)

    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    heading = "## Unreleased ADAPT-QA AQ-9 deep assurance expansion\n"
    if heading not in changelog:
        section = dedent('''
        ## Unreleased ADAPT-QA AQ-9 deep assurance expansion

        - Adds a deterministic AQ9 machine contract and schema for mutation, property, metamorphic, and bounded-fuzz assurance over existing QA logic without creating a second QA engine.
        - Preserves existing Cosmic Ray targets and adds the adaptive-assurance scope classifier as a real mutation target, with protected policy and AQ9 runtime regressions in the mutation test command.
        - Adds 64 property cases, 32 metamorphic cases, and 256 reproducible bounded-fuzz cases using fixed seed `20260911`, keeping non-exact AQ9 scopes fail-closed.
        - Adds semantic parity validation across contract, schema, Cosmic Ray configuration, behavior registration, README references, and non-authorizing governance boundaries.
        - Changes no production runtime authority, whitelist authority, provider/credential/telemetry state, release authority, or existing assurance threshold.

        ''').lstrip()
        changelog_path.write_text(section + changelog, encoding="utf-8")

    readme_path = ROOT / "README.json"
    readme_text = readme_path.read_text(encoding="utf-8")
    validation_anchor = (
        '    "prai_workflow_dispatch_baseline": "PRAI workflow_dispatch requires the explicit approved_base_sha input bound to ORCHESTRA_APPROVED_BASE_SHA; pull_request comparison identity remains event-derived."\n'
    )
    if '"aq9_deep_assurance_contract"' not in readme_text:
        if validation_anchor not in readme_text:
            raise RuntimeError("README validation anchor not found")
        replacement = validation_anchor[:-1] + ',\n' + (
            '    "aq9_deep_assurance_contract": "machine/adaptive/aq9-deep-assurance.v1.json",\n'
            '    "aq9_deep_assurance_schema": "machine/schemas/aq9-deep-assurance.v1.schema.json",\n'
            '    "aq9_deep_assurance_validator": "scripts/validation/validate_aq9.py",\n'
            '    "aq9_deep_assurance_runtime_test": "tests/runtime/test_adaptive_assurance_aq9.py"\n'
        )
        readme_text = readme_text.replace(validation_anchor, replacement, 1)

    doc_anchor = '    "adaptive_assurance_aq8_reference": "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md"\n'
    if '"adaptive_assurance_aq9_reference"' not in readme_text:
        if doc_anchor not in readme_text:
            raise RuntimeError("README AQ8 documentation anchor not found")
        readme_text = readme_text.replace(
            doc_anchor,
            '    "adaptive_assurance_aq8_reference": "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md",\n'
            '    "adaptive_assurance_aq9_reference": "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md"\n',
            1,
        )
    json.loads(readme_text)
    readme_path.write_text(readme_text, encoding="utf-8")

    run_tests_path = ROOT / "tests/behavior/run_tests.py"
    run_tests = run_tests_path.read_text(encoding="utf-8")
    anchor = '        {"Name": "validate_aq8.py", "Path": "scripts/validation/validate_aq8.py"},\n'
    if '"Name": "validate_aq9.py"' not in run_tests:
        if anchor not in run_tests:
            raise RuntimeError("run_tests AQ8 anchor not found")
        run_tests = run_tests.replace(
            anchor,
            anchor + '        {"Name": "validate_aq9.py", "Path": "scripts/validation/validate_aq9.py"},\n',
            1,
        )
    run_tests_path.write_text(run_tests, encoding="utf-8")


def main() -> int:
    write_json("machine/adaptive/aq9-deep-assurance.v1.json", build_contract())
    write_json("machine/schemas/aq9-deep-assurance.v1.schema.json", build_schema())
    write_text("scripts/validation/validate_aq9.py", build_validator())
    write_text("tests/runtime/test_adaptive_assurance_aq9.py", build_runtime_test())
    write_text("docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md", build_doc())
    patch_existing_files()
    for path in INVENTORY:
        if not (ROOT / path).exists():
            raise RuntimeError(f"AQ9 expected path missing after materialization: {path}")
    print("AQ9_MATERIALIZATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
