# Codex–Sinag end-to-end workflow acceptance pilot

**Record:** EXPERIMENT_PROTOCOL_PREPARED; LIVE_CODEX_NOT_RUN
**Date:** 2026-10-15 (Asia/Manila)
**Orchestra baseline:** `d619deb51c4184f034f0986bc342ca6d447b1ecf`
**Sinag baseline:** private `Baelfyre/Sinag`, `main` at `2b6b611fa39418777a3e3353adcde64e5d3a8eee`
**Project scope:** Sinag main/home page only for UI; Sinag existing product documentation for Scribe; synthetic scoped data for memory and offline JEV.
**Authority:** Preparation and read-only analysis now; local Codex execution requires the user to start the host. No PR merge, Sinag production change or release is implied.

## Hypothesis

Orchestra should improve source-grounded documentation and disciplined UI development *without* sacrificing child safety, educational accuracy, accessibility, local-first privacy, recoverable progress, or Sinag's approved design language. Test real skill invocation and usefulness separately from deterministic source-contract tests. Absence of an integration is `NOT_WIRED`, not `PASS`.

## Preflight

1. Fetch live `origin/main` for both repositories and pin exact commits/trees. Verify source is current; report and resolve drift before the experiment. Never reuse a dirty primary worktree.
2. Check Codex version, model, reasoning setting, available skill names, workspace root, browser/screenshot capability and permissions. Record Impeccable's exact installed source/version; `skills-lock.json` in Sinag lists TypeSafe AI but does **not** demonstrate Impeccable installation.
3. Run the relevant existing Sinag tests and content validator *before* editing. Capture a source-bound baseline in an isolated local test folder.
4. If browser access is authorized and available, capture main-page screenshots and interaction evidence at 375px and 1280px, plus keyboard, focus, reduced motion, enlarged text, light/paper/night and high-contrast states. A historical 2026-09-28 UI report recorded no overflow at 375px/1280px; do not copy this historical result as current proof.
5. Work in separate disposable local worktrees/sessions; never write learner data, credentials, or raw private Sinag code/screenshots to public Orchestra or Padayon logs.

## Main test sequence — proposal before execution

### Stage A — Scribe as-built documentation baseline (READ_ONLY)

- Input: Sinag `README.md`, `README.json`, `index.html`, CSS/JS entry, `docs/governance/PRIME_DIRECTIVE.md`, `docs/governance/DEVELOPMENT_STANDARDS.md`, `docs/governance/UI_SPACING_BASELINE_V1.md`, relevant feature docs, tests, and actual current behavior.
- Mode: `SYSTEM_TO_DOCS`; use `RECONCILE` for conflicts. Produce **one reusable six-dimension coverage matrix**, not six compulsory files.
- PRD: approved educational intent, audiences, scope, privacy/child safeguards, acceptance criteria. TRD: actual stack, runtime, integration and constraints. Application flow: observed onboarding, home navigation, practice and parent handoffs. Design brief: approved semantics, tokens, accessibility and responsive states. Data schema: local progress storage, backed-up data and content boundaries. Implementation plan: minimal proposed refinements, owners and qualification.
- Every statement names source path/revision, status (`PROPOSED`, `APPROVED`, `IMPLEMENTED`, `VALIDATED`, `MISSING_EVIDENCE`, `UNRESOLVED`), specialist fact owner, and relevant requirement/acceptance ID if actually present.
- Compare with a same-model plain Codex reconstruction. Independently score factual precision, drift detection, correct abstention, unnecessary document creation, token/time only if measured, and authority separation.

### Stage B — UI diagnosis: independently attributed findings (READ_ONLY)

- Freeze current Sinag home-page DOM/rendered baseline. Cloak reviews the actual learner experience, information hierarchy, child-appropriate wording, navigation, keyboard and responsive states, accessibility and design-token conformance.
- If independently installed and permitted, Impeccable runs its own `critique` and `audit` focused on the same page. Record exact skill invocation, detector output, version and any non-LLM checks. Do not automatically install, initialize, run hooks, or mutate Sinag files.
- Separately label `CLOAK`, `IMPECCABLE`, `BOTH`, and `DISPUTED`. Verify each claim against DOM, screenshots or reproducible interactions; severity follows user impact, not number of findings.
- Do **not** seed the test with fictitious defects: historical main page validation passed mobile/desktop overflow and specific keyboard behavior. Current evidence determines whether those still pass.

### Stage C — proposed implementation packet (NO SOURCE MODIFICATION)

- Scribe consolidates a `PROPOSED`, source-backed packet with: problem, before-state, expected benefit, affected paths, requirement IDs, impact and non-goals, exact UI changes, design tokens, behavioral states, data/privacy implications, test coverage, owner attribution, and rollback path.
- Cloak owns UI requirements; Impeccable contributes separately attributable critique; Clockwork/Chronicler/Cipher own architecture/data/security facts where materially implicated; Overseer defines verification; Ponytail owns implementation only after admitted authorization.
- Produce at least two viable alternatives when supported, including `NO_CHANGE` as an eligible option when the baseline already satisfies requirements. No option is promoted to approved solely from documentation completeness.
- Make a decision table containing alternative, positive/negative evidence, objective risks, unknowns, affected contracts, reversibility and proposed acceptance test.

### Stage D — JEV adjudication (OPTIONAL, NON-AUTHORIZING)

- Review the independently prepared Cloak/Impeccable recommendations and their disagreements after verification, risk assessment and mitigation alternatives are identified.
- The post-mitigation JEV adapter is optional. JEV responsibility-routing is currently an **offline contract without a production Conductor caller**. The user-owned TypeSafe provider BYOK setup is not live-qualified. Do not make a real provider/API call, solicit keys, or claim live JEV judgment absent an explicitly qualified, approved route.
- If JEV is unavailable, record `NOT_WIRED` or `NO_ADVICE`, and preserve the verified comparison for human decision. If an authorized offline JEV contract simulation is used, label it `OFFLINE_SIMULATION`, not a real provider's judgment.
- JEV may weigh alternatives and abstain but may not change governance, override Sinag's Prime Directive, resolve specialist authority by itself, execute patches, or grant release approval.
- Test a stale-source or contradictory-evidence negative case; advice must be rejected, refreshed or qualified rather than reused as current.

### Stage E — controlled local implementation (SEPARATE GO DECISION)

- **Stop at `PROPOSAL_READY_FOR_REVIEW`** until the user approves a specific Sinag candidate and bounded local edit scope. That user decision occurs after Stages A–D, before touching implementation source.
- When approved, implement the chosen option only in a disposable Sinag worktree; do not modify `main`, learner-content truth, content review metadata, actual local progress or protected governance records.
- Run Sinag source tests, content validation, syntax and relevant accessibility/browser checks. Capture before/after images for every supported viewport/theme plus regressions for child flow, keyboard, focus and no-overflow.
- Show exact diff and defect/benefit measurements to the user. No push, merge, deployment or public release without separately satisfied qualifications and explicit authorizations.

### Stage F — Scribe documentation reconciliation and evidence (READ_ONLY until approved changes)

- Ask Scribe to reconcile the accepted change with existing requirements, design brief, flow, and README.md / README.json pairing when product scope or documented claims changed.
- Preserve implemented vs validated status and unapproved/future states; do not create six redundant documents. Verify crosswalk against actual post-change source, test evidence and owner decisions.
- Repeat the same source fact/traceability rubric as Stage A. Record whether the new workflow correctly updated only affected documentation.

## Adaptive memory sidecar (synthetic only)

- Test A1 scoped explicit preference, A2 opt-in read-only context, A3 shadow candidate conflict with a current instruction, and unavailable D3B capability producer. Never use child profiles or Sinag production learner history.
- Explicit user direction must dominate inferred preference; no cross-user/project leak; no silent execution/routing promotion. If the local Codex bridge is not wired, record `NOT_WIRED` and distinguish deterministic offline tests from live memory.

## Evaluation and stop criteria

- One frozen attempt per arm first. Compare plain Codex vs Orchestra Scribe and Cloak-only vs Cloak+Impeccable only when host, model, source and task are matched. Valid unfavorable results are preserved, never re-prompted away.
- Per-case rubric, 0–2 each: activation correctness, factual grounding, specialist contribution, actionable/reproducible quality, scope/efficiency. Report `/10` with evidence; do not claim statistical benefit from one run.
- Hard stop on child privacy leakage, account/telemetry addition, wrong content approval, unsafe source modifications, token/design-system violations without approval, missing required evidence, unexpected outbound/paid call, unapproved dependencies, false evidence, or JEV implied execution authority.
- Use `PASS`, `FAIL`, `PARTIAL`, `INCONCLUSIVE`, `NOT_RUN`, `BLOCKED`, `NOT_WIRED`, `NOT_INSTALLED` distinctly. `NOT_RUN` must never become `PASS` from expectations or previous CI.
- Capture actual command logs, host/skill identity, source/head/tree, input/fixture hashes, rendered screenshots, reviewer, latency/token counters if trustworthy, true/false positives, duplicate findings, disposition and next owner. Do not expose full private Sinag source or user data through public evidence repositories.

## Outcome routing

- Detailed test receipts remain in the private Sinag test workspace or a scoped private evidence branch. Orchestra records sanitized integration/effectiveness evidence with links and exact revisions. Padayon records the cross-project conclusion, decision rationale, blockers, and proposed follow-up.
- If only some workflows run, state which are source-qualified versus host-qualified. Regressions require minimal, separately authorized repair work and follow-up tests.
- Release qualification is separate. A passing Sinag pilot cannot qualify unrelated Orchestra changes or authorize new version publication.

## First local pilot observation — 2026-10-15

**Disposition:** `SINAG_PROPOSAL_READY_FOR_IMPLEMENTATION_DECISION`; implementation **not authorized**, no Sinag source changed. This is an observed first-pass report, not a claim of host-wide effectiveness or release readiness.

**Evidence integrity:** private 18-record JSONL ledger independently SHA-256 verified as `6D7461514995629DF9BBF2A8E8A6781019F299D8048366B71ED8C004134CC188`. The local evidence bundle and its detailed receipts are not reproduced in this public record. Source identities: Orchestra `d619deb51c4184f034f0986bc342ca6d447b1ecf` (tree `ba54d6d7d9f9a96e716e99da647dfe5beee28a98`); private Sinag `2b6b611fa39418777a3e3353adcde64e5d3a8eee` (tree `63bcf1151d811be73ae8125a0e58d25e128b1c94`).

| Track | Observed finding | Evidence limitation |
| --- | --- | --- |
| Baseline | Six Sinag validators passed; Node suite 294 passed, zero failed | Local Node 24.14.1; project CI pins Node 22 |
| Scribe | Manual source-guided reconciliation recorded documentation drift and unresolved decisions | Native Codex skill activation unobserved; comparative baseline contamination and uncalibrated scores prevent causal benefit claim |
| Home/Cloak | Keyboard, two viewport sizes, themes, enlarged text and reduced motion exercised; zero confirmed UI defects; NO_CHANGE proposed | Screenshot bytes not retained, so independent visual inspection incomplete |
| Impeccable | Manual guide assessment raised one reduced-motion question; reconciliation: DISPUTED / NEEDS_VERIFICATION | Target 4.5.0 engine/detector unavailable; no live plugin execution |
| JEV | Eleven offline contract tests passed; `NO_ADVICE` | No live provider route, no independent live judgment |
| Memory | Eleven synthetic contract checks reported passing across four cases; scope and authority boundaries preserved | MEM-A standalone smoke failed before import (`ModuleNotFoundError: No module named orchestra_runtime`); real Codex memory injection/D3B unobserved |
| Action controls | T04 proposal contained `NO_CHANGE` and evidence-only option; T06/T07 not run; no Sinag changes | Neither alternative is authorization to implement |

**Run accounting:** eight configured `gpt-6-luna` assessment dispatches at max reasoning; one Scribe route acknowledgment counted conservatively as another run unit; 9/12 units, zero retries. Root-thread model telemetry, timeouts and token/cost counters unavailable. `configured` is not a proof of the exact executing model in each output.

**Reviewer recommendation (not yet recorded as human authorization):** select `T04-B` for a **single bounded read-only Sinag Home reduced-motion/state-feedback evidence check**, retaining permitted sanitized screenshot bytes and interaction/focus receipts for independent inspection. Until confirmed otherwise, keep **`NO_CHANGE` as the default code disposition**. No UI patch is justified by the first pilot. T04-B does not authorize edits, plugin downloads, provider calls, PR merge, or release. Any demonstrated defect requires separate exact-path implementation proposal and user decision.

**Separate follow-up gaps:** product owner to reconcile README/source descriptions of navigation, language-pair direction, Shape Words status, progress wiring, accessibility and deployed URL; repair MEM-A import-context harness in a fresh bounded test authorization; verify Node 22 parity. No release qualification is claimed.
