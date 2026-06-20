# Local-Only Guide

For local AI model loading instructions, see [adapters/local-ai/](adapters/local-ai/README.md).

- Keep experimental skills and generated prompts in a dedicated local tools directory.
- If local agent files must exist inside a project, add them to `.git/info/exclude` so the exclusion stays machine-local.
- Use `.gitignore` only when every contributor should share the exclusion.
- Run `git status` before staging and keep AI tooling separate from project source commits.
- Never stage local credentials, generated routing notes, or machine-specific configuration.
