# Orchestra ecosystem Guidelines

When operating within this repository or when this plugin is active, adhere to the following routing and execution guidelines:

1. **Governance Layer**: `The Steward` (business alignment, scope, SDLC) and `The Governor` (legal, compliance, privacy, IP, licensing) sit above the Conductor. Governance review is dynamic, need-based, and adapts to the active operating mode (Ideation, Prototype, Implementation, Audit, Release). The Conductor cannot override governance decisions.
2. **Routing Layer**: `Conductor` is the exclusive router and workflow orchestrator. Do not invent custom subagent chains or bypass the Conductor for complex tasks.
3. **Implementation Layer**: `Ponytail` handles focused implementation, strictly keeping code minimal, reversible, and free of over-engineering.
4. **Communication Layer**: `Caveman` controls output compression to preserve context limits during long multi-file operations.
5. **Domain Specialists**: Specialists (`Clockwork`, `Cloak`, `Cipher`, `Chronicler`, `Weaver`, `Scribe`, `Overseer`, `Dagger`) exclusively own their respective domains.
6. **Source of Truth**: Do not guess specialist logic or rules. The authoritative source of truth for any skill's behavior is always located in its corresponding `skills/*/SKILL.md` file. Always defer to the explicit instructions in those files.
7. **Local Sync Preflight Rule**: Before starting a new local development phase or repository-editing session, run `python scripts/preflight_sync_check.py` against `origin/main`. Do not begin edits if the local branch is behind, diverged, dirty, or unverifiable. Ahead-only state may proceed, but the unpublished commits must be reported.

## Repo Source vs Runtime Rule

Apply persistent project updates only to Git-tracked repo source paths. Do not treat `.agents/`, generated runtime copies, installed adapter copies, cache folders, or local execution mirrors as the source of truth. Before editing, verify the target file path is inside the tracked repo source and not inside `.agents/`. If a task touches skill files, update `skills/<skill>/...` in the repository source, not `.agents/skills/<skill>/...`. Runtime copies may be inspected for comparison, but persistent fixes must be applied to the Git-tracked source.
