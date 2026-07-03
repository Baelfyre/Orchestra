# Stress Testing Foundations Guide

## Purpose
This guide provides a practical general reference for Dagger to expand QA evidence into stress, negative, resilience, chaos, and recovery scenarios while preserving safety gates. It ensures Dagger identifies missing guardrails, crash conditions, and failure modes objectively and safely.

## Source-of-Truth Rule
Dagger expands approved QA scenarios into failure-focused scenarios. Dagger must separate planning, approved execution, observed result, suspected risk, and confirmed defect.

## Dagger and Overseer Boundary
- **Overseer** owns QA validation gates, formal test planning, pass/fail decisions, regression scope, UAT, and release readiness.
- **Dagger** does not own formal QA planning or release readiness decisions.
- Dagger expands Overseerâ€™s QA baseline into stress and failure-mode testing, and hands findings back to Overseer for readiness decisions.

## Stress Testing vs Load Testing vs Chaos Testing
- **Stress Testing**: What happens when capacity, limits, resources, or timing are pressured?
- **Load Testing**: How does the system behave under expected or increasing normal usage?
- **Chaos Testing**: How does the system behave when dependencies or infrastructure fail?
- **Negative Testing**: How does the system behave when invalid, unexpected, malformed, missing, excessive, repeated, conflicting, or unauthorized inputs occur?
- **Resilience Testing**: Can the system continue, degrade safely, recover, retry, rollback, or fail closed?

## When to Use Dagger
Use Dagger to discover edge cases, test guardrails, explore misuse cases, or simulate failure scenarios that go beyond normal functional QA boundaries.

## Required Overseer Baseline
Before expanding, consult Overseerâ€™s baseline: requirements, acceptance criteria, pass/fail criteria, regression scope, and existing defect history.

## Stress Testing Scope Expansion
Identify breaking points in system workflows. Stress scenarios must include expected safe behavior, not only expected failure.

## Negative Testing Expansion
Evaluate behavior against unexpected inputs. This is not about functional correctness but about failure handling.

## Failure-Mode Thinking
Assume components will fail. Identify target boundaries, triggers, and the expected safe degradation or failure mode.

## Resource Pressure Categories
Resource pressure may include CPU, memory, disk, network, database connection pool, file handles, queue depth, timeout limits, rate limits, session limits, and concurrent users.

## Dependency Failure Scenarios
Simulate API latency, timeout, missing services, corrupted data payloads, and authentication rejections from third-party or internal dependencies.

## State Corruption and Recovery Scenarios
Recovery checks should include retry, rollback, reconnect, resume, cleanup, restore, fallback, graceful degradation, and user-facing error behavior.

## Timeout, Retry, and Recovery Behavior
Verify that systems do not hang indefinitely and that retries are bounded and back off gracefully.

## Concurrency and Race Condition Pressure
Simulate simultaneous actions that compete for the same resource or state.

## Data Integrity Under Stress
Verify that partial failures do not leave data in an invalid or orphaned state. Rollbacks must be complete.

## User Workflow Stress
Interrupt user workflows midway (e.g., closing a browser during a transaction) and verify the system state remains consistent.

## Safety-Gated Execution
Unapproved destructive tests remain planning-only. Real user data, production systems, external targets, and unauthorized systems are out of scope. Do not suggest destructive execution without explicit authorization, non-production scope, rollback, monitoring, and safety gate approval.

## Evidence Requirements
Test evidence must include: revision, environment, trigger, input class, expected safe behavior, observed behavior if executed, safety gate status, and handoff owner. A planned or unrun stress test must never be marked as passed.

## Severity and Risk Framing
Evaluate the likelihood and impact of the discovered failure mode. Provide actionable evidence for prioritization.

## Handoff Back to Overseer
All executed failure scenarios and discovered risks must be handed back to Overseer so they can be integrated into QA validation gates and readiness decisions.

## Dagger Stress Review Checklist
- [ ] Is the scenario explicitly aligned with an existing Overseer QA baseline?
- [ ] Are real user data and production systems completely excluded?
- [ ] Is the expected safe behavior explicitly defined?
- [ ] Are safety gates cleared before execution?
- [ ] Have findings been properly handed back to Overseer?

## Dagger Output Discipline
- Output must be structured, objective, and evidence-based.
- No offensive security instructions, exploit chains, malware behavior, credential theft, persistence, or exfiltration guidance.
- Maintain strict adherence to Caveman formatting and safety gates.
