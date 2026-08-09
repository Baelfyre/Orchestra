# Codex Adapter for Orchestra

This adapter provides a Codex-compatible export of the current Orchestra skills. The current published GitHub Release and repository metadata are `v1.2.0`.

## Purpose

Codex may reject extended frontmatter fields (like `role`, `activation_level`, etc.) in `SKILL.md`. It expects skill discovery to rely purely on simple `name` and `description` metadata.

This adapter exports Codex-compatible skills with only `name` and `description` in the frontmatter while preserving the original Markdown body, instructions, and progressive disclosure boundaries of the canonical skills.

## Release-Candidate Boundary

The `1.2.0` repository version corresponds to published annotated tag and GitHub Release `v1.2.0`. Accepted R7 live-host evidence is verified and reconciled locally in `docs/validation/R7_LIVE_INSTALLED_HOST_VALIDATION_EVIDENCE.md`; the repository simulation fixture remains pending/empty by design and is not live evidence.

## Note

- The canonical Orchestra skills remain the source of truth. They are metadata-rich and Markdown-first.
- This adapter is exclusively for Codex compatibility.
- It does not replace the Markdown-first framework.
