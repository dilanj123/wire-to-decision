"""Decoder for the frozen TotalView-ITCH MVP subset."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .errors import CanonicalDataError, require_uint
from .mold import FramedMessage
from .types import (
    FailureReason,
    FieldValidity,
    ModelConfig,
    ModelStatus,
    MutationKind,
    NormalizedEvent,
    Side,
    SourceMessageType,
)


class DecodeKind(str, Enum):
    MUTATION_EVENT = "MUTATION_EVENT"
    KNOWN_NON_MUTATING = "KNOWN_NON_MUTATING"
    FILTERED_OTHER_INSTRUMENT = "FILTERED_OTHER_INSTRUMENT"
    FAIL_CLOSED = "FAIL_CLOSED"


class ItchErrorCode(str, Enum):
    WRONG_LENGTH = "WRONG_LENGTH"
    TRUNCATED = "TRUNCATED"
    INVALID_SIDE = "INVALID_SIDE"
    SYMBOL_MISMATCH = "SYMBOL_MISMATCH"
    UNSUPPORTED_MESSAGE = "UNSUPPORTED_MESSAGE"


MESSAGE_LENGTHS = {
    SourceMessageType.ADD_NO_MPID: 36,
    SourceMessageType.ADD_MPID: 40,
    SourceMessageType.EXECUTE: 31,
    SourceMessageType.EXECUTE_WITH_PRICE: 36,
    SourceMessageType.CANCEL: 23,
    SourceMessageType.DELETE: 19,
    SourceMessageType.REPLACE: 35,
    SourceMessageType.TRADE: 44,
}


@dataclass(frozen=True)
class DecodeResult:
    kind: DecodeKind
    event: Optional[NormalizedEvent]
    source_type: Optional[SourceMessageType]
    status: ModelStatus
    error: Optional[ItchErrorCode] = None

    @property
    def success(self) -> bool:
        return self.kind is not DecodeKind.FAIL_CLOSED


def decode_itch_message(framed_message: FramedMessage, config: ModelConfig) -> DecodeResult:
    """Decode one complete Mold-framed ITCH payload into one normalized event."""

    if not isinstance(framed_message, FramedMessage):
        raise TypeError("framed_message must be FramedMessage")
    if not isinstance(config, ModelConfig):
        raise TypeError("config must be ModelConfig")
    payload = framed_message.payload
    if not payload:
        return _failure(None, ItchErrorCode.TRUNCATED, FailureReason.TRUNCATED)

    try:
        source_type = SourceMessageType.from_encoding(payload[0:1])
    except (CanonicalDataError, UnicodeError):
        return _failure(None, ItchErrorCode.UNSUPPORTED_MESSAGE, FailureReason.UNSUPPORTED_MESSAGE)

    expected_length = MESSAGE_LENGTHS.get(source_type)
    if expected_length is None:
        return _failure(source_type, ItchErrorCode.UNSUPPORTED_MESSAGE, FailureReason.UNSUPPORTED_MESSAGE)
    if len(payload) != expected_length:
        return _failure(source_type, ItchErrorCode.WRONG_LENGTH, FailureReason.MALFORMED)

    stock_locate = int.from_bytes(payload[1:3], "big")
    timestamp = int.from_bytes(payload[5:11], "big")
    status = ModelStatus()

    if source_type is SourceMessageType.TRADE:
        return DecodeResult(DecodeKind.KNOWN_NON_MUTATING, None, source_type, status)
    if stock_locate != config.tracked_stock_locate:
        return DecodeResult(DecodeKind.FILTERED_OTHER_INSTRUMENT, None, source_type, status)

    if source_type in (SourceMessageType.ADD_NO_MPID, SourceMessageType.ADD_MPID):
        return _decode_add(framed_message, config, source_type, stock_locate, timestamp)
    if source_type in (SourceMessageType.EXECUTE, SourceMessageType.EXECUTE_WITH_PRICE):
        kind = MutationKind.EXECUTE if source_type is SourceMessageType.EXECUTE else MutationKind.EXECUTE_WITH_PRICE
        event = NormalizedEvent(
            kind=kind,
            source_type=source_type,
            mold_sequence=framed_message.mold_sequence,
            itch_timestamp=timestamp,
            stock_locate=stock_locate,
            field_valid=FieldValidity(True, False, True, False, False),
            old_order_reference=_u64(payload, 11),
            quantity=_u32(payload, 19),
        )
        return DecodeResult(DecodeKind.MUTATION_EVENT, event, source_type, status)
    if source_type is SourceMessageType.CANCEL:
        event = NormalizedEvent(
            kind=MutationKind.CANCEL,
            source_type=source_type,
            mold_sequence=framed_message.mold_sequence,
            itch_timestamp=timestamp,
            stock_locate=stock_locate,
            field_valid=FieldValidity(True, False, True, False, False),
            old_order_reference=_u64(payload, 11),
            quantity=_u32(payload, 19),
        )
        return DecodeResult(DecodeKind.MUTATION_EVENT, event, source_type, status)
    if source_type is SourceMessageType.DELETE:
        event = NormalizedEvent(
            kind=MutationKind.DELETE,
            source_type=source_type,
            mold_sequence=framed_message.mold_sequence,
            itch_timestamp=timestamp,
            stock_locate=stock_locate,
            field_valid=FieldValidity(True, False, False, False, False),
            old_order_reference=_u64(payload, 11),
        )
        return DecodeResult(DecodeKind.MUTATION_EVENT, event, source_type, status)
    if source_type is SourceMessageType.REPLACE:
        event = NormalizedEvent(
            kind=MutationKind.REPLACE,
            source_type=source_type,
            mold_sequence=framed_message.mold_sequence,
            itch_timestamp=timestamp,
            stock_locate=stock_locate,
            field_valid=FieldValidity(True, True, True, True, False),
            old_order_reference=_u64(payload, 11),
            new_order_reference=_u64(payload, 19),
            quantity=_u32(payload, 27),
            price=_u32(payload, 31),
        )
        return DecodeResult(DecodeKind.MUTATION_EVENT, event, source_type, status)

    return _failure(source_type, ItchErrorCode.UNSUPPORTED_MESSAGE, FailureReason.UNSUPPORTED_MESSAGE)


def _decode_add(
    framed_message: FramedMessage,
    config: ModelConfig,
    source_type: SourceMessageType,
    stock_locate: int,
    timestamp: int,
) -> DecodeResult:
    payload = framed_message.payload
    if config.symbol_check_enable and payload[24:32] != config.expected_stock_symbol:
        return _failure(source_type, ItchErrorCode.SYMBOL_MISMATCH, FailureReason.SYMBOL_MISMATCH)
    try:
        side = Side.from_source_encoding(payload[19:20])
    except (CanonicalDataError, UnicodeError):
        return _failure(source_type, ItchErrorCode.INVALID_SIDE, FailureReason.MALFORMED)
    event = NormalizedEvent(
        kind=MutationKind.ADD,
        source_type=source_type,
        mold_sequence=framed_message.mold_sequence,
        itch_timestamp=timestamp,
        stock_locate=stock_locate,
        field_valid=FieldValidity(False, True, True, True, True),
        new_order_reference=_u64(payload, 11),
        quantity=_u32(payload, 20),
        price=_u32(payload, 32),
        side=side,
    )
    return DecodeResult(DecodeKind.MUTATION_EVENT, event, source_type, ModelStatus())


def _failure(source_type: Optional[SourceMessageType], error: ItchErrorCode, reason: FailureReason) -> DecodeResult:
    return DecodeResult(DecodeKind.FAIL_CLOSED, None, source_type, ModelStatus.failed(reason), error)


def _u32(payload: bytes, offset: int) -> int:
    return int.from_bytes(payload[offset : offset + 4], "big")


def _u64(payload: bytes, offset: int) -> int:
    return int.from_bytes(payload[offset : offset + 8], "big")
