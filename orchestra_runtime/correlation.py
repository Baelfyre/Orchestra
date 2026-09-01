"""Compatibility facade for the correlation domain primitive.

New code should import from ``orchestra_runtime.domain.context.correlation``.
This module remains temporarily to preserve the public and historical import path.
"""

# ARCHITECTURE_COMPATIBILITY_FACADE
from .domain.context.correlation import (
    _generate_correlation_id,
    generate_correlation_id,
    is_valid_correlation_id,
    validate_correlation_id,
)

__all__ = [
    "generate_correlation_id",
    "validate_correlation_id",
    "is_valid_correlation_id",
]
