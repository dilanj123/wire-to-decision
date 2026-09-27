"""Top-level functional reference oracle for complete post-MAC frames."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .book import BookResult, OrderBook
from .framing import FramingResult, frame_packet
from .itch import DecodeResult, decode_itch_message
from .mold import FramedMessage, FramingState
from .decision import DecisionModel
from .types import DecisionEvent, FailureReason, ModelConfig, ModelStatus


class OracleErrorCode(str, Enum):
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


@dataclass(frozen=True)
class OracleMessageResult:
    framed_message: FramedMessage
    decode_result: DecodeResult
    book_result: Optional[BookResult]
    decision_event: Optional[DecisionEvent]


@dataclass(frozen=True)
class OracleFrameResult:
    framing_result: Optional[FramingResult]
    messages: tuple[OracleMessageResult, ...]
    decisions: tuple[DecisionEvent, ...]
    terminal_error: Optional[object]
    accepted: bool
    filtered: bool
    quarantined: bool
    status: ModelStatus
    expected_sequence: int


class ReferenceOracle:
    """Own the persistent framing, bounded-book, and decision components."""

    def __init__(self, config: ModelConfig) -> None:
        self.rearm(config)

    @property
    def config(self) -> ModelConfig:
        return self._config

    @property
    def framing_state(self) -> FramingState:
        return self._framing_state

    @property
    def book(self) -> OrderBook:
        return self._book

    @property
    def decision_model(self) -> DecisionModel:
        return self._decision_model

    @property
    def status(self) -> ModelStatus:
        return self._book.status

    def rearm(self, config: ModelConfig) -> None:
        """Install known configuration and restore a clean model state."""

        if not isinstance(config, ModelConfig):
            raise TypeError("config must be a ModelConfig")
        self._config = config
        self._framing_state = FramingState.from_config(config)
        self._book = OrderBook()
        self._decision_model = DecisionModel(config)

    def process_frame(self, frame: bytes) -> OracleFrameResult:
        """Process one whole post-MAC frame without hidden recovery."""

        if not isinstance(frame, bytes):
            raise TypeError("frame must be bytes")
        if not self._book.book_valid or self._book.recovery_required:
            return OracleFrameResult(
                framing_result=None,
                messages=(),
                decisions=(),
                terminal_error=OracleErrorCode.RECOVERY_REQUIRED,
                accepted=False,
                filtered=False,
                quarantined=True,
                status=self._book.status,
                expected_sequence=self._framing_state.expected_sequence,
            )

        framing = frame_packet(frame, self._config, self._framing_state)
        self._framing_state = framing.next_state
        message_results: list[OracleMessageResult] = []
        decisions: list[DecisionEvent] = []
        terminal_error: Optional[object] = None

        for framed_message in framing.messages:
            decoded = decode_itch_message(framed_message, self._config)
            if decoded.kind.name == "FAIL_CLOSED":
                message_results.append(OracleMessageResult(framed_message, decoded, None, None))
                terminal_error = decoded.error
                self._quarantine(decoded.status.failure_reason)
                break
            if decoded.event is None:
                message_results.append(OracleMessageResult(framed_message, decoded, None, None))
                continue

            book_result = self._book.apply(decoded.event)
            if not book_result.applied:
                message_results.append(OracleMessageResult(framed_message, decoded, book_result, None))
                terminal_error = book_result.error
                self._quarantine(book_result.status.failure_reason)
                break
            decision_event = self._decision_model.evaluate_after_mutation(
                decoded.event,
                self._book.bid_total,
                self._book.ask_total,
                book_result.status,
            )
            message_results.append(OracleMessageResult(framed_message, decoded, book_result, decision_event))
            if decision_event is not None:
                decisions.append(decision_event)

        if terminal_error is None and framing.error is not None:
            terminal_error = framing.error
        if framing.next_state.status.recovery_required:
            reason = framing.next_state.status.failure_reason or FailureReason.MALFORMED
            self._quarantine(reason)

        return OracleFrameResult(
            framing_result=framing,
            messages=tuple(message_results),
            decisions=tuple(decisions),
            terminal_error=terminal_error,
            accepted=framing.success,
            filtered=(framing.error is not None and not framing.next_state.status.recovery_required),
            quarantined=self._book.recovery_required,
            status=self._book.status,
            expected_sequence=self._framing_state.expected_sequence,
        )

    def _quarantine(self, reason: Optional[FailureReason]) -> None:
        failure_reason = reason or FailureReason.MALFORMED
        self._book.invalidate(failure_reason)
        self._framing_state = FramingState(
            self._framing_state.active_session,
            self._framing_state.expected_sequence,
            self._book.status,
        )
