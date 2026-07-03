#!/usr/bin/env sh
set -eu

ROOT=${1:-"$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"}
missing=0

check() {
  if [ ! -e "$ROOT/$1" ]; then
    echo "Missing: $1" >&2
    missing=1
  fi
}

skills="conductor cloak scribe weaver chronicler overseer cipher dagger clockwork the-steward the-governor"
adapters="codex vscode antigravity claude-code local-ai"
templates="generic-skill-template.md review-output-template.md audit-output-template.md routing-output-template.md safety-gate-template.md scorecard-template.md local-install-template.md"
tests="tests/behavior/BEHAVIOR_TEST_MATRIX.md tests/behavior/MANUAL_TESTING_GUIDE.md tests/behavior/GOVERNANCE_SCENARIOS.md"

for file in README.md CHANGELOG.md LICENSE .gitignore AGENTS.md ROUTING_MAP.md SKILL_INDEX.md docs/CONTRIBUTING.md docs/meta/CHANGELOG.md docs/meta/DISCLAIMER.md docs/project/FOUNDATION.md docs/project/ROADMAP.md docs/project/PLUGIN_READINESS.md docs/project/MANIFEST_SCHEMA.md docs/project/V1_READINESS_CHECKLIST.md docs/setup/INSTALLATION.md docs/setup/LOCAL_ONLY_GUIDE.md docs/setup/COMPATIBILITY.md docs/setup/VALIDATION.md examples/plugin-manifest.example.json assets/logo/orchestra.ico; do check "$file"; done
skill_count=0
for skill in $skills; do
  check "skills/$skill/SKILL.md"
  check "skills/$skill/OUTPUT_FORMATS.md"
  check "assets/icons/$skill.ico"
  skill_count=$((skill_count + 1))
done
adapter_count=0
for adapter in $adapters; do check "adapters/$adapter"; adapter_count=$((adapter_count + 1)); done
template_count=0
for template in $templates; do check "templates/$template"; template_count=$((template_count + 1)); done
test_count=0
for test_file in $tests; do check "$test_file"; test_count=$((test_count + 1)); done

[ "$missing" -eq 0 ] || exit 1
echo "Structure valid: $skill_count skills, $adapter_count adapters, $template_count templates, $test_count tests."
