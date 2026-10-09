# Codex Adapter Installation Guide

To install the Codex-compatible exported skills, we highly recommend a repository-local installation rather than modifying your global `.codex` environment.

## Repository-local installation
Install the skills directly into your project's local agent folder:

`.agents/skills/`

**Example target:**
`C:\+Term3\ProjectAOOP_Group4\.agents\skills\`

By using this approach, you ensure that the skills are scoped only to the relevant project, avoiding pollution of `C:\Users\ongoj\.codex`.

## Automated Install
You can use the provided `install-to-repo.ps1` script to automate this local installation. See the script source for usage details.
