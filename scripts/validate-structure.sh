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

skills="amalgam-conductor cloak-meister scribe-meister meister-weaver meister-chronicler acme-overseer cipher-meister hidden-dagger"
adapters="codex vscode antigravity claude-code local-ai"
templates="generic-skill-template.md review-output-template.md audit-output-template.md routing-output-template.md safety-gate-template.md scorecard-template.md local-install-template.md"

for file in README.md LICENSE .gitignore CONTRIBUTING.md CHANGELOG.md SKILL_INDEX.md FOUNDATION.md INSTALLATION.md LOCAL_ONLY_GUIDE.md COMPATIBILITY.md VALIDATION.md ROADMAP.md assets/logo/orchestra-of-amalgamation.png; do check "$file"; done
skill_count=0
for skill in $skills; do
  check "skills/$skill/SKILL.md"
  check "assets/icons/$skill.png"
  skill_count=$((skill_count + 1))
done
adapter_count=0
for adapter in $adapters; do check "adapters/$adapter"; adapter_count=$((adapter_count + 1)); done
template_count=0
for template in $templates; do check "templates/$template"; template_count=$((template_count + 1)); done

[ "$missing" -eq 0 ] || exit 1
echo "Structure valid: $skill_count skills, $adapter_count adapters, $template_count templates."
