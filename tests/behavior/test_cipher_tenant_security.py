#!/usr/bin/env python3
"""
Deterministic behavioral tests for Cipher Tenant-Security Governance (OR-GOV-8A).

Tests:
  T1  - Confirmed multi-tenant protected resource
  T2  - Single-tenant system
  T3  - Undecided tenancy
  T4  - Client changes tenant_id
  T5  - Authorized same-tenant object access
  T6  - Unauthorized cross-tenant object access
  T7  - Role permitted but wrong tenant
  T8  - Support/admin cross-tenant without explicit policy
  T9  - Explicitly authorized support/admin cross-tenant
  T10 - Shared/global resource
  T11 - Tenant-aware background job
  T12 - Missing tenant context
  T13 - Stale cached authorization
  T14 - UI hidden but backend route accessible
  T15 - Persistence isolation handoff to Chronicler
  T16 - Validation handoff to Overseer
  T17 - Future tenancy only — no premature implementation
  T18 - Evidence missing — no vulnerability fabrication
  NEG - Negative authority boundaries
  PAR - Guide parity and doctrine markers
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GUIDE_SOURCE = ROOT / "skills" / "cipher" / "TENANT_SECURITY_GOVERNANCE_GUIDE.md"
GUIDE_CODEX = ROOT / "adapters" / "codex" / "skills" / "cipher" / "TENANT_SECURITY_GOVERNANCE_GUIDE.md"
SKILL_MD = ROOT / "skills" / "cipher" / "SKILL.md"
SKILL_MD_CODEX = ROOT / "adapters" / "codex" / "skills" / "cipher" / "SKILL.md"
OUTPUT_FORMATS = ROOT / "skills" / "cipher" / "OUTPUT_FORMATS.md"
PROFILE_SCHEMA_PATH = ROOT / "machine" / "schemas" / "project-architecture-governance-profile.v1.schema.json"
VALIDATION_SCHEMA_PATH = ROOT / "machine" / "schemas" / "architecture-validation-contract.v1.schema.json"

# Load schemas
with open(PROFILE_SCHEMA_PATH, "r", encoding="utf-8") as f:
    PROFILE_SCHEMA = json.load(f)

with open(VALIDATION_SCHEMA_PATH, "r", encoding="utf-8") as f:
    VALIDATION_SCHEMA = json.load(f)


def _guide_text():
    return GUIDE_SOURCE.read_text(encoding="utf-8")


def _skill_text():
    return SKILL_MD.read_text(encoding="utf-8")


# ===== T1: Confirmed multi-tenant protected resource =====
def test_t1_multi_tenant_protected_resource():
    """Multi-tenant profile requires full authorization chain in guide."""
    tenancy_enum = PROFILE_SCHEMA["properties"]["tenancy_model"]["enum"]
    assert "MULTI_TENANT" in tenancy_enum

    guide = _guide_text()
    # Full authorization chain must be documented
    assert "authenticated subject" in guide
    assert "trusted tenant context" in guide
    assert "tenant membership" in guide
    assert "requested action" in guide
    assert "target resource" in guide
    assert "resource tenant ownership" in guide
    assert "authorization decision" in guide


# ===== T2: Single-tenant system =====
def test_t2_single_tenant_system():
    """Single-tenant must not force multi-tenant machinery."""
    tenancy_enum = PROFILE_SCHEMA["properties"]["tenancy_model"]["enum"]
    assert "SINGLE_TENANT" in tenancy_enum

    guide = _guide_text()
    assert "NOT_APPLICABLE" in guide
    assert "Do not force multi-tenant authorization machinery" in guide


# ===== T3: Undecided tenancy =====
def test_t3_undecided_tenancy():
    """UNDECIDED_BLOCKING must not invent a model."""
    tenancy_enum = PROFILE_SCHEMA["properties"]["tenancy_model"]["enum"]
    assert "UNDECIDED_BLOCKING" in tenancy_enum

    guide = _guide_text()
    assert "Do not invent a model" in guide
    assert "Conductor" in guide


# ===== T4: Client changes tenant_id =====
def test_t4_client_changes_tenant_id():
    """Server must verify tenant authority, not trust client-supplied IDs."""
    guide = _guide_text()
    assert "tenant_id" in guide
    assert "organization_id" in guide
    assert "server must verify authority" in guide.lower() or "server must verify" in guide.lower()
    assert "CLIENT_CONTEXT_SELECTION_IS_NOT_SERVER_AUTHORIZATION" in guide


# ===== T5: Authorized same-tenant object access =====
def test_t5_authorized_same_tenant_access():
    """Guide must describe authorized same-tenant access as valid."""
    guide = _guide_text()
    assert "Authorized tenant succeeds" in guide


# ===== T6: Unauthorized cross-tenant object access =====
def test_t6_unauthorized_cross_tenant_access():
    """Cross-tenant access must default to DENY."""
    guide = _guide_text()
    assert "subject tenant != resource tenant" in guide
    assert "DENY" in guide
    assert "DEFAULT_DENY_ACROSS_TENANT_BOUNDARIES" in guide


# ===== T7: Role permitted but wrong tenant =====
def test_t7_role_permitted_wrong_tenant():
    """Role check alone is insufficient when tenant boundary also applies."""
    guide = _guide_text()
    assert "role check alone is insufficient" in guide.lower()
    assert "tenant boundary" in guide.lower() or "tenant/resource ownership" in guide.lower()


# ===== T8: Support/admin cross-tenant without explicit policy =====
def test_t8_admin_cross_tenant_no_policy():
    """Do not infer cross-tenant admin authority from absence of prohibition."""
    guide = _guide_text()
    assert "Do not infer cross-tenant" in guide
    assert "affirmatively authorized" in guide.lower() or "explicitly" in guide.lower()


# ===== T9: Explicitly authorized support/admin cross-tenant =====
def test_t9_explicit_cross_tenant_admin():
    """Privileged cross-tenant workflows must be explicitly defined."""
    guide = _guide_text()
    assert "Privileged cross-tenant workflows" in guide
    assert "Explicitly defined" in guide.lower() or "explicitly defined" in guide.lower()


# ===== T10: Shared/global resource =====
def test_t10_shared_global_resource():
    """Guide must distinguish tenant-owned from shared/global/system resources."""
    guide = _guide_text()
    assert "Tenant-owned" in guide
    assert "Shared/global" in guide
    assert "System-owned" in guide
    assert "Public" in guide
    assert "Cross-tenant administrative" in guide


# ===== T11: Tenant-aware background job =====
def test_t11_tenant_aware_background_job():
    """Background/async execution must carry tenant context."""
    guide = _guide_text()
    assert "Background job" in guide or "Background jobs" in guide
    assert "Queues" in guide or "queues" in guide
    assert "Webhooks" in guide or "webhooks" in guide
    assert "Service-to-service" in guide or "service-to-service" in guide
    assert "Clockwork owns propagation" in guide


# ===== T12: Missing tenant context =====
def test_t12_missing_tenant_context():
    """Missing tenant context must be handled safely."""
    guide = _guide_text()
    assert "Missing tenant context" in guide


# ===== T13: Stale cached authorization =====
def test_t13_stale_cached_authorization():
    """Stale cached authorization must not bypass tenant isolation."""
    guide = _guide_text()
    assert "Stale" in guide
    assert "cached authorization" in guide.lower() or "authorization caches" in guide.lower()


# ===== T14: UI hidden but backend route accessible =====
def test_t14_ui_hidden_backend_accessible():
    """UI visibility is not security enforcement."""
    guide = _guide_text()
    assert "UI VISIBILITY != SECURITY ENFORCEMENT" in guide
    assert "UI_VISIBILITY_IS_NOT_SECURITY_ENFORCEMENT" in guide
    assert "Server-side enforcement" in guide


# ===== T15: Persistence isolation handoff to Chronicler =====
def test_t15_persistence_handoff_chronicler():
    """Cipher defines what isolation must hold, Chronicler defines how."""
    guide = _guide_text()
    assert "Cipher defines what isolation must hold" in guide
    assert "Chronicler defines how" in guide
    # Must not mandate specific persistence strategy
    assert "must not mandate" in guide.lower() or "Cipher must not mandate" in guide


# ===== T16: Validation handoff to Overseer =====
def test_t16_validation_handoff_overseer():
    """Cipher defines validation properties, Overseer owns the result."""
    guide = _guide_text()
    assert "Cipher defines validation properties" in guide
    assert "Overseer" in guide
    assert "does not mark them" in guide.lower() or "Cipher does not mark them" in guide

    # ArchitectureValidationContract must include tenant_isolation_validation
    val_props = VALIDATION_SCHEMA["properties"]
    assert "tenant_isolation_validation" in val_props


# ===== T17: Future tenancy only — no premature implementation =====
def test_t17_future_tenancy_no_premature_implementation():
    """Must not invent multi-tenancy because future expansion is possible."""
    guide = _guide_text()
    assert "Do not invent multi-tenancy" in guide
    assert "future expansion" in guide.lower() or "merely possible" in guide.lower()


# ===== T18: Evidence missing — no vulnerability fabrication =====
def test_t18_no_vulnerability_fabrication():
    """Missing evidence must not convert to confirmed vulnerability."""
    guide = _guide_text()
    assert "TENANT_SECURITY_MUST_BE_EVIDENCE_BOUND" in guide
    assert "No missing evidence converts to a confirmed vulnerability" in guide


# ===== Negative authority boundaries =====
def test_negative_authority_boundaries():
    """Cipher must not exceed its authority boundaries in tenant-security."""
    guide = _guide_text()
    skill = _skill_text()

    # Cipher does not own architecture
    assert "Clockwork" in guide
    assert "Clockwork" in skill
    # Cipher does not own persistence
    assert "Chronicler" in guide
    assert "Chronicler" in skill
    # Cipher does not own implementation
    assert "Ponytail" in guide
    assert "Ponytail" in skill
    # Cipher does not own validation
    assert "Overseer" in guide
    assert "Overseer" in skill
    # Cipher does not own UI design
    assert "Cloak" in guide

    # Verify boundary language
    assert "Cipher does not own architecture" in guide or "not a Cipher decision" in guide
    assert "not a Cipher decision" in guide


# ===== Guide parity and doctrine markers =====
def test_guide_parity_and_markers():
    """Verify source and Codex mirror guide parity and essential doctrine markers."""
    assert GUIDE_SOURCE.is_file(), "Missing Cipher tenant-security governance guide source"
    assert GUIDE_CODEX.is_file(), "Missing Cipher tenant-security governance guide Codex mirror"
    assert GUIDE_SOURCE.read_bytes() == GUIDE_CODEX.read_bytes(), (
        "Parity mismatch between source and Codex guide"
    )

    text = _guide_text()
    # Doctrine markers
    assert "TENANT_SECURITY_MUST_BE_EVIDENCE_BOUND" in text
    assert "UI_VISIBILITY_IS_NOT_SECURITY_ENFORCEMENT" in text
    assert "UNKNOWN_TENANT_MODEL_MUST_NOT_BE_INVENTED" in text
    assert "DEFAULT_DENY_ACROSS_TENANT_BOUNDARIES" in text
    assert "CLIENT_CONTEXT_SELECTION_IS_NOT_SERVER_AUTHORIZATION" in text

    # Key sections
    assert "Ownership Split" in text
    assert "Core Tenant-Security Authorization Chain" in text
    assert "Trusted Tenant Context" in text
    assert "Default Deny" in text
    assert "Global and Shared Resources" in text
    assert "Background and Asynchronous Execution" in text
    assert "Persistence Boundary" in text
    assert "UI Boundary" in text
    assert "Information Leakage" in text
    assert "Single-Tenant Proportionality" in text
    assert "Undecided Tenancy" in text
    assert "Overseer Validation Handoff" in text
    assert "Downstream Specialist Handoffs" in text


# ===== Progressive disclosure integration =====
def test_progressive_disclosure_integration():
    """SKILL.md must reference TENANT_SECURITY_GOVERNANCE_GUIDE.md."""
    skill = _skill_text()
    assert "TENANT_SECURITY_GOVERNANCE_GUIDE.md" in skill
    assert "tenant-security governance" in skill


# ===== Tenancy model enum coverage =====
def test_tenancy_model_enum_coverage():
    """Verify all canonical tenancy models are present in schema."""
    expected = {
        "SINGLE_TENANT", "MULTI_TENANT", "HYBRID",
        "UNDECIDED_BLOCKING", "NOT_APPLICABLE",
    }
    actual = set(PROFILE_SCHEMA["properties"]["tenancy_model"]["enum"])
    assert actual == expected


# ===== Tenant isolation policy refs in schema =====
def test_tenant_isolation_policy_refs_in_schema():
    """ProjectArchitectureGovernanceProfile must include tenant_isolation_policy_refs."""
    props = PROFILE_SCHEMA["properties"]
    assert "tenant_isolation_policy_refs" in props


# ===== ArchitectureValidationContract tenant validation =====
def test_architecture_validation_tenant_obligation():
    """ArchitectureValidationContract must have tenant_isolation_validation."""
    props = VALIDATION_SCHEMA["properties"]
    assert "tenant_isolation_validation" in props
    required = VALIDATION_SCHEMA["required"]
    assert "tenant_isolation_validation" in required


def main():
    tests = [
        test_t1_multi_tenant_protected_resource,
        test_t2_single_tenant_system,
        test_t3_undecided_tenancy,
        test_t4_client_changes_tenant_id,
        test_t5_authorized_same_tenant_access,
        test_t6_unauthorized_cross_tenant_access,
        test_t7_role_permitted_wrong_tenant,
        test_t8_admin_cross_tenant_no_policy,
        test_t9_explicit_cross_tenant_admin,
        test_t10_shared_global_resource,
        test_t11_tenant_aware_background_job,
        test_t12_missing_tenant_context,
        test_t13_stale_cached_authorization,
        test_t14_ui_hidden_backend_accessible,
        test_t15_persistence_handoff_chronicler,
        test_t16_validation_handoff_overseer,
        test_t17_future_tenancy_no_premature_implementation,
        test_t18_no_vulnerability_fabrication,
        test_negative_authority_boundaries,
        test_guide_parity_and_markers,
        test_progressive_disclosure_integration,
        test_tenancy_model_enum_coverage,
        test_tenant_isolation_policy_refs_in_schema,
        test_architecture_validation_tenant_obligation,
    ]
    for t in tests:
        t()
    print(f"All Cipher Tenant-Security Governance tests passed successfully ({len(tests)}/{len(tests)}).")


if __name__ == "__main__":
    main()
