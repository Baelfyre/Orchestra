# Source-Backed API Change Example

## Status

`DOCUMENTATION_PLANNED`; no release or documentation-site publication occurred.

## Evidence Identity

- API contract: `api/openapi.yaml` at fictional reviewed commit `abc1234`
- Implementation evidence: fictional PR #42 exact head `def5678`
- Validation: contract test report `report-2026-08-12`, `PASS` for the same head
- Release evidence: `NOT_FOUND`; change must remain under `Unreleased`

## Documented Change

`POST /orders` accepts an optional idempotency-key header in the reviewed contract. The reference update must document header syntax, repeated-request response, conflict/error behavior, and one schema-valid redacted example. It must not claim production availability or a release version.

## Compatibility and Migration

Existing clients that omit the optional header remain supported according to the reviewed contract. Any future requirement to make the header mandatory is `PLANNED` and requires a separately accepted compatibility decision, deprecation notice, migration guide, and effective date.

## Link Checks

- operation anchor exists under the target renderer;
- schema links resolve with exact case;
- error-envelope and authentication references target the same API version;
- changelog link remains in the pending section;
- no link claims a release, tag, or deployed endpoint.

## Ownership

Clockwork supplies compatibility facts, Cipher supplies authentication/security facts, Overseer supplies validation evidence, and Scribe transcribes them. Scribe does not publish the docs or create release authority.
