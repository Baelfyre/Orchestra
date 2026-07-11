# Codex Adapter for Orchestra

This adapter provides a Codex-compatible export of the Orchestra `v1.1.1 Post-Release Hardening` skills.

## Purpose

Codex may reject extended frontmatter fields (like `role`, `activation_level`, etc.) in `SKILL.md`. It expects skill discovery to rely purely on simple `name` and `description` metadata.

This adapter exports Codex-compatible skills with only `name` and `description` in the frontmatter while perfectly preserving the original Markdown body, instructions, and progressive disclosure boundaries of the canonical skills.

## Note

* The canonical Orchestra skills remain the absolute source of truth. They are metadata-rich and Markdown-first.
* This adapter is exclusively for Codex compatibility.
* It does not replace the Markdown-first framework.
