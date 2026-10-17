# v1.12.0 Release Readiness Evidence

## Evidence identity

```text
candidate_version=1.12.0
candidate_status=PREPARED_NOT_QUALIFIED
starting_head=cb0218adfc3f8385c44398ad11e91e0e749ca2b5
starting_tree=93c227324222df0f9dba65448e1592182fd08e8a
qualification_head=PENDING_FINAL_LOCAL_COMMIT
qualification_tree=PENDING_FINAL_LOCAL_COMMIT
release_candidate=docs/releases/v1.12.0-offline-jev-pilot-release-candidate.md
pilot_protocol=docs/setup/JEV_OFFLINE_PILOT.md
pilot_window=2026-10-17..2026-11-07 (suggested; manual weekly sessions)
pilot_sessions_completed=0
external_provider_calls=0
actual_jev_inference=false
original_v6_source_evidence=NOT_PRESENT; sanitized_fixture_replay_only
r3_a_host_trust=UNQUALIFIED
r3_b_c=UNCHANGED; no new qualification claim
live_typesafe_integration=UNQUALIFIED
production_jev_wiring=NOT_WIRED
```

The starting candidate was independently verified clean at the recorded branch/HEAD/tree. It is four commits ahead of the locally fetched `origin/main` and not behind it. The candidate contains the merge of that local `origin/main` ref. This local sync observation is not a live remote or GitHub status read.

## Validation record

Update this section only with commands actually executed against the stated source tree. Historical reports are not current execution evidence.

| Check | Command / evidence | Result |
|---|---|---|
| Initial focused JEV and assurance baseline | Independent local run on starting HEAD; 10 selected test files | 299 passed, 0 failed, 0 skipped; 9.87 s |
| Offline pilot runner | `python -B scripts/jev_offline_pilot.py --output-dir <outside-repository-path>` | Pending implementation validation |
| Focused JEV regressions after changes | `python -B -m pytest -p no:cacheprovider --basetemp <temporary-path> -q tests/runtime/test_jev_adjudication.py tests/runtime/test_jev_provider_projection.py tests/runtime/test_jev_responsibility_adjudication.py tests/runtime/test_jev_v6_handoff.py tests/runtime/test_jev_offline_pilot.py` | 230 passed, 0 failed, 0 skipped; 3.00 s; includes final pilot guard/catalog refinements |
| Full runtime suite and coverage | `python -B -m pytest -p no:cacheprovider --basetemp <temporary-path> tests/runtime --cov=orchestra_runtime --cov-branch --cov-report=term-missing --cov-report=json:<temporary-path> --junitxml=<temporary-path> --cov-fail-under=0` | 3,571 passed, 0 failed, 0 skipped; 535.62 s; 97.61% statements, 95.00% branches; run preceded final pilot-only guard/catalog refinements; `orchestra_runtime` source was unchanged |
| Critical coverage inventory | `python -B scripts/validation/build_coverage_inventory.py --coverage <temporary-path>/coverage.json --output <temporary-path>/coverage-inventory.json --critical-statement-floor 98 --critical-branch-floor 95` | PASS; no critical-module failures |
| PRAI duplicate-name workflow invocation | `python -B -m pytest -p no:cacheprovider --import-mode=importlib -q tests/runtime/test_prai.py tests/behavior/test_prai.py` | 43 passed, 0 failed, 0 skipped; 11.99 s |
| Behavior and governance runner | `ORCHESTRA_APPROVED_BASE_SHA=8f315c5a39118368c47effac0d8dc6bef903fba1 python -B tests/behavior/run_tests.py` | Pending; baseline is the locally fetched PR base |
| Architecture boundaries | `python -B scripts/validation/validate_architecture_boundaries.py` | PASS |
| Structure, manifest, stale-reference checks | `python -B scripts/validate_structure.py`; `python -B scripts/validate_manifest.py`; `python -B scripts/check_stale_references.py` | All PASS |
| Cross-platform validation | Existing Windows and Linux workflow-equivalent checks | Pending |
| Exact-head pull-request checks | Required checks for final PR head | Pending; no PR created yet |

## Pytest collection resolution

The combined default collection of `tests/runtime` and `tests/behavior` has a pre-existing duplicate `test_prai` module-name collision. Applying `--import-mode=importlib` to both directories also breaks unrelated test-local imports. No global pytest configuration or test names were changed. The repository's compatible execution paths are used instead: run `tests/runtime` separately, execute `tests/behavior/run_tests.py`, and use `--import-mode=importlib` for the existing two-file PRAI workflow invocation, which passed above.

## Open qualification items

- The three-week observation window has not completed; no pilot conclusion is available.
- The original V6 packet and source artifacts referenced by hashes are not present. Do not reconstruct them or label the fixture as real evidence.
- The local full TypeSafe request path and production composition are not exercised by this offline pilot.
- R3-A host trust is explicitly unqualified.
- Required pull-request checks, protected-matrix applicability, and live GitHub state remain unverified until an authorized PR run.
- `tests/behavior/run_tests.py` requires an explicit baseline for local runs. Use the verified current PR base, never a fabricated SHA.

## Release disposition

`NOT_QUALIFIED_PENDING_VALIDATION_AND_PILOT`

Passing offline tests can support pull-request review. They do not establish actual JEV inference, real evidence provenance, production integration, R3-A host trust, exact-head CI readiness, or release/publication authority.
