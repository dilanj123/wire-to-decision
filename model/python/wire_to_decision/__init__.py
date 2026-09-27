"""Canonical Python data primitives for Wire-to-Decision."""

from .constants import MAX_ORDERS, ORDER_SETS, ORDER_WAYS
from .book import BookErrorCode, BookResult, OrderBook
from .decision import DecisionModel, DecisionResult
from .framing import FramingErrorCode, FramingResult, frame_packet
from .errors import CanonicalDataError
from .hash import order_set_index
from .itch import DecodeKind, DecodeResult, ItchErrorCode, decode_itch_message
from .mold import FramedMessage, FramingState, MoldErrorCode, MoldResult, parse_mold_packet
from .types import (
    DecisionAction,
    DecisionEvent,
    FailureReason,
    FieldValidity,
    ModelConfig,
    ModelStatus,
    MutationKind,
    NormalizedEvent,
    OrderEntry,
    Side,
    SourceMessageType,
)

__all__ = [
    "CanonicalDataError",
    "BookErrorCode",
    "BookResult",
    "DecisionAction",
    "DecisionEvent",
    "DecisionModel",
    "DecisionResult",
    "DecodeKind",
    "DecodeResult",
    "FailureReason",
    "FieldValidity",
    "FramedMessage",
    "FramingErrorCode",
    "FramingResult",
    "FramingState",
    "ItchErrorCode",
    "MAX_ORDERS",
    "ModelConfig",
    "ModelStatus",
    "MoldErrorCode",
    "MoldResult",
    "MutationKind",
    "NormalizedEvent",
    "ORDER_SETS",
    "ORDER_WAYS",
    "OrderEntry",
    "OrderBook",
    "Side",
    "SourceMessageType",
    "frame_packet",
    "decode_itch_message",
    "order_set_index",
    "parse_mold_packet",
]
