# Offline JEV validation pilot

## Scope

The pilot replays local pytest scenarios against Orchestra's JEV contracts. It does not call TypeSafe, generate actual model judgments, invoke Scribe, change Sinag, or wire JEV into production. Every response is marked as a synthetic typed response, a fake-transport response, a fixture replay, or no response.

The suggested manual observation window is **2026-10-17 through 2026-11-07**, with one session per week. The runner does not schedule sessions or decide whether the pilot has passed.

## Run a session

From a clean candidate branch worktree:

```powershell
python -B scripts/jev_offline_pilot.py --list
python -B scripts/jev_offline_pilot.py --output-dir "$env:LOCALAPPDATA\Orchestra\jev-offline-pilot"
```

For a focused session, repeat `--scenario` for the selected stable IDs. Compare a new artifact with a prior session by adding `--compare <prior-session.json>`. Scenario IDs and mapped pytest node IDs are in [the versioned catalog](../../tests/fixtures/jev_offline_pilot_scenarios.v1.json).

The default output directory is `~/.orchestra/jev-offline-pilot`. An explicitly supplied output directory must also be outside the repository. The runner requires a clean branch worktree, records branch/HEAD/tree, disables pytest's cache provider, uses a temporary pytest base directory, and fails if the repository snapshot changes. It blocks socket creation, DNS, urllib dispatch, and HTTP connection dispatch in the test process. The guard is process-local; scenarios must not spawn a child process that performs network work.

## Evidence record

Each session JSON stores the UTC session date and ID, candidate identity, scenario-catalog SHA-256, selected scenario IDs, expected outcomes, observed assertion status, evidence gaps, response provenance, test counts, elapsed and CPU time, artifact size, comparison with a previous session, blocked network-attempt count, and source-integrity result. Raw JEV payloads, credentials, response bodies, and failure messages are not recorded. Memory use is labeled `NOT_MEASURED`; do not infer a memory result from elapsed time or artifact size. Any blocked network attempt makes the pilot session fail, even if a test catches the guard exception.

An observed eligibility value is recorded only when all mapped pytest assertions pass. It means the local test oracle confirmed its expected contract. It is not a captured model response or independently verified real-world eligibility. Failed or skipped assertions produce an unconfirmed result and a regression classification.

The V6 scenario is a **sanitized fixture replay**. The original normalized V6 packet and linked source artifacts are absent from this repository, so the fixture does not establish real evidence ingestion. The findings remain `UNVERIFIED`, and the adapter does not create an eligible JEV state from that packet.

The current state contract treats verification records as optional unless a finding sets `verification_required=true`. Thus a `VERIFIED` finding with that flag omitted or false and no linked verification record can pass the verification-record gate; an explicit true flag requires supporting verification, while non-boolean values are rejected. This is existing local contract behavior, not independent proof that an upstream producer verified the finding.

## Scenario coverage

The catalog maps stable scenario IDs to existing JEV tests for single-owner bypass, contested ownership, conflicting synthetic mitigation advice and dissent, insufficient or unverified evidence, V6 findings, stale candidates, forged V6 packet/candidate bindings, unavailable trusted bindings, malformed NOUL/Choice responses, inconclusive recommendations, sanitized request bytes, sequential/concurrent replay rejection, transport failure without retry, and the advisory-only authority boundary.

R3-A host trust remains **UNQUALIFIED**. The missing-binding case covers the injected application port only. Live TypeSafe integration and production JEV wiring remain unavailable and unqualified. Existing test coverage does not qualify R3-A, vendor behavior, credential onboarding, user consent, or production composition.
This pilot does not modify or make a new qualification claim for R3-B/C.

## Multiweek assessment template

At the end of the window, reconcile the saved session artifacts and record:

```text
pilot_window=2026-10-17..2026-11-07
session_artifacts=<paths to sanitized local JSON records>
candidate_heads=<HEAD/tree pairs from each session>
scenario_status_changes=<scenario ID and prior/current status>
regression_failures=<scenario ID, failure class, disposition>
unresolved_evidence_gaps=<summary>
external_provider_calls=0
actual_jev_inference=false
original_v6_evidence=NOT_PRESENT; fixture_replay_only
r3_a_host_trust=UNQUALIFIED
live_typesafe_integration=UNQUALIFIED
production_jev_wiring=NOT_WIRED
pilot_assessment=PASS | NEEDS_REPAIR | INCONCLUSIVE
reviewer=<human reviewer>
review_date=<date>
```

A `PASS` here supports a later integration decision only. It does not activate a provider, qualify host trust, create release authority, or publish the release.
