"""Bounded 512-set x 2-way order state and aggregate model."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .constants import MAX_U48, ORDER_SETS, ORDER_WAYS
from .hash import order_set_index
from .types import FailureReason, ModelStatus, MutationKind, NormalizedEvent, OrderEntry, Side


class BookErrorCode(str, Enum):
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    DUPLICATE_REFERENCE = "DUPLICATE_REFERENCE"
    COLLISION_CAPACITY = "COLLISION_CAPACITY"
    UNKNOWN_REFERENCE = "UNKNOWN_REFERENCE"
    OVER_EXECUTE = "OVER_EXECUTE"
    OVER_CANCEL = "OVER_CANCEL"
    NEW_REFERENCE_CONFLICT = "NEW_REFERENCE_CONFLICT"
    AGGREGATE_RANGE = "AGGREGATE_RANGE"


@dataclass(frozen=True)
class BookResult:
    applied: bool
    status: ModelStatus
    error: Optional[BookErrorCode] = None


class OrderBook:
    """The bounded software equivalent of the frozen order-store architecture."""

    def __init__(self) -> None:
        self._ways: list[list[Optional[OrderEntry]]] = [
            [None for _ in range(ORDER_WAYS)] for _ in range(ORDER_SETS)
        ]
        self.bid_total = 0
        self.ask_total = 0
        self.status = ModelStatus()

    @property
    def book_valid(self) -> bool:
        return self.status.book_valid

    @property
    def recovery_required(self) -> bool:
        return self.status.recovery_required

    @property
    def order_count(self) -> int:
        return sum(entry is not None for ways in self._ways for entry in ways)

    def reset(self) -> None:
        """Explicitly re-arm into the known empty valid state."""

        self._ways = [[None for _ in range(ORDER_WAYS)] for _ in range(ORDER_SETS)]
        self.bid_total = 0
        self.ask_total = 0
        self.status = ModelStatus()

    def lookup(self, order_reference: int) -> Optional[OrderEntry]:
        """Search only the two ways selected by WIRE-D006."""

        set_index = order_set_index(order_reference)
        for entry in self._ways[set_index]:
            if entry is not None and entry.order_reference == order_reference:
                return entry
        return None

    def set_ways(self, set_index: int) -> tuple[Optional[OrderEntry], Optional[OrderEntry]]:
        if not isinstance(set_index, int) or not 0 <= set_index < ORDER_SETS:
            raise ValueError("set_index must be in the bounded order-set range")
        return tuple(self._ways[set_index])  # type: ignore[return-value]

    def recompute_aggregates(self) -> tuple[int, int]:
        bid = 0
        ask = 0
        for ways in self._ways:
            for entry in ways:
                if entry is None:
                    continue
                if entry.side is Side.BUY:
                    bid += entry.remaining_quantity
                else:
                    ask += entry.remaining_quantity
        return bid, ask

    def apply(self, event: NormalizedEvent) -> BookResult:
        """Atomically apply one normalized mutation, or fail closed."""

        if not isinstance(event, NormalizedEvent):
            raise TypeError("event must be a NormalizedEvent")
        if not self.book_valid or self.recovery_required:
            return BookResult(False, self.status, BookErrorCode.RECOVERY_REQUIRED)

        staged = [ways[:] for ways in self._ways]
        result = self._apply_staged(staged, self.bid_total, self.ask_total, event)
        if result[2] is not None:
            error, reason = result[2]
            self.status = ModelStatus.failed(reason)
            return BookResult(False, self.status, error)

        self._ways = staged
        self.bid_total, self.ask_total = result[0], result[1]
        return BookResult(True, self.status)

    def _apply_staged(self, ways, bid_total: int, ask_total: int, event: NormalizedEvent):
        if event.kind is MutationKind.ADD:
            return self._add(ways, bid_total, ask_total, event)
        if event.kind in (MutationKind.EXECUTE, MutationKind.EXECUTE_WITH_PRICE):
            return self._reduce(ways, bid_total, ask_total, event, BookErrorCode.OVER_EXECUTE)
        if event.kind is MutationKind.CANCEL:
            return self._reduce(ways, bid_total, ask_total, event, BookErrorCode.OVER_CANCEL)
        if event.kind is MutationKind.DELETE:
            return self._delete(ways, bid_total, ask_total, event)
        if event.kind is MutationKind.REPLACE:
            return self._replace(ways, bid_total, ask_total, event)
        raise ValueError(f"unsupported mutation kind: {event.kind}")

    def _add(self, ways, bid_total, ask_total, event):
        reference = event.new_order_reference
        if reference is None or event.quantity is None or event.price is None or event.side is None:
            raise ValueError("validated ADD event is missing required fields")
        set_index = order_set_index(reference)
        target = ways[set_index]
        if any(entry is not None and entry.order_reference == reference for entry in target):
            return bid_total, ask_total, (BookErrorCode.DUPLICATE_REFERENCE, FailureReason.STATE_INTEGRITY)
        free_way = next((index for index, entry in enumerate(target) if entry is None), None)
        if free_way is None:
            return bid_total, ask_total, (BookErrorCode.COLLISION_CAPACITY, FailureReason.HASH_CAPACITY)
        new_bid, new_ask, error = self._adjust_side_total(bid_total, ask_total, event.side, event.quantity)
        if error is not None:
            return bid_total, ask_total, error
        target[free_way] = OrderEntry(reference, event.price, event.quantity, event.side)
        return new_bid, new_ask, None

    def _reduce(self, ways, bid_total, ask_total, event, over_error):
        reference = event.old_order_reference
        quantity = event.quantity
        if reference is None or quantity is None:
            raise ValueError("validated reduction event is missing required fields")
        location = self._locate(ways, reference)
        if location is None:
            return bid_total, ask_total, (BookErrorCode.UNKNOWN_REFERENCE, FailureReason.STATE_INTEGRITY)
        set_index, way_index = location
        entry = ways[set_index][way_index]
        if entry is None or quantity > entry.remaining_quantity:
            return bid_total, ask_total, (over_error, FailureReason.STATE_INTEGRITY)
        new_bid, new_ask, error = self._adjust_side_total(bid_total, ask_total, entry.side, -quantity)
        if error is not None:
            return bid_total, ask_total, error
        remaining = entry.remaining_quantity - quantity
        ways[set_index][way_index] = None if remaining == 0 else OrderEntry(entry.order_reference, entry.price, remaining, entry.side)
        return new_bid, new_ask, None

    def _delete(self, ways, bid_total, ask_total, event):
        reference = event.old_order_reference
        if reference is None:
            raise ValueError("validated DELETE event is missing old_order_reference")
        location = self._locate(ways, reference)
        if location is None:
            return bid_total, ask_total, (BookErrorCode.UNKNOWN_REFERENCE, FailureReason.STATE_INTEGRITY)
        set_index, way_index = location
        entry = ways[set_index][way_index]
        if entry is None:
            return bid_total, ask_total, (BookErrorCode.UNKNOWN_REFERENCE, FailureReason.STATE_INTEGRITY)
        new_bid, new_ask, error = self._adjust_side_total(bid_total, ask_total, entry.side, -entry.remaining_quantity)
        if error is not None:
            return bid_total, ask_total, error
        ways[set_index][way_index] = None
        return new_bid, new_ask, None

    def _replace(self, ways, bid_total, ask_total, event):
        old_reference = event.old_order_reference
        new_reference = event.new_order_reference
        if old_reference is None or new_reference is None or event.quantity is None or event.price is None:
            raise ValueError("validated REPLACE event is missing required fields")
        old_location = self._locate(ways, old_reference)
        if old_location is None:
            return bid_total, ask_total, (BookErrorCode.UNKNOWN_REFERENCE, FailureReason.STATE_INTEGRITY)
        new_location = self._locate(ways, new_reference)
        if new_location is not None and new_reference != old_reference:
            return bid_total, ask_total, (BookErrorCode.NEW_REFERENCE_CONFLICT, FailureReason.STATE_INTEGRITY)
        old_set, old_way = old_location
        old_entry = ways[old_set][old_way]
        if old_entry is None:
            return bid_total, ask_total, (BookErrorCode.UNKNOWN_REFERENCE, FailureReason.STATE_INTEGRITY)
        new_set = order_set_index(new_reference)
        destination = ways[new_set]
        if new_set != old_set and all(entry is not None for entry in destination):
            return bid_total, ask_total, (BookErrorCode.COLLISION_CAPACITY, FailureReason.HASH_CAPACITY)
        ways[old_set][old_way] = None
        free_way = next((index for index, entry in enumerate(destination) if entry is None), None)
        if free_way is None:
            return bid_total, ask_total, (BookErrorCode.COLLISION_CAPACITY, FailureReason.HASH_CAPACITY)
        delta = event.quantity - old_entry.remaining_quantity
        new_bid, new_ask, error = self._adjust_side_total(bid_total, ask_total, old_entry.side, delta)
        if error is not None:
            return bid_total, ask_total, error
        destination[free_way] = OrderEntry(new_reference, event.price, event.quantity, old_entry.side)
        return new_bid, new_ask, None

    @staticmethod
    def _locate(ways, reference: int):
        set_index = order_set_index(reference)
        for way_index, entry in enumerate(ways[set_index]):
            if entry is not None and entry.order_reference == reference:
                return set_index, way_index
        return None

    @staticmethod
    def _adjust_side_total(bid_total, ask_total, side: Side, delta: int):
        if side is Side.BUY:
            new_bid, error = OrderBook._checked_total(bid_total, delta)
            return new_bid, ask_total, error
        new_ask, error = OrderBook._checked_total(ask_total, delta)
        return bid_total, new_ask, error

    @staticmethod
    def _checked_total(total: int, delta: int):
        candidate = total + delta
        if not 0 <= candidate <= MAX_U48:
            return total, (BookErrorCode.AGGREGATE_RANGE, FailureReason.AGGREGATE_RANGE)
        return candidate, None
