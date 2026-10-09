from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any


_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _clean_nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must be a non-empty string")
    if any(ord(ch) < 32 for ch in cleaned):
        raise ValueError(f"{field_name} must not contain control characters")
    return cleaned


def normalize_git_sha(value: str, field_name: str = "git_sha") -> str:
    cleaned = _clean_nonempty(value, field_name).lower()
    if not _GIT_SHA_RE.fullmatch(cleaned):
        raise ValueError(f"{field_name} must be an exact 40-character hexadecimal Git object id")
    return cleaned


def normalize_sha256(value: str, field_name: str = "sha256") -> str:
    cleaned = _clean_nonempty(value, field_name).lower()
    if not _SHA256_RE.fullmatch(cleaned):
        raise ValueError(f"{field_name} must be an exact 64-character hexadecimal SHA-256 digest")
    return cleaned


def normalize_timestamp(value: str, field_name: str = "timestamp") -> str:
    cleaned = _clean_nonempty(value, field_name)
    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an RFC3339/ISO-8601 timestamp with timezone") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    normalized = parsed.astimezone(timezone.utc)
    return normalized.isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize supported JSON data deterministically for hashing and transport."""
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"value is not canonical Orchestra JSON: {exc}") from exc
    return payload.encode("utf-8")


def receipt_digest(value: Any) -> str:
    """Return a stable SHA-256 identity over canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


__all__ = [
    "canonical_json_bytes",
    "normalize_git_sha",
    "normalize_sha256",
    "normalize_timestamp",
    "receipt_digest",
]
