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

## T04-C local UI prototype — independent screenshot review (2026-10-15)

**Status:** `PROTOTYPE_GEOMETRY_VERIFIED; HUMAN_VISUAL_ACCEPTANCE_PENDING; MINOR_REFINEMENT_RECOMMENDED`. This is a new experimental worktree variant, not a production change, merged candidate, or proof that JEV/Impeccable executed.

At frozen private Sinag source `2b6b611fa39418777a3e3353adcde64e5d3a8eee` (tree `63bcf1151d811be73ae8125a0e58d25e128b1c94`), a disposable worktree changes only `src/js/app.js` by moving existing `.hero-actions` from below the lead paragraph to directly below the greeting. No labels, routes, or instructional copy are changed. Diff SHA-256 `2253A1263B230738192C38D36009F50AE4769124664E3BA8B9A7AE75227974D0`. No code commit, push, merge or deployment reported.

| Captured view | Action group start before → after | Movement | Lead/action gap before → after |
| --- | --- | --- | --- |
| Mobile 375×812, light/night | 364.3125 → 237.25 px | 127.0625 px upward | 16 → 0 px |
| Desktop 1280×900, light/night | 414 → 342.46875 px | 71.53125 px upward | 16 → 0 px |

An independent inspection of the eight supplied neutral before/after PNG files verified every PNG SHA-256 against `t04c-visual-comparison.json` and the after manifest (zero mismatches). Their side-by-side visual comparison shows greater CTA prominence but cramped separation between the action block and descriptive paragraph; the computed bounding boxes are directly adjacent. The existing `.hero-copy .lead` CSS supplies bottom margin, not margin above a preceding CTA. Treat this as a **visual-polish issue**, not a proven child comprehension or WCAG failure. Consider restoring separation using an *existing approved spacing token*, followed by four-view screenshot recapture; do not introduce one-off pixel literals.

All 294 Node tests passed, and the reported syntax, whitespace, route, focus, reduced-motion and narrow/desktop overflow checks passed. The actual retained Node test log ends `pass 294, fail 0, skipped 0`; its SHA-256 is `8F66F538ED80E8CEFA99C99398C6B9E60B4D3D4076F9156363AE0344C42BA4A2`. Screenshots rendered Google Fonts icon ligatures as words because remote font requests were intentionally blocked; this affects visual representativeness and is not attributable to the one-line action-order change. No formal axe/WCAG scan or learner preference/comprehension test was supplied.

The follow-up Impeccable context step was reported to succeed, but attempted `audit` exited 1 with `Unknown command`; **no detector result** exists. The earlier Cloak/Impeccable assessments were baseline-only, not post-change independent reviews; Orchestra routing acknowledgments were not substantive specialist judgments. JEV was not called. Accordingly the experiment shows a correct **directed layout mutation** and regression-test continuity, not demonstrated incremental effectiveness of Cloak+Impeccable collaboration or JEV.

**Proposed next action, not automatically authorized:** local revision R1 confined to the original disposable Sinag worktree, scoped spacing around `.hero-actions + .lead` with approved semantic spacing token, capture new actual screenshots under icon-font-available and separately offline conditions, check keyboard/visual rhythm and obtain human visual decision. Keep original variant and unfavorable evidence. No merge, release or activation follows.

**Evidence handling:** raw PNGs, interaction receipts, and all local paths stay in the private evidence bundle. Audit indices: `t04c-visual-comparison.json` SHA-256 `271EEE71F449DD4185C4214D8ECE5415E1AD2C0CE5E58F6F75AC4F3BF7664A56`; `after-interaction-evidence.json` SHA-256 `9B736170806836F5ADFDEEB86EB92E687468DAEE73165D5A06B150DC3C764B37`. No private learner data was used (synthetic `Pilot`).

## T04-C R1 completed local refinement — evidence review (2026-10-15)

**Status:** `VISUAL_REVIEW_RECOMMENDS_R1; HUMAN_ACCEPTANCE_NOT_RECORDED; NO_MERGE`. Based on an independently inspected user-supplied private `T04C_R1.zip` bundle. The private prototype remains uncommitted in an isolated Sinag worktree. The observation is not production UI acceptance.

**Frozen Sinag baseline:** commit `2b6b611fa39418777a3e3353adcde64e5d3a8eee`, tree `63bcf1151d811be73ae8125a0e58d25e128b1c94`. **Final prototype diff:** SHA-256 `13399474b0980e4230793ece7e235f2d0bfabb69c65ff444fd01f57672564aa5`. Only `src/js/app.js` (previous P0 action reorder) and `src/css/components/core.css` (R1 adjacent lead spacing rule) differ from the baseline.

- Original → P0 → R1 actual screenshots were supplied for 375×812 and 1280×900, Light and Night. The preserved 16px `--space-3` margin separates the action block from the lead while maintaining the earlier CTA elevation: 127.0625px mobile and 71.53125px desktop. A reviewer inspection considers R1 more clearly grouped than P0; visual preference/comprehension of real learners was not measured.
- **Evidence verification:** 23 manifest/report/log/PNG SHA-256 values in the supplied report independently matched the ZIP contents. The screenshot comparison files are private and not attached here.
- **Engineering:** actual retained Node v22.23.2 and v24.19.0 logs show 294 pass, zero fail for each. Recorded HTML, CSS, JS syntax, content, registry sync (read-only), governed spacing and `git diff --check` pass. Synthetic/local Edge browser checks covered routes and return navigation, Tab and Shift+Tab, focus-visible, reduced-motion, enlarged text, and no horizontal overflow at the tested two sizes and two themes.
- **Specialists:** an independently supplied Cloak `QUICK_UI_HANDOFF` describes no material regression, but no separate signed/hash-addressable specialist artifact was supplied; Orchestra MCP `cloak` returned routing acknowledgment only. The Impeccable 4.5.0 skill is present, local engine help exposes `detect`, but that detector was **not run**; prior `audit` returned `Unknown command`. JEV was unavailable and **not called** (`NO_ADVICE`). No claim of multi-specialist causal improvement is established.
- **Remaining limits:** Google Fonts was blocked by the loopback-only capture, so icon ligature words are visible and production-font appearance was not tested. No axe/WCAG/screen-reader assessment or user testing; no release readiness. The prototype only demonstrates a correct limited layout transformation and tested regression preservation.

**Recommendation, not human authorization:** retain R1 as the preferred local visual candidate over P0, but first verify font/icon rendering in an approved controlled environment, review the final image and decide whether to accept the prototype. Do not silently install external tools, run paid JEV, edit Sinag `main`, push, merge or release. Document observed skill contributions separately from route acknowledgments. Existing `T04-B` reduced-motion concern remains unproven unless reproduced.
