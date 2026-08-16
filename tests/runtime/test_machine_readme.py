import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_machine_readme_is_strictly_versioned_and_points_to_human_readme():
    machine = _load("README.json")
    schema = _load("machine/schemas/readme-machine-index.schema.json")
    assert machine["schema_version"] == "orchestra.readme-machine-index.v1"
    assert machine["document_role"] == "machine_repository_index"
    assert machine["authority"] == "derived_and_parity_validated_projection"
    assert machine["human_readme"] == "README.md"
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False


def test_machine_readme_repository_identity_matches_plugin_manifest():
    machine = _load("README.json")
    plugin = _load("plugin.json")
    repo = machine["repository"]
    assert repo["name"] == plugin["display_name"]
    assert repo["url"] == plugin["repository"]
    assert repo["license"] == plugin["license"]
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


def test_machine_readme_control_plane_stage_matches_machine_migration_state():
    machine = _load("README.json")
    migration = _load("machine/migration/control-plane.v1.json")
    assert machine["governance"]["control_plane_stage"] == migration["current_stage"]
    assert machine["governance"]["control_plane_stage_source"] == "machine/migration/control-plane.v1.json#/current_stage"


def test_machine_readme_murmurs_projection_matches_presentation_policy():
    machine = _load("README.json")
    policy = _load("machine/presentation/murmurs-policy.v1.json")
    presentation = machine["architecture"]["presentation"]
    assert presentation["host_default_mode"] == "NORMAL"
    assert presentation["opt_in_mode"] == "MURMURS"
    assert presentation["dispositions"] == ["SILENT", "MURMUR", "EXPLAIN"]
    assert presentation["model_generated_filler"] is False
    assert presentation["vocabulary_injected_into_model_context"] is False
    assert presentation["presentation_may_change_machine_state"] == policy["authority_effect"]["presentation_may_change_machine_state"]
    assert presentation["presentation_may_override_governance"] == policy["authority_effect"]["presentation_may_override_governance"]
    assert presentation["required_explanation_events"] == policy["explain_required"]


def test_machine_readme_merge_readiness_is_fail_closed():
    requirements = _load("README.json")["governance"]["ordinary_merge_requirements"]
    assert requirements == {
        "mergeable": True,
        "mergeable_state": "clean",
        "expected_head_protection": True,
        "governed_bypass_allowed": False,
    }


def test_machine_readme_scan_order_is_unique_contiguous_and_existing():
    machine = _load("README.json")
    records = machine["machine_scan_order"]
    orders = [record["order"] for record in records]
    assert orders == list(range(1, len(records) + 1))
    assert len({record["path"] for record in records}) == len(records)
    for record in records:
        path = ROOT / record["path"]
        assert path.exists(), record["path"]


def test_machine_readme_contract_references_exist():
    machine = _load("README.json")
    for key, value in machine["machine_contracts"].items():
        if key == "schemas_directory":
            assert (ROOT / value).is_dir()
        else:
            assert (ROOT / value).is_file(), f"{key}: {value}"


def test_ai_review_guidance_prefers_machine_contracts_for_exact_values():
    guidance = _load("README.json")["ai_review_guidance"]
    assert guidance["preferred_entrypoint"] == "README.json"
    assert guidance["do_not_synthesize_full_git_identifiers"] is True
    assert guidance["prefer_machine_contracts_for_exact_values"] is True
    assert guidance["retrieve_human_docs_for_rationale"] is True
    assert guidance["treat_mergeable_boolean_without_clean_mergeable_state_as_insufficient"] is True
    assert guidance["treat_murmurs_as_presentation_only"] is True
    assert guidance["do_not_claim_murmurs_token_savings_without_comparable_host_reported_counters"] is True
