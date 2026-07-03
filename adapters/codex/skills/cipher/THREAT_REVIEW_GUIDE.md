# Threat Review Guide

## Asset Identification
- Identify data, identities, services, operations, availability, secrets, and audit evidence requiring protection.
- State business or user impact without inventing value.

## Trust Boundaries
- Mark where identity, ownership, privilege, network, process, tenant, or external-service trust changes.
- Document controls and assumptions at each boundary.

## Entry Points
- Inventory authorized interfaces such as UI submissions, APIs, uploads, callbacks, jobs, imports, admin tools, and dependency updates.
- Assume attackers can bypass the UI and call APIs directly. Consider direct API abuse, request tampering, replay, automation, ID manipulation, and backend injection.
- Do not probe or test without permission.

## Actors
- Use evidence-backed roles and broad threat categories.
- Avoid attributing intent or capability without evidence.

## Abuse Cases
- Describe defensive misuse scenarios at the level needed to identify controls.
- Do not provide operational exploit steps, payloads, evasion, or persistence guidance.

## Risk Severity
- Evaluate impact, likelihood, exposure, prerequisites, affected scope, existing safeguards, detectability, and confidence.
- Separate severity from remediation scheduling.

## Mitigation Mapping
- Map each validated risk to preventive, detective, corrective, and recovery controls as needed.
- Prefer minimal controls at the correct trust boundary and define verification.
- Ensure API hardening controls are considered (e.g., rate limits, throttling, WAF, backpressure, circuit breakers, DDoS mitigation).
- Validate that enforcement occurs on the backend, not the frontend.

## Missing Evidence Handling
- State whether missing code, configuration, data flow, deployment, logs, or policy reduces confidence or blocks a conclusion.
- Do not convert missing evidence into a finding.

## Defensive-Only Boundaries
- Keep analysis scoped to authorized defensive review.
- Refuse exploit chains, credential theft, malware, evasion, persistence, exfiltration, and unauthorized access guidance.

## Require User Approval

Stop before active testing, scanning external systems, changing authentication or authorization, rotating secrets, changing permissions, modifying security or privacy configuration, accessing production data, or deploying remediation.
