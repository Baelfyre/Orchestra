from __future__ import annotations

# @codebase_provenance_JEO
# @codebase_rights_JEO

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import sqlite3
from threading import Barrier

import pytest


class _SyntheticReceiptLifecycle:
    """Test-only SQLite proof of atomic one-time consumption and audit."""

    def __init__(self, path: Path, *, fail_audit: bool = False) -> None:
        self.path = path
        self.fail_audit = fail_audit
        with closing(self._connect()) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS receipts ("
                "reference TEXT PRIMARY KEY, receipt_id TEXT NOT NULL UNIQUE, "
                "consumed_context TEXT)"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS audit_events ("
                "event_id INTEGER PRIMARY KEY, receipt_id TEXT, reference TEXT NOT NULL, "
                "execution_context TEXT NOT NULL, outcome TEXT NOT NULL, reason TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS one_success_audit_per_receipt "
                "ON audit_events(receipt_id) WHERE outcome = 'CONSUMED'"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5, isolation_level=None)

    def add_receipt(self, reference: str, receipt_id: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                "INSERT INTO receipts(reference, receipt_id) VALUES (?, ?)",
                (reference, receipt_id),
            )

    def consume_and_audit(self, reference: str, execution_context: str) -> bool:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT receipt_id, consumed_context FROM receipts WHERE reference = ?",
                (reference,),
            ).fetchone()
            if row is None:
                receipt_id, consumed, reason = None, False, "unknown_receipt"
            else:
                receipt_id = row[0]
                consumed = row[1] is None and connection.execute(
                    "UPDATE receipts SET consumed_context = ? "
                    "WHERE reference = ? AND consumed_context IS NULL",
                    (execution_context, reference),
                ).rowcount == 1
                reason = "consumed" if consumed else "already_consumed"

            if self.fail_audit:
                raise sqlite3.OperationalError("synthetic audit write failure")
            connection.execute(
                "INSERT INTO audit_events "
                "(receipt_id, reference, execution_context, outcome, reason) "
                "VALUES (?, ?, ?, ?, ?)",
                (receipt_id, reference, execution_context, "CONSUMED" if consumed else "DENIED", reason),
            )
            connection.commit()
            return consumed
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def receipt_state(self, reference: str) -> tuple[str | None, str | None] | None:
        with closing(self._connect()) as connection:
            return connection.execute(
                "SELECT receipt_id, consumed_context FROM receipts WHERE reference = ?",
                (reference,),
            ).fetchone()

    def audit_outcomes(self) -> tuple[str, ...]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT outcome FROM audit_events ORDER BY event_id"
            ).fetchall()
        return tuple(row[0] for row in rows)


def test_audit_failure_rolls_back_synthetic_consumption_and_audit(tmp_path: Path) -> None:
    store = _SyntheticReceiptLifecycle(tmp_path / "receipts.sqlite", fail_audit=True)
    store.add_receipt("opaque-ref", "receipt-1")

    with pytest.raises(sqlite3.OperationalError, match="synthetic audit write failure"):
        store.consume_and_audit("opaque-ref", "context-1")

    assert store.receipt_state("opaque-ref") == ("receipt-1", None)
    assert store.audit_outcomes() == ()


def test_concurrent_synthetic_consumption_has_one_winner_and_two_audits(tmp_path: Path) -> None:
    store = _SyntheticReceiptLifecycle(tmp_path / "receipts.sqlite")
    store.add_receipt("opaque-ref", "receipt-1")
    barrier = Barrier(2)

    def attempt(context: str) -> bool:
        barrier.wait(timeout=5)
        return store.consume_and_audit("opaque-ref", context)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(attempt, ("context-a", "context-b")))

    assert sum(results) == 1
    assert store.receipt_state("opaque-ref")[1] in {"context-a", "context-b"}
    assert store.audit_outcomes().count("CONSUMED") == 1
    assert store.audit_outcomes().count("DENIED") == 1


def test_restart_preserves_consumption_and_replay_is_denied(tmp_path: Path) -> None:
    path = tmp_path / "receipts.sqlite"
    first_process = _SyntheticReceiptLifecycle(path)
    first_process.add_receipt("opaque-ref", "receipt-1")
    assert first_process.consume_and_audit("opaque-ref", "context-1") is True

    restarted_process = _SyntheticReceiptLifecycle(path)
    assert restarted_process.consume_and_audit("opaque-ref", "context-2") is False
    assert restarted_process.receipt_state("opaque-ref") == ("receipt-1", "context-1")
    assert restarted_process.audit_outcomes() == ("CONSUMED", "DENIED")
