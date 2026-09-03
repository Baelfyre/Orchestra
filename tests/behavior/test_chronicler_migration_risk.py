"""Deterministic OR-GOV-4 behavior checks for Chronicler migration planning."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "skills" / "chronicler" / "MIGRATION_RISK_CONTRACT_GUIDE.md"
CODEX_GUIDE = ROOT / "adapters" / "codex" / "skills" / "chronicler" / "MIGRATION_RISK_CONTRACT_GUIDE.md"
SCHEMA = ROOT / "machine" / "schemas" / "migration-risk-contract.v1.schema.json"

try:
    import jsonschema
except ImportError:  # pragma: no cover - repository validation normally installs jsonschema
    jsonschema = None


def _guide() -> str:
    return GUIDE.read_text(encoding="utf-8")


def _contract(**overrides: object) -> dict[str, object]:
    contract: dict[str, object] = {
        "schema_version": "orchestra.migration-risk-contract.v1",
        "contract_name": "MigrationRiskContract",
        "owner": "chronicler",
        "revision": "rev-or-gov-4-test",
        "database_engine": "SQLite",
        "schema_revision": "20260903_local_dev",
        "production_data": False,
        "locking_implications": "Local file-lock behavior requires confirmation for the exact operation.",
        "compatibility_required": False,
        "backfill_required": False,
        "migration_pattern": "DIRECT",
        "risk": "LOW",
        "human_gate_required": False,
    }
    contract.update(overrides)
    return contract


def _schema_errors(contract: dict[str, object]) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if jsonschema is not None:
        return [error.message for error in jsonschema.Draft202012Validator(schema).iter_errors(contract)]
    required = schema["required"]
    errors = [f"missing {name}" for name in required if name not in contract]
    if not isinstance(contract.get("production_data"), bool):
        errors.append("production_data must be boolean")
    return errors


def _assert_valid(contract: dict[str, object]) -> None:
    assert _schema_errors(contract) == []


def test_t1_development_only_nullable_field_is_low_and_direct() -> None:
    contract = _contract(
        schema_revision="20260903_local_nullable_column",
        production_data=False,
        migration_pattern="DIRECT",
        risk="LOW",
        human_gate_required=False,
    )
    _assert_valid(contract)
    assert contract["production_data"] is False
    assert contract["backfill_required"] is False
    assert "DEVELOPMENT_ONLY" in _guide()


def test_t2_live_tenant_migration_requires_compatibility_and_backfill() -> None:
    contract = _contract(
        database_engine="UNKNOWN",
        database_version="UNKNOWN",
        production_data=True,
        affected_records="several million existing production rows",
        write_traffic="UNKNOWN",
        locking_implications="Locking and write impact require engine/version and live-traffic evidence.",
        compatibility_required=True,
        backfill_required=True,
        migration_pattern="EXPAND_CONTRACT",
        deployment_sequence=["expand permissively", "backfill in measured batches", "validate", "enforce later"],
        risk="HIGH",
        human_gate_required=True,
    )
    _assert_valid(contract)
    assert contract["compatibility_required"] is True
    assert contract["backfill_required"] is True
    assert len(contract["deployment_sequence"]) > 1
    assert "one-step destructive enforcement" in _guide()


def test_t3_unknown_production_size_stays_unknown() -> None:
    contract = _contract(production_data=True, affected_records="UNKNOWN", risk="UNKNOWN")
    _assert_valid(contract)
    assert contract["affected_records"] == "UNKNOWN"
    assert "Do not invent" in _guide()


def test_t4_unknown_production_presence_is_a_schema_gap_not_false() -> None:
    contract = _contract(production_data="UNKNOWN")
    assert _schema_errors(contract)
    assert contract["production_data"] != False  # noqa: E712 - explicit truth-preservation assertion
    guide = _guide()
    assert "MIGRATION_RISK_SCHEMA_GAP: UNKNOWN_PRODUCTION_STATE_NOT_REPRESENTABLE" in guide
    assert "never encode unknown production presence as `false`" in guide


def test_t5_index_on_active_table_requires_engine_and_lock_evidence() -> None:
    contract = _contract(
        database_engine="UNKNOWN",
        database_version="UNKNOWN",
        production_data=True,
        index_operation="TO_BE_MEASURED",
        migration_pattern="ENGINE_SPECIFIC",
        risk="UNKNOWN",
    )
    _assert_valid(contract)
    guide = _guide()
    assert "ENGINE_SPECIFIC_CLAIM_BLOCKED" in guide
    assert "Index operations" in guide


def test_t6_drop_column_is_destructive_and_gated() -> None:
    contract = _contract(
        production_data=True,
        migration_pattern="OTHER",
        risk="HIGH",
        human_gate_required=True,
        rollback_boundary="Before removal only; after removal restore or forward repair may be required.",
        failure_recovery="Confirm downstream readers and backup/recovery evidence before any contract step.",
    )
    _assert_valid(contract)
    assert contract["human_gate_required"] is True
    assert "Destructive or irreversible changes" in _guide()
    assert "does not execute destructive SQL" in _guide()


def test_t7_expand_contract_is_explicit_for_coexisting_app_versions() -> None:
    contract = _contract(
        production_data=True,
        compatibility_required=True,
        backfill_required=True,
        migration_pattern="EXPAND_CONTRACT",
        deployment_sequence=["expand", "transition", "backfill", "validate", "switch", "contract"],
        rollback_boundary="Before contract while old readers remain supported.",
        risk="HIGH",
        human_gate_required=True,
    )
    _assert_valid(contract)
    assert contract["compatibility_required"] is True
    assert contract["migration_pattern"] == "EXPAND_CONTRACT"
    assert "old and new application versions" in _guide()


def test_t8_unknown_write_traffic_requires_measurement() -> None:
    contract = _contract(
        production_data=True,
        write_traffic="UNKNOWN",
        backfill_required=True,
        migration_pattern="BATCHED_BACKFILL",
        risk="UNKNOWN",
    )
    _assert_valid(contract)
    assert contract["write_traffic"] == "UNKNOWN"
    assert "measurement needed" in _guide()


def test_t9_missing_engine_blocks_dialect_specific_claims() -> None:
    contract = _contract(database_engine="UNKNOWN", database_version="UNKNOWN", migration_pattern="OTHER", risk="UNKNOWN")
    _assert_valid(contract)
    assert "ENGINE_SPECIFIC_CLAIM_BLOCKED" in _guide()
    assert "portable" in _guide()


def test_t10_confirmed_engine_can_activate_engine_specific_guidance() -> None:
    contract = _contract(
        database_engine="PostgreSQL",
        database_version="16.2",
        migration_tool="alembic",
        production_data=True,
        index_operation="CREATE INDEX CONCURRENTLY",
        migration_pattern="ENGINE_SPECIFIC",
        risk="MEDIUM",
        human_gate_required=True,
    )
    _assert_valid(contract)
    assert contract["database_engine"] == "PostgreSQL"
    assert contract["database_version"] == "16.2"
    assert "confirmed engine/version" in _guide()


def test_t11_dual_read_write_is_conditional() -> None:
    contract = _contract(
        production_data=True,
        compatibility_required=True,
        migration_pattern="EXPAND_CONTRACT",
        deployment_sequence=["expand", "backfill", "validate", "switch"],
        risk="MEDIUM",
        human_gate_required=True,
    )
    _assert_valid(contract)
    assert "DUAL_READ_WRITE" not in contract["deployment_sequence"]
    assert "reserved for migrations that genuinely require" in _guide()


def test_t12_successful_command_does_not_prove_complete_backfill() -> None:
    contract = _contract(
        production_data=True,
        backfill_required=True,
        migration_pattern="BATCHED_BACKFILL",
        completion_criteria=["backfill backlog = zero", "invariant query returns no mismatches"],
        risk="HIGH",
        human_gate_required=True,
    )
    _assert_valid(contract)
    assert "backfill backlog = zero" in contract["completion_criteria"]
    assert "exit code 0 does not prove data completion" in _guide()


def test_t13_trivial_development_migration_avoids_heavyweight_ceremony() -> None:
    contract = _contract(production_data=False, migration_pattern="DIRECT", risk="LOW", human_gate_required=False)
    _assert_valid(contract)
    assert contract["human_gate_required"] is False
    assert "not automatically a human blocker" in _guide()


def test_t14_security_sensitive_tenant_field_adds_cipher_handoff() -> None:
    contract = _contract(
        production_data=True,
        affected_records="UNKNOWN",
        compatibility_required=True,
        backfill_required=True,
        migration_pattern="EXPAND_CONTRACT",
        evidence_refs=["schema-review:tenant-context", "cipher-review:pending"],
        risk="HIGH",
        human_gate_required=True,
    )
    _assert_valid(contract)
    guide = _guide()
    assert "Cipher reviews tenant isolation" in guide
    assert "Chronicler" in guide


def test_negative_authority_boundaries_are_explicit() -> None:
    guide = _guide()
    for marker in (
        "does not grant authority",
        "does not execute",
        "does not activate Dagger",
        "No contract, route, or successful test",
        "must not claim release readiness",
    ):
        assert marker in guide
    for pattern in ("DIRECT", "EXPAND_CONTRACT", "BATCHED_BACKFILL", "DUAL_READ_WRITE", "ONLINE_DDL", "ENGINE_SPECIFIC", "OTHER"):
        assert pattern in guide


def test_chronicler_route_and_handoff_sequence_are_machine_deterministic() -> None:
    routing = json.loads((ROOT / "machine" / "routing" / "routes.v1.json").read_text(encoding="utf-8"))
    route = next(item for item in routing["direct_routes"] if item["route_id"] == "migration-risk-contract")
    assert route["target"] == "chronicler"
    sequence = next(item for item in routing["ordered_sequences"] if item["route_id"] == "migration-risk-implementation-validation")
    assert sequence["sequence"] == ["chronicler", "ponytail", "overseer"]


def test_source_and_codex_migration_guide_are_identical() -> None:
    assert GUIDE.read_bytes() == CODEX_GUIDE.read_bytes()
