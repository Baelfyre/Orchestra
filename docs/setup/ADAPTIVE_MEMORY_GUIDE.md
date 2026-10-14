# Adaptive memory — user and developer guide

> **Availability:** Scoped A1/A2 runtime interfaces and A3 shadow components exist. Portable backend and D3B capability-memory contracts have stricter activation limits. This is not an always-on cross-host memory service.

## Components and behavior

| Component | Available foundation | Boundary |
| --- | --- | --- |
| A1 local | Hash-validated scoped observations, explicit preferences and governed outcomes | No authority, raw chat ingestion or automatic inferred promotion |
| A2 advisory | Opt-in, read-only context for the already-selected specialist | No routing change; deterministic fallback if stale or missing |
| A3 shadow | Evidence-based tendency candidates and shadow comparisons | No active promotion or execution influence |
| Portable memory | Privacy-minimized candidate staging through LOCAL_JSON, GIT_JSON, HTTP_API or CUSTOM | No ready-made cloud sync or backend promotion |
| D3B capability memory/discovery | Explicit-trigger offline snapshots, cache references, revalidation hints | No verified host producer or real private-memory activation |

## Local storage

The normal user-scoped A1 root is under `~/.orchestra/adaptive/v1/<hashed-user>/`. It contains an integrity-checked observation log and a rebuildable profile; opt-in A3 shadow records are stored separately. `ORCHESTRA_ADAPTIVE_HOME` can override the root. A supplied repository root cannot be used as the adaptive store.

The store does not accept raw-conversation source records or credential-like values. Machine-local deletion and compaction affect active records; they **do not guarantee forensic erasure** from backups and disk snapshots.

## Scope and precedence

Records may be global-user, project, specialist, or task/session scoped. A2 requires matching user and relevant narrower scope. Priority is current explicit instruction, matching explicit preference, separately confirmed pattern, allowable inferred candidate, then deterministic default. A3 cannot confirm its own patterns or grant execution permission.

When a profile is stale, incompatible, unavailable or scoped to a different user, context compilation falls back rather than guessing. Learned confidence is not evidence of authority, validity, permissions, or measured effectiveness.

## Portability and capability observations

Backend classes describe possible integrations, not installed services. Portable exports omit raw conversations, credentials, local user IDs and task IDs; backend validation/promotion, synchronization, retention and security remain independently governed.

The D3B inventory producer currently reports UNKNOWN without a qualified trusted host bridge. A cached capability claim is not proof that a tool exists, is approved, or can be invoked. No startup full-computer scan or silent tool execution is enabled.

## Source references

- [A1 local memory](../architecture/ADAPTIVE_MEMORY_A0_A1.md)
- [A2 specialist context](../architecture/ADAPTIVE_CONTEXT_A2.md)
- [A3 shadow implementation](../architecture/ADAPTIVE_SHADOW_LEARNING_A3_IMPLEMENTATION.md)
- [Portable memory](../architecture/PORTABLE_ADAPTIVE_MEMORY.md)
- [D3B capability memory](../architecture/ADAPTIVE_CAPABILITY_MEMORY.md)
- [D3B capability discovery](../architecture/ADAPTIVE_CAPABILITY_DISCOVERY.md)

Only publish specific host controls or automatic behaviors after they are implemented and validated against the target release.
