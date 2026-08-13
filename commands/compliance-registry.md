---
name: compliance-registry
description: "Manage and inspect the verified local Orchestra Compliance Registry cache."
---
# Compliance Registry Command

Use `scripts/compliance_registry.py` for deterministic registry lifecycle operations.

Supported actions:
- `status`: inspect the active local registry without network access
- `verify`: revalidate active manifest identity and file hashes without network access
- `sync`: fetch the latest non-draft, non-prerelease trusted release from `Baelfyre/Orchestra-Compliance-Registry`, verify it as a candidate, enforce anti-rollback, then atomically activate it
- `install`: verify and activate a local registry ZIP for air-gapped or pre-downloaded use
- `query`: read source and obligation records from the verified active local cache
- `pin`: write `.orchestra/compliance.lock.json` for exact project registry identity and selected jurisdictions/providers
- `update-check`: perform a lightweight network check for a newer trusted release

Normal Governor and Steward review should query the verified local cache rather than repeatedly reading the remote repository. Registry content is knowledge and evidence, not execution authority, legal advice, release authority, or policy activation.
