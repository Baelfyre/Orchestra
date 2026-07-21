import json
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.repositories import ManifestRepository, SkillSourceRepository
from orchestra_runtime.services import SkillRegistry


SKILL_NAME_ALIASES = {
    "Steward": "the-steward",
    "The Steward": "the-steward",
    "Governor": "the-governor",
    "The Governor": "the-governor",
}

REFERENCE_VALIDATION_SKILLS = {
    "conductor",
    "the-steward",
    "the-governor",
    "arbiter",
    "overseer",
}
PORTABLE_REFERENCES = {
    "conductor": (
        ("docs/routing/EXECUTION_MODES_POLICY.md", "../../docs/routing/EXECUTION_MODES_POLICY.md", "REFERENCE_CONTEXT.md#execution-modes-policy", "execution-modes-policy"),
        ("SKILL_INDEX.md", "../../SKILL_INDEX.md", "REFERENCE_CONTEXT.md#skill-index", "skill-index"),
        ("docs/routing/MINIMAL_PROMPT_FORMAT.md", "../../docs/routing/MINIMAL_PROMPT_FORMAT.md", "REFERENCE_CONTEXT.md#minimal-prompt-format", "minimal-prompt-format"),
        ("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md", "docs/governance/GOVERNANCE_DECISION_PROTOCOL.md", "REFERENCE_CONTEXT.md#governance-decision-protocol", "governance-decision-protocol"),
    ),
    "the-steward": (
        ("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md", "../../docs/governance/GOVERNANCE_DECISION_PROTOCOL.md", "REFERENCE_CONTEXT.md#governance-decision-protocol", "governance-decision-protocol"),
        ("docs/governance/PROJECT_CONTEXT_DECISION_PROMPT.md", "../../docs/governance/PROJECT_CONTEXT_DECISION_PROMPT.md", "REFERENCE_CONTEXT.md#project-context-decision-prompt", "project-context-decision-prompt"),
        ("docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md", "../../docs/governance/PROJECT_CONTEXT_ENFORCEMENT_POLICY.md", "REFERENCE_CONTEXT.md#project-context-enforcement-policy", "project-context-enforcement-policy"),
        ("docs/templates/PROJECT_CONTEXT_TEMPLATE.md", "../../docs/templates/PROJECT_CONTEXT_TEMPLATE.md", "REFERENCE_CONTEXT.md#project-context-template", "project-context-template"),
    ),
    "the-governor": (
        ("docs/governance/GOVERNANCE_DECISION_PROTOCOL.md", "../../docs/governance/GOVERNANCE_DECISION_PROTOCOL.md", "REFERENCE_CONTEXT.md#governance-decision-protocol", "governance-decision-protocol"),
    ),
}
TRACKED_EXPORT_PARITY_PATHS = (
    (
        Path("skills/cloak/templates/bryl-minimal-design.md"),
        Path("adapters/codex/skills/cloak/templates/bryl-minimal-design.md"),
    ),
)
NORMALIZED_EXPORT_PARITY_PATHS = (
    (Path("skills/conductor/SKILL.md"), Path("adapters/codex/skills/conductor/SKILL.md")),
    (Path("ROUTING_MAP.md"), Path("adapters/codex/skills/conductor/ROUTING_MAP.md")),
    (Path("skills/arbiter/SKILL.md"), Path("adapters/codex/skills/arbiter/SKILL.md")),
    (Path("skills/arbiter/OUTPUT_FORMATS.md"), Path("adapters/codex/skills/arbiter/OUTPUT_FORMATS.md")),
    (Path("skills/overseer/SKILL.md"), Path("adapters/codex/skills/overseer/SKILL.md")),
    (Path("skills/overseer/OUTPUT_FORMATS.md"), Path("adapters/codex/skills/overseer/OUTPUT_FORMATS.md")),
    (Path("skills/the-steward/SKILL.md"), Path("adapters/codex/skills/the-steward/SKILL.md")),
    (Path("skills/the-governor/SKILL.md"), Path("adapters/codex/skills/the-governor/SKILL.md")),
    (Path("skills/the-steward/OUTPUT_FORMATS.md"), Path("adapters/codex/skills/the-steward/OUTPUT_FORMATS.md")),
    (Path("skills/the-governor/OUTPUT_FORMATS.md"), Path("adapters/codex/skills/the-governor/OUTPUT_FORMATS.md")),
)
def print_error(message):
    print(f"\033[91mERROR: {message}\033[0m")


def read_text(path):
    return path.read_text(encoding="utf-8")


def parse_frontmatter(content):
    return re.search(r"(?s)^---\r?\n(.*?)\r?\n---", content)


def strip_frontmatter(content):
    match = parse_frontmatter(content)
    if not match:
        return content.strip()
    return content[match.end():].strip()


def normalize_body_for_parity(content):
    body = strip_frontmatter(content)
    normalized = []
    in_code_fence = False
    for line in body.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            in_code_fence = not in_code_fence
        elif not in_code_fence:
            references = (reference for group in PORTABLE_REFERENCES.values() for reference in group)
            for source, canonical, exported, anchor in sorted(references, key=lambda item: len(item[1]), reverse=True):
                marker = f"__PORTABLE_REFERENCE_{anchor.upper().replace('-', '_')}__"
                # Retain legacy-depth parity compatibility; operational reference
                # validation runs first and still rejects that path when unresolved.
                if canonical.startswith("../../"):
                    line = line.replace(f"../../{canonical}", marker)
                line = line.replace(canonical, marker).replace(exported, marker)
            line = line.replace("../../ROUTING_MAP.md", "ROUTING_MAP.md")
            line = line.replace("../../../../ROUTING_MAP.md", "ROUTING_MAP.md")
        normalized.append(line)
    return "".join(normalized)


def iter_prose_lines(content):
    in_code_fence = False
    for line_number, line in enumerate(content.splitlines(), 1):
        if re.match(r"^\s*(```|~~~)", line):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence or line.startswith(("    ", "\t")):
            continue
        yield line_number, line


def get_markdown_links(content):
    for line_number, line in iter_prose_lines(content):
        for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", line):
            yield line_number, match


def normalize_link_target(raw_target):
    target = raw_target.strip()
    if not target or target.startswith("#"):
        return None
    if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return target.split("#", 1)[0]


def is_within(path, boundary):
    try:
        path.relative_to(boundary)
        return True
    except ValueError:
        return False


def validate_reference(markdown_file, raw_target, boundary, root, reference_type):
    target = normalize_link_target(raw_target)
    if not target:
        return 0

    target_path = (markdown_file.parent / target).resolve()
    relative_file = markdown_file.relative_to(root).as_posix()
    if not is_within(target_path, boundary):
        print_error(f"Path escape in {relative_file}: {target}")
        return 1
    if not target_path.is_file():
        print_error(f"Missing {reference_type} target in {relative_file}: {target}")
        return 1
    return 0


def validate_local_references(markdown_root, boundary, root=None, validate_backticks=True):
    boundary = boundary.resolve()
    root = (root or boundary).resolve()
    markdown_root = markdown_root.resolve()
    markdown_files = [markdown_root] if markdown_root.is_file() else sorted(markdown_root.rglob("*.md"))
    errors = 0

    for markdown_file in markdown_files:
        content = read_text(markdown_file)
        for _, match in get_markdown_links(content):
            errors += validate_reference(markdown_file, match.group(1), boundary, root, "Markdown link")

        if not validate_backticks or "examples" in markdown_file.relative_to(markdown_root if markdown_root.is_dir() else markdown_file.parent).parts:
            continue

        for _, line in iter_prose_lines(content):
            prose_without_links = re.sub(r"!?\[[^\]]*\]\([^)]+\)", "", line)
            for match in re.finditer(r"`([^`]+\.(?:md|json))`", prose_without_links, re.IGNORECASE):
                errors += validate_reference(markdown_file, match.group(1), boundary, root, "backtick file reference")
    return errors


def validate_simple_frontmatter(skill, skill_file):
    errors = 0
    content = read_text(skill_file)
    fm_match = parse_frontmatter(content)
    if not fm_match:
        print_error(f"Could not parse frontmatter in exported SKILL.md for {skill}")
        return 1

    fm = fm_match.group(1)
    for line in fm.splitlines():
        if not re.match(r"^name:", line) and not re.match(r"^description:", line):
            print_error(f"Exported SKILL.md for {skill} contains non-compliant frontmatter: {line}")
            errors += 1
    if not re.search(rf"^name:\s*{re.escape(skill)}", fm, re.MULTILINE):
        print_error(f"Exported SKILL.md for {skill} has mismatched name in frontmatter")
        errors += 1
    return errors


def get_routable_skills(routing_map_path):
    routable = set()
    if not routing_map_path.is_file():
        return routable

    for line in read_text(routing_map_path).splitlines():
        if not line.startswith("|"):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if len(columns) < 2 or columns[0] in {"Task Type", "-----------"}:
            continue
        for match in re.finditer(r"`([a-z][a-z0-9-]+)`", columns[1]):
            routable.add(match.group(1))
    return routable


def get_conductor_required_skills(conductor_skill_path, manifest_skills):
    if not conductor_skill_path.is_file():
        return set()

    content = read_text(conductor_skill_path)
    required = {slug for slug in manifest_skills if re.search(rf"`{re.escape(slug)}`", content)}
    for label, slug in SKILL_NAME_ALIASES.items():
        if re.search(rf"\b{re.escape(label)}\b", content):
            required.add(slug)
    return required


def build_portable_reference_context(root, skill):
    lines = [
        "# Portable Reference Context",
        "",
        "Generated from canonical Orchestra sources. Indented snapshots are code-only context; file references inside snapshots are not package navigation targets.",
    ]
    for source, canonical, exported, anchor in PORTABLE_REFERENCES[skill]:
        source_path = root / source
        lines.extend(("", f'<a id="{anchor}"></a>', f"## Source: {source}", ""))
        source_lines = read_text(source_path).replace("\r\n", "\n").rstrip("\r\n").split("\n")
        lines.extend(f"    {line.rstrip()}" if line.rstrip() else "" for line in source_lines)
    return "\n".join(lines) + "\n"


def validate_portable_reference_context(root, codex_skills_dir):
    errors = 0
    for skill in PORTABLE_REFERENCES:
        bundle = codex_skills_dir / skill / "REFERENCE_CONTEXT.md"
        if not bundle.is_file():
            print_error(f"Missing portable reference bundle: {bundle.relative_to(codex_skills_dir.parent).as_posix()}")
            errors += 1
            continue
        expected = build_portable_reference_context(root, skill)
        if read_text(bundle) != expected:
            print_error(f"Portable reference bundle differs from canonical sources: {bundle.relative_to(codex_skills_dir.parent).as_posix()}")
            errors += 1
    return errors


def validate_tracked_export_parity(root):
    errors = 0

    for source_relative, export_relative in TRACKED_EXPORT_PARITY_PATHS:
        source_path = root / source_relative
        export_path = root / export_relative

        if not source_path.is_file():
            print_error(f"Missing source file for export parity validation: {source_relative.as_posix()}")
            errors += 1
            continue

        if not export_path.is_file():
            print_error(f"Missing exported file for parity validation: {export_relative.as_posix()}")
            errors += 1
            continue

        if source_path.read_bytes() != export_path.read_bytes():
            print_error(
                "Tracked export copy differs from source: "
                f"{export_relative.as_posix()} != {source_relative.as_posix()}"
            )
            errors += 1

    return errors


def validate_normalized_export_parity(root):
    errors = 0
    for source_relative, export_relative in NORMALIZED_EXPORT_PARITY_PATHS:
        source_path = root / source_relative
        export_path = root / export_relative
        if not source_path.is_file():
            print_error(f"Missing source file for normalized export parity validation: {source_relative.as_posix()}")
            errors += 1
            continue
        if not export_path.is_file():
            print_error(f"Missing exported file for normalized export parity validation: {export_relative.as_posix()}")
            errors += 1
            continue

        source_body = normalize_body_for_parity(read_text(source_path))
        export_body = normalize_body_for_parity(read_text(export_path))
        if source_body != export_body:
            print_error(
                "Normalized export body differs from source: "
                f"{export_relative.as_posix()} != {source_relative.as_posix()}"
            )
            errors += 1
    return errors


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Validate Codex export output.")
    parser.add_argument(
        "--export-root",
        type=Path,
        default=None,
        help="Root directory containing the exported Codex skills folder.",
    )
    parser.add_argument(
        "--skip-tracked-export-parity",
        action="store_true",
        help="Skip tracked export parity checks.",
    )
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent.parent
    export_root = args.export_root.resolve() if args.export_root else script_dir
    codex_skills_dir = export_root / "skills"
    
    manifest_path = root / "plugin.json"
    if not manifest_path.is_file():
        print_error(f"plugin.json not found at {manifest_path}")
        sys.exit(1)
        
    manifest = json.loads(read_text(manifest_path))
    registry = SkillRegistry(ManifestRepository(root), SkillSourceRepository(root))
    skills = [skill.slug for skill in registry.load_skills()]
    skill_set = set(skills)
    
    errors = 0

    for skill in sorted(REFERENCE_VALIDATION_SKILLS):
        errors += validate_local_references(
            root / "skills" / skill,
            boundary=root,
            root=root,
            validate_backticks=True,
        )
    
    for skill in skills:
        skill_dir = codex_skills_dir / skill
        if not skill_dir.is_dir():
            print_error(f"Missing exported skill folder: {skill_dir}")
            errors += 1
            continue
            
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            print_error(f"Missing SKILL.md in exported {skill}")
            errors += 1
        else:
            errors += validate_simple_frontmatter(skill, skill_file)
                
        out_file = skill_dir / "OUTPUT_FORMATS.md"
        if not out_file.is_file():
            print_error(f"Missing OUTPUT_FORMATS.md in exported {skill}")
            errors += 1
            
        stale_routing = skill_dir / "ROUTING_MATRIX.md"
        if stale_routing.is_file():
            print_error(f"Found stale ROUTING_MATRIX.md in exported {skill}")
            errors += 1
            
        if skill == "conductor":
            map_file = skill_dir / "ROUTING_MAP.md"
            if not map_file.is_file():
                print_error("Missing ROUTING_MAP.md in exported conductor")
                errors += 1

        errors += validate_local_references(
            skill_dir,
            boundary=export_root,
            root=export_root,
            validate_backticks=skill in REFERENCE_VALIDATION_SKILLS,
        )

    errors += validate_portable_reference_context(root, codex_skills_dir)

    routing_map = codex_skills_dir / "conductor" / "ROUTING_MAP.md"
    conductor_skill = codex_skills_dir / "conductor" / "SKILL.md"
    required_skills = get_routable_skills(routing_map) | get_conductor_required_skills(conductor_skill, skill_set)
    for required_skill in sorted(required_skills):
        if required_skill not in skill_set:
            continue
        if not (codex_skills_dir / required_skill / "SKILL.md").is_file():
            print_error(f"Exported conductor references missing skill: {required_skill}")
            errors += 1

    if not args.skip_tracked_export_parity and export_root == script_dir.resolve():
        errors += validate_tracked_export_parity(root)
        errors += validate_normalized_export_parity(root)
                
    if errors > 0:
        print_error(f"Codex export validation failed with {errors} errors.")
        sys.exit(1)
        
    print("\033[92mSUCCESS: Codex export validation passed!\033[0m")
    sys.exit(0)

if __name__ == "__main__":
    main()
