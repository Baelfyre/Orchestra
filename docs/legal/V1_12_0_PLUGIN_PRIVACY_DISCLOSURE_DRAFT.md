# Orchestra v1.12.0 Plugin Data Handling and Privacy Notice

**Status: DRAFT FOR GOVERNOR REVIEW. Not approved or published legal terms.** Scope: source/plugin distribution, not a standalone hosted service. This document records implementation facts and unresolved disclosure fields without asserting facts about an independent AI host's service.

## 1. Product and operator boundary

The Orchestra owner confirmed on 2026-11-08 that v1.12.0 is a locally installed AI-assisted project-development plugin; Orchestra does not operate its own server as part of this release, and there are no Apple App Store or Google Play submissions. Supported installation guidance includes Codex and Antigravity; Claude Code plugin packaging is supported, but active runtime continuity is scaffold-only. Other IDE adapters remain scaffold-only. See [installation](../setup/INSTALLATION.md), [compatibility](../setup/COMPATIBILITY.md), and [release scope evidence](../releases/v1.12.0-release-clearance-evidence.md).

**Do not confuse the plugin with the host.** A selected host and its AI provider may process task prompts, repository files, model responses, tools, diagnostics and account data under their own configuration and policies. Orchestra does not claim to control, erase, or disclose every operation of independent hosts. Users should review the privacy and data controls of the host they choose.

## 2. Source-backed data inventory

| Capability | Potentially user-related data | Storage / recipient | Activation and use | Known retention / deletion behavior |
| --- | --- | --- | --- | --- |
| A1 local adaptive observations | Scoped user key, subject keys, explicit user preferences, governed observation evidence and timestamps | Machine-local `~/.orchestra/adaptive/v1/<hashed-user>/observations.jsonl`, derived `profile.json`, `store-meta.json`; `ORCHESTRA_ADAPTIVE_HOME` may override | A1 interfaces exist; source/guide do **not** establish automatic active learning on every host | Records may have optional `expires_at`; `prune_expired` and `delete_scope` compact selected active observations. No default global retention duration or automatic scheduler was verified. Derived profile is invalidated after compaction. No forensic erasure guarantee |
| A2 advisory context | Eligible user/project/specialist-scoped patterns | Reads locally eligible A1/profile data when enabled | Opt-in and read-only for already selected specialist; cannot broaden permissions | Inherits A1 storage lifecycle; no separate universal host retention policy verified |
| A3 shadow evidence | Local shadow signals and comparisons | Under user-scoped `~/.orchestra/adaptive/` shadow path, per architecture guide | Shadow evaluation only, not automatically promoted to authority | A3 lifecycle and cleanup behavior must be confirmed before claiming a global TTL |
| Legacy continuity JSONL | Project ID, event type, timestamps, event payload and hash-chain references | Host-chosen filesystem path via `JsonlContinuityStore` | Only when a host or developer explicitly constructs and uses the store; source search did not establish a default active host | Append and load exist; no general retention or secure-erasure policy verified |
| MCP stdio transport | Selected commands, inputs, execution output and runtime metadata | Host process and configured host services | Deterministic stdio route; not an Orchestra-operated Internet server | Host logging/storage and provider retention are outside this verified plugin implementation boundary |
| TypeSafe/JEV provider | Potential minimized advisory payloads if activated in a future qualified integration | No verified production dispatch or trusted BYOK enrollment for v1.12 | Further activation and live inference explicitly deferred | No provider data-transfer or retention guarantees are made |

Source references: `orchestra_runtime/adaptive/{models,store,privacy}.py`; `orchestra_runtime/context_state.py`; `docs/setup/ADAPTIVE_MEMORY_GUIDE.md`; `docs/architecture/ADAPTIVE_SHADOW_LEARNING_A3_IMPLEMENTATION.md`; `docs/developer/MCP_STDIO_TRANSPORT.md`; `docs/setup/JEV_LOCAL_API.md`.

These rows describe capabilities and possible local data, **not** proof of actual collection by every installed user, live activation on all hosts, or a fully audited installed-host environment. The hashed storage directory is not a guarantee of anonymized record content.

## 3. Retention and deletion

- **A1 active data:** No globally enforced calendar retention period has been verified. Optional per-record expiry and the `prune_expired` API exist, but expiration is not a verified always-on scheduled purge. Records remain in the local environment until affected by explicit pruning, scoped deletion, or separate host/user action; this is an observed storage behavior, **not a promise that every integration retains indefinitely**.
- **Explicit A1 deletion:** `delete_scope` compacts the active JSONL record set, and generated profile state is invalidated by compaction. Source-backed local export is available through `export_bundle`. The export itself creates another local copy at a chosen destination, so users must manage their own exports.
- **A3, continuity, local backups and host snapshots:** No universal end-to-end deletion or backup purge guarantee is established. The system does not claim forensic secure erasure of deleted bytes, exports, backups, or disk snapshots.
- **Host/vendor data:** Any deletion, account closure, training opt-out, or provider retention settings of Codex, Antigravity, Claude Code, or their models are subject to that host/provider's own policies; Orchestra cannot truthfully promise host-side deletion.

The final Governor review must determine whether these observed behaviors and disclosures suffice for the intended release channels, or whether additional implementation or a concrete retention policy is required.

## 4. Sharing, disclosure, and security

No Orchestra-operated backend was declared by the owner for this release. This **does not** establish the absence of user-configured host providers, diagnostics, optional future backends, manual support submissions, or separate installed integration services.

The source includes scope validation, integrity checks, fail-closed routing, and sensitive-record restrictions. These protections do not guarantee that personal information cannot enter user-provided prompts, project files, host logs, local snapshots, or manual exports. Avoid copying credentials into prompts, tracked repositories, or memory exports.

## 5. Regional applicability and contact

- **GDPR/CCPA:** Applicability has not been established for the full user/jurisdiction mix; record as `MAY_APPLY_PENDING_REVIEW`, not automatically `N/A`.
- **Orchestra owner-operated contact/support/telemetry:** No separately verified service or responsible private-data contact is documented by this source-only audit. **Owner/operator disclosure channel and any actual support-data intake remain pending**. A public GitHub issue is not an appropriate destination for private personal-data submissions.
- **Independent host privacy notices:** The user's selected IDE, account, and AI provider terms apply separately to their services.

## 6. Review and publication status

**PENDING:** Governor review of local data/retention sufficiency; affected host activation and disclosures; owner-designated appropriate private contact if needed; jurisdiction screening; any required release Privacy Policy finalization. This draft is not evidence that all conditional privacy gates have passed. The v1.12.0 release and tag remain unpublished.
