"""Pure post-MAC Ethernet II / IPv4 / UDP / MoldUDP64 framing model."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .checksum import ipv4_header_checksum_valid
from .constants import MAX_U16
from .errors import CanonicalDataError, require_uint
from .mold import FramedMessage, FramingState, MoldErrorCode, MoldResult, parse_mold_packet
from .types import FailureReason, ModelConfig, ModelStatus


ETHERNET_HEADER_BYTES = 14
IPV4_HEADER_BYTES = 20
UDP_HEADER_BYTES = 8
IPV4_ETHERTYPE = 0x0800
IPV4_PROTOCOL_UDP = 17


class FramingErrorCode(str, Enum):
    FRAME_TRUNCATED = "FRAME_TRUNCATED"
    UNSUPPORTED_ETHERTYPE = "UNSUPPORTED_ETHERTYPE"
    INVALID_IPV4_VERSION = "INVALID_IPV4_VERSION"
    UNSUPPORTED_IPV4_IHL = "UNSUPPORTED_IPV4_IHL"
    IPV4_HEADER_TRUNCATED = "IPV4_HEADER_TRUNCATED"
    IPV4_CHECKSUM = "IPV4_CHECKSUM"
    IPV4_LENGTH = "IPV4_LENGTH"
    IPV4_FRAGMENTED = "IPV4_FRAGMENTED"
    WRONG_DESTINATION_IP = "WRONG_DESTINATION_IP"
    NON_UDP_PROTOCOL = "NON_UDP_PROTOCOL"
    UDP_HEADER_TRUNCATED = "UDP_HEADER_TRUNCATED"
    UDP_LENGTH = "UDP_LENGTH"
    WRONG_DESTINATION_PORT = "WRONG_DESTINATION_PORT"
    UDP_CHECKSUM_UNSUPPORTED = "UDP_CHECKSUM_UNSUPPORTED"
    MOLD = "MOLD"


@dataclass(frozen=True)
class FramingResult:
    messages: tuple[FramedMessage, ...]
    next_state: FramingState
    error: Optional[FramingErrorCode | MoldErrorCode] = None

    @property
    def success(self) -> bool:
        return self.error is None


def frame_packet(frame: bytes, config: ModelConfig, state: Optional[FramingState] = None) -> FramingResult:
    """Validate one complete post-MAC frame and parse its raw Mold messages."""

    if not isinstance(frame, bytes):
        raise TypeError("frame must be bytes")
    if not isinstance(config, ModelConfig):
        raise TypeError("config must be ModelConfig")
    if state is None:
        state = FramingState.from_config(config)
    if not isinstance(state, FramingState):
        raise TypeError("state must be FramingState")
    if len(frame) < ETHERNET_HEADER_BYTES:
        return _profile_failure(state, FramingErrorCode.FRAME_TRUNCATED, fatal=True)
    if int.from_bytes(frame[12:14], "big") != IPV4_ETHERTYPE:
        return _profile_failure(state, FramingErrorCode.UNSUPPORTED_ETHERTYPE)

    ip = frame[ETHERNET_HEADER_BYTES:]
    if len(ip) < IPV4_HEADER_BYTES:
        return _profile_failure(state, FramingErrorCode.IPV4_HEADER_TRUNCATED, fatal=True)
    version = ip[0] >> 4
    ihl_words = ip[0] & 0x0F
    if version != 4:
        return _profile_failure(state, FramingErrorCode.INVALID_IPV4_VERSION)
    if ihl_words != 5:
        return _profile_failure(state, FramingErrorCode.UNSUPPORTED_IPV4_IHL)
    total_length = int.from_bytes(ip[2:4], "big")
    if total_length < IPV4_HEADER_BYTES or total_length > len(ip):
        return _profile_failure(state, FramingErrorCode.IPV4_LENGTH, fatal=True)
    ip_datagram = ip[:total_length]
    if not ipv4_header_checksum_valid(ip_datagram[:IPV4_HEADER_BYTES]):
        return _profile_failure(state, FramingErrorCode.IPV4_CHECKSUM, fatal=True)
    flags_fragment = int.from_bytes(ip[6:8], "big")
    if (flags_fragment & 0x2000) != 0 or (flags_fragment & 0x1FFF) != 0:
        return _profile_failure(state, FramingErrorCode.IPV4_FRAGMENTED, fatal=True)
    if int.from_bytes(ip[16:20], "big") != config.destination_ipv4:
        return _profile_failure(state, FramingErrorCode.WRONG_DESTINATION_IP)
    if ip[9] != IPV4_PROTOCOL_UDP:
        return _profile_failure(state, FramingErrorCode.NON_UDP_PROTOCOL)

    udp_payload = ip_datagram[IPV4_HEADER_BYTES:]
    if len(udp_payload) < UDP_HEADER_BYTES:
        return _profile_failure(state, FramingErrorCode.UDP_HEADER_TRUNCATED, fatal=True)
    destination_port = int.from_bytes(udp_payload[2:4], "big")
    udp_length = int.from_bytes(udp_payload[4:6], "big")
    if udp_length < UDP_HEADER_BYTES or udp_length != len(udp_payload):
        return _profile_failure(state, FramingErrorCode.UDP_LENGTH, fatal=True)
    if destination_port != config.destination_udp_port:
        return _profile_failure(state, FramingErrorCode.WRONG_DESTINATION_PORT)
    if int.from_bytes(udp_payload[6:8], "big") != 0:
        return _profile_failure(state, FramingErrorCode.UDP_CHECKSUM_UNSUPPORTED)

    mold = parse_mold_packet(udp_payload[UDP_HEADER_BYTES:], state)
    if mold.error is None:
        return FramingResult(mold.messages, mold.next_state)
    return FramingResult(mold.messages, mold.next_state, mold.error)


def _profile_failure(state: FramingState, error: FramingErrorCode, fatal: bool = False) -> FramingResult:
    """Return a rejected profile packet without mutating framing state."""

    if not fatal:
        return FramingResult((), state, error)
    failed = FramingState(state.active_session, state.expected_sequence, ModelStatus.failed(FailureReason.MALFORMED))
    return FramingResult((), failed, error)
