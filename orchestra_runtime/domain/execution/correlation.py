from __future__ import annotations

import uuid


def validate_correlation_id(value: str) -> str:
    """Validate an RFC 9562 UUIDv7 correlation identifier.

    Validation is deterministic domain behavior. Clock and entropy backed UUIDv7
    generation intentionally remains outside this module.
    """
    if not isinstance(value, str):
        raise TypeError("correlation_id must be a string")
    if not value or value != value.strip():
        raise ValueError("correlation_id must be a non-empty, unpadded string")

    try:
        parsed = uuid.UUID(value)
    except Exception as exc:
        raise ValueError(f"malformed correlation_id: {value}") from exc

    version_digit = (parsed.int >> 76) & 0xF
    if version_digit != 7:
        raise ValueError(f"correlation_id version must be 7, got {version_digit}")

    if parsed.variant != uuid.RFC_4122:
        raise ValueError("correlation_id variant must be RFC 4122 / RFC 9562 compatible")

    canonical_str = str(parsed)
    if value.lower() != canonical_str:
        raise ValueError("correlation_id must use canonical hyphenated UUID format")

    return canonical_str


def is_valid_correlation_id(value: object) -> bool:
    """Return whether value satisfies the canonical correlation identifier contract."""
    if not isinstance(value, str):
        return False
    try:
        validate_correlation_id(value)
        return True
    except (ValueError, TypeError):
        return False
