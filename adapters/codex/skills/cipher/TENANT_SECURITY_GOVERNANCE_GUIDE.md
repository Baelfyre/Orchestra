# Tenant-Security Governance Guide

Cipher's deterministic tenant-security reasoning framework.

## Doctrine

```
TENANT_SECURITY_MUST_BE_EVIDENCE_BOUND
UI_VISIBILITY_IS_NOT_SECURITY_ENFORCEMENT
UNKNOWN_TENANT_MODEL_MUST_NOT_BE_INVENTED
DEFAULT_DENY_ACROSS_TENANT_BOUNDARIES
CLIENT_CONTEXT_SELECTION_IS_NOT_SERVER_AUTHORIZATION
```

## Ownership Split

Tenant-security governance spans multiple specialists. Each specialist owns a distinct concern:

| Concern | Owner | Boundary |
|---------|-------|----------|
| Tenant architecture and boundary structure | Clockwork | Defines propagation topology, architectural placement, and isolation mechanism selection |
| Tenant trust, authorization, and security/isolation requirements | Cipher | Defines what security properties must hold across tenant boundaries |
| Persistence and schema enforcement for tenant isolation | Chronicler | Defines how persistence enforces isolation requirements |
| Implementation | Ponytail | Executes within accepted specialist contracts |
| Validation evidence | Overseer | Determines test strategy and produces validation results |

Cipher defines security requirements. Cipher does not own architecture, persistence mechanics, implementation, or validation strategy.

## 1. Tenancy Source

Consume the accepted project tenancy posture from `ProjectArchitectureGovernanceProfile`:

```
tenancy_model:
  SINGLE_TENANT
  MULTI_TENANT
  HYBRID
  UNDECIDED_BLOCKING
  NOT_APPLICABLE
```

and:

```
tenant_isolation_policy_refs
```

The tenancy model is an accepted governance fact, not a Cipher decision. Cipher consumes this posture to determine which tenant-security requirements apply.

Do not invent multi-tenancy because future expansion is merely possible. Do not assume single-tenancy merely because multi-tenancy is not currently deployed.

## 2. Core Tenant-Security Authorization Chain

For each protected operation, evaluate the full authorization chain:

```
authenticated subject
  ->
trusted tenant context
  ->
tenant membership / relationship
  ->
requested action
  ->
target resource
  ->
resource tenant ownership
  ->
property/field sensitivity where relevant
  ->
authorization decision
```

Each link in this chain represents a distinct trust decision. Skipping a link creates a security gap.

Do not reduce tenant authorization to:

```
user.role == X
```

when tenant/resource ownership also matters. A role check alone is insufficient when object ownership, tenant boundary, relationship, or resource state also determines permission.

## 3. Trusted Tenant Context

Tenant identity must come from an accepted trusted boundary.

The client may select context. The server must verify authority over that context.

Do not treat client-supplied:

```
tenant_id
organization_id
account_id
```

as authorization merely because it is syntactically valid.

Server-side verification must confirm that the authenticated subject has authority over the selected tenant context. This verification must occur at the authoritative boundary, not at a downstream convenience point.

## 4. Default Deny Across Tenant Boundaries

Unless an accepted rule explicitly permits cross-tenant access:

```
subject tenant != resource tenant -> DENY
```

Do not infer cross-tenant administrator or support authority from the absence of an explicit prohibition. Cross-tenant access must be affirmatively authorized.

Privileged cross-tenant workflows must be:
- Explicitly defined in accepted policy
- Scoped to specific operations
- Auditable
- Subject to the same evidence-first reasoning as any other security boundary

## 5. Global and Shared Resources

Not every object belongs to a tenant. Security behavior must follow the accepted resource ownership model. Explicitly distinguish:

| Ownership | Security Behavior |
|-----------|-------------------|
| Tenant-owned | Subject must have tenant authority |
| Shared/global | Access governed by resource-specific policy, not tenant boundary |
| System-owned | Access governed by system privilege, not tenant membership |
| Public | Accessible without tenant context where intended |
| Cross-tenant administrative | Requires explicit cross-tenant authorization policy |

Do not force tenant ownership onto resources that are intentionally shared or global. Do not assume that a shared resource requires no access control.

## 6. Background and Asynchronous Execution

Tenant context requirements apply to all execution paths, not only browser request context. Evaluate tenant security for:

- Background jobs and workers
- Queues and event handlers
- Callbacks and webhooks
- Scheduled jobs
- Service-to-service calls
- Exports and imports
- Maintenance processes

Do not assume that browser request context automatically propagates to background execution. Tenant context must be explicitly carried and verified where protected operations occur outside the originating request.

**Ownership boundary**: Clockwork owns propagation topology and mechanism design. Cipher owns the security requirement that tenant context remain trustworthy across execution boundaries.

## 7. Cache, Session, and Context Boundaries

Where applicable, tenant isolation requirements must account for:

- Cache keys and cached authorization state
- Session state
- Server-side context and ambient state
- Authorization caches
- Shared process state

Stale or incorrectly scoped cached state can silently bypass tenant isolation. Authorization caches that do not include tenant context in their key space may return cross-tenant authorization decisions.

**Ownership boundary**: Clockwork owns cache architecture and session mechanism. Cipher defines the security requirement that isolation must hold across these boundaries. Cipher does not prescribe a cache architecture.

## 8. Persistence Boundary

Cipher defines what isolation must hold. Chronicler defines how persistence enforces it.

Possible persistence mechanisms include:

- Tenant predicate filtering
- Composite key with tenant identifier
- Tenant-scoped uniqueness constraints
- Row-level security policies
- Separate schema per tenant
- Separate database per tenant

The choice among these mechanisms is a Chronicler and Clockwork decision, not a Cipher decision. Cipher must not mandate row-level security universally or prescribe a specific persistence isolation strategy.

Cipher's tenant-security requirement is the input. Chronicler's persistence design is the implementation.

## 9. UI Boundary

```
UI VISIBILITY != SECURITY ENFORCEMENT
```

Hidden UI elements do not constitute authorization. A UI that hides an admin button for non-admin users does not enforce authorization if the backend route remains accessible without the corresponding server-side check.

Required principle:
- Cloak may design security-aware UX (hiding elements, disabling controls, showing access-denied states)
- Cipher defines the security rules that must be enforced
- Server-side enforcement remains required where applicable regardless of UI state
- A finding that UI hides a control does not create a vulnerability unless the backend also lacks enforcement

## 10. Information Leakage

Review cross-tenant information leakage through:

- Error messages that reveal tenant-specific data
- Search results that include cross-tenant objects
- Counts and aggregations across tenant boundaries
- Autocomplete suggestions from other tenants
- Exports that include cross-tenant data
- Logs accessible to other tenants
- Notifications delivered across tenant boundaries
- Object IDs that encode tenant information
- Metadata that reveals tenant structure
- Object existence responses (404 vs 403 distinction)

Do not overclaim vulnerabilities without evidence. An object ID that contains a tenant identifier is not automatically a vulnerability unless it enables unauthorized cross-tenant access or reveals sensitive tenant information.

## 11. Single-Tenant Proportionality

If the accepted project profile declares:

```
tenancy_model: SINGLE_TENANT
```

and there is no tenant-security requirement:

Do not force multi-tenant authorization machinery. Return tenant-security concerns as:

```
NOT_APPLICABLE
```

or use the equivalent existing Cipher classification. Single-tenant systems do not require cross-tenant isolation, tenant-aware cache keys, tenant-scoped persistence, or multi-tenant background job context.

If the single-tenant system has specific trust boundaries (for example, between organizational units within a single tenant), those are ordinary authorization boundaries, not tenant-security boundaries.

## 12. Undecided Tenancy

If the accepted project profile declares:

```
tenancy_model: UNDECIDED_BLOCKING
```

and the security design materially depends on the tenant model:

Do not invent a model. Do not assume single-tenant. Do not assume multi-tenant.

Route through Conductor to the owning upstream decision. The tenancy model is a `ProjectArchitectureGovernanceProfile` decision, not a Cipher decision.

If the security review can proceed without tenant-model dependency (for example, general authentication or input validation), continue with the non-tenant-dependent findings and note the tenant-security gap for future resolution.

## 13. Evidence Status

Preserve Cipher's existing evidence classification:

| Status | Meaning |
|--------|---------|
| Confirmed | Supported by inspected evidence |
| Likely / needs verification | Evidence suggests a problem but a material fact is missing |
| Informational / hardening | Not a demonstrated vulnerability |
| Not applicable / false positive | Does not apply to the inspected boundary |

No missing evidence converts to a confirmed vulnerability. A tenant-security concern without evidence of cross-tenant access is not a confirmed cross-tenant vulnerability.

## 14. Overseer Validation Handoff

Cipher defines validation properties. Overseer determines test strategy and `ArchitectureValidationContract` result.

Example tenant-security validation properties:

| Property | Description |
|----------|-------------|
| Authorized tenant succeeds | Authenticated subject with valid tenant authority can access tenant-owned resource |
| Unauthorized tenant fails | Subject without tenant authority is denied access |
| Cross-tenant ID substitution fails | Replacing a resource ID with one from another tenant results in denial |
| Background job retains tenant boundary | Asynchronous execution preserves and verifies tenant context |
| Global resource remains intentionally shared | Shared resources are accessible without spurious tenant restrictions |
| Missing tenant context denied | Operations requiring tenant context fail safely when context is absent |
| Stale cached authorization rejected | Cached authorization from a revoked or changed tenant relationship is not honored |
| UI-hidden route server-enforced | Backend routes enforce authorization regardless of frontend visibility |

Cipher defines these properties. Cipher does not mark them `PROVEN`. Overseer owns the validation result.

## Cross-Specialist Coordination

A Cipher `SpecialistDomainContract` may carry the tenant-security decision in cross-specialist coordination. The contract captures:

- Owned decisions (tenant-security requirements)
- Constraints (isolation boundaries, default deny, trusted context)
- Acceptance criteria (validation properties for Overseer)
- Dependencies (Clockwork architecture, Chronicler persistence)
- Prohibited changes (removing tenant enforcement without explicit policy change)

The `ArchitectureValidationContract.tenant_isolation_validation` obligation consumes Cipher's tenant-security requirements as input.

## Downstream Specialist Handoffs

| Need | Route To |
|------|----------|
| Tenant architecture, propagation topology, isolation mechanism selection | Clockwork |
| Persistence enforcement, schema design, tenant predicate implementation | Chronicler |
| Frontend security UX, tenant-aware UI patterns | Cloak |
| Implementation of accepted security requirements | Ponytail |
| Test strategy, validation evidence, readiness | Overseer |
| Documentation of tenant-security decisions | Scribe |
| Legal/compliance sufficiency of tenant isolation | The Governor through Conductor |
| Ambiguous multi-specialist sequencing | Conductor |
