# Orchestra Pre-R8 Repository Hygiene Audit

## Disposition

```text
AUDITED_BASE_SHA=81ce2b440fc4e1091637045a7227f6192e93a042
README_RECONCILIATION=COMPLETE
TRACKED_FILE_CLASSIFICATION=COMPLETE
LOCAL_REMOTE_BRANCH_CLASSIFICATION=COMPLETE_AT_AUDIT_SNAPSHOT
FILE_DELETION_PERFORMED=false
BRANCH_DELETION_PERFORMED=false
RELEASE_EVIDENCE_REFRESH_REQUIRED_AFTER_HYGIENE_MERGE=true
R8_PUBLICATION=BLOCKED_REQUIRES_SEPARATE_HUMAN_AUTHORIZATION
```

The machine-readable inventory is [PRE_R8_REPOSITORY_HYGIENE_CLASSIFICATION.json](PRE_R8_REPOSITORY_HYGIENE_CLASSIFICATION.json). It records every tracked candidate path and every local or `origin` branch observed after a fresh fetch. Classification is evidence, not deletion authority.

## Tracked Files

The candidate contains 743 classified paths after this report is added:

| Classification | Count | Disposition |
|---|---:|---|
| `KEEP_ACTIVE` | 697 | Current source, tests, configuration, documentation, governed records, exported adapter surfaces, compatibility aliases, and the hygiene evidence. |
| `KEEP_HISTORICAL_EVIDENCE` | 46 | Source-pinned Artificer handoffs/reviews and prior release history. |
| `ARCHIVE_SUPERSEDED` | 0 | No path had sufficient evidence for a move. |
| `DELETE_PROVEN_STALE` | 0 | No tracked path met the deletion proof threshold. |
| `CONSOLIDATE_DUPLICATE` | 0 | Identical blobs alone did not prove redundant ownership. |
| `REVIEW_REQUIRED` | 0 | Every path received a conservative evidence-backed disposition. |

Exact adapter/source mirrors and legacy-named icons are retained because repository export and alias contracts establish active compatibility roles. Hash equality is not proof that one path is removable.

## Branches

The audit snapshot contains 313 classified refs: 118 local branches and 195 `origin` branches.

| Classification | Count | Disposition |
|---|---:|---|
| `KEEP_ACTIVE` | 10 | Local and remote `main`, plus every branch checked out by a registered worktree. |
| `KEEP_HISTORICAL_EVIDENCE` | 20 | Unique-commit refs, release-history refs, the recovery backup, and the autonomous-run archive. |
| `DELETE_PROVEN_STALE` | 283 | Classification candidates only: tips are fully reachable from `origin/main`, have no unique commits, no active worktree, no open PR, and no protected recovery or release role. |
| all other categories | 0 | No branch met another disposition at this snapshot. |

No branch is deleted by this change. Before any separately authorized deletion, a fresh canonical read must prove all of the following at once: the ref is not `main`; is not the recovery backup or autonomous-run archive; is not an open PR head; is not used by a worktree; has zero commits unique to current canonical `main`; is reachable from current canonical `main`; and has no release or recovery-history role. Any missing, stale, or contradictory evidence blocks deletion.

Mandatory preserved refs include:

- `main`;
- `origin/backup/main-pre-v1.2-autonomous-2026-08-07`;
- `origin/archive/autonomous-run-2026-08-07-pre-rollback`;
- every active-worktree branch listed in the machine-readable inventory;
- every open PR branch, if one exists at the exact deletion-time read;
- every branch with commits unique to canonical `main`;
- every `release/*` history branch.

## Provenance and Acknowledgements

Repository evidence proves three external-source reviews relevant to README acknowledgement:

- Spec Kitty at `8466727ebbbc01fcaf43575657c9b1b9553784d9`: selected concepts were independently adapted; promotion records state that no code was copied and reject direct field/state-machine copying and external dependency adoption.
- OpenHero at `16ffaa7e6dc39eb390011d81c420353b5d1dbaff`: static source review and governance decisions only; no source execution or copying, no promotion claim, and no media or dependency reuse.
- Strix at `09872744f5a9d3ffad750478f823e656ac1a7c88`: four concept-only promotions are `IMPLEMENTED`; the records expressly prohibit source, prompt, payload, example, media, and documentation-expression reuse.

No Artificer provenance record proves wholesale integration, endorsement, affiliation, copied schemas, dependency adoption, or blanket license permission. The README therefore makes none of those claims.

## Release and Host Boundary

R7 and R7R are `MERGED_VERIFIED`. GA-0 through GA-7 are `MERGED_VERIFIED`. Codex and Antigravity have accepted R7 live-host evidence. Claude Code remains `SCAFFOLD_ONLY`, and active Claude runtime continuity is not claimed. Repository fixtures remain simulation-only and pending/empty by design.

The latest public release remains `v1.1.2`; `v1.2.0` remains `PREPARED_NOT_RELEASED`. Merging this hygiene revision changes the candidate SHA and invalidates earlier revision-bound release-readiness evidence. Full canonical validation and a refreshed `docs/validation/V1_2_0_RELEASE_READINESS_EVIDENCE.md` record are mandatory before returning to the R8 human gate.
