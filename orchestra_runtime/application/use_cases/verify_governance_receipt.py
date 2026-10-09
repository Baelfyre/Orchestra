"""Validate, consume, audit, then derive authorization from a canonical receipt."""

# @codebase_provenance_JEO
# @codebase_rights_JEO

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Callable

from ...domain.execution.operation_contracts import OperationContract
from ...domain.governance.receipts import (
    AuthorizationDecision,
    GovernanceReceipt,
    GovernanceReceiptAuditEvent,
    GovernanceReceiptRequest,
    GovernanceReceiptVerification,
    GovernanceValidationResult,
    GovernanceValidationStatus,
    ReceiptProvenance,
    ResolvedGovernanceReceipt,
)
from ..ports.governance_receipts import (
    GovernanceReceiptContextProvider,
    GovernanceReceiptStore,
)


_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


class VerifyGovernanceReceipt:
    def __init__(
        self,
        store: GovernanceReceiptStore,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(store, GovernanceReceiptStore):
            raise TypeError("store must implement GovernanceReceiptStore")
        self._store = store
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def execute(
        self, receipt_reference: str, request: GovernanceReceiptRequest
    ) -> GovernanceReceiptVerification:
        reference = receipt_reference.strip() if isinstance(receipt_reference, str) else ""
        resolved: ResolvedGovernanceReceipt | None = None
        reason = "invalid_receipt_reference"
        if _REFERENCE.fullmatch(reference):
            try:
                resolved = self._store.resolve(reference)
                reason = "unknown_receipt" if resolved is None else self._validate(resolved, request)
            except Exception:
                reason = "receipt_resolver_failure"
        if not reason:
            try:
                if resolved is None or not self._store.consume_once(
                    resolved.receipt.decision_or_receipt_id, request.execution_context_id
                ):
                    reason = "receipt_already_consumed"
            except Exception:
                reason = "receipt_consumption_failure"

        status = GovernanceValidationStatus.DENIED if reason else GovernanceValidationStatus.VERIFIED
        receipt = resolved.receipt if isinstance(resolved, ResolvedGovernanceReceipt) else None
        validation = GovernanceValidationResult(
            status,
            reason or "verified",
            receipt.decision_or_receipt_id if receipt else None,
            receipt.digest if receipt else None,
        )
        event = GovernanceReceiptAuditEvent(
            receipt_reference=reference if _REFERENCE.fullmatch(reference) else "invalid-reference",
            operation_id=request.operation_id,
            execution_context_id=request.execution_context_id,
            repository=request.repository,
            candidate_head=request.candidate_head,
            candidate_tree=request.candidate_tree,
            validation_status=status,
            reason_code=validation.reason_code,
            receipt_id=receipt.decision_or_receipt_id if receipt else None,
            receipt_digest=receipt.digest if receipt else None,
        )
        try:
            self._store.record_audit(event)
        except Exception:
            validation = GovernanceValidationResult(
                GovernanceValidationStatus.DENIED,
                "audit_write_failure",
                receipt.decision_or_receipt_id if receipt else None,
                receipt.digest if receipt else None,
            )

        if validation.allowed and receipt is not None:
            authorization = AuthorizationDecision(
                decision_id=f"governance-authorization.{receipt.digest[:24]}",
                authorized=True,
                operation_id=request.operation_id,
                execution_context_id=request.execution_context_id,
                reason_code="verified",
                receipt_id=receipt.decision_or_receipt_id,
                receipt_digest=receipt.digest,
                repository=request.repository,
                candidate_base=request.candidate_base,
                candidate_head=request.candidate_head,
                candidate_tree=request.candidate_tree,
                allowed_scope=request.requested_scope,
                evidence_digest=request.evidence_digest,
            )
        else:
            authorization = AuthorizationDecision.denied(
                request.operation_id, request.execution_context_id, validation.reason_code
            )
        return GovernanceReceiptVerification(validation, authorization)

    def _validate(self, resolved: ResolvedGovernanceReceipt, request: GovernanceReceiptRequest) -> str:
        if not isinstance(resolved, ResolvedGovernanceReceipt):
            return "malformed_receipt"
        receipt = resolved.receipt
        if not isinstance(receipt, GovernanceReceipt):
            return "malformed_receipt"
        if resolved.provenance is not ReceiptProvenance.CANONICAL_HUMAN_GOVERNANCE_STORE:
            return "untrusted_receipt_provenance"
        if resolved.canonical_digest != receipt.digest:
            return "canonical_receipt_digest_mismatch"
        if receipt.human_authority_source != "HUMAN_GOVERNANCE_DECISION":
            return "forged_authority_source"
        try:
            now = self._clock()
            if now.tzinfo is None or now.utcoffset() is None:
                return "invalid_verifier_clock"
            issued = datetime.fromisoformat(receipt.issued_at.replace("Z", "+00:00"))
            expires = datetime.fromisoformat(receipt.expires_at.replace("Z", "+00:00"))
            now = now.astimezone(timezone.utc)
        except Exception:
            return "malformed_receipt_time"
        if issued > now:
            return "receipt_not_yet_valid"
        if now >= expires:
            return "receipt_expired"
        if receipt.repository != request.repository:
            return "repository_mismatch"
        if receipt.candidate_base != request.candidate_base:
            return "base_sha_mismatch"
        if receipt.candidate_head != request.candidate_head:
            return "head_sha_mismatch"
        if receipt.candidate_tree != request.candidate_tree:
            return "tree_sha_mismatch"
        if receipt.protected_rule != request.protected_rule:
            return "protected_rule_mismatch"
        if request.operation_id not in receipt.allowed_operations:
            return "operation_out_of_scope"
        if receipt.allowed_scope != request.requested_scope:
            return "scope_mismatch"
        if receipt.evidence_digest != request.evidence_digest:
            return "evidence_digest_mismatch"
        if (
            receipt.execution_context_binding != request.execution_context_id
            or receipt.issued_execution_context_id == request.execution_context_id
            or receipt.fresh_execution_context_required is not True
            or receipt.consumption_semantics.value != "SINGLE_USE"
        ):
            return "execution_context_or_consumption_mismatch"
        return ""


class AuthorizeGovernedOperation:
    """Trusted host-context lookup; accepts no prompt, metadata, or inline receipt."""

    def __init__(
        self,
        verifier: VerifyGovernanceReceipt,
        context_provider: GovernanceReceiptContextProvider,
    ) -> None:
        if not isinstance(context_provider, GovernanceReceiptContextProvider):
            raise TypeError("context_provider must implement GovernanceReceiptContextProvider")
        self._verifier = verifier
        self._context_provider = context_provider

    def authorize(self, operation: OperationContract, execution_context_id: str) -> AuthorizationDecision:
        if not operation.requires_verified_governance_receipt:
            return AuthorizationDecision.denied(
                operation.operation_id, execution_context_id, "receipt_not_required_for_operation"
            )
        try:
            context = self._context_provider.for_operation(operation.operation_id, execution_context_id)
        except Exception:
            context = None
        if context is None or not isinstance(context, tuple) or len(context) != 2:
            return AuthorizationDecision.denied(
                operation.operation_id, execution_context_id, "trusted_receipt_context_unavailable"
            )
        reference, request = context
        if (
            not isinstance(request, GovernanceReceiptRequest)
            or request.operation_id != operation.operation_id
            or request.execution_context_id != execution_context_id
        ):
            return AuthorizationDecision.denied(
                operation.operation_id, execution_context_id, "trusted_receipt_context_mismatch"
            )
        return self._verifier.execute(reference, request).authorization
