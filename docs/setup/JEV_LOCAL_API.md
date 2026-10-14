# JEV local API and BYOK — status and requirements

> **Availability:** Developer reference, **not a verified end-user setup procedure**. The optional TypeSafe System One provider adapter exists, but a trusted user/workspace host bridge, secure credential onboarding, exact outbound preview/consent, and a production-qualified flow remain unavailable.

## What JEV does

JEV optionally advises on already-reviewed mitigation alternatives. It cannot verify findings, own specialist decisions, change risk grades, grant permissions, merge, deploy, or amend governance. Without eligible alternatives or qualified provider integration, Orchestra continues its ordinary review workflow.

## Current source interfaces

- [TypeSafe adapter](../../orchestra_runtime/infrastructure/providers/typesafe_jev.py): accepts an injected credential callback; it does not supply a public user-key enrollment command.
- [Adjudication use case](../../orchestra_runtime/application/use_cases/jev_adjudication.py): binds advisory results to a candidate and checks freshness.
- [Offline provider projection](../../orchestra_runtime/application/services/jev_provider_projection.py): synthetic minimized data representation; no production dispatch or proof of consent.
- [Responsibility-adjudication contract](../architecture/JEV_RESPONSIBILITY_ADJUDICATION.md): offline-only and separate from the mitigation-advice path.

There is currently **no verified universal configuration key, secure-store CLI command, or local setup UI**. Do not paste an API key into prompts, repository files, or an invented environment variable.

## Required flow before user activation

1. **Supported host:** verify active user, workspace, permissions and revocation from a trusted host source, not prompt text.
2. **User-owned provider account:** review TypeSafe terms, pricing, processing and retention before enabling third-party requests.
3. **Credential storage:** use a qualified user-scoped OS credential store with no secrets in Git, logs, memory export or the chat.
4. **Inspect outbound data:** show the exact minimized payload and residual identifiers before sending a request.
5. **Explicit consent:** bind approval to one payload, candidate and user; changing any of them invalidates approval.
6. **Bound transport:** validate endpoint, response contract, timeouts, token accounting, errors, freshness, and no unauthorized redirects or retries.
7. **Independent qualification:** complete live-provider compatibility, privacy/security and host acceptance checks before publishing operational setup commands.

These are prerequisites, **not currently executable setup steps**.

## Safe fallback

| Condition | Outcome |
| --- | --- |
| Missing trusted principal, consent surface or API key | No provider call |
| No material alternatives | JEV optional; ordinary workflow continues |
| Unsupported provider response or network failure | Sanitized error; no accepted advice |
| Candidate changed or output is unbound | Do not reuse stale answers |

Provider use may transmit user-approved data and incur charges. Alias substitution and basic hazard checks do not guarantee privacy or consent. There is no claim of zero retention or vendor-endorsed public BYOK.

Read [Evidence-Gated Decision Hierarchy](../architecture/EVIDENCE_GATED_DECISION_HIERARCHY.md). Tested host-specific setup commands must replace this status guide only after authorized implementation and qualification.
