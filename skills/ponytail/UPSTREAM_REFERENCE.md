# Upstream Ponytail Reference

## Purpose

Preserve provenance and sync boundaries for the Ponytail specialist without making the external repository an implicit authority over Orchestra.

## Source Lineage

Orchestra's Ponytail role was incorporated from the Ponytail project and then adapted to Orchestra's specialist ownership, governance, validation, handoff, and host-packaging contracts.

Upstream source repository:

`DietrichGebert/ponytail`

Maintainer fork used during earlier Orchestra incorporation:

`Baelfyre/ponytail`

License reported by the upstream/fork repository: MIT.

## 2026-08-12 Upstream Checkpoint

At the start of Orchestra Specialist Knowledge Layer phase SK1:

```text
Baelfyre/ponytail main
14a0d79548d4de8fc2de95c1b94bb0de63a739d3
package 4.8.4

DietrichGebert/ponytail main
2ed6c52c9d7e5e56942508591085fd45dea277d3
package 4.9.0

skills/ponytail/SKILL.md blob at both revisions
02c0712c86277d49d18a77da3a2b825657bf02d1
```

The package-level upstream delta after the fork checkpoint included host-adapter, compatibility, packaging, and release work. The core Ponytail `SKILL.md` blob was unchanged between those two revisions.

## SK1 Disposition

Do not import the upstream repository wholesale into Orchestra.

Retain these useful Ponytail principles:
- question speculative work through YAGNI;
- inspect before editing;
- reuse code already present in the repository;
- prefer standard-library and native-platform capabilities;
- avoid unnecessary dependencies and abstractions;
- fix shared root causes rather than repeated symptoms;
- keep the implementation diff as small as correctness allows;
- leave a focused check for non-trivial changed logic.

Orchestra adds stronger requirements that remain authoritative:
- specialist ownership boundaries;
- cross-layer contract gating;
- evidence-bound validation;
- exact-head continuity;
- explicit external-action authority;
- security, persistence, UI/UX, QA, and governance handoffs;
- portable adapter parity.

## Future Sync Rule

When checking upstream Ponytail again:

1. identify the true upstream repository and current main/tag;
2. compare the last reviewed upstream revision with current upstream;
3. inspect core skill/intelligence changes separately from packaging/adapter changes;
4. classify each relevant delta as concept, instruction, runtime code, test, packaging, or documentation;
5. import only improvements that fit Ponytail's Orchestra role and do not conflict with Orchestra governance;
6. preserve attribution/license obligations when copying source text or code;
7. run the full Orchestra validation workflow after any accepted integration.

A newer upstream version does not automatically make Orchestra stale, and an unchanged core skill does not prevent Orchestra-native specialist improvements.
