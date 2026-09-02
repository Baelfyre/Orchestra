# Orchestra AR-2 Domain Execution Correlation Extraction

## Status

`AR_2_DOMAIN_EXECUTION_CORRELATION_IMPLEMENTATION_CANDIDATE`

This bounded AR-2 increment separates deterministic correlation-identifier validation from clock and entropy backed UUIDv7 generation.

## Canonical domain ownership

`orchestra_runtime.domain.execution.correlation` owns the pure correlation-identifier contract:

- `validate_correlation_id`
- `is_valid_correlation_id`

The contract preserves the existing RFC 9562 UUIDv7 rules:

- values must be strings;
- values must be non-empty and unpadded;
- malformed UUID input is rejected;
- UUID versions other than version 7 are rejected;
- non-RFC-4122/RFC-9562 variants are rejected;
- non-hyphenated representations are rejected;
- canonical uppercase UUID text is accepted and normalized to lowercase.

The domain module uses only deterministic UUID parsing. It has no clock, entropy, filesystem, provider, MCP, host, application-port, persistence, or audit dependency.

## Legacy compatibility boundary

`orchestra_runtime.correlation` remains the public and transitional generation surface. Existing imports of `validate_correlation_id` and `is_valid_correlation_id` resolve to the exact canonical domain functions.

The legacy module deliberately retains:

- `generate_correlation_id`;
- `_generate_correlation_id`;
- clock access through `time.time_ns`;
- entropy acquisition through `secrets.token_bytes`;
- UUIDv7 construction.

Generation is intentionally not moved into the domain because clock and entropy acquisition are environmental effects rather than deterministic domain validation.

## Dependency rule

The extracted execution-domain module obeys the AR-2 dependency direction:

```text
orchestra_runtime.domain -> orchestra_runtime.domain | orchestra_runtime.shared
```

Its only runtime dependency is the Python standard-library `uuid` module. It does not import legacy runtime modules or external layers.

## Behavioral preservation

The extraction changes ownership, not behavior. The existing correlation test suite continues to exercise generation, validation, run-identity integration, runtime composition, child propagation, envelopes, and adapters through the legacy/public surfaces.

Additional assertions verify that:

1. legacy and public validation exports are identity-equal to the canonical domain functions;
2. the domain module contains no clock, entropy, filesystem, host, provider, application-port, or legacy-runtime imports;
3. the domain module does not expose correlation-ID generation.

## Sequencing value

This separation establishes the deterministic execution-identity primitive needed before moving `RunIdentity` inward. `RunIdentity` currently resides in the mixed legacy `orchestra_runtime.models` module and depends on correlation validation. Making that validator canonical in `domain.execution` removes the legacy dependency that would otherwise invert the domain boundary.

A later bounded AR-2 unit may therefore classify and move `RunIdentity` without importing `orchestra_runtime.correlation` into the domain. That later move is not part of this candidate and requires its own validation gate.

## Explicit non-goals

This bounded extraction does not:

- move or alter UUIDv7 generation;
- move `RunIdentity`;
- move lifecycle state, lifecycle controllers, audit events, or execution results;
- start AR-3 application/use-case extraction;
- start AR-4 infrastructure extraction;
- alter authority, capability, provider, MCP, routing, governance, or execution behavior;
- retire the public `orchestra_runtime.correlation` surface;
- authorize release or tag publication, deployment, production mutation, policy activation, installed-integration refresh, destructive cleanup, branch deletion, force push, or history rewrite.

AR-2 remains active after this unit until the remaining qualified pure-domain ownership slices are completed.
