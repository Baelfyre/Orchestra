import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import helpers

LOW_RISK_REQUIRED_FIELDS = [
    "Project Name",
    "Project Purpose",
    "Project Type",
    "Current Stage",
    "Known Constraints",
    "Validation Requirements",
]

RECOMMENDED_REQUIRED_FIELDS = LOW_RISK_REQUIRED_FIELDS + [
    "Primary Users",
    "User or Maintainer Preferences",
]

STRICT_REQUIRED_FIELDS = [
    "Project Name",
    "Project Purpose",
    "Project Type",
    "Data Sensitivity",
    "Primary Users",
    "Runtime or Deployment Context",
    "Governance Level",
    "Safety Boundaries",
    "Validation Requirements",
    "Known Non-Goals",
    "Maintainer Approval Rules",
]

FIELD_ALIASES = {
    "Project Purpose": ["Project Purpose", "Goal"],
    "Data Sensitivity": ["Data Sensitivity", "Data Use"],
    "Known Constraints": ["Known Constraints", "Constraints"],
    "Validation Requirements": ["Validation Requirements", "Validation Notes"],
    "User or Maintainer Preferences": ["User or Maintainer Preferences", "User Preferences"],
}

GOVERNANCE_LABELS = {
    "advisory": "Advisory",
    "recommended": "Recommended",
    "strict-governed": "Strict-Governed",
}

HEADING_PATTERN = re.compile(r"(?m)^#{1,6}\s+(.+?)\s*$")


def normalize_name(value):
    return re.sub(r"\s+", " ", value.strip().strip(":"))


def normalize_governance_level(value):
    if value is None:
        return None

    normalized = re.sub(r"[\s_]+", "-", value.strip().lower())
    aliases = {
        "advisory": "advisory",
        "recommended": "recommended",
        "strict": "strict-governed",
        "strict-governed": "strict-governed",
    }
    return aliases.get(normalized)


def is_operating_mode(value):
    return normalize_governance_level(value) is None


def format_governance_level(level):
    return GOVERNANCE_LABELS[level]


def extract_heading_sections(content):
    matches = list(HEADING_PATTERN.finditer(content))
    sections = {}

    for index, match in enumerate(matches):
        title = normalize_name(match.group(1)).casefold()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        sections[title] = content[start:end].strip()

    return sections


def extract_label_value(content, label):
    pattern = re.compile(rf"(?im)^(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*:\s*(.+?)\s*$")
    match = pattern.search(content)
    if not match:
        return None
    return match.group(1).strip()


def extract_section_value(sections, label):
    body = sections.get(normalize_name(label).casefold())
    if not body:
        return None

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        stripped = stripped.lstrip("-*>").strip().strip("`")
        if stripped:
            return stripped

    return None


def find_field_value(content, sections, field_name):
    labels = FIELD_ALIASES.get(field_name, [field_name])

    for label in labels:
        label_value = extract_label_value(content, label)
        if label_value:
            return label_value

    for label in labels:
        section_value = extract_section_value(sections, label)
        if section_value:
            return section_value

    return None


def find_missing_fields(content, sections, required_fields):
    missing_fields = []

    for field_name in required_fields:
        if not find_field_value(content, sections, field_name):
            missing_fields.append(field_name)

    return missing_fields


def resolve_requested_governance_level(args):
    if args.governance_level:
        explicit_level = normalize_governance_level(args.governance_level)
        if explicit_level is None:
            helpers.write_color_host(
                "ERROR",
                "The Steward: Unsupported --governance-level value. Use Advisory, Recommended, or Strict-Governed.",
            )
            sys.exit(2)
        return explicit_level, "--governance-level"

    shorthand_level = normalize_governance_level(args.mode)
    if shorthand_level and not is_operating_mode(args.mode):
        return shorthand_level, "--mode"

    return None, None


def determine_governance_level(content, sections, requested_level):
    document_value = find_field_value(content, sections, "Governance Level")
    normalized_document_level = normalize_governance_level(document_value) if document_value else None

    if document_value and normalized_document_level is None:
        helpers.write_color_host(
            "WARNING",
            f"The Steward: Unrecognized Governance Level '{document_value}'. Defaulting to Advisory unless an explicit override is provided.",
        )

    if normalized_document_level:
        return normalized_document_level, "PROJECT_CONTEXT.md"

    if requested_level:
        return requested_level, "CLI override"

    return "advisory", "default"


def required_fields_for_level(level):
    if level == "strict-governed":
        return STRICT_REQUIRED_FIELDS
    if level == "recommended":
        return RECOMMENDED_REQUIRED_FIELDS
    return LOW_RISK_REQUIRED_FIELDS


def handle_missing_context(context_file, operating_mode, governance_level, governance_source):
    display_level = format_governance_level(governance_level)

    if governance_level == "strict-governed":
        helpers.write_color_host(
            "ERROR",
            f"The Steward: {context_file} is missing. {display_level} repositories require project context before validation can proceed.",
        )
        sys.exit(1)

    if governance_level == "recommended":
        helpers.write_color_host(
            "WARNING",
            f"The Steward: {context_file} is missing. {display_level} governance is non-blocking by default, but context should be added before coordinated or release-critical work. Source: {governance_source or 'default'}.",
        )
        sys.exit(0)

    mode_note = f" Proceeding for {operating_mode}." if operating_mode else ""
    helpers.write_color_host(
        "WARNING",
        f"The Steward: {context_file} is missing. Defaulting to {display_level} governance, so validation remains advisory only.{mode_note}",
    )
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        default="Implementation Mode",
        help="Legacy operating mode name, or governance shorthand: advisory, recommended, strict-governed.",
    )
    parser.add_argument(
        "--governance-level",
        help="Explicit governance level override: Advisory, Recommended, or Strict-Governed.",
    )
    parser.add_argument("--context-file", default="PROJECT_CONTEXT.md")
    args, _ = parser.parse_known_args()

    root = helpers.get_project_root()
    context_path = os.path.join(root, args.context_file)

    requested_governance_level, governance_source = resolve_requested_governance_level(args)
    operating_mode = args.mode if is_operating_mode(args.mode) else None

    if not os.path.isfile(context_path):
        fallback_level = requested_governance_level or "advisory"
        handle_missing_context(args.context_file, operating_mode, fallback_level, governance_source)

    with open(context_path, "r", encoding="utf-8") as context_file:
        content = context_file.read()

    sections = extract_heading_sections(content)
    governance_level, effective_source = determine_governance_level(content, sections, requested_governance_level)
    missing_fields = find_missing_fields(content, sections, required_fields_for_level(governance_level))
    display_level = format_governance_level(governance_level)

    if missing_fields:
        missing_list = ", ".join(missing_fields)
        if governance_level == "strict-governed":
            helpers.write_color_host(
                "ERROR",
                f"The Steward: Project Context is incomplete for {display_level} governance. Missing required sections: {missing_list}",
            )
            sys.exit(1)

        helpers.write_color_host(
            "WARNING",
            f"The Steward: Project Context is incomplete for {display_level} governance. Missing recommended sections: {missing_list}. Source: {effective_source}. Proceeding without blocking.",
        )
        sys.exit(0)

    helpers.write_color_host(
        "SUCCESS",
        f"The Steward: Project Context is complete for {display_level} governance. Source: {effective_source}.",
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
