# Portable Adaptive Memory

Orchestra's adaptive-learning core is storage-agnostic.

A1 local observations, A2 advisory context, and A3 shadow candidates remain local by default. When a user or project chooses to make a validated pattern portable, Orchestra can emit a privacy-minimized `orchestra.portable-memory-candidate.v1` record for a selected storage backend.

## Storage is a user choice

Orchestra does not require, name, or assume a particular external memory product, repository, database, or service. A deployment may use any backend that can satisfy the portable-memory contract, including:

| Adapter kind | Typical use |
| --- | --- |
| `LOCAL_JSON` | Local JSON or JSONL files, optionally synchronized by the user |
| `GIT_JSON` | A user-selected Git repository containing validated JSON memory records |
| `HTTP_API` | An organization-managed or remote memory service |
| `CUSTOM` | Any user-supplied adapter implementing the backend protocol |

Backend identity and configuration belong to the user's environment or project configuration. They do not need to be committed to the Orchestra repository.

## Portable candidate flow

```text
A1 local observations
        ↓
A3 shadow learning
        ↓
Evidence-bounded candidate
        ↓
Explicit privacy review
        ↓
Portable memory candidate
        ↓
User-selected backend adapter
        ↓
Backend-specific validation / staging
        ↓
Backend-specific governed promotion
```

A portable candidate is not a promotion by itself. It remains `PENDING_BACKEND_VALIDATION` and carries `canonical_write_authorized=false`.

## What Orchestra exports

The portable record may contain:

- pattern key, type, category, and value;
- repository, project, use-case, and specialist scope selected for the portable record;
- evidence references and SHA-256 digests;
- confidence and observation chronology;
- non-authority and privacy assertions; and
- an abstract destination backend descriptor supplied by local configuration.

The portable boundary explicitly excludes raw conversation content, sensitive data, credentials, local user identifiers, and task-session identifiers.

## Authority boundary

Portable memory is advisory knowledge. It cannot grant execution authority, policy authority, new capabilities, provider access, routing changes, specialist ownership changes, validation bypasses, release authority, deployment authority, or permission to relax governance.

Confidence is not authority. Storage availability is not authority. A successful backend write is not authority.

Current instructions and governed project state continue to take precedence over learned memory.

## Implementing a custom backend

The public backend interface is defined by:

```text
orchestra_runtime.adaptive.portable_memory.PortableMemoryBackend
```

A backend provides two bounded operations:

```text
validate_candidate(candidate)
stage_candidate(candidate, destination)
```

These operations deliberately stop before backend-specific canonical promotion. Git commits, database writes, synchronization, review workflows, retention, supersession, encryption, and publication policy are responsibilities of the selected backend and its own governance.

The machine-readable contract is available at:

- `machine/schemas/portable-memory-candidate.schema.json`
- `machine/adaptive/memory-backends.v1.json`

## Privacy and portability

Users who want cross-device memory can select a synchronized backend. Users who want machine-local learning can keep `LOCAL_JSON`. Organizations can provide a private backend without exposing its identity or implementation details in Orchestra's public source.

Orchestra therefore treats portable memory as a capability boundary, not a built-in storage dependency.
