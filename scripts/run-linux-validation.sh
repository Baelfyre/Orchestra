#!/usr/bin/env sh
set -eu

echo "ORCHESTRA LINUX VALIDATION"

python scripts/validate_structure.py
python scripts/validate_manifest.py
python scripts/check_stale_references.py
python scripts/governance_check.py --strict
python tests/behavior/run_tests.py
python adapters/codex/validate_codex_export.py
python scripts/router_benchmark_runner.py
python tests/behavior/test_router_benchmark_fixture_validation.py
python scripts/runtime_guardrail.py --enabled --enforce
python scripts/check_prompt_load_thresholds.py
python -m json.tool plugin.json > /dev/null

# Path-scoped diff check avoids Windows bind-mount line-ending noise
git diff --check -- \
  docker/orchestra-linux-test.Dockerfile \
  scripts/run-linux-validation.sh \
  scripts/check-stale-references.sh \
  scripts/validate-structure.sh \
  .gitattributes

echo "LINUX VALIDATION PASSED"