<!-- @codebase_provenance_JEO -->
<!-- @codebase_rights_JEO -->

# ADR: Cipher Offline Inference Boundary (R5)

- **Status:** Proposed, architecture only
- **Date:** 2026-11-05
- **Scope:** Offline review plumbing and a deterministic stub. This decision does not authorize implementation, provider access, or data transfer.

## Context

The host review path materializes a read-only workspace from a repository candidate. Its current snapshot digest covers repository identity, base/head/tree identity, ordered change metadata, and before/after content. ReadOnlySpecialistExecutionRequest and SpecialistReviewResult bind review output to request and snapshot digests. The separate provider-capability broker is shadow-only: it reports evidence-based advisories and cannot select or switch providers.

The existing Codex app-server bridge is a live model path. Its read-only and network restrictions are inputs to that host, not evidence of an offline boundary or verified Windows process isolation.

## Decision

R5 remains offline. The trusted host supplies an immutable snapshot and typed request to a deterministic stub. The stub makes no model or provider call, opens no credential source, uses no network, writes no workspace files, and returns a fixed INCONCLUSIVE result. Its conclusion identifies OFFLINE_STUB_NO_INFERENCE; its evidence references bind only the request and snapshot. It must not emit PASS or substantive findings. A runtime lifecycle value of COMPLETED is transport completion, not review clearance.

The proposed canonical snapshot identity binds:

- a schema/version tag and normalized repository identity;
- base commit, candidate commit, and candidate tree SHA values;
- the sorted, normalized relative-path change manifest, including status and prior path for renames;
- SHA-256 digests of each present base/current file byte sequence, with explicit absent markers;
- an aggregate digest of the exact materialized snapshot;
- request digest and the selected Cipher source digest.

Canonical serialization, path normalization, and absent-value encoding must be fixed before implementation. Recompute the identity from the copied bytes and reject drift, duplicate normalized paths, path escape, oversized input, or any mismatch. A hash binds bytes; it does not prove who supplied them, that the host is uncompromised, or that the snapshot is complete.

Keep the inference boundary narrow: host-owned snapshot and request in; schema-checked result out. The stub has no policy, authority, routing, tool, shell, persistence, or provider-selection interface. Do not use provider eligibility as execution approval. The existing provider-capability broker remains advisory and separate.

The test-only stub limits its serialized response to 4096 bytes and rejects a response returned after 2 seconds. Its synchronous deadline check cannot interrupt a hung operation. For a future broker, 64 KiB is a proposed response limit, not the fixture's limit; the caller must support cancellation and terminate a future process worker and its children on timeout. These future controls are not measured runtime guarantees. Validate every evidence reference against the host-minted request and snapshot manifest: accept only listed normalized paths and matching content digests, reject arbitrary file/URL references, and invalidate references when the bound snapshot changes. A valid reference proves location and binding, not the truth of a claim.

## Threat model and controls

Treat task text, repository content, filenames, evidence references, and any future model response as untrusted. Repository text can contain prompt injection or secrets. R5 does not interpret that text. A future model prompt must keep trusted instructions outside clearly bounded data, minimize included paths, disable tools and delegation, validate the returned schema and exact request/snapshot binding, and still assume prompt injection can influence model output. Delimiters do not eliminate that risk.

Relevant threats are snapshot substitution or drift, path traversal and reparse-point escape, oversized or malformed content, prompt injection, result forgery, unexpected child processes or network access, and secret exposure. Snapshot hashing and typed-result matching address binding errors only. They do not establish a security finding, prevent host compromise, or make read-only content safe to disclose.

## Windows isolation requirements for any future worker

R5's deterministic stub should remain a pure offline function. If a later design launches an engine, use a restricted process only for a trusted, pinned local runtime; it shares the host kernel. Use a disposable VM for an untrusted/native runtime or when the host data boundary requires a separate guest. VM isolation also needs verification and does not establish freedom from every host or hypervisor risk.

Before starting a process worker, fail closed unless all checks succeed:

1. Read the actual Windows build and process architecture with RtlGetVersion and IsWow64Process2; compare them with a versioned, explicit support matrix. Unknown builds are unsupported.
2. Verify the pinned executable's normalized path, signature/hash, and absence of a reparse-point escape. Create the worker with a restricted, non-admin token or AppContainer profile; inspect its SID, integrity level, groups, privileges, and capabilities. No credential, user-profile, or source-write access is allowed.
3. Start suspended, assign the process to a Job Object configured for kill-on-close, bounded child count, and no breakaway, then query the effective job limits before resume. Any failed assignment or query blocks execution.
4. Pass only explicit standard I/O and read-only snapshot handles. Use an allowlisted environment and temporary directory; verify source ACLs are read-only to the worker.
5. Verify effective OS egress denial for the worker identity and run a no-data connectivity canary from a disposable worker. A successful connection or unverifiable policy blocks execution. A firewall-enabled flag alone is insufficient.

Before a VM worker starts, verify the required hypervisor/virtualization feature and supported host build; validate the guest image and clean ephemeral state by digest; disable host folders, clipboard, credential integration, and network; attach only a read-only snapshot; and run a guest egress canary before mounting task data. Missing or unverifiable isolation controls block execution. These are proposed acceptance checks, not controls demonstrated by this ADR.

## Required validation cases before any worker is accepted

- Attempt to create a host marker file outside the snapshot; access must be denied and the marker must remain absent.
- Attempt shell launch and child-process creation; both must be denied, and cancellation must leave no worker descendants running.
- Request arbitrary MCP/tool invocation from task text and source content; no tool endpoint may be available or called.
- Attempt controlled DNS and network connections; egress must fail from the worker, including after cancellation/restart paths.
- Include source text that instructs the engine to ignore policy, execute commands, or exfiltrate data; the offline stub must still return its fixed INCONCLUSIVE result. For a future model, verify no tool, shell, write, or egress action occurs, while treating semantic prompt-injection resistance as unproven.
- Change a referenced file after snapshot creation and supply an unlisted path or wrong digest; the host must reject the stale or forged evidence reference.

Passing unit tests alone is insufficient. Acceptance needs independent Windows evidence for the exact worker build and snapshot, including observed token/job/handle state, marker-file denial, child-process termination, blocked egress, and host-side reference validation. Preserve the failed and skipped cases; no single test result establishes isolation or prompt-injection immunity.

## Future transfer, approvals, and cost

No transfer occurs in R5. Any later networked or provider-backed phase requires separate approval for the exact repository, snapshot fields, purpose, recipient, provider/model, region, retention and training terms, credential mechanism, network path, validation, and rollback. Obtain data-owner and repository-owner approval; route architecture to Clockwork, security to Cipher, validation evidence to Overseer, scope/operational review to the Steward, and privacy/IP/legal review to the Governor when applicable. Provider credentials and exact outbound authority require their own approved boundary. This ADR grants none of them.

Cost is **unquantified**: R5 makes no model call. A later estimate needs the selected provider/model, snapshot size, tokenization, expected calls and retries, region, and approved spend ceiling.

## Limitations

This document proposes architecture only. The snapshot/result interfaces do not yet carry all proposed per-file identity fields as separate values. The deterministic stub proves no inference quality and cannot perform a Cipher review. Windows checks, process/VM isolation, egress denial, and any future transfer are not implemented or validated here. No provider, credential, configuration, environment, or transcript was inspected; no provider was run.

## Source basis

- orchestra_runtime/application/ports/specialist_execution.py: immutable review-change and read-only workspace interfaces.
- orchestra_runtime/specialist_execution.py: repository identity, bounded snapshot materialization, drift checks, and review request/result binding.
- orchestra_runtime/domain/execution/operation_contracts.py and orchestra_runtime/interfaces.py: typed read-only request/result and effect-free engine entry point.
- orchestra_runtime/domain/adaptive/provider_capability.py: shadow-only provider-capability advisory contract.
- internal/codex_app_server_bridge.py: earlier live model bridge and its host-supplied read-only/network restrictions.
