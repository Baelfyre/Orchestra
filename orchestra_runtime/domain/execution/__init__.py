"""Pure execution-domain identity semantics."""

from .correlation import is_valid_correlation_id, validate_correlation_id

__all__ = ("is_valid_correlation_id", "validate_correlation_id")
