"""The project-owned WIRE-D006 order-reference set-index hash."""

from .errors import require_uint


def order_set_index(order_ref: int) -> int:
    """Return the frozen 9-bit XOR-fold set index for a 64-bit reference."""

    order_ref = require_uint(order_ref, 64, "order_ref")
    folded = 0
    for shift in (0, 9, 18, 27, 36, 45, 54):
        folded ^= (order_ref >> shift) & 0x1FF
    folded ^= (order_ref >> 63) & 0x1
    return folded & 0x1FF
