"""Small standard-library-free helpers for the IPv4 one's-complement checksum."""


def internet_checksum(data: bytes) -> int:
    """Return the 16-bit one's-complement checksum of an even-length buffer."""

    if not isinstance(data, bytes):
        raise TypeError("checksum input must be bytes")
    if len(data) % 2:
        data += b"\x00"
    total = 0
    for offset in range(0, len(data), 2):
        total += int.from_bytes(data[offset : offset + 2], "big")
        total = (total & 0xFFFF) + (total >> 16)
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def ipv4_header_checksum_valid(header: bytes) -> bool:
    """Return whether a complete IPv4 header has a valid checksum."""

    if not isinstance(header, bytes):
        raise TypeError("IPv4 header must be bytes")
    return len(header) % 2 == 0 and internet_checksum(header) == 0
