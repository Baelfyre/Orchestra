# Orchestra Project Maturity

This document classifies Orchestra's published v1.9.0 surfaces and prepared v1.10.0 candidate. It distinguishes implemented deterministic controls from bounded/advisory capabilities and from planned work so compatibility or test success is not mistaken for authority or production maturity.

## Current v1.10.0 candidate

- **Universal Adaptive Integration**: UAI-0 through UAI-10 are canonically verified within the candidate scope. Host/transport capability remains separate from provider/model eligibility and Conductor/AWF specialist routing.
- **GitHub Copilot Conductor**: `SUPPORTED_VERIFIED` from the maintainer live retest. Copilot Auto mode did not expose the underlying provider/model, so that identity remains unresolved and unadmitted.
- **Conductor routing**: Conductor remains the sole internal specialist router. Clear ownership may enable a direct single-specialist fast route; it is not a router bypass.
- **Package and host metadata**: all 11 package/version surfaces and the host update contract are prepared at `1.10.0`; the current public release remains v1.9.0.
- **Publication boundary**: the candidate is `PREPARED_NOT_PUBLISHED`; no tag, GitHub Release, deployment, policy activation, or installed-integration refresh is included.

## Current v1.9.0 publication

- **UIEF-5 through UIEF-10**: UIEF-5 is canonically merged and verified. UIEF-6 and UIEF-8 are verified from existing specialist and regression contracts. UIEF-7 is verified with deterministic static validation and no new rendered-application evidence. UIEF-9 is verified with the historical `NO_BENEFIT_ESTABLISHED` disposition and no new provider experiment. UIEF-10 documentation and release closeout are canonically verified.
- **Package and host metadata**: all 11 package/version surfaces and the host update contract are published at `1.9.0`; host maturity and installed integrations are unchanged.
- **Adaptive Host Integration**: future roadmap item only; no host integration, automatic adaptation, provider mutation, or policy activation is included.

## Stable / Enforced

- **Specialist and manifest structure**: `SKILL.md`, manifest, routing, and machine specialist contracts are deterministic and validated.
- **Governance and authority separation**: routing, capabilities, validation, compatibility, mergeability, and learned state remain separate from execution authority.
- **Prime Directive and Development Lifecycle V2**: the constitutional Prime Directive plus candidate admission, freeze, qualification, promotion, merge verification, recovery, and retirement evidence are canonical through post-v1.7 PR #592 without introducing a second runtime lifecycle, autonomy engine, Arbiter, or merge engine.
- **Behavior validation**: `tests/behavior/run_tests.py` remains a primary cross-platform deterministic validation runner.
- **Runtime test evidence**: CI records statement and branch coverage. Overall evidence floors are 97% statement / 95% branch; critical-module inventory floors are 98% statement / 95% branch.
- **Cross-platform validation**: native Windows, Ubuntu, and macOS jobs are required on protected `main`.
- **Protected-main release discipline**: exact-head checks, signed commits, linear history, Squash-only merge, review-thread resolution, and the live required-status matrix are enforced by repository rules. Active ruleset `17927422` currently contains each required context exactly once following the separately authorized duplicate-status correction performed before PR #592 merged.
- **Adapter SDK / PRAP v1 certification**: stable read-only compatibility surface through `orchestra_runtime.protocol.sdk` and `scripts/certify_adapter.py`.
- **MCP stdio transport**: bounded `2026-07-28` stdio transport exposing `server/discover`, `tools/list`, and `tools/call` while preserving existing runtime authority boundaries.

## Implemented but Bounded / Non-Promoted

- **Adaptive intelligence A1-A5**: local memory, bounded specialist context, shadow learning, shadow selection, and topology evaluation are implemented within explicit non-authorizing boundaries. A5 execution-effective topology promotion is not performed because qualifying benefit was not established.
- **Portable adaptive memory**: optional storage-agnostic transport supports local JSON, Git-backed JSON, HTTP/API, and custom backends for explicitly reviewed learned candidates. Automatic external-memory promotion remains disabled.
- **UI design fidelity UIX-0 through UIX-9C V3**: repository contracts, evidence preservation, specialist integration, optional adapter boundaries, portability, controlled-proof preparation, and the separately authorized post-release UIX-9C V3 study are complete. UIX-9C V3 ended `NO_BENEFIT_ESTABLISHED` with six valid observations, three corrected valid pairs, and 39 unchanged primary comparisons. The result establishes neither repeatable governed benefit nor harm and is not promoted into runtime behavior.
- **Registry O1-O6 adaptive consumption**: deterministic capability/freshness/query/receipt handling is implemented; Registry evidence remains evidence, not authority.
- **Murmurs**: retained as optional historical presentation research. Repeatable efficiency benefit was not established and Murmurs is not a default execution requirement.
- **Scaffold-only hosts**: Claude Code runtime continuity, Cursor, Windsurf, VS Code/VSCodium, JetBrains, Zed, and Neovim remain scaffold-only where declared. Package-version parity does not promote host maturity.

## Experimental / Compatibility

- **Legacy PowerShell wrappers**: retained for Windows-oriented compatibility where documented, but Python validation is the primary CI path.
- **External audit sandboxes**: useful for independent review, but strict evidence/freshness checks require trustworthy Git identity and refs; incomplete Git reconstructions may intentionally fail closed.

## Planned

- **Registry O7 query optimization**: approved and planned, not part of v1.7.0 runtime implementation. O7.0 consumer-contract freeze may be performed against the frozen R7 architecture; implementation phases remain separately governed and must preserve O1-O6 fallback compatibility and Registry authority boundaries.
- **Host graduation**: scaffold-only hosts require separate evidence and explicit promotion; no automatic graduation is implied.
- **Further UIX live experiments**: not currently authorized or required. Any new provider/model study requires a new evidence-backed purpose and separate live-call authority rather than retrying UIX-9C until a positive result appears.
