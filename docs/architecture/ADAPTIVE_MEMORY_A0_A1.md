# Local Adaptive Intelligence: A0 Boundary Review and A1 Memory Foundation

## Status

- **A0:** complete.
- **A1:** implemented on a bounded feature branch under explicit A0-A1 authority.
- **A2 and later:** not authorized and not implemented by this unit.
- **Runtime effect in A1:** none. The adaptive package is not imported by `RouterService`, `RuntimeComposition`, authority, capability, governance, specialist context assembly, or lifecycle execution.

Machine contracts:

- `machine/adaptive/a0-boundary-review.v1.json`
- `machine/adaptive/a1-memory-contract.v1.json`
- `machine/provenance/adaptive-orchestration-research.v1.json`

## A0 source state

A0 was reviewed against Orchestra `main` commit `ba35764a14111518c7da729b5a4c69c6af485a9b`, tree `0d569c57f77254c01af15c063e1e6582ff9e8d02`, with the `v1.6.0` tag resolving to that commit.

Padayon's connected integration did not permit a direct private-repository `main` dereference. The expected Padayon identity `6ad0502aeec135e837ed569de688913888029da1` is supported by merged Padayon PR #146, whose merge commit is that exact SHA and whose closeout records the Orchestra v1.6.0 publication identity. This limitation remains explicit instead of being converted into a stronger verification claim.

Orchestra PR #312 remains a stale, superseded v1.5.0 draft and is outside this work. Issue #316 remains a separate live-host measurement follow-up. Issue #331 remains maintenance debt; the existing canonical compatibility bridge allows normal protected merges without ruleset bypass.

## Research provenance

The A0 review uses the following sources as research references only:

| Source | Pinned review identity | License record | Orchestra use |
| --- | --- | --- | --- |
| Sakana AI Fugu repository | `ca7f1884b400e39018c6884d40b45c66cd78413e` | `NOASSERTION` from repository metadata during A0 | Architecture research only |
| Fugu Technical Report | arXiv `2606.21228v2`, 2026-06-23 | CC BY 4.0 | Architecture research only |
| TRINITY | arXiv `2512.04695v3`, 2026-04-27 | CC BY 4.0 | Architecture research only |
| Conductor | arXiv `2512.04388v5`, 2026-05-06 | CC BY 4.0 | Architecture research only |

Clean sources:

```text
https://github.com/SakanaAI/fugu
https://arxiv.org/abs/2606.21228
https://arxiv.org/abs/2512.04695
https://arxiv.org/abs/2512.04388
```

No Fugu, TRINITY, or Conductor source is copied, vendored, installed, or treated as runtime authority by A0-A1. Orchestra independently specifies the local-memory contract. The detailed A0 pin is recorded in `machine/provenance/adaptive-orchestration-research.v1.json`; the broader v1.6 provenance snapshot remains a historical release record rather than a source of new adaptive authority.

## Architecture boundary

The deterministic control plane remains unchanged:

```text
coordination validation
  -> trusted initialization
  -> adapter/context assembly
  -> command parsing
  -> deterministic routing
  -> trusted runtime binding
  -> authority
  -> capability
  -> governance
  -> lifecycle activation
  -> operation
  -> audit/evidence/result
```

A future adaptive read plane, if separately authorized in A2, may attach only after deterministic specialist eligibility plus authority, capability, and governance ceilings have been established. A1 does not implement that attachment or an adaptive context compiler.

### Existing components reused as patterns

A1 reuses established Orchestra engineering patterns without changing their semantics:

- canonical JSON and stable digest functions from `orchestra_runtime/evidence.py`;
- hash-chained JSONL integrity concepts from `orchestra_runtime/context_state.py`;
- fail-closed schema and identity validation;
- normalized governed phase-outcome signals from `orchestra_runtime/retrospective.py`.

`CurrentProjectState` remains continuity state and is not repurposed as learned memory.

## A1 local store

A1 introduces `orchestra_runtime.adaptive` as a separate machine-local data domain.

Default layout:

```text
~/.orchestra/adaptive/
  v1/
    <sha256-derived-user-storage-key>/
      observations.jsonl
      profile.json
      store-meta.json
```

`ORCHESTRA_ADAPTIVE_HOME` may override the root. When a repository root is supplied, the store refuses a location inside that repository. Normal learning therefore does not require or perform Git writes.

The canonical observation source is JSONL. `profile.json` is derived and can be rebuilt from the validated observation log. SQLite is intentionally deferred until scale, query, or concurrency evidence justifies it. TOON is not authoritative and is not introduced by A1.

## Scope model

Every adaptive record belongs to one explicit scope:

1. `global_user`
2. `project`
3. `specialist`
4. `task_session`

A global record cannot carry project, specialist, or task identifiers. Project scope requires a project identifier. Specialist scope requires a specialist identifier and may optionally be constrained to a project. Task/session scope requires a task/session identifier and may additionally carry project and specialist constraints.

A1 stores these scopes and preserves them during materialization. It does not implement A2 specialist-context retrieval or cross-scope ranking.

## Observation contract

A1 permits only normalized source classes for its public append helpers:

- explicit user instruction;
- explicit user correction/removal;
- governed inferred candidate materialization;
- `OrchestraPhaseRetrospective` normalized outcome evidence.

Arbitrary `raw_conversation` source records are rejected by the A1 store. Retrospective normalization keeps only structured fields used for governed outcomes: phase identity/status, unit counts, remediation count, capacity wait count, human escalation count, and evidence fingerprint. Free-form outcome summaries, limitations, follow-up prose, and arbitrary conversation content are not copied into the observation payload by this adapter.

Issue #316's measurement discipline also applies to later adaptive effectiveness work: unavailable trustworthy measurements remain unavailable. A1 does not derive token, cost, or latency metrics from proxies.

## Explicit and inferred knowledge

A1 distinguishes evidence classes instead of flattening them into one preference type.

Explicit scoped preferences materialize as `confirmed` with confidence `1.0`. Inferred observations materialize as `candidate`. A1 intentionally exposes no automatic inferred-candidate promotion helper. `GOVERNED_OUTCOME_RECORDED` observations remain evidence and do not directly become learned preferences.

Promotion logic, shadow comparison, and behavioral learning are later-phase concerns and remain outside A1.

## Non-learnable boundary

The following subject roots are rejected by A1 adaptive records:

- authority;
- capability;
- required specialist ownership;
- governance;
- human gates;
- security prohibitions;
- mandatory validation;
- evidence integrity;
- audit requirements;
- fail-closed behavior;
- exact-head, release, and merge gates;
- privacy/provider restrictions;
- resource ceilings.

Historical success, repetition, or high confidence cannot create permission because these dimensions are structurally excluded from learned memory.

## Privacy and threat controls

A0 identified scope leakage, poisoning, authority escalation through preferences, tampering/replay, one-off preference promotion, sensitive-data retention, cross-project disclosure, provider leakage, and unbounded compute growth as primary threats.

A1 mitigates the subset relevant to local memory through:

- explicit scope identities;
- source-type allowlisting;
- canonical JSON and hash-chained observations;
- sensitive-key and credential-like-value rejection;
- explicit versus inferred evidence classes;
- no A1 automatic inferred promotion;
- machine-local storage outside the repository;
- explicit export, scope deletion, and expiry pruning;
- profile invalidation after compaction;
- fail-closed unknown schema behavior.

A1 does not invent a universal retention duration. Expiry is supported where a trustworthy expiry is supplied. A later product/privacy decision must define default retention periods if desired.

## Delete and compaction semantics

Deletion is handled as local privacy compaction, not as a Git-history operation. Matching observations are removed from the active JSONL file, retained observations are resequenced and re-chained, and any materialized profile is invalidated. The next profile is rebuilt from the new validated log head.

This provides active local deletion semantics but does not claim forensic secure erasure from storage media, filesystem snapshots, backups, or host-level recovery systems. Exports explicitly record `forensic_secure_erase_guaranteed: false`.

## Migration and recovery

A1 is the first store layout and therefore begins at layout version `1`. Unknown observation/profile schema versions fail closed. Future layout changes require an explicit versioned migration contract rather than implicit reinterpretation.

`profile.json` is derived. If it is malformed, stale, or deleted, `JsonlAdaptiveStore.recover_profile()` reconstructs it from the hash-validated JSONL log. Profile writes are refused when the declared source head does not equal the current observation head.

## A1 validation contract

A1 validation must prove at minimum:

- non-learnable subjects fail closed;
- explicit current instructions cannot escape task/session scope;
- credential-like material is rejected;
- raw-conversation source types are rejected;
- JSONL round-trip and hash-chain tamper detection work;
- unsupported schema versions fail closed;
- repository-local store roots are rejected;
- explicit and inferred records remain semantically distinct;
- governed outcomes do not become preferences;
- inferred candidates are not auto-confirmed in A1;
- invalid confidence fails before a valid profile can be produced;
- corrupt derived profiles can be recovered from JSONL;
- stale profile writes are rejected;
- delete compaction removes active records, re-chains retained records, and invalidates the profile;
- expiry pruning works with normalized timestamps;
- export is structured and does not claim forensic secure erase;
- machine JSON fixtures validate against their JSON Schemas.

## A2 stop boundary

This unit must stop after the A1 local-memory foundation and its validation evidence are complete. It must not implement:

- adaptive specialist context injection;
- adaptive routing or route ranking;
- learned model/worker selection;
- learned Tuner topology;
- provider integration;
- training;
- active-policy promotion;
- recursive or test-time compute.

Those remain separately gated by issue #340 and require fresh authorization.
