"""MoldUDP64 downstream framing and expected-sequence transition model."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .constants import MOLD_SESSION_BYTES, MAX_U64
from .errors import CanonicalDataError, require_bytes_exact, require_uint
from .types import FailureReason, ModelConfig, ModelStatus


MOLD_HEADER_BYTES = 20
MOLD_END_OF_SESSION = 0xFFFF


class MoldErrorCode(str, Enum):
    SESSION_MISMATCH = "SESSION_MISMATCH"
    SEQUENCE_ERROR = "SEQUENCE_ERROR"
    HEADER_TRUNCATED = "HEADER_TRUNCATED"
    MESSAGE_LENGTH_TRUNCATED = "MESSAGE_LENGTH_TRUNCATED"
    MESSAGE_TRUNCATED = "MESSAGE_TRUNCATED"
    TRAILING_BYTES = "TRAILING_BYTES"
    END_OF_SESSION = "END_OF_SESSION"


@dataclass(frozen=True)
class FramedMessage:
    mold_sequence: int
    payload: bytes

    def __post_init__(self) -> None:
        require_uint(self.mold_sequence, 64, "mold_sequence")
        if not isinstance(self.payload, bytes):
            raise TypeError("payload must be bytes")


@dataclass(frozen=True)
class FramingState:
    active_session: bytes
    expected_sequence: int
    status: ModelStatus = ModelStatus()

    def __post_init__(self) -> None:
        require_bytes_exact(self.active_session, MOLD_SESSION_BYTES, "active_session")
        require_uint(self.expected_sequence, 64, "expected_sequence")
        if not isinstance(self.status, ModelStatus):
            raise TypeError("status must be ModelStatus")

    @classmethod
    def from_config(cls, config: ModelConfig) -> "FramingState":
        return cls(config.active_session, config.expected_sequence)


@dataclass(frozen=True)
class MoldResult:
    messages: tuple[FramedMessage, ...]
    next_state: FramingState
    error: Optional[MoldErrorCode] = None

    @property
    def success(self) -> bool:
        return self.error is None


def parse_mold_packet(payload: bytes, state: FramingState) -> MoldResult:
    """Parse one UDP payload, retaining completed prefix messages on failure."""

    if not isinstance(payload, bytes):
        raise TypeError("Mold payload must be bytes")
    if not isinstance(state, FramingState):
        raise TypeError("state must be FramingState")
    if len(payload) < MOLD_HEADER_BYTES:
        return _failure(payload_messages=(), state=state, code=MoldErrorCode.HEADER_TRUNCATED, reason=FailureReason.TRUNCATED)

    session = payload[:MOLD_SESSION_BYTES]
    sequence = int.from_bytes(payload[10:18], "big")
    count = int.from_bytes(payload[18:20], "big")
    if session != state.active_session:
        return _failure((), state, MoldErrorCode.SESSION_MISMATCH, FailureReason.SESSION_MISMATCH)
    if sequence != state.expected_sequence:
        return _failure((), state, MoldErrorCode.SEQUENCE_ERROR, FailureReason.SEQUENCE_ERROR)

    if count == 0:
        if len(payload) != MOLD_HEADER_BYTES:
            return _failure((), state, MoldErrorCode.TRAILING_BYTES, FailureReason.MALFORMED)
        return MoldResult((), state)
    if count == MOLD_END_OF_SESSION:
        if len(payload) != MOLD_HEADER_BYTES:
            return _failure((), state, MoldErrorCode.TRAILING_BYTES, FailureReason.MALFORMED)
        failed = FramingState(state.active_session, state.expected_sequence, ModelStatus(book_valid=False, recovery_required=True))
        return MoldResult((), failed, MoldErrorCode.END_OF_SESSION)

    messages: list[FramedMessage] = []
    cursor = MOLD_HEADER_BYTES
    for index in range(count):
        if cursor + 2 > len(payload):
            return _failure(tuple(messages), state, MoldErrorCode.MESSAGE_LENGTH_TRUNCATED, FailureReason.TRUNCATED)
        message_length = int.from_bytes(payload[cursor : cursor + 2], "big")
        cursor += 2
        if cursor + message_length > len(payload):
            return _failure(tuple(messages), state, MoldErrorCode.MESSAGE_TRUNCATED, FailureReason.TRUNCATED)
        message = payload[cursor : cursor + message_length]
        cursor += message_length
        messages.append(FramedMessage((sequence + index) & MAX_U64, message))

    if cursor != len(payload):
        return _failure(tuple(messages), state, MoldErrorCode.TRAILING_BYTES, FailureReason.MALFORMED)

    next_state = FramingState(state.active_session, (state.expected_sequence + count) & MAX_U64, state.status)
    return MoldResult(tuple(messages), next_state)


def _failure(
    payload_messages: tuple[FramedMessage, ...],
    state: FramingState,
    code: MoldErrorCode,
    reason: FailureReason,
) -> MoldResult:
    failed = FramingState(state.active_session, state.expected_sequence, ModelStatus.failed(reason))
    return MoldResult(payload_messages, failed, code)
