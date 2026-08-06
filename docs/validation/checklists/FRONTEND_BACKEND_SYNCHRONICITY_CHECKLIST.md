# Frontend-to-Backend Synchronicity Checklist

Use this checklist with the [Cross-Module Logic Audit Protocol](../CROSS_MODULE_LOGIC_AUDIT_PROTOCOL.md) and a frozen `CrossLayerContractPacket`.

## Identity and scope

- [ ] Repository, branch, approved baseline, current commit, packet revision, and contract hash match.
- [ ] Changed, staged, untracked, ignored-relevant, and generated paths are complete.
- [ ] Every changed path is allowlisted and every protected path is unchanged.
- [ ] External actions and installed integrations remain separately authorized.

## Workflow trace

- [ ] `UI_CONTROL` identifies the control, visible affordance, and accessibility name.
- [ ] `CLIENT_EVENT` identifies the user event and duplicate-event behavior.
- [ ] `CLIENT_STATE_OR_FORM_MODEL` maps client state and client validation.
- [ ] `SERIALIZED_REQUEST` maps names, types, nullability, defaults, and omitted fields.
- [ ] `API_ROUTE` identifies method, route, content type, authentication, and authorization.
- [ ] `BACKEND_HANDLER` maps parsing, validation, errors, and status codes.
- [ ] `SERVICE_OPERATION` identifies business operation, side effects, retries, and idempotency.
- [ ] `REPOSITORY_AND_PERSISTENCE` identifies the existing repository boundary or explicitly records `DEFERRED_NOT_APPLICABLE`.
- [ ] `API_RESPONSE` maps success and error payloads to the request and domain result.
- [ ] `CLIENT_CACHE_OR_STATE_UPDATE` identifies reconciliation, invalidation, optimistic behavior, and stale responses.
- [ ] `FINAL_RENDERED_STATE` proves the user-visible result and recovery behavior.

## Parity and state coverage

- [ ] Client and server field rules agree for required, optional, null, empty, range, format, and normalization behavior.
- [ ] Authorized, unauthorized, and edge-case personas receive consistent navigation, route, content, and backend enforcement.
- [ ] Applicable loading, queued, processing, cancellation, timeout, success, error, empty, deleted, and stale states are represented.
- [ ] Backend failures remain visible, actionable, and do not appear as success.
- [ ] Retry and duplicate submission behavior is deterministic and idempotent where required.
- [ ] Keyboard, focus, semantics, status announcements, and error associations are preserved.

## Findings and evidence

- [ ] Each finding has one owner, severity, affected stages, evidence, impact, minimal remediation, and required validation.
- [ ] Contradictions are recorded but not silently resolved by The Tuner.
- [ ] Executable happy-path and failure-path evidence is current and bound to the packet identity.
- [ ] Missing evidence produces `CROSS_LAYER_EVIDENCE_INSUFFICIENT`.
- [ ] Changed identity produces `CROSS_LAYER_CONTRACT_STALE` or `SPECIALIST_REENTRY_REQUIRED`.
- [ ] No open invalidation event remains before `CROSS_LAYER_ALIGNMENT_CONFIRMED`.

## Closeout

- [ ] Focused validator and behavior tests pass.
- [ ] Full behavior, runtime regression, packaging, prompt-budget, governance, export-parity, scope, secret, and diff checks pass.
- [ ] Generated temporary exports are inspected and removed without modifying installed integrations.
- [ ] Overseer evidence and Arbiter continuation state are recorded.
- [ ] Human Git and merge gates remain explicit.
