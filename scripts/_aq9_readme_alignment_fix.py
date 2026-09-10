#!/usr/bin/env python3
"""Temporary AQ9 alignment repair. Self-deleted before candidate commit."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

readme_path = ROOT / "README.json"
text = readme_path.read_text(encoding="utf-8")

validation_added = '''    "prai_workflow_dispatch_baseline": "PRAI workflow_dispatch requires the explicit approved_base_sha input bound to ORCHESTRA_APPROVED_BASE_SHA; pull_request comparison identity remains event-derived.",
    "aq9_deep_assurance_contract": "machine/adaptive/aq9-deep-assurance.v1.json",
    "aq9_deep_assurance_schema": "machine/schemas/aq9-deep-assurance.v1.schema.json",
    "aq9_deep_assurance_validator": "scripts/validation/validate_aq9.py",
    "aq9_deep_assurance_runtime_test": "tests/runtime/test_adaptive_assurance_aq9.py"
'''
validation_original = '''    "prai_workflow_dispatch_baseline": "PRAI workflow_dispatch requires the explicit approved_base_sha input bound to ORCHESTRA_APPROVED_BASE_SHA; pull_request comparison identity remains event-derived."
'''
if validation_added not in text:
    raise SystemExit("AQ9 temporary validation block not found")
text = text.replace(validation_added, validation_original, 1)

reference_added = '''    "adaptive_assurance_aq8_reference": "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md",
    "adaptive_assurance_aq9_reference": "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md"
'''
reference_original = '''    "adaptive_assurance_aq8_reference": "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md"
'''
if reference_added not in text:
    raise SystemExit("AQ9 temporary architecture-reference block not found")
text = text.replace(reference_added, reference_original, 1)

machine_anchor = '''    "adaptive_assurance_aq8_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ8.md",
'''
machine_addition = machine_anchor + '''    "adaptive_assurance_aq9_contract": "machine/adaptive/aq9-deep-assurance.v1.json",
    "adaptive_assurance_aq9_schema": "machine/schemas/aq9-deep-assurance.v1.schema.json",
    "adaptive_assurance_aq9_validator": "scripts/validation/validate_aq9.py",
    "adaptive_assurance_aq9_validation": "tests/runtime/test_adaptive_assurance_aq9.py",
    "adaptive_assurance_aq9_documentation": "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md",
'''
if '"adaptive_assurance_aq9_contract"' not in text:
    if machine_anchor not in text:
        raise SystemExit("AQ9 machine_contracts anchor not found")
    text = text.replace(machine_anchor, machine_addition, 1)
readme_path.write_text(text, encoding="utf-8")

validator_path = ROOT / "scripts/validation/validate_aq9.py"
validator = validator_path.read_text(encoding="utf-8")
old = '''    validation = readme["validation"]
    documentation = readme["documentation"]
    _require(validation["aq9_deep_assurance_contract"] == "machine/adaptive/aq9-deep-assurance.v1.json", "README AQ9 contract reference drift")
    _require(validation["aq9_deep_assurance_schema"] == "machine/schemas/aq9-deep-assurance.v1.schema.json", "README AQ9 schema reference drift")
    _require(validation["aq9_deep_assurance_validator"] == "scripts/validation/validate_aq9.py", "README AQ9 validator reference drift")
    _require(validation["aq9_deep_assurance_runtime_test"] == "tests/runtime/test_adaptive_assurance_aq9.py", "README AQ9 runtime-test reference drift")
    _require(documentation["adaptive_assurance_aq9_reference"] == "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md", "README AQ9 architecture reference drift")
'''
new = '''    machine_contracts = readme["machine_contracts"]
    _require(machine_contracts["adaptive_assurance_aq9_contract"] == "machine/adaptive/aq9-deep-assurance.v1.json", "README AQ9 contract reference drift")
    _require(machine_contracts["adaptive_assurance_aq9_schema"] == "machine/schemas/aq9-deep-assurance.v1.schema.json", "README AQ9 schema reference drift")
    _require(machine_contracts["adaptive_assurance_aq9_validator"] == "scripts/validation/validate_aq9.py", "README AQ9 validator reference drift")
    _require(machine_contracts["adaptive_assurance_aq9_validation"] == "tests/runtime/test_adaptive_assurance_aq9.py", "README AQ9 runtime-test reference drift")
    _require(machine_contracts["adaptive_assurance_aq9_documentation"] == "docs/architecture/ADAPTIVE_ASSURANCE_AQ9.md", "README AQ9 architecture reference drift")
'''
if old not in validator:
    raise SystemExit("AQ9 validator README block not found")
validator_path.write_text(validator.replace(old, new, 1), encoding="utf-8")

print("AQ9_README_ALIGNMENT=PASS")
