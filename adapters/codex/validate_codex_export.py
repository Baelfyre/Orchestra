import json
import re
import sys
from pathlib import Path


SKILL_NAME_ALIASES = {
    "Steward": "the-steward",
    "The Steward": "the-steward",
    "Governor": "the-governor",
    "The Governor": "the-governor",
}

ALLOWED_BACKTICK_EXPORT_TARGETS = {"templates/bryl-minimal-design.md"}
TRACKED_EXPORT_PARITY_PATHS = (
    (
        Path("skills/cloak/templates/bryl-minimal-design.md"),
        Path("adapters/codex/skills/cloak/templates/bryl-minimal-design.md"),
    ),
)


def print_error(message):
    print(f"\033[91mERROR: {message}\033[0m")


def read_text(path):
    return path.read_text(encoding="utf-8")


def parse_frontmatter(content):
    return re.search(r"(?s)^---\r?\n(.*?)\r?\n---", content)


def get_markdown_links(content):
    return re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", content)


def normalize_link_target(raw_target):
    target = raw_target.strip()
    if not target or target.startswith("#"):
        return None
    if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
        return None
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return target.split("#", 1)[0]


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


def validate_markdown_links(skill_dir, root):
    errors = 0
    for markdown_file in skill_dir.rglob("*.md"):
        content = read_text(markdown_file)
        for match in get_markdown_links(content):
            target = normalize_link_target(match.group(1))
            if not target:
                continue

            target_path = (markdown_file.parent / target).resolve()
            if target_path.exists():
                continue

            relative_file = markdown_file.relative_to(root).as_posix()
            print_error(f"Missing relative link target in {relative_file}: {target}")
            errors += 1
    return errors


def get_backtick_file_refs(content):
    return re.finditer(r"`([^`]+(?:\.md|\.json))`", content)


def validate_allowed_backtick_targets(markdown_file, root):
    errors = 0
    content = read_text(markdown_file)

    for match in get_backtick_file_refs(content):
        target = normalize_link_target(match.group(1))
        if target not in ALLOWED_BACKTICK_EXPORT_TARGETS:
            continue

        target_path = (markdown_file.parent / target).resolve()
        if target_path.exists():
            continue

        relative_file = markdown_file.relative_to(root).as_posix()
        print_error(f"Missing backtick file reference in {relative_file}: {target}")
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

def main():
    script_dir = Path(__file__).resolve().parent
    codex_skills_dir = script_dir / "skills"
    root = script_dir.parent.parent
    
    manifest_path = root / "plugin.json"
    if not manifest_path.is_file():
        print_error(f"plugin.json not found at {manifest_path}")
        sys.exit(1)
        
    manifest = json.loads(read_text(manifest_path))
        
    skills = [s.get("slug") for s in manifest.get("skills", []) if s.get("slug")]
    skill_set = set(skills)
    
    errors = 0
    
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
            errors += validate_allowed_backtick_targets(skill_file, root)
                
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

        errors += validate_markdown_links(skill_dir, root)

    routing_map = codex_skills_dir / "conductor" / "ROUTING_MAP.md"
    conductor_skill = codex_skills_dir / "conductor" / "SKILL.md"
    required_skills = get_routable_skills(routing_map) | get_conductor_required_skills(conductor_skill, skill_set)
    for required_skill in sorted(required_skills):
        if required_skill not in skill_set:
            continue
        if not (codex_skills_dir / required_skill / "SKILL.md").is_file():
            print_error(f"Exported conductor references missing skill: {required_skill}")
            errors += 1

    errors += validate_tracked_export_parity(root)
                
    if errors > 0:
        print_error(f"Codex export validation failed with {errors} errors.")
        sys.exit(1)
        
    print("\033[92mSUCCESS: Codex export validation passed!\033[0m")
    sys.exit(0)

if __name__ == "__main__":
    main()
