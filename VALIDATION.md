# Validation

1. Run `scripts/validate-structure.ps1` or `scripts/validate-structure.sh`.
2. Run `scripts/check-stale-references.ps1` or `scripts/check-stale-references.sh`.
3. Confirm every skill folder contains `SKILL.md` and required support files.
4. Validate local Markdown links and balanced code fences.
5. Scan for private names, local paths, emails, secrets, unsupported compliance claims, and project-specific examples.
6. Confirm Amalgam Conductor routes UI, documentation, diagrams, databases, QA, security/privacy, and gated resilience correctly.
7. Confirm Acme Overseer owns normal QA and Cipher Meister owns normal security/privacy review.
8. Confirm Hidden Dagger is not automatic, requires a safety gate, excludes production and real user data, and provides defensive guidance only.
9. Confirm external tools are not bundled and adapter guides avoid unsupported native-compatibility claims.

Run the official skill validator supplied by your Codex installation against each `skills/*` folder when available.

## Expected output

Successful structure validation:

```text
Structure valid: 8 skills, 5 adapters, 7 templates.
```

Successful stale-reference validation:

```text
No stale or disallowed references found.
```

On failure, the structure scripts print `Missing: <path>`. The stale-reference scripts print `<path>:<line>: <matching text>`. All validators exit with status 1 when findings exist.
