"""Pure validation-domain semantics."""

from .architecture_validation import (
    ARCHITECTURE_VALIDATION_CONTRACT_SCHEMA_VERSION,
    VALIDATION_DIMENSIONS,
    VALIDATION_PROOF_STATES,
    evaluate_architecture_validation,
)

__all__ = (
    "ARCHITECTURE_VALIDATION_CONTRACT_SCHEMA_VERSION",
    "VALIDATION_DIMENSIONS",
    "VALIDATION_PROOF_STATES",
    "evaluate_architecture_validation",
)
