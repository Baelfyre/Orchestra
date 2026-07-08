# V1.1.0 Specialist Governance & Boundary Standard Readiness Checklist

Before tagging the `v1.1.0 Specialist Governance & Boundary Standard` release of the Orchestra, the following checks must all pass:

- [x] **Markdown-first architecture preserved**: No compiled code, binary requirements, or forced dependencies.
- [x] **All manifest-declared skills present**: The current plugin manifest, skill folders, and command surfaces validate together, including Conductor, governance authorities, specialists, and Ponytail.
- [x] **Output formats externalized**: `OUTPUT_FORMATS.md` successfully decoupled for progressive disclosure token savings.
- [x] **Routing map centralized**: `ROUTING_MAP.md` handles all inter-skill delegation and conflict resolution.
- [x] **Behavior tests present**: `tests/behavior/` contains the matrix and manual guide for validation.
- [x] **Plugin readiness documented only**: Clear architectural roadmap provided without coupling to a specific vendor's plugin runtime.
- [x] **Manifest verification passing**: `validate-manifest.ps1` runs cleanly, guaranteeing zero drift between JSON schema and `SKILL.md` frontmatter.
- [x] **Validation scripts passing**: `validate-structure.ps1` runs cleanly across all core files, adapters, tests, and skills.
- [x] **No stale repository names**: All instances of the legacy "Orchestra of Amalgamation" string replaced.
- [x] **No stale routing matrix references**: Legacy `ROUTING_MATRIX.md` references successfully purged.
- [x] **No runtime plugin dependencies**: The core product remains pure context material for LLMs.
