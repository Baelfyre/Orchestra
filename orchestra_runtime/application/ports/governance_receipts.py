"""Pluggable trusted receipt and authorization boundaries."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...domain.execution.operation_contracts import OperationContract
from ...domain.governance.receipts import (
    AuthorizationDecision,
    GovernanceReceiptAuditEvent,
    GovernanceReceiptRequest,
    ResolvedGovernanceReceipt,
)


@runtime_checkable
class GovernanceReceiptStore(Protocol):
    """Canonical store; consume_once must be durable and atomic."""

    def resolve(self, receipt_reference: str) -> ResolvedGovernanceReceipt | None: ...

    def consume_once(self, receipt_id: str, execution_context_id: str) -> bool: ...

    def record_audit(self, event: GovernanceReceiptAuditEvent) -> None: ...


@runtime_checkable
class GovernanceReceiptContextProvider(Protocol):
    """Trusted host lookup; receipt references never come from prompts or MCP metadata."""

    def for_operation(
        self, operation_id: str, execution_context_id: str
    ) -> tuple[str, GovernanceReceiptRequest] | None: ...


@runtime_checkable
class ProtectedOperationAuthorizer(Protocol):
    def authorize(
        self, operation: OperationContract, execution_context_id: str
    ) -> AuthorizationDecision: ...
