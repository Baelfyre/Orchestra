# Specialist Authoring Standard

## Purpose and scope

This document defines the shared authoring contract for Orchestra specialists.

Use it when:
- creating a new specialist under `skills/<skill>/`
- revising an existing specialist's `SKILL.md`
- reviewing whether a specialist's role, boundaries, output contract, and routing behavior are clear enough for Conductor and future maintainers

This standard applies to specialist-facing Markdown source in the tracked repository.
It does not define runtime adapter behavior, CI workflow behavior, or manifest loader behavior beyond the documented `SKILL.md` authoring contract.

## Required specialist frontmatter fields

Every specialist `SKILL.md` must include a YAML frontmatter block with these fields:

- `name`
- `description`
- `slug`
- `role`
- `primary_use`
- `avoid_when`
- `activation_level`
- `depends_on`
- `output_formats`

Required rules:
- Frontmatter is the source of truth for specialist metadata.
- Frontmatter values must stay consistent with `plugin.json` and `SKILL_INDEX.md` through the existing repository validation flow.
- `description` should be short, precise, and safe to reuse in registries and indexes.
- `slug` must match the skill folder name.
- `role` should describe the specialist's job, not its implementation style.
- `primary_use` should describe the core work the specialist is meant to handle.
- `avoid_when` must define when the specialist should not be used and should route to the correct owner where possible.
- `activation_level` must use the repository's established role levels such as `Commander`, `Governor`, `Governance`, `Specialist`, or `Gated`.
- `depends_on` must reflect actual orchestration dependencies only. Do not invent dependency chains.
- `output_formats` must match the formats the specialist can actually produce.

## Required body sections

Specialist files may vary by domain, but the authoring baseline should include these concepts in clearly labeled sections:

1. identity, purpose, or quick reference
2. activation conditions, trigger model, or supported work
3. progressive disclosure or context-loading rules when supporting files exist
4. role boundaries and scope enforcement
5. output format contract
6. Conductor integration, routing rules, or handoff rules
7. local-only safety or approval safety

Recommended section names include:
- `## Quick Reference`
- `## Purpose`
- `## Activation Conditions`
- `## Progressive Disclosure Rule`
- `## Supported work`
- `## Scope Enforcement`
- `## Output formats`
- `## Conductor integration (Handoff Rules)`
- `## Local-only safety`

The exact labels may differ by domain, but the behavior they define should be present.

## Role boundary rules

Every specialist must define clear ownership boundaries.

Required rules:
- State what the specialist owns.
- State what the specialist does not own.
- State when work must be rerouted instead of partially answered out of scope.
- Preserve separation of concerns between governance, routing, implementation, validation, security, persistence, diagrams, and documentation.

Authoring rules:
- Do not describe a specialist as a universal problem solver.
- Do not let a specialist silently absorb another specialist's responsibility.
- If a task crosses domains, the skill should point back to Conductor or the correct downstream specialist.
- If the specialist is read-only, say so directly.

## Activation and `avoid_when` rules

Every specialist must make activation conditions explicit.

Required rules:
- Describe the task types, artifacts, or trigger terms that justify using the specialist.
- Describe when the specialist should not be used.
- Keep `avoid_when` and body-level routing guidance aligned.

Authoring rules:
- Activation conditions should be concrete enough for Conductor and maintainers to route predictably.
- `avoid_when` should block wrong-owner work, not just restate the specialist title.
- Route to a specific specialist when the alternative owner is known.
- If ambiguity remains, direct the task back to Conductor.

## Output format rules

Every specialist must define an output contract.

Required rules:
- Frontmatter `output_formats` must match the supported outputs.
- If the specialist uses `OUTPUT_FORMATS.md`, the headings in that file must match the declared output formats.
- The `SKILL.md` body should tell the specialist when to load `OUTPUT_FORMATS.md`.

Authoring rules:
- Output formats must be minimal, specific, and useful for the domain.
- Do not declare formats that the skill does not actually explain.
- Do not make a specialist invent ad hoc output structures when a declared format exists.

## Handoff rules

Every specialist must define how it hands off cross-domain work.

Required rules:
- Name downstream owners when implementation, security policy, persistence, validation, diagrams, or long-form documentation leave the specialist's scope.
- Preserve Conductor's ownership of routing and orchestration.
- Preserve governance ownership for The Steward, The Governor, and Arbiter where applicable.

Authoring rules:
- Handoffs should be explicit, not implied.
- Handoffs should name the correct specialist or Conductor, not a vague "another tool" or "developer".
- If the specialist is expected to emit `SPECIALIST_REROUTE_REQUIRED`, say so clearly in the scope enforcement section.

## Local-only safety rules

Every specialist should declare repository-safety and publication boundaries appropriate to its domain.

Required rules:
- State whether generated notes, drafts, or artifacts should remain local by default.
- State whether staging, committing, pushing, pull requests, or `.gitignore` changes require approval.
- Preserve existing repository rules for destructive work, governance work, and tracked-source-only edits.

Authoring rules:
- Keep safety text aligned with the specialist's real operating risk.
- Do not overstate authority that belongs to Conductor, governance, or repository policy.
- Use local-first defaults unless the repository intentionally tracks the generated artifact.

## Validation expectations

Specialist authoring should define what validation evidence is expected after work is done.

Required rules:
- State the narrowest relevant validation expectations for the specialist's output or handoff.
- Distinguish review guidance from implementation ownership.
- Require evidence-first claims where the skill depends on artifacts, logs, screenshots, tests, or diffs.

Authoring rules:
- Do not convert the specialist into a CI owner unless that is its actual domain.
- Do not require unrelated full-suite validation in a specialist file when narrower validation is sufficient.
- Validation guidance should help the downstream owner prove the work, not duplicate repository-wide CI documentation.

## Routing discipline

Specialist authoring must support Conductor's routing model.

Required rules:
- Support router-first execution and progressive disclosure.
- Respect governance gates and execution-mode boundaries defined elsewhere in the repository.
- Return `SPECIALIST_REROUTE_REQUIRED` when the request is outside the specialist's scope.
- Avoid bypassing Conductor for cross-domain work.

Authoring rules:
- Do not embed a second routing system inside a specialist.
- Do not override governance roles from specialist files.
- Keep routing language aligned with `SKILL_INDEX.md`, `ROUTING_MAP.md`, and the Conductor skill.

## Authoring checklist

Use this checklist before considering a new or revised specialist complete:

- [ ] Frontmatter includes all required fields.
- [ ] `slug` matches the folder name.
- [ ] `output_formats` matches the specialist's documented outputs.
- [ ] The body explains what the specialist owns.
- [ ] The body explains what the specialist does not own.
- [ ] Activation conditions are explicit.
- [ ] `avoid_when` is explicit and aligned with body-level routing rules.
- [ ] Scope enforcement states reroute behavior for out-of-scope requests.
- [ ] Progressive disclosure rules are present when support files exist.
- [ ] Handoff rules name the correct downstream specialists or Conductor.
- [ ] Local-only safety or approval boundaries are documented.
- [ ] Validation expectations are evidence-based and narrowly scoped.
- [ ] The specialist does not silently assume implementation, governance, CI, or release ownership it does not own.

## Non-goals

This standard is not:
- a runtime manifest
- a CI or validation enforcement change
- a requirement to normalize all existing specialists in the same phase
- a reason to add links from exported skill docs
- a reason to change specialist metadata unless a separate task explicitly requires it
- a replacement for domain-specific rules inside individual specialist files

## Related references

- [Contributing](../CONTRIBUTING.md)
- [Plugin Readiness](PLUGIN_READINESS.md)
- [Manifest Schema](MANIFEST_SCHEMA.md)
- [Governance Layer](../governance/GOVERNANCE_LAYER.md)
- [Minimal Prompt Format](../routing/MINIMAL_PROMPT_FORMAT.md)
