"""Canonical, side-effect-free data types for the Python reference model."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .constants import MAX_IMBALANCE, MAX_U48
from .errors import CanonicalDataError, require_bytes_exact, require_nonnegative_int, require_uint


class Side(str, Enum):
    BUY = "B"
    SELL = "S"

    @classmethod
    def from_source_encoding(cls, value: str | bytes) -> "Side":
        if isinstance(value, bytes):
            if len(value) != 1:
                raise CanonicalDataError("side encoding must contain one byte")
            value = value.decode("ascii", errors="strict")
        if not isinstance(value, str) or len(value) != 1:
            raise CanonicalDataError("side encoding must contain one character")
        try:
            return cls(value)
        except ValueError as exc:
            raise CanonicalDataError(f"unsupported side encoding: {value!r}") from exc

    def to_source_encoding(self) -> str:
        return self.value


class MutationKind(str, Enum):
    ADD = "ADD"
    EXECUTE = "EXECUTE"
    EXECUTE_WITH_PRICE = "EXECUTE_WITH_PRICE"
    CANCEL = "CANCEL"
    DELETE = "DELETE"
    REPLACE = "REPLACE"


class SourceMessageType(str, Enum):
    ADD_NO_MPID = "A"
    ADD_MPID = "F"
    EXECUTE = "E"
    EXECUTE_WITH_PRICE = "C"
    CANCEL = "X"
    DELETE = "D"
    REPLACE = "U"
    TRADE = "P"

    @classmethod
    def from_encoding(cls, value: str | bytes) -> "SourceMessageType":
        if isinstance(value, bytes):
            if len(value) != 1:
                raise CanonicalDataError("message type encoding must contain one byte")
            value = value.decode("ascii", errors="strict")
        if not isinstance(value, str) or len(value) != 1:
            raise CanonicalDataError("message type encoding must contain one character")
        try:
            return cls(value)
        except ValueError as exc:
            raise CanonicalDataError(f"unsupported ITCH message type: {value!r}") from exc


class DecisionAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class FailureReason(str, Enum):
    SESSION_MISMATCH = "SESSION_MISMATCH"
    SEQUENCE_ERROR = "SEQUENCE_ERROR"
    MALFORMED = "MALFORMED"
    TRUNCATED = "TRUNCATED"
    UNSUPPORTED_MESSAGE = "UNSUPPORTED_MESSAGE"
    STATE_INTEGRITY = "STATE_INTEGRITY"
    HASH_CAPACITY = "HASH_CAPACITY"
    AGGREGATE_RANGE = "AGGREGATE_RANGE"
    SYMBOL_MISMATCH = "SYMBOL_MISMATCH"


@dataclass(frozen=True)
class FieldValidity:
    """Named validity indicators for the optional normalized-event fields."""

    old_order_reference: bool
    new_order_reference: bool
    quantity: bool
    price: bool
    side: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("old_order_reference", self.old_order_reference),
            ("new_order_reference", self.new_order_reference),
            ("quantity", self.quantity),
            ("price", self.price),
            ("side", self.side),
        ):
            if not isinstance(value, bool):
                raise TypeError(f"{name} validity must be bool")


_SOURCE_BY_KIND = {
    MutationKind.ADD: frozenset({SourceMessageType.ADD_NO_MPID, SourceMessageType.ADD_MPID}),
    MutationKind.EXECUTE: frozenset({SourceMessageType.EXECUTE}),
    MutationKind.EXECUTE_WITH_PRICE: frozenset({SourceMessageType.EXECUTE_WITH_PRICE}),
    MutationKind.CANCEL: frozenset({SourceMessageType.CANCEL}),
    MutationKind.DELETE: frozenset({SourceMessageType.DELETE}),
    MutationKind.REPLACE: frozenset({SourceMessageType.REPLACE}),
}


@dataclass(frozen=True)
class NormalizedEvent:
    """Common mutation contract between protocol parsing and book state."""

    kind: MutationKind
    source_type: SourceMessageType
    mold_sequence: int
    itch_timestamp: int
    stock_locate: int
    field_valid: FieldValidity
    old_order_reference: Optional[int] = None
    new_order_reference: Optional[int] = None
    quantity: Optional[int] = None
    price: Optional[int] = None
    side: Optional[Side] = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MutationKind):
            raise TypeError("kind must be a MutationKind")
        if not isinstance(self.source_type, SourceMessageType):
            raise TypeError("source_type must be a SourceMessageType")
        require_uint(self.mold_sequence, 64, "mold_sequence")
        require_uint(self.itch_timestamp, 48, "itch_timestamp")
        require_uint(self.stock_locate, 16, "stock_locate")
        if not isinstance(self.field_valid, FieldValidity):
            raise TypeError("field_valid must be a FieldValidity")
        if self.source_type not in _SOURCE_BY_KIND[self.kind]:
            raise CanonicalDataError("source_type is incompatible with mutation kind")
        if self.old_order_reference is not None:
            require_uint(self.old_order_reference, 64, "old_order_reference")
        if self.new_order_reference is not None:
            require_uint(self.new_order_reference, 64, "new_order_reference")
        if self.quantity is not None:
            require_uint(self.quantity, 32, "quantity")
        if self.price is not None:
            require_uint(self.price, 32, "price")
        if self.side is not None and not isinstance(self.side, Side):
            raise TypeError("side must be a Side")

        if self.kind is MutationKind.ADD:
            self._require(self.old_order_reference is None, "ADD cannot contain old_order_reference")
            self._require(self.new_order_reference is not None, "ADD requires new_order_reference")
            self._require(self.quantity is not None and self.quantity > 0, "ADD requires positive quantity")
            self._require(self.price is not None, "ADD requires price")
            self._require(self.side is not None, "ADD requires side")
            self._require(self.field_valid == FieldValidity(False, True, True, True, True), "invalid ADD field_valid")
        elif self.kind in (MutationKind.EXECUTE, MutationKind.EXECUTE_WITH_PRICE, MutationKind.CANCEL):
            self._require(self.old_order_reference is not None, "mutation requires old_order_reference")
            self._require(self.quantity is not None and self.quantity > 0, "mutation requires positive quantity")
            self._require(self.new_order_reference is None, "mutation cannot contain new_order_reference")
            self._require(self.price is None, "execute/cancel does not carry resting price")
            self._require(self.side is None, "execute/cancel inherits side from state")
            self._require(self.field_valid == FieldValidity(True, False, True, False, False), "invalid execution/cancel field_valid")
        elif self.kind is MutationKind.DELETE:
            self._require(self.old_order_reference is not None, "DELETE requires old order_reference")
            self._require(self.new_order_reference is None, "DELETE cannot contain new_order_reference")
            self._require(self.quantity is None, "DELETE cannot contain quantity")
            self._require(self.price is None, "DELETE cannot contain price")
            self._require(self.side is None, "DELETE inherits side from state")
            self._require(self.field_valid == FieldValidity(True, False, False, False, False), "invalid DELETE field_valid")
        elif self.kind is MutationKind.REPLACE:
            self._require(self.old_order_reference is not None, "REPLACE requires old order_reference")
            self._require(self.new_order_reference is not None, "REPLACE requires new_order_reference")
            self._require(self.quantity is not None and self.quantity > 0, "REPLACE requires positive quantity")
            self._require(self.price is not None, "REPLACE requires new price")
            self._require(self.side is None, "REPLACE inherits side from state")
            self._require(self.field_valid == FieldValidity(True, True, True, True, False), "invalid REPLACE field_valid")

    @staticmethod
    def _require(condition: bool, message: str) -> None:
        if not condition:
            raise CanonicalDataError(message)


@dataclass(frozen=True)
class ModelConfig:
    destination_ipv4: int
    destination_udp_port: int
    tracked_stock_locate: int
    symbol_check_enable: bool
    expected_stock_symbol: Optional[bytes]
    active_session: bytes
    expected_sequence: int
    decision_threshold: int
    initial_budget: int
    decision_enable: bool

    def __post_init__(self) -> None:
        require_uint(self.destination_ipv4, 32, "destination_ipv4")
        require_uint(self.destination_udp_port, 16, "destination_udp_port")
        require_uint(self.tracked_stock_locate, 16, "tracked_stock_locate")
        require_uint(self.expected_sequence, 64, "expected_sequence")
        require_nonnegative_int(self.decision_threshold, "decision_threshold")
        if self.decision_threshold > MAX_IMBALANCE:
            raise CanonicalDataError("decision_threshold exceeds signed aggregate range")
        require_nonnegative_int(self.initial_budget, "initial_budget")
        if not isinstance(self.symbol_check_enable, bool):
            raise TypeError("symbol_check_enable must be bool")
        if not isinstance(self.decision_enable, bool):
            raise TypeError("decision_enable must be bool")
        require_bytes_exact(self.active_session, 10, "active_session")
        if self.expected_stock_symbol is not None:
            require_bytes_exact(self.expected_stock_symbol, 8, "expected_stock_symbol")
        if self.symbol_check_enable and self.expected_stock_symbol is None:
            raise CanonicalDataError("expected_stock_symbol is required when symbol checking is enabled")


@dataclass(frozen=True)
class OrderEntry:
    order_reference: int
    price: int
    remaining_quantity: int
    side: Side

    def __post_init__(self) -> None:
        require_uint(self.order_reference, 64, "order_reference")
        require_uint(self.price, 32, "price")
        require_uint(self.remaining_quantity, 32, "remaining_quantity")
        if self.remaining_quantity == 0:
            raise CanonicalDataError("a live OrderEntry requires positive remaining_quantity")
        if not isinstance(self.side, Side):
            raise TypeError("side must be a Side")


@dataclass(frozen=True)
class DecisionEvent:
    action: DecisionAction
    trigger_mold_sequence: int
    itch_timestamp: int
    signed_imbalance: int

    def __post_init__(self) -> None:
        if not isinstance(self.action, DecisionAction):
            raise TypeError("action must be a DecisionAction")
        require_uint(self.trigger_mold_sequence, 64, "trigger_mold_sequence")
        require_uint(self.itch_timestamp, 48, "itch_timestamp")
        if isinstance(self.signed_imbalance, bool) or not isinstance(self.signed_imbalance, int):
            raise TypeError("signed_imbalance must be an integer")
        if not -MAX_U48 <= self.signed_imbalance <= MAX_U48:
            raise CanonicalDataError("signed_imbalance exceeds the aggregate range")


@dataclass(frozen=True)
class ModelStatus:
    book_valid: bool = True
    recovery_required: bool = False
    failure_reason: Optional[FailureReason] = None

    def __post_init__(self) -> None:
        if not isinstance(self.book_valid, bool) or not isinstance(self.recovery_required, bool):
            raise TypeError("status flags must be bool")
        if self.failure_reason is not None and not isinstance(self.failure_reason, FailureReason):
            raise TypeError("failure_reason must be a FailureReason")
        if self.recovery_required and self.book_valid:
            raise CanonicalDataError("recovery_required cannot coexist with a valid book")
        if self.failure_reason is not None and (self.book_valid or not self.recovery_required):
            raise CanonicalDataError("a failure reason requires fail-closed status")

    @classmethod
    def failed(cls, reason: FailureReason) -> "ModelStatus":
        return cls(book_valid=False, recovery_required=True, failure_reason=reason)
