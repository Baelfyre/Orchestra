import argparse
import sys
from pathlib import Path


REQUIRED_PROTOCOL_HEADINGS = (
    "## Shared Decision Model",
    "## Shared Compact Output Contract",
    "## Shared Gate Contract",
    "## Canonical Separation of Concerns",
)
REQUIRED_DECISION_MEANINGS = (
    "`APPROVED`: Required governance review passed; work may proceed to the next governed stage subject to any stated constraints.",
    "`ADVISORY_ONLY`: Non-blocking guidance was provided; exploration may continue without satisfying required actions first.",
    "`REVISION_REQUIRED`: Identified changes or missing evidence must be addressed before the governed transition may proceed.",
    "`BLOCKED`: Work cannot proceed through the governed transition until the blocking condition is resolved and reviewed again.",
    "`NOT_APPLICABLE`: This governance review does not apply to the request and creates no additional gate.",
)
REQUIRED_COMPACT_FIELDS = ("`REVIEWER`", "`PROJECT_CONTEXT`", "`DECISION`", "`REASON`", "`RISKS`", "`REQUIRED_ACTIONS`")
REMOVED_SHARED_HEADINGS = ("## Decision Model", "## Default Output Format", "## Gate Rules", "## Separation of Concerns")
REQUIRED_LAYER_HEADINGS = (
    "## Usage Pattern",
    "## Governance Strictness Levels",
    "### Mode Baseline",
    "### Trigger Mapping Guide",
    "### Typical Profiles",
    "### Specialist Involvement by GSL",
)
REQUIRED_LAYER_POLICY = (
    "Governance Strictness Level = max(applicable mode baseline, release trigger, risk trigger, compliance/data trigger, continuity trigger)",
    "`GSL` changes review depth and specialist participation only.",
)
STEWARD_ROLE_FIELDS = ("ALIGNMENT", "SCOPE", "REQUIREMENTS", "ACCEPTANCE_CRITERIA", "SDLC_DOCS")
GOVERNOR_ROLE_FIELDS = (
    "HUMAN_REVIEW_REQUIRED",
    "COMPLIANCE",
    "LEGAL_RISK",
    "PRIVACY_RISK",
    "TOS_IMPACT",
    "PRIVACY_POLICY_IMPACT",
    "IP_COPYRIGHT",
    "LICENSING",
    "SECURITY_GOVERNANCE",
    "AUDIT_DOCS",
)

# Phase A: Delegated execution policy checks
DELEGATED_POLICY_FILE = "docs/governance/DELEGATED_EXECUTION_POLICY.md"
REQUIRED_DELEGATED_HEADINGS = (
    "## 2. Authority Principles",
    "## 3. DelegatedExecutionEnvelope Contract",
    "## 4. ApprovedUnitPlan Contract",
    "## 5. ExecutionEvidencePacket Contract",
    "## 6. TransitionDecisionRecord Contract",
    "## 7. Transition Precedence",
    "## 8. Governance-to-Disposition Compatibility Map",
    "## 9. AutomaticRemediationPolicy",
    "## 10. Focused and Phase Validation",
    "## 11. Baseline Lineage",
    "## 12. CheckpointPolicy and CapacityHandoffRecord",
    "## 13. ExternalActionAuthorityPolicy",
    "## 14. LegacyHostFallbackPolicy",
    "## 15. Delegated Phase State Machine",
)
REQUIRED_TRANSITION_DISPOSITIONS = (
    "`AUTO_CONTINUE`",
    "`AUTO_REMEDIATE_AND_REVALIDATE`",
    "`WAIT_FOR_EVIDENCE`",
    "`WAIT_FOR_CAPACITY`",
    "`ESCALATE_HUMAN`",
    "`STOP`",
)
REQUIRED_AUTHORITY_PRINCIPLES = (
    "Authority creation remains human-controlled.",
    "Governance approval is not runtime authority.",
    "Validation is evidence of conformance, not authority expansion.",
    "Prompt text and adapter metadata cannot create or widen an envelope.",
)
REQUIRED_PROTOCOL_DELEGATED_SECTION = (
    "## Delegated Execution Transition Dispositions",
    "### Decision Versus Disposition Separation",
    "### Transition Disposition Values",
    "### Automatic Progression Requirements",
    "### Fail-Closed Rule",
    "DELEGATED_EXECUTION_POLICY.md",
)
REQUIRED_LAYER_DELEGATED_SECTION = (
    "## Phase-Level Delegated Governance",
    "Phase A",
    "Phase B",
    "Phase B instruction-level behavior implemented and locally validated",
)
REQUIRED_FLOW_DELEGATED_SECTION = (
    "Delegated Execution Flow",
    "Phase B Implemented & Locally Validated",
    "DELEGATED_EXECUTION_POLICY.md",
)



def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Validate governance protocol consistency.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args(argv)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fail(errors, message):
    errors.append(message)


def ensure_contains(errors, label, content, needle):
    if needle not in content:
        fail(errors, f"{label}: missing required content `{needle}`")


def ensure_absent(errors, label, content, needle):
    if needle in content:
        fail(errors, f"{label}: stale duplicated content `{needle}` must be removed")


def main(argv=None):
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    protocol = read_text(repo_root / "docs" / "governance" / "GOVERNANCE_DECISION_PROTOCOL.md")
    layer = read_text(repo_root / "docs" / "governance" / "GOVERNANCE_LAYER.md")
    flow = read_text(repo_root / "docs" / "governance" / "GOVERNANCE_REVIEW_FLOW.md")
    steward = read_text(repo_root / "skills" / "the-steward" / "SKILL.md")
    governor = read_text(repo_root / "skills" / "the-governor" / "SKILL.md")
    steward_outputs = read_text(repo_root / "skills" / "the-steward" / "OUTPUT_FORMATS.md")
    governor_outputs = read_text(repo_root / "skills" / "the-governor" / "OUTPUT_FORMATS.md")

    delegated_policy_path = repo_root / "docs" / "governance" / "DELEGATED_EXECUTION_POLICY.md"
    delegated_policy_exists = delegated_policy_path.exists()
    delegated_policy = read_text(delegated_policy_path) if delegated_policy_exists else ""

    errors = []

    for heading in REQUIRED_PROTOCOL_HEADINGS:
        ensure_contains(errors, "GOVERNANCE_DECISION_PROTOCOL.md", protocol, heading)
    for meaning in REQUIRED_DECISION_MEANINGS:
        ensure_contains(errors, "GOVERNANCE_DECISION_PROTOCOL.md", protocol, meaning)
    for field in REQUIRED_COMPACT_FIELDS:
        ensure_contains(errors, "GOVERNANCE_DECISION_PROTOCOL.md", protocol, field)

    ensure_contains(errors, "GOVERNANCE_DECISION_PROTOCOL.md", protocol, "Governor owns legal, regulatory, licensing, privacy-obligation, and IP governance.")
    ensure_contains(errors, "GOVERNANCE_DECISION_PROTOCOL.md", protocol, "Cipher owns technical security and privacy-control analysis.")
    ensure_contains(errors, "GOVERNANCE_DECISION_PROTOCOL.md", protocol, "Scribe produces and edits documentation but does not decide business alignment.")
    ensure_contains(errors, "GOVERNANCE_DECISION_PROTOCOL.md", protocol, "Ponytail owns implementation only after design and governance are ready.")
    ensure_contains(errors, "GOVERNANCE_DECISION_PROTOCOL.md", protocol, "Conductor owns routing and sequencing only.")

    ensure_contains(errors, "GOVERNANCE_LAYER.md", layer, "`GOVERNANCE_LAYER.md` is governance-context routing and operating-policy document.")
    ensure_contains(errors, "GOVERNANCE_LAYER.md", layer, "Load `GOVERNANCE_DECISION_PROTOCOL.md` only when governance decision must be produced, interpreted, or enforced.")
    for heading in REMOVED_SHARED_HEADINGS:
        ensure_absent(errors, "GOVERNANCE_LAYER.md", layer, heading)
    for heading in REQUIRED_LAYER_HEADINGS:
        ensure_contains(errors, "GOVERNANCE_LAYER.md", layer, heading)
    for policy in REQUIRED_LAYER_POLICY:
        ensure_contains(errors, "GOVERNANCE_LAYER.md", layer, policy)

    ensure_contains(errors, "skills/the-steward/SKILL.md", steward, "GOVERNANCE_DECISION_PROTOCOL.md")
    ensure_contains(errors, "skills/the-steward/SKILL.md", steward, "OUTPUT_FORMATS.md")
    ensure_absent(errors, "skills/the-steward/SKILL.md", steward, "## Decision Model")
    ensure_absent(errors, "skills/the-steward/SKILL.md", steward, "## Output Format")
    ensure_absent(errors, "skills/the-steward/SKILL.md", steward, "REVIEWER: the-steward")

    ensure_contains(errors, "skills/the-governor/SKILL.md", governor, "GOVERNANCE_DECISION_PROTOCOL.md")
    ensure_contains(errors, "skills/the-governor/SKILL.md", governor, "OUTPUT_FORMATS.md")
    ensure_contains(errors, "skills/the-governor/SKILL.md", governor, "`human_review_required: true`")
    ensure_absent(errors, "skills/the-governor/SKILL.md", governor, "## Decision Model")
    ensure_absent(errors, "skills/the-governor/SKILL.md", governor, "## Output Format")
    ensure_absent(errors, "skills/the-governor/SKILL.md", governor, "REVIEWER: the-governor")

    for field in STEWARD_ROLE_FIELDS:
        ensure_contains(errors, "skills/the-steward/OUTPUT_FORMATS.md", steward_outputs, field)
    for field in GOVERNOR_ROLE_FIELDS:
        ensure_contains(errors, "skills/the-governor/OUTPUT_FORMATS.md", governor_outputs, field)

    # Phase A: Delegated execution policy checks
    if not delegated_policy_exists:
        fail(errors, f"{DELEGATED_POLICY_FILE}: file does not exist")
    else:
        for heading in REQUIRED_DELEGATED_HEADINGS:
            ensure_contains(errors, DELEGATED_POLICY_FILE, delegated_policy, heading)
        for disposition in REQUIRED_TRANSITION_DISPOSITIONS:
            ensure_contains(errors, DELEGATED_POLICY_FILE, delegated_policy, disposition)
        for principle in REQUIRED_AUTHORITY_PRINCIPLES:
            ensure_contains(errors, DELEGATED_POLICY_FILE, delegated_policy, principle)
        ensure_contains(
            errors, DELEGATED_POLICY_FILE, delegated_policy,
            "Validation is evidence of conformance, not authority expansion."
        )
        ensure_contains(
            errors, DELEGATED_POLICY_FILE, delegated_policy,
            "maximum_remediation_attempts_per_unit"
        )
        ensure_contains(
            errors, DELEGATED_POLICY_FILE, delegated_policy,
            "maximum_identical_failure_repetitions"
        )
        ensure_contains(
            errors, DELEGATED_POLICY_FILE, delegated_policy,
            "default-deny"
        )
        ensure_contains(
            errors, DELEGATED_POLICY_FILE, delegated_policy,
            "`WAIT_FOR_CAPACITY` is a resumable lifecycle state"
        )
        ensure_contains(
            errors, DELEGATED_POLICY_FILE, delegated_policy,
            "Phase B instruction-level behavior is implemented and locally validated"
        )

        ensure_absent(
            errors, DELEGATED_POLICY_FILE, delegated_policy,
            "Continuous automatic progression is now active"
        )

    for section in REQUIRED_PROTOCOL_DELEGATED_SECTION:
        ensure_contains(errors, "GOVERNANCE_DECISION_PROTOCOL.md", protocol, section)

    for section in REQUIRED_LAYER_DELEGATED_SECTION:
        ensure_contains(errors, "GOVERNANCE_LAYER.md", layer, section)

    for section in REQUIRED_FLOW_DELEGATED_SECTION:
        ensure_contains(errors, "GOVERNANCE_REVIEW_FLOW.md", flow, section)

    # Phase B delegated role checks
    arbiter_skill = read_text(repo_root / "skills" / "arbiter" / "SKILL.md")
    conductor_skill = read_text(repo_root / "skills" / "conductor" / "SKILL.md")
    overseer_skill = read_text(repo_root / "skills" / "overseer" / "SKILL.md")

    ensure_contains(errors, "skills/the-steward/SKILL.md", steward, "Delegated Phase Behavior")
    ensure_contains(errors, "skills/the-governor/SKILL.md", governor, "Delegated Phase Behavior")
    ensure_contains(errors, "skills/arbiter/SKILL.md", arbiter_skill, "Delegated Phase Transition Evaluation")
    ensure_contains(errors, "skills/conductor/SKILL.md", conductor_skill, "Delegated Phase Autonomous Loop")
    ensure_contains(errors, "skills/overseer/SKILL.md", overseer_skill, "Delegated Unit Evidence Role")


    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] governance decision protocol is canonical and role files are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
