# Codex Adapter for Orchestra

This adapter provides a Codex-compatible export of the current Orchestra skills. Repository release-candidate metadata is `1.2.0`; the latest public GitHub Release remains `v1.1.2` until the separate publication gate completes.

## Purpose

Codex may reject extended frontmatter fields (like `role`, `activation_level`, etc.) in `SKILL.md`. It expects skill discovery to rely purely on simple `name` and `description` metadata.

This adapter exports Codex-compatible skills with only `name` and `description` in the frontmatter while preserving the original Markdown body, instructions, and progressive disclosure boundaries of the canonical skills.

## Release-Candidate Boundary

The `1.2.0` repository version is preparation metadata, not proof of a published release or installed-host parity. R7 live-host evidence and the separate R8 tag/GitHub Release gate remain required before `v1.2.0` is represented as published.

## Note

- The canonical Orchestra skills remain the source of truth. They are metadata-rich and Markdown-first.
- This adapter is exclusively for Codex compatibility.
- It does not replace the Markdown-first framework.
