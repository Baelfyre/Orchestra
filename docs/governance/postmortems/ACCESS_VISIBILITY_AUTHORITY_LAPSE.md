# Postmortem: Access / Visibility Authority Lapse

**Issue:** ReportAccessPolicy authority model mismatch in MotorPH project

## What Happened
The workflow proved the access rule in abstract but did not prove it against actual seeded personas. The failure was a data-model mismatch, not just a code bug.

- `ReportAccessPolicy.java` originally relied on permission or active direct reports.
- Seed data mapped specific users (e.g., `10012` as `Payroll Team Leader`), but the database gave `10012` no direct reports and no approval permissions.
- The policy was internally consistent but missed the expected business persona.
- The current fallback uses `User.department` as a leadership-title signal, which is a temporary heuristic rather than an authoritative permission.

## What Was Missed
The main lapse was not implementation speed, but **verification scope**. The validation did not require proof of the actual named personas.

## Corrective Actions
1. **Persona Validation Gate**: Signoff now requires testing concrete named accounts (e.g., `10012`), not only generic unit cases.
2. **Data-vs-Policy Checkpoint**: Conductor explicitly classifies failures as bad seed data, missing permission mapping, missing reporting-chain mapping, or real policy gaps before routing to implementation.
3. **Route Proof Plus Visibility Proof**: Validation must confirm both UI visibility and backend routing separately.
4. **Named-Persona Regression Test**: Behavior testing matrix must include seed-style cases (e.g., leadership title, payroll role, no direct reports).
5. **Arbiter Hold**: Arbiter will hold task closeout if access tasks depend on seed assumptions that are unverified.

This case study enforces a stronger persona-based validation process to replace broad implementation heuristics.
