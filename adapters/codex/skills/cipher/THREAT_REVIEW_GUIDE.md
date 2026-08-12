# Threat Review Guide

## Use Proportional Modeling

Do not build a full threat model for every security task.

Use:
- a **boundary review** for a narrow route, permission, header, dependency or configuration issue;
- a **flow review** for authentication, authorization, payment-like, upload, webhook, import/export or sensitive business workflows;
- a **system threat model** only when the scope materially crosses multiple trust boundaries or introduces a new security architecture.

## 1. Security Objective

State what must remain true, for example:
- only the correct actor can perform the operation;
- one tenant cannot access another tenant's data;
- untrusted input cannot control an interpreter or outbound destination;
- credentials are not exposed to clients/logs/artifacts;
- a sensitive workflow cannot be automated beyond intended policy;
- security evidence remains attributable and tamper-resistant enough for its purpose.

Avoid vague objectives such as "make it secure."

## 2. Assets

Identify only assets supported by the scope:
- identities and credentials;
- authorization state;
- personal/sensitive data;
- business-critical state transitions;
- secrets/keys;
- availability/shared resources;
- audit evidence;
- external-service trust.

## 3. Entry Points

Inventory relevant interfaces:
- browser/API requests;
- uploads/imports;
- callbacks/webhooks;
- OAuth/OIDC redirects;
- background jobs/queues;
- admin/support tools;
- scheduled tasks;
- third-party APIs;
- configuration/dependency updates.

Assume the UI can be bypassed. Do not actively probe systems without authorization.

## 4. Trust Boundaries

Mark where any of these changes:
- authenticated identity;
- privilege/role;
- object ownership;
- tenant/account/organization;
- process/service;
- network trust;
- browser/server;
- application/third party;
- trusted/untrusted data;
- human approval/automated execution.

A boundary is more useful than a generic attacker label because it identifies where a control must hold.

## 5. Actors and Capabilities

Use evidence-backed roles and broad adversary categories. Describe only the capability needed for the defensive scenario, such as:
- unauthenticated caller;
- ordinary authenticated user;
- user in another tenant;
- compromised low-privilege account;
- malicious automation;
- untrusted third-party service response.

Do not invent attribution, sophistication, motivation or access that the evidence does not support.

## 6. Abuse Cases

Write concise defensive abuse cases:

`Given <capability>, an actor attempts <boundary crossing> to violate <security objective>.`

Then identify:
- required preconditions;
- current safeguards;
- missing control;
- observable evidence;
- verification needed after remediation.

Do not include exploit payloads, credential theft, stealth, persistence, exfiltration or evasion instructions.

## 7. Control Mapping

Map validated risks to the minimum relevant control types:
- preventive;
- detective;
- corrective;
- recovery.

Optionally map to CWE, versioned ASVS requirements, OWASP API categories, RFC guidance or repository policy when the mapping is supported.

Taxonomy does not replace evidence.

## 8. Authorization-Specific Review

For access-control threats, test the model conceptually across:
- function/action;
- object/resource;
- property/field;
- tenant/account/organization;
- ownership/delegation;
- administrative/support privilege;
- background/service actor.

Do not assume a role check covers all of these dimensions.

## 9. Sensitive Business Flows

For booking, reservation, purchase, waitlist, credential-reset, invitation, enrollment, voting-like, quota, promotion or limited-resource workflows, identify:
- authoritative state transition;
- who may initiate it;
- ordering/eligibility rules;
- automation/replay/duplicate behavior;
- resource-consumption controls;
- auditability;
- server-side invariants.

Rate limits may support the design but must not substitute for the underlying authorization or state-transition rule.

## 10. Risk and Confidence

Assess:
- impact;
- exposure;
- prerequisites;
- affected scope;
- existing safeguards;
- detectability;
- confidence.

Keep severity separate from confidence and remediation scheduling.

## Missing Evidence

State exactly what is missing and whether it:
- reduces confidence;
- prevents severity assignment;
- prevents a finding entirely;
- requires another specialist or authorized environment.

Missing evidence is never approval and never a vulnerability by itself.

## Defensive Boundary

Cipher stops at defensive analysis and control requirements. Active exploitation, destructive testing, credential use, external scanning, production access or remediation deployment requires separate authority and the correct specialist.