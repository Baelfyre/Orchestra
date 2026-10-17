# v1.12.0 Release Readiness Evidence

## Evidence identity

```text
candidate_version=1.12.0
candidate_status=PREPARED_NOT_QUALIFIED
starting_head=cb0218adfc3f8385c44398ad11e91e0e749ca2b5
starting_tree=93c227324222df0f9dba65448e1592182fd08e8a
implementation_commit=12af49f8db91f967895d52d2810c40216550b4e3
implementation_tree=2df69ce25416114208d8a0211c72409007ba2e39
runner_fix_commit=8faf27f0a15b2bb45e4636799144ce94783b6bae
runner_fix_tree=f459fa4f7d84c2b9d5032b87fe95d7ca64fdac80
initial_pr_ci_snapshot_head=281185fcef68283a0ad3526594ef3a7d2dd415eb
initial_pr_ci_snapshot_tree=124a3b2e5c4e7a7e5b818e12e9221dcab9ff1172
qualification_head=PENDING_FOLLOW_UP_EXACT_HEAD_VALIDATION
qualification_tree=PENDING_FOLLOW_UP_EXACT_HEAD_VALIDATION
release_candidate=docs/releases/v1.12.0-offline-jev-pilot-release-candidate.md
pilot_protocol=docs/setup/JEV_OFFLINE_PILOT.md
pilot_window=2026-10-17..2026-11-07 (suggested; manual weekly sessions)
formal_weekly_pilot_sessions_completed=0
preparatory_harness_smoke_runs=2
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
| Offline pilot runner | Two runs of `python -B scripts/jev_offline_pilot.py --output-dir %TEMP%\orchestra-v112-jev-pilot-final` on `8faf27f0a15b2bb45e4636799144ce94783b6bae` | Both PASS: 14 scenarios and 49 mapped tests, 49 passed, 0 failed, 0 skipped per run; blocked network attempts 0; provider calls 0; actual inference false; source integrity unchanged. Second run comparison: 0 status changes, 0 new or removed scenarios. Artifacts: `jev-offline-pilot-20261017T170342826785Z.json` and `jev-offline-pilot-20261017T170348924696Z.json`. |
| Pilot runner bootstrap regression | First direct run after `12af49f8db91f967895d52d2810c40216550b4e3` | FAIL: pytest exit 4, 0 collected because direct script launch omitted the repository root from `sys.path`; fixed in `8faf27f0a15b2bb45e4636799144ce94783b6bae`; the two subsequent runs above pass. |
| Focused JEV regressions after changes | `python -B -m pytest -p no:cacheprovider --basetemp <temporary-path> -q tests/runtime/test_jev_adjudication.py tests/runtime/test_jev_provider_projection.py tests/runtime/test_jev_responsibility_adjudication.py tests/runtime/test_jev_v6_handoff.py tests/runtime/test_jev_offline_pilot.py` | 230 passed, 0 failed, 0 skipped; 3.46 s on the implementation content recorded as runner-fix commit `8faf27f0a15b2bb45e4636799144ce94783b6bae` |
| Full runtime suite and coverage | `python -B -m pytest -p no:cacheprovider --basetemp <temporary-path> tests/runtime --cov=orchestra_runtime --cov-branch --cov-report=term-missing --cov-report=json:<temporary-path> --junitxml=<temporary-path> --cov-fail-under=0` | 3,571 passed, 0 failed, 0 skipped; 535.62 s; 97.61% statements, 95.00% branches; run preceded final pilot-only guard/catalog refinements; `orchestra_runtime` source was unchanged |
| Critical coverage inventory | `python -B scripts/validation/build_coverage_inventory.py --coverage <temporary-path>/coverage.json --output <temporary-path>/coverage-inventory.json --critical-statement-floor 98 --critical-branch-floor 95` | PASS; no critical-module failures |
| PRAI duplicate-name workflow invocation | `python -B -m pytest -p no:cacheprovider --import-mode=importlib -q tests/runtime/test_prai.py tests/behavior/test_prai.py` | 43 passed, 0 failed, 0 skipped; 11.99 s |
| Signed materialization and TrueSheet | `python -B -m pytest -p no:cacheprovider --basetemp <temporary-path> -q tests/behavior/test_signed_materialization.py tests/behavior/test_truesheet_reference.py` | 9 passed, 0 failed, 0 skipped; 1.99 s |
| Behavior and governance runner | `ORCHESTRA_APPROVED_BASE_SHA=8f315c5a39118368c47effac0d8dc6bef903fba1 python -B tests/behavior/run_tests.py` | Two full runs on `8faf27f0a15b2bb45e4636799144ce94783b6bae` both exited 1; neither is an aggregate PASS. First run reported 3 failing scripts (`test_evidence_identity.py`, `test_evidence_baseline_resolution.py`, `test_artificer_governance_records.py`); second reported 4 (`test_prompt_load_budget.py`, `test_governance_protocol_consistency.py`, `test_artificer_records.py`, `test_artificer_audit_report_renderer.py`). Each reported script passed when rerun individually; the Artificer governance-record rerun had 23 tests, 22 passed and 1 skipped. The failure source remains unresolved; exact PR CI is required. |
| Architecture boundaries | `python -B scripts/validation/validate_architecture_boundaries.py` | PASS |
| Structure, manifest, stale-reference checks | `python -B scripts/validate_structure.py`; `python -B scripts/validate_manifest.py`; `python -B scripts/check_stale_references.py` | All PASS |
| Windows and Linux syntax / manifest checks | Windows `python -B -m compileall -q orchestra_runtime scripts internal/context` with external bytecode cache; WSL Python 3.14 equivalent plus `python3 -B -m json.tool plugin.json` | PASS on both. WSL emitted a systemd user-session warning. Linux pytest was NOT RUN because WSL Python has no pytest installed; WSL Git status also cannot resolve this Windows-linked worktree's `.git` pointer. No dependencies or Git settings were changed. |
| Initial exact-head pull-request checks | GitHub PR #975, head `281185fcef68283a0ad3526594ef3a7d2dd415eb`, tree `124a3b2e5c4e7a7e5b818e12e9221dcab9ff1172` | 8 checks passed and 2 failed. `governance-check` required `README.md` and `README.json` parity for the public JEV release candidate and runtime changes. `native-windows-latest` had 7 JEV V6 fixture failures: Windows CRLF checkout bytes hashed to `b2c8bee1b6323ee04f437035a06bbf89d391384abd213f6dcf39dcbdd98992af`, while the manifest pins LF bytes `3e52cb1258ad47921774ffc49e587d23111450528a77e8681c66d022fc75e9c0`. This record describes the pre-correction head; corrected exact-head CI remains required. |

## Pytest collection resolution

The combined default collection of `tests/runtime` and `tests/behavior` has a pre-existing duplicate `test_prai` module-name collision. Applying `--import-mode=importlib` to both directories also breaks unrelated test-local imports. No global pytest configuration or test names were changed. The repository's compatible execution paths are used instead: run `tests/runtime` separately, execute `tests/behavior/run_tests.py`, and use `--import-mode=importlib` for the existing two-file PRAI workflow invocation, which passed above.

## Open qualification items

- The three-week observation window has not completed; no pilot conclusion is available.
- The original V6 packet and source artifacts referenced by hashes are not present. Do not reconstruct them or label the fixture as real evidence.
- The local full TypeSafe request path and production composition are not exercised by this offline pilot.
- R3-A host trust is explicitly unqualified.
- The full local behavior runner did not pass in either attempt; reported failures passed individually, but no aggregate green result is available.
- The initial PR CI snapshot identified documentation parity and Windows fixture line-ending defects. The follow-up commit must pass required checks at its exact head; no earlier result is reusable for that state.
- `tests/behavior/run_tests.py` requires an explicit baseline for local runs. Use the verified current PR base, never a fabricated SHA.

## Release disposition

`NOT_QUALIFIED_PENDING_VALIDATION_AND_PILOT`

Passing offline tests can support pull-request review. They do not establish actual JEV inference, real evidence provenance, production integration, R3-A host trust, exact-head CI readiness, or release/publication authority.
