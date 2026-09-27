"""Deterministic imbalance-crossing and risk-budget model."""

from dataclasses import dataclass
from typing import Optional

from .book import BookResult, OrderBook
from .constants import MAX_IMBALANCE, MAX_U48
from .errors import require_uint
from .types import (
    DecisionAction,
    DecisionEvent,
    ModelConfig,
    ModelStatus,
    NormalizedEvent,
)


@dataclass(frozen=True)
class DecisionResult:
    """Result of applying one event to the book and evaluating a crossing."""

    book_result: BookResult
    decision_event: Optional[DecisionEvent]


class DecisionModel:
    """Stateful deterministic decision layer above the bounded order book."""

    def __init__(self, config: ModelConfig) -> None:
        if not isinstance(config, ModelConfig):
            raise TypeError("config must be a ModelConfig")
        self.config = config
        self.reset()

    @property
    def previous_imbalance(self) -> int:
        return self._previous_imbalance

    @property
    def current_budget(self) -> int:
        return self._current_budget

    @property
    def decision_count(self) -> int:
        return self._decision_count

    def reset(self) -> None:
        """Explicitly re-arm decision state without changing the order book."""

        self._previous_imbalance = 0
        self._current_budget = self.config.initial_budget
        self._decision_count = 0

    def evaluate_after_mutation(
        self,
        event: NormalizedEvent,
        bid_total: int,
        ask_total: int,
        status: ModelStatus,
        decision_enable: Optional[bool] = None,
    ) -> Optional[DecisionEvent]:
        """Evaluate one successfully applied tracked mutation.

        The caller must invoke this only after a successful book mutation.
        Previous imbalance advances for every valid successful mutation even
        when decision enable or budget suppresses event emission.
        """

        if not isinstance(event, NormalizedEvent):
            raise TypeError("event must be a NormalizedEvent")
        if not isinstance(status, ModelStatus):
            raise TypeError("status must be a ModelStatus")
        if decision_enable is not None and not isinstance(decision_enable, bool):
            raise TypeError("decision_enable must be bool when overridden")
        require_uint(bid_total, 48, "bid_total")
        require_uint(ask_total, 48, "ask_total")

        current_imbalance = bid_total - ask_total
        if not -MAX_IMBALANCE <= current_imbalance <= MAX_IMBALANCE:
            raise ValueError("current imbalance exceeds signed aggregate range")

        if not status.book_valid or status.recovery_required:
            return None

        previous = self._previous_imbalance
        emitted: Optional[DecisionEvent] = None
        enabled = self.config.decision_enable if decision_enable is None else decision_enable
        if enabled and self._current_budget:
            threshold = self.config.decision_threshold
            if previous < threshold <= current_imbalance:
                emitted = DecisionEvent(
                    DecisionAction.BUY,
                    event.mold_sequence,
                    event.itch_timestamp,
                    current_imbalance,
                )
            elif previous > -threshold >= current_imbalance:
                emitted = DecisionEvent(
                    DecisionAction.SELL,
                    event.mold_sequence,
                    event.itch_timestamp,
                    current_imbalance,
                )

        self._previous_imbalance = current_imbalance
        if emitted is not None:
            self._current_budget -= 1
            self._decision_count += 1
            if self._current_budget < 0 or self._decision_count > self.config.initial_budget:
                raise AssertionError("decision budget invariant violated")
        return emitted

    def apply_and_evaluate(
        self,
        book: OrderBook,
        event: NormalizedEvent,
        decision_enable: Optional[bool] = None,
    ) -> DecisionResult:
        """Apply an event and evaluate only when the book mutation succeeds."""

        if not isinstance(book, OrderBook):
            raise TypeError("book must be an OrderBook")
        result = book.apply(event)
        if not result.applied:
            return DecisionResult(result, None)
        decision_event = self.evaluate_after_mutation(
            event, book.bid_total, book.ask_total, result.status, decision_enable
        )
        return DecisionResult(result, decision_event)
