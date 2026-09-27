"""Canonical Python data primitives for Wire-to-Decision."""

from .constants import MAX_ORDERS, ORDER_SETS, ORDER_WAYS
from .framing import FramingErrorCode, FramingResult, frame_packet
from .errors import CanonicalDataError
from .hash import order_set_index
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
    "DecisionAction",
    "DecisionEvent",
    "FailureReason",
    "FieldValidity",
    "FramedMessage",
    "FramingErrorCode",
    "FramingResult",
    "FramingState",
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
    "Side",
    "SourceMessageType",
    "frame_packet",
    "order_set_index",
    "parse_mold_packet",
]
