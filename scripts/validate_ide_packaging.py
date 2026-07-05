import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestra_runtime.factories import AdapterFactory


PACKAGING_SCAFFOLDS = {
    "cursor": (
        "README.md",
        "install-guide.md",
        "workspace-instructions.template.md",
        "package.json",
    ),
    "windsurf": (
        "README.md",
        "install-guide.md",
        "workspace-instructions.template.md",
        "package.json",
    ),
    "vscode": (
        "README.md",
        "install-guide.md",
        "workspace-instructions.template.md",
        "package.json",
    ),
}

RESTRICTED_ORCHESTRA_KEYS = {
    "routing",
    "governance",
    "execution",
    "manifest_parsing",
    "audit_logging",
}


def load_package_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_packaging_scaffold(repo_root: Path | str) -> list[str]:
    root = Path(repo_root)
    errors: list[str] = []

    for adapter_name, required_files in PACKAGING_SCAFFOLDS.items():
        adapter_dir = root / "adapters" / adapter_name
        for relative_name in required_files:
            if not (adapter_dir / relative_name).is_file():
                errors.append(f"Missing packaging file: adapters/{adapter_name}/{relative_name}")

        package_path = adapter_dir / "package.json"
        if not package_path.is_file():
            continue

        try:
            payload = load_package_manifest(package_path)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in adapters/{adapter_name}/package.json: {exc}")
            continue

        orchestra_block = payload.get("orchestra")
        if not isinstance(orchestra_block, dict):
            errors.append(f"Missing orchestra metadata block in adapters/{adapter_name}/package.json")
            continue

        if orchestra_block.get("runtime_adapter") != adapter_name:
            errors.append(
                f"Incorrect runtime adapter reference in adapters/{adapter_name}/package.json: "
                f"{orchestra_block.get('runtime_adapter')}"
            )

        if orchestra_block.get("scaffold_only") is not True:
            errors.append(f"Expected scaffold_only=true in adapters/{adapter_name}/package.json")

        restricted_hits = RESTRICTED_ORCHESTRA_KEYS.intersection(orchestra_block.keys())
        if restricted_hits:
            errors.append(
                f"Packaging manifest in adapters/{adapter_name}/package.json claims core-owned responsibilities: "
                f"{', '.join(sorted(restricted_hits))}"
            )

        templates = orchestra_block.get("entry_templates", [])
        if not isinstance(templates, list) or not templates:
            errors.append(f"Missing entry_templates in adapters/{adapter_name}/package.json")
        else:
            for template_name in templates:
                if not (adapter_dir / template_name).is_file():
                    errors.append(
                        f"Missing referenced entry template in adapters/{adapter_name}/package.json: {template_name}"
                    )

        try:
            AdapterFactory.create(adapter_name, root)
        except ValueError as exc:
            errors.append(f"AdapterFactory cannot build '{adapter_name}': {exc}")

    return errors


def main():
    errors = validate_packaging_scaffold(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        sys.exit(1)

    print("SUCCESS: IDE packaging scaffolds validated.")
    sys.exit(0)


if __name__ == "__main__":
    main()
