# Codex Adapter for Orchestra

This adapter provides a Codex-compatible export of the current Orchestra skills. The current published GitHub Release is `v1.5.0`; repository `main` may contain post-release candidate work without moving that immutable release.

## Purpose

Codex may reject extended frontmatter fields (like `role`, `activation_level`, etc.) in `SKILL.md`. It expects skill discovery to rely purely on simple `name` and `description` metadata.

This adapter exports Codex-compatible skills with only `name` and `description` in the frontmatter while preserving the original Markdown body, instructions, and progressive disclosure boundaries of the canonical skills.

## Host update planning

Codex is a supported Host Update maturity target. Generate the deterministic read-only plan with:

```text
python scripts/host_update.py --host codex --json
```

The plan may describe the existing fast-forward repository update and Codex validation path, but it never refreshes or reinstalls the active Codex integration. Installed-host mutation requires separate explicit authorization. See `docs/setup/HOST_UPDATES.md`.

## Note

- The canonical Orchestra skills remain the source of truth. They are metadata-rich and Markdown-first.
- This adapter is exclusively for Codex compatibility.
- It does not replace the Markdown-first framework.
