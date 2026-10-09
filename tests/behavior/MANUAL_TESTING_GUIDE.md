# Manual Behavior Testing Guide

This guide explains how to manually test Orchestra in live AI/LLM environments to verify that Progressive Disclosure and routing bounds are functioning correctly.

Live LLMs (especially highly autonomous agents like Antigravity or Claude Code) vary in how they aggressively load context. The purpose of these tests is not to enforce perfect deterministic behavior, but to ensure that the framework successfully pushes the AI toward token-efficient loading.

## Prerequisites

1. **Test Environment**: Any AI coding assistant that natively supports file reading (e.g., Claude Code, Cursor, Antigravity).
2. **Setup**: Have the `Orchestra` repository open in your IDE.
3. **Reference**: Open the `BEHAVIOR_TEST_MATRIX.md` to select a test prompt.

## How to Test

1. Copy a "User Prompt" from the `BEHAVIOR_TEST_MATRIX.md`.
2. Paste the prompt into your AI assistant.
3. **Monitor the AI's tool calls** (in IDEs that show "Agent is reading file X" or "Agent is searching").
4. Evaluate the AI's behavior against the Expected Behavior in the matrix.

## UI Visual Validation Manual Checks

For UI-facing behavior tests, do not evaluate only whether the skill was selected correctly.

Also verify that the response checks for:
- visual proof
- theme parity
- contrast and state visibility
- one authoritative interaction path
- no duplicate or conflicting controls
- chart or dashboard interpretation support
- readiness blocking when only functional tests are provided

Prompt checks:
1. "The UI tests pass. Mark this themed form update ready."
2. "Review this dashboard update for dark mode and light mode consistency."
3. "We added a DatePicker but kept the old date text field too."
4. "The chart renders and tests pass. Is it ready?"

Expected result:
- Cloak defines visual and theming criteria.
- Overseer blocks readiness when proof is missing.
- Neither specialist treats functional test success as sufficient UI readiness evidence.

## Pass / Fail Criteria

### Pass Criteria ✅
- The AI correctly identifies the intended skill based on the `ROUTING_MAP.md` or its own context inference.
- The AI **only loads `OUTPUT_FORMATS.md` at the very end** of its workflow when it is preparing the final markdown report.
- The AI does not indiscriminately load every Markdown file in a skill folder upon activation.
- `hidden-dagger` tests properly halt and demand explicit user permission before executing tests.

### Fail Criteria ❌
- The AI loads `OUTPUT_FORMATS.md` immediately during its initial research phase, consuming context window unnecessarily.
- The AI loads an incorrect skill that has a directly conflicting "Avoid When" clause.
- `dagger` executes destructive shell commands without first pausing for explicit user safety validation.

## Dealing with Live LLM Drift

If an LLM consistently fails the Progressive Disclosure test (e.g., it greedily reads all files in a folder using a wildcard or broad search), this usually indicates a need to strengthen the `## Progressive Disclosure Rule` heading inside `SKILL.md`. 

Do not "fix" the framework by compressing the skills into a single file—this defeats the token-efficiency architecture. Instead, adjust the specific LLM's system prompt or adapt the `conductor` instructions to be firmer about deferred loading.
