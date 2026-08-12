# API and Versioned Documentation Guide

## API Reference Source

Start from the exact OpenAPI/AsyncAPI/schema revision, route definitions, generated reference artifact, or verified implementation. Record the contract revision and supported server/client version.

For each operation document method/topic, path/channel, purpose, authentication reference, parameters, headers, request schema, response/status variants, error envelope, idempotency or pagination behavior, rate/size limits, and examples only when confirmed.

Examples must conform to the schema and must not contain credentials or personal records. A `200` example cannot stand in for error, authorization, validation, conflict, or retry behavior.

## Compatibility and Change

Identify additive versus breaking changes under the repository's actual compatibility policy. Cover renamed/removed fields, requiredness, enum expansion, defaulting, precision, ordering, unknown-field behavior, and event replay where relevant. Clockwork owns interface compatibility decisions; Cipher owns auth/security requirements; Chronicler owns stored-data semantics.

## Versioned Documentation

Distinguish:

- current documentation for the canonical supported version;
- supported-previous documentation with explicit support status;
- archived documentation that is read-only and clearly non-current;
- future/draft documentation labeled as unimplemented.

Define canonical URLs, version selector behavior, redirects, search indexing, cross-version links, and code-sample version alignment. Avoid silently redirecting an old incompatible API page to current behavior.

## Deprecation and Sunset

Record what is deprecated, first affected version, replacement, migration steps, warning channel, effective date, sunset/removal date if approved, support contact, and source authority. Do not invent dates or imply removal authority from documentation alone.
