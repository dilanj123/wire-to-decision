"""Validation errors for the canonical Wire-to-Decision data model."""


class CanonicalDataError(ValueError):
    """Raised when canonical model data violates a frozen contract."""


def require_uint(value: int, width: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0 or value >= (1 << width):
        raise CanonicalDataError(f"{name} must fit in {width} unsigned bits")
    return value


def require_nonnegative_int(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise CanonicalDataError(f"{name} must be non-negative")
    return value


def require_bytes_exact(value: bytes, size: int, name: str) -> bytes:
    if not isinstance(value, bytes):
        raise TypeError(f"{name} must be bytes")
    if len(value) != size:
        raise CanonicalDataError(f"{name} must contain exactly {size} bytes")
    return value
