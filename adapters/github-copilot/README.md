# GitHub Copilot Adapter for Orchestra

## Overview

This adapter provides the integration scaffolding for GitHub Copilot under the **Universal Adaptive Integration (UAI)** architecture.

Under UAI, integration with GitHub Copilot is decoupled into:
1. **Host Capability Discovery**: Verifying which integration surfaces (repository instructions, Agent Skills, custom agents, MCP tools, CLI) are active and supported in the specific Copilot environment.
2. **Transport Selection**: Selecting the smallest, most compatible integration strategy (e.g., repository instructions vs. Agent Skills vs. MCP transport).
3. **Provider Advisory**: Consulting the Provider Capability Broker in shadow mode to evaluate model fitness without automatic provider mutation.
4. **Specialist & Workflow Preservation**: Preserving Conductor as the sole internal specialist router and deterministic AWF as the workflow topology authority.

Clear ownership can let Conductor choose a direct single-specialist fast route, but it never authorizes a host, native custom agent, or adapter to bypass Conductor. UAI transport selection remains separate from specialist and workflow routing.

## Status

- Adapter ID: `github-copilot`
- Maturity: `SCAFFOLD_PREPARED_PROBE_ACTIVE`
- Live External Host: `GitHub Copilot` (Cloud Agent, VS Code Chat, Copilot CLI)
- Authoritative Plan: `projects/orchestra/10-approved/plans/Orchestra_Universal_Adaptive_Integration_Architecture_2026-09-06.md`

## Integration Surfaces

1. **Repository Instructions**: `.github/copilot-instructions.md` (root instruction anchor for all Copilot surfaces interacting with the repository).
2. **Agent Skills**: Compatible with GitHub Copilot Agent Skills (`.github/skills/` or `skills/` with `SKILL.md` frontmatter).
3. **Custom Agents**: Supported via `.github/agents/*.agent.md` where custom agents are enabled.
4. **MCP Tools**: Compatible with Copilot MCP configuration in supported client environments.
5. **Instruction Fallback**: Bounded instruction-only path when richer tool or skill transports are unavailable.

## Probe and Conformance

See [probe-guide.md](probe-guide.md) for the exact capability probe matrix and execution steps.
