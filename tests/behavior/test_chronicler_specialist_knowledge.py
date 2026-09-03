from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "skills" / "chronicler"
CODEX = ROOT / "adapters" / "codex" / "skills" / "chronicler"

REQUIRED_SUPPORT = [
    "DATABASE_CHECKLIST.md",
    "DATABASE_STANDARDS.md",
    "DB_DOCUMENTATION_TEMPLATES.md",
    "OUTPUT_FORMATS.md",
    "SQL_FOUNDATIONS_GUIDE.md",
    "SQL_REVIEW_GUIDE.md",
    "DATABASE_DIALECT_ORM_GUIDE.md",
    "TRANSACTION_ISOLATION_LOCKING_GUIDE.md",
    "QUERY_PLAN_TENANT_ISOLATION_GUIDE.md",
    "ZERO_DOWNTIME_MIGRATION_GUIDE.md",
    "MIGRATION_RISK_CONTRACT_GUIDE.md",
    "examples/constraints-review-example.md",
    "examples/database-documentation-example.md",
    "examples/erd-database-review-example.md",
    "examples/schema-review-example.md",
    "examples/seed-data-review-example.md",
    "examples/zero-downtime-schema-change-example.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, *needles: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"Missing required Chronicler knowledge markers: {missing}")


def main() -> None:
    for relative in REQUIRED_SUPPORT:
        source = SOURCE / relative
        mirror = CODEX / relative
        if not source.is_file():
            raise AssertionError(f"Missing canonical Chronicler support file: {relative}")
        if not mirror.is_file():
            raise AssertionError(f"Missing Codex Chronicler support file: {relative}")
        if source.read_bytes() != mirror.read_bytes():
            raise AssertionError(f"Chronicler source/Codex support parity failed: {relative}")

    skill = read(SOURCE / "SKILL.md")
    for filename in [
        "DATABASE_DIALECT_ORM_GUIDE.md",
        "TRANSACTION_ISOLATION_LOCKING_GUIDE.md",
        "QUERY_PLAN_TENANT_ISOLATION_GUIDE.md",
        "ZERO_DOWNTIME_MIGRATION_GUIDE.md",
        "MIGRATION_RISK_CONTRACT_GUIDE.md",
    ]:
        if filename not in skill:
            raise AssertionError(f"Chronicler progressive disclosure does not reference {filename}")
    require(skill, "engine, major version", "example SQL and migration patterns as planning guidance")

    dialect = read(SOURCE / "DATABASE_DIALECT_ORM_GUIDE.md")
    require(
        dialect,
        "PostgreSQL",
        "MySQL",
        "SQL Server",
        "SQLite",
        "generated SQL",
        "optimistic concurrency tokens",
        "migration-history drift",
    )

    transactions = read(SOURCE / "TRANSACTION_ISOLATION_LOCKING_GUIDE.md")
    require(
        transactions,
        "READ COMMITTED",
        "REPEATABLE READ",
        "SERIALIZABLE",
        "snapshot isolation",
        "write skew",
        "deadlock graph",
        "bounded retry",
    )

    plans = read(SOURCE / "QUERY_PLAN_TENANT_ISOLATION_GUIDE.md")
    require(
        plans,
        "EXPLAIN ANALYZE",
        "estimated versus actual rows",
        "non-sargable",
        "composite foreign keys",
        "connection-pool reset",
        "two synthetic tenants",
    )

    migration = read(SOURCE / "ZERO_DOWNTIME_MIGRATION_GUIDE.md")
    require(
        migration,
        "Expand-Migrate-Contract",
        "stable-key batches",
        "replication lag",
        "Rollback Boundaries",
        "`PLANNED_UNEXECUTED`",
        "Never infer production authority",
    )

    contract = read(SOURCE / "MIGRATION_RISK_CONTRACT_GUIDE.md")
    require(
        contract,
        "MigrationRiskContract",
        "MIGRATION SAFETY MUST BE EVIDENCE-BOUND",
        "MIGRATION_RISK_SCHEMA_GAP: UNKNOWN_PRODUCTION_STATE_NOT_REPRESENTABLE",
        "ENGINE_SPECIFIC_CLAIM_BLOCKED",
        "EXPAND_CONTRACT",
        "BATCHED_BACKFILL",
        "DUAL_READ_WRITE",
        "ONLINE_DDL",
        "rollback_boundary",
        "human_gate_required",
        "does not execute destructive SQL",
    )

    example = read(SOURCE / "examples" / "zero-downtime-schema-change-example.md")
    require(
        example,
        "`PLANNED_UNEXECUTED`",
        "No schema or data mutation occurred",
        "PostgreSQL 16 non-production clone",
        "Stop Conditions",
        "No executable production command is provided",
    )

    if (SOURCE / "patterns").exists():
        raise AssertionError("SK6 audit selected Markdown-only depth; unexpected Chronicler patterns directory was added")

    print(
        "Chronicler specialist knowledge regression passed for "
        f"{len(REQUIRED_SUPPORT)} mirrored support files with no database execution."
    )


if __name__ == "__main__":
    main()
