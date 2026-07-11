import os
import sys

# Add scripts directory to path to import helpers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import helpers

def main():
    root = helpers.get_project_root()

    required_root = [
        'README.md',
        'CHANGELOG.md',
        'LICENSE',
        'plugin.json',
        'AGENTS.md',
        'ROUTING_MAP.md',
        'SKILL_INDEX.md',
        'docs/CONTRIBUTING.md',
        'docs/meta/CHANGELOG.md',
        'docs/meta/DISCLAIMER.md',
        'docs/project/FOUNDATION.md',
        'docs/project/ROADMAP.md',
        'docs/project/PLUGIN_READINESS.md',
        'docs/project/MANIFEST_SCHEMA.md',
        'docs/project/V1_READINESS_CHECKLIST.md',
        'docs/setup/INSTALLATION.md',
        'docs/setup/LOCAL_ONLY_GUIDE.md',
        'docs/setup/COMPATIBILITY.md',
        'docs/setup/VALIDATION.md',
        'assets/logo/orchestra.ico'
    ]

    adapters = ['codex','cursor','jetbrains','neovim','windsurf','vscode','zed','antigravity','claude-code','local-ai']

    templates = [
        'generic-skill-template.md','review-output-template.md','audit-output-template.md',
        'routing-output-template.md','safety-gate-template.md','scorecard-template.md',
        'local-install-template.md'
    ]

    tests = [
        'tests/behavior/BEHAVIOR_TEST_MATRIX.md',
        'tests/behavior/MANUAL_TESTING_GUIDE.md',
        'tests/behavior/GOVERNANCE_SCENARIOS.md'
    ]

    missing = []

    manifest = helpers.get_json_manifest(os.path.join(root, 'plugin.json'))
    manifest_skills = manifest.get('skills', [])
    manifest_commands = manifest.get('commands', [])

    helpers.write_color_host('INFO', 'Structure Validator: Verifying root repository files...')
    for file in required_root:
        if not helpers.test_file_not_empty(os.path.join(root, file.replace('/', os.sep))):
            missing.append(file)

    helpers.write_color_host('INFO', 'Structure Validator: Verifying manifest-declared skills and assets...')
    for skill in manifest_skills:
        skill_path = skill.get('skill_path', '')
        skill_md = os.path.join(root, skill_path.replace('/', os.sep))
        if not helpers.test_file_not_empty(skill_md):
            missing.append(skill_path)

        skill_folder = os.path.dirname(skill_md)
        formats_file = os.path.join(skill_folder, 'OUTPUT_FORMATS.md')
        formats_file_relative = os.path.relpath(formats_file, root).replace(os.sep, '/')
        if not helpers.test_file_not_empty(formats_file):
            missing.append(formats_file_relative)

        icon_path = skill.get('icon_path', '')
        if icon_path and not helpers.test_file_not_empty(os.path.join(root, icon_path.replace('/', os.sep))):
            missing.append(icon_path)

    helpers.write_color_host('INFO', 'Structure Validator: Verifying manifest-declared commands...')
    for command in manifest_commands:
        command_file = f"commands/{command}.md"
        if not helpers.test_file_not_empty(os.path.join(root, command_file.replace('/', os.sep))):
            missing.append(command_file)

    helpers.write_color_host('INFO', 'Structure Validator: Verifying adapters, templates and test configurations...')
    for adapter in adapters:
        path = os.path.join(root, "adapters", adapter)
        if not os.path.isdir(path):
            missing.append(f"adapters/{adapter}")

    for template in templates:
        path = os.path.join(root, "templates", template)
        if not helpers.test_file_not_empty(path):
            missing.append(f"templates/{template}")

    for test_file in tests:
        path = os.path.join(root, test_file.replace('/', os.sep))
        if not helpers.test_file_not_empty(path):
            missing.append(test_file)

    if missing:
        for m in missing:
            helpers.write_color_host('ERROR', f"Missing or invalid file: {m}")
        sys.exit(1)

    helpers.write_color_host('SUCCESS', f"Structure valid: {len(manifest_skills)} skills, {len(manifest_commands)} commands, {len(adapters)} adapters, {len(templates)} templates, {len(tests)} tests verified.")
    sys.exit(0)

if __name__ == "__main__":
    main()
