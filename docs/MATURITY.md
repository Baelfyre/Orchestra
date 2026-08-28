# Orchestra Project Maturity

This document classifies the current maturity of Orchestra's public v1.7.0 surfaces and post-release canonical maintenance. It distinguishes implemented deterministic controls from bounded/advisory capabilities and from planned work so compatibility or test success is not mistaken for authority or production maturity.

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
