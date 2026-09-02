from __future__ import annotations

import secrets
import time
import uuid
from typing import Callable

from .domain.execution.correlation import is_valid_correlation_id, validate_correlation_id


def generate_correlation_id() -> str:
    """Generate a valid RFC 9562 UUIDv7 correlation identifier string."""
    return _generate_correlation_id()


def _generate_correlation_id(
    *,
    clock: Callable[[], int] | None = None,
    rand_bytes: Callable[[int], bytes] | None = None,
) -> str:
    """Internal implementation for UUIDv7 generation with optional clock/entropy injection for testing.

    Layout:
    - 48 bits: Unix timestamp in milliseconds
    - 4 bits: version 7 (0b0111)
    - 12 bits: rand_a (random data)
    - 2 bits: variant (0b10)
    - 62 bits: rand_b (random data)
    """
    now_ms = clock() if clock is not None else (time.time_ns() // 1_000_000)
    if not isinstance(now_ms, int) or now_ms < 0 or now_ms > 0xFFFFFFFFFFFF:
        raise ValueError("timestamp must be an integer within 48-bit unsigned range")

    if rand_bytes is not None:
        rnd = rand_bytes(10)
        if not isinstance(rnd, (bytes, bytearray)):
            raise TypeError("rand_bytes must return bytes")
        if len(rnd) != 10:
            raise ValueError("rand_bytes must return exactly 10 random bytes")
    else:
        rnd = secrets.token_bytes(10)

    rand_a = int.from_bytes(rnd[0:2], "big") & 0x0FFF
    rand_b_high = int.from_bytes(rnd[2:4], "big") & 0x3FFF
    rand_b_low = int.from_bytes(rnd[4:10], "big")

    ver_rand_a = 0x7000 | rand_a
    var_rand_b_high = 0x8000 | rand_b_high

    uuid_int = (now_ms << 80) | (ver_rand_a << 64) | (var_rand_b_high << 48) | rand_b_low
    return str(uuid.UUID(int=uuid_int))
