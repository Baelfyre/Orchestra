# Frontend Review Guide

1. Identify the artifact sources reviewed, the target user, the primary task, the supported viewport, and the available rendered states.
2. Inspect the smallest relevant component, style, state owner, and design-system evidence before making recommendations.
3. Review form usability, user-facing validation messaging, and the visible loading, empty, error, success, retry, and permission states that affect the task.
4. Report confirmed task, accessibility, containment, consistency, recovery, and design-system issues by severity. Separate confirmed evidence from assumptions and `NEEDS EVIDENCE`.
5. Produce a frontend handoff blueprint that names semantic structure, affected components, design-system constraints, responsive or accessibility rules, and downstream routing boundaries without writing production code.
6. Reuse native controls, current components, and existing tokens before suggesting new variants or dependencies.
7. Verify build output and representative interaction states after implementation.

Route implementation to `ponytail`, architecture and state ownership to `clockwork`, security policy to `cipher`, database semantics to `chronicler`, normal QA and validation gates to `overseer`, project documentation to `scribe`, system diagrams to `weaver`, and destructive guardrail pressure testing to gated `dagger`.
