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
    steward = read_text(repo_root / "skills" / "the-steward" / "SKILL.md")
    governor = read_text(repo_root / "skills" / "the-governor" / "SKILL.md")
    steward_outputs = read_text(repo_root / "skills" / "the-steward" / "OUTPUT_FORMATS.md")
    governor_outputs = read_text(repo_root / "skills" / "the-governor" / "OUTPUT_FORMATS.md")

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

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[PASS] governance decision protocol is canonical and role files are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
