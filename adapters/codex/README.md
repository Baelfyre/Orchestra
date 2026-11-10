# Kontrolled Kaos on Codex

This adapter provides a Codex-compatible export of the established specialist skills. Kontrolled Kaos is the public product identity; Conductor remains the internal routing specialist. Release and publication status remains governed separately in the [release records](../../docs/reference/releases/README.md).

## Purpose

Codex may reject extended frontmatter fields (like `role`, `activation_level`, etc.) in `SKILL.md`. It expects skill discovery to rely purely on simple `name` and `description` metadata. The product alias `$kaos` is packaged separately from the 14 canonical specialist skills.

This adapter exports Codex-compatible skills with only `name` and `description` in the frontmatter while preserving the original Markdown body, instructions, and progressive disclosure boundaries of the canonical skills.

## Host update planning

Codex is a supported Host Update maturity target. Generate the deterministic read-only plan with:

```text
python scripts/host_update.py --host codex --json
```

The plan may describe the existing fast-forward repository update and Codex validation path, but it never refreshes or reinstalls the active Codex integration. Installed-host mutation requires separate explicit authorization. See `docs/setup/HOST_UPDATES.md`.

## Note

- The canonical skills remain the source of truth. They are metadata-rich and Markdown-first.
- This adapter is exclusively for Codex compatibility.
- It does not replace the Markdown-first framework.
