# Kontrolled Kaos Codex Installation Guide

The preferred setup is the Kontrolled Kaos marketplace package. The existing `conductor@orchestra` package keys remain for compatibility, and `$kaos` is the new skill entry point. This guide covers the repository-local fallback only.

## Repository-local installation
Install the skills directly into your project's local agent folder:

`.agents/skills/`

**Example target:**
`C:\+Term3\ProjectAOOP_Group4\.agents\skills\`

By using this approach, you ensure that the skills are scoped only to the relevant project, avoiding pollution of `C:\Users\ongoj\.codex`.

## Automated Install
You can use the provided `install-to-repo.ps1` script to automate this local installation. See the script source for usage details.
