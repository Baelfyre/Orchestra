# Historical Assurance Exact-Scope Exceptions

## Purpose

This policy allows a human-approved integration scope to be separated from historical AQ5, AQ7, and PRAI implementation inventories when those historical inventories do not describe the current integration work.

It does **not** bypass current validation. It only answers whether the historical exact-scope implementation inventories apply to a complete, separately approved integration set.

## Issue #937 F1/F2 integration

Human governance approved the exact PR #939 F1/F2 integration inventory on 2026-10-09.

The registered scope is stored in `machine/governance/historical-assurance-scope-exceptions.v1.json` as `ISSUE_937_F1_F2_INTEGRATION` and is bound for audit purposes to:

- approved base: `77603f68af5476dd39c6a4febf0284d06e115d40`
- reviewed source head: `6caa0bf7cb8a13f868d17c0bab76457432f3cc18`
- PR: #939
- exact inventory: 47 paths

For AQ5, AQ7, and PRAI historical scope classification:

- the complete registered 47-path set is `NOT_APPLICABLE` to those historical implementation inventories;
- a partial registered set remains `APPLICABLE`;
- a superset remains `APPLICABLE`;
- a mixed scope remains `APPLICABLE`;
- adding any F3/JEV path remains `APPLICABLE`;
- duplicate or unsafe paths fail closed.

## Authority boundary

This policy is human-owned protected governance. The registration does not grant or imply:

- validation success;
- branch-coverage exemption;
- merge authority;
- F3 execution or JEV/TypeSafe authority;
- provider, telemetry, production, or deployment authority;
- release authority;
- permission to alter or weaken other assurance thresholds.

The current validation and governance gates continue to apply after historical-scope separation.
