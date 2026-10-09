# Link and Claim Validation Guide

## Claim Ledger

For a drift-prone or consequential claim, record:

```text
claim -> source artifact -> source revision -> last verified -> effective date/status -> owner
```

Use immutable commit, tag, report, schema, issue, or authoritative URL references where appropriate. A source existing is not enough; it must directly support the claim and match the documented revision.

Classify claims as `VERIFIED_CURRENT`, `VERIFIED_HISTORICAL`, `PLANNED`, `PENDING_VALIDATION`, `BLOCKED`, or `UNVERIFIED`. Never infer current status from an older report without a live reread when the fact can drift.

## Local Link Validation

- resolve relative paths from each containing file;
- check exact path case, file existence, and fragment/anchor existence;
- detect path escape, stale renamed targets, duplicate reference definitions, and orphaned images;
- validate generated documentation links after export, not only source links;
- distinguish a missing target from a link intentionally pointing to a future `[DRAFT]` artifact.

## External Sources

Prefer primary authoritative sources. Record jurisdiction, edition/version, publication/effective date, and last access when relevant. An inaccessible link becomes `UNVERIFIED` until rechecked; do not fabricate replacement evidence.

## Command and Status Validation

Verify commands in the documented shell, working directory, runtime, and revision. Record skipped platform variants. Re-read badges, releases, support versions, PRs, and policy state before publication because these claims are drift-prone.

Any source change invalidates dependent documentation evidence. Update or explicitly mark the affected claim stale; do not leave a previously verified label attached to changed facts.
