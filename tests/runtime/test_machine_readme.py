import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_machine_readme_is_strictly_versioned_and_points_to_human_entrypoints():
    machine = _load("README.json")
    schema = _load("machine/schemas/readme-machine-index.schema.json")
    assert machine["schema_version"] == "orchestra.readme-machine-index.v2"
    assert machine["document_role"] == "machine_repository_index"
    assert machine["authority"] == "derived_and_parity_validated_projection"
    assert machine["human_readme"] == "README.md"
    assert machine["human_documentation_map"] == "docs/README.md"
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == machine["schema_version"]


def test_machine_readme_repository_identity_matches_plugin_manifest():
    machine = _load("README.json")
    plugin = _load("plugin.json")
    repo = machine["repository"]
    assert repo["name"] == plugin["display_name"]
    assert repo["url"] == plugin["repository"]
    assert repo["license"] == plugin["license"]
    assert repo["package_version"] == plugin["version"]
    assert repo["package_version_source"] == "plugin.json#/version"


def test_machine_readme_specialist_count_matches_compiled_registry():
    machine = _load("README.json")
    registry = _load("machine/specialists/registry.v1.json")
    assert machine["specialists"]["count"] == len(registry["specialists"])
    assert machine["specialists"]["registry_source"] == "machine/specialists/registry.v1.json"


def test_machine_readme_governance_dispositions_match_machine_policy():
    machine = _load("README.json")
    policy = _load("machine/governance/policy.v1.json")
    assert machine["governance"]["transition_dispositions"] == policy["transition_dispositions"]
    assert machine["governance"]["machine_policy"] == "machine/governance/policy.v1.json"


def test_machine_readme_scan_order_is_unique_contiguous_and_existing():
    machine = _load("README.json")
    records = machine["machine_scan_order"]
    orders = [record["order"] for record in records]
    assert orders == list(range(1, len(records) + 1))
    assert len({record["path"] for record in records}) == len(records)
    for record in records:
        path = ROOT / record["path"].rstrip("/")
        assert path.exists(), record["path"]


def test_machine_readme_contract_references_exist():
    machine = _load("README.json")
    for key, value in machine["machine_contracts"].items():
        path = ROOT / value.rstrip("/")
        assert path.exists(), f"{key}: {value}"
        if key.endswith("_directory") or key == "schemas_directory":
            assert path.is_dir(), f"{key}: {value}"
        else:
            assert path.is_file(), f"{key}: {value}"


def test_ai_review_guidance_prefers_machine_contracts_for_exact_values():
    guidance = _load("README.json")["ai_review_guidance"]
    assert guidance["preferred_entrypoint"] == "README.json"
    assert guidance["do_not_synthesize_full_git_identifiers"] is True
    assert guidance["prefer_machine_contracts_for_exact_values"] is True
    assert guidance["retrieve_human_docs_for_rationale"] is True
    assert guidance["do_not_infer_authority_from_prose"] is True
