# Security Tooling Interpretation Guide

Security tools generate evidence candidates. Cipher validates what they mean for the actual repository and environment.

## Finding Triage Model

For each finding record:
1. tool and rule/advisory identity;
2. affected path/package/route;
3. source of evidence;
4. reachability or runtime exposure when knowable;
5. existing safeguards;
6. confidence;
7. technical impact;
8. project-specific priority;
9. remediation owner;
10. verification needed after remediation.

## SAST and CodeQL

Check:
- actual source-to-sink/control-flow path;
- framework sanitizers, validators or authorization guards;
- whether the source is attacker/user influenced;
- whether the sink is security-sensitive;
- generated/test/example/dead code;
- configuration that enables or disables the path.

Do not dismiss a result solely because a sanitizer exists; verify that it is context-appropriate and on the relevant path.

Do not confirm a vulnerability solely because a static rule matched.

## DAST

Confirm:
- exact environment;
- route/host;
- identity/role;
- request preconditions;
- deployed configuration/version;
- reproducibility at a safe defensive level;
- whether a generic header/status/content heuristic actually demonstrates the claimed impact.

Active scanning of external or production systems requires separate authority.

## Dependency / SCA Findings

Determine:
- package name and exact resolved version;
- direct vs transitive dependency;
- production/runtime vs development/test/build-only exposure;
- affected version range and authoritative advisory source;
- fixed version or mitigation;
- whether the vulnerable component/feature is reachable or used when evidence exists;
- compatibility/regression risk of the upgrade.

CVSS and advisory severity describe the vulnerability, not the complete project-specific risk.

A development-only dependency can still matter for supply-chain/build compromise, but that is a different exposure than a production runtime vulnerability.

## SBOM

An SBOM proves inventory metadata, not safety.

Use it to:
- identify components and versions;
- correlate advisories;
- compare release contents;
- support provenance review.

Do not claim that SBOM generation itself resolves vulnerabilities.

## Secret Scanners

Never print or copy the suspected secret.

Triage by:
- path and metadata;
- secret type/pattern;
- whether it is a placeholder/example/test fixture;
- whether it is current, revoked or rotated using authorized metadata;
- whether repository history/artifacts/logs expose it.

Real credential handling, rotation and incident response require appropriate authority.

## IaC and Configuration Scanners

Confirm:
- actual deployment path/environment;
- variable/default resolution;
- compensating platform controls;
- whether the flagged resource is reachable;
- whether configuration is generated or overridden downstream.

## Container / Image Scanners

Review:
- final image contents;
- runtime user/privileges;
- base image support status;
- reachable packages;
- package manager vs application dependency duplication;
- whether the vulnerable binary/library is present in the shipped layer.

## False Positives and Accepted Risk

A false positive needs evidence showing the rule does not apply.

Risk acceptance is a governance decision, not a Cipher shortcut. Cipher can document residual technical risk and evidence; the appropriate authority decides acceptance.

## Remediation Handoff

- dependency/code/config implementation -> Ponytail;
- architecture placement or compensating boundary -> Clockwork;
- validation/regression strategy -> Overseer;
- legal/compliance acceptance -> The Governor through Conductor.