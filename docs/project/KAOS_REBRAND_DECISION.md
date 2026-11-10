# Kontrolled Kaos Public Identity Decision

**Date:** 2026-11-10
**Status:** Owner-approved, bounded source migration; host and release gates remain separate.

## Decision

Implement the owner-approved public identity migration from **Orchestra** to **Kontrolled Kaos**, described as an **AI-Assisted Development Framework**, using the canonical repository `Baelfyre/Kaos`. The previous product name remains attached to historical releases and evidence.

This decision changes product presentation and host registration only. It does not grant legal, trademark, exception, merge, release, or publication approval.

## Preserved contracts

- The established 14 specialists, names, slugs, source files, icons, and specialist mappings remain unchanged.
- Conductor remains the sole existing routing specialist. The `$kaos` and `/kaos` aliases point to that Conductor contract; no second dispatcher is added.
- Governance, safety controls, runtime APIs, authority boundaries, release gates, and package version `1.12.0` remain unchanged.
- Historical Orchestra release records remain attributed under their original product name. The current public release remains Orchestra `v1.11.0`; this rebrand does not publish `v1.12.0`.

## Host identity and migration

- **Codex:** package and marketplace IDs `conductor@orchestra` remain as compatibility keys. The new product skill entry is `$kaos`; refresh the existing marketplace package to receive it.
- **Antigravity:** `.antigravity-plugin/plugin.json` registers `kaos`; the additional skill exposes `/kaos`. The root `plugin.json` remains the internal Orchestra registry.
- **Claude Code:** plugin ID changes to `kaos`; marketplace key `orchestra` remains for source compatibility. The existing Conductor skill is invoked as `/kaos:conductor`, following Claude Code's plugin namespace rule. Existing users should install the new package, verify it, and then remove `orchestra@orchestra` if no longer needed.
- **Other hosts:** scaffold package IDs and maturity remain unchanged; display labels use Kontrolled Kaos. GitHub Copilot's probe remains `AVAILABLE_NOT_YET_VERIFIED`. `@Kaos` is not claimed unless a host explicitly documents and verifies that invocation.

No user installation or marketplace publication is performed by this change. Package validators and any interactive host invocations are reported separately in the validation ledger.

## Emblem provenance

The approved source image was supplied at `C:\Users\ongoj\Downloads\Kontrolled Kaos_ Dual K Emblem.png` and copied byte-for-byte to `assets/branding/kontrolled-kaos-dual-k-emblem.png`.

- SHA-256: `b94250447506eaa1410804216cbef768df6e10dd5bde7ca02fb169dd79063673`
- Format and size: PNG, 1254 × 1254 pixels, RGB, no alpha channel
- No redraw, recolor, crop, regeneration, or image conversion was performed.

## Host validation status

- **Codex:** isolated local marketplace discovery and package installation were verified in a temporary `CODEX_HOME`; the alias file was present in the installed package. A conversational `$kaos` invocation was not tested.
- **Antigravity:** `agy plugin validate . --json` exited successfully and discovered 15 skills, including the Kaos alias. Strict mode exits non-zero with warnings because it ignores the repository-root `AGENTS.md`, `commands/`, and `plugin.json`; interactive `/kaos` invocation was not tested.
- **Claude Code:** `claude plugin validate --strict .` passed. Interactive `/kaos:conductor` invocation was not tested.
- **Other hosts:** scaffold-only maturity and existing `AVAILABLE_NOT_YET_VERIFIED` states remain unchanged.

These checks establish package structure and local discovery only. Interactive invocation, rights, privacy, governance, and release approvals remain separate gates governed by their original records.
