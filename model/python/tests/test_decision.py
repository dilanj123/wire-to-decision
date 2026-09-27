import unittest

from wire_to_decision import (
    DecisionAction,
    DecisionModel,
    FramedMessage,
    ModelConfig,
    MutationKind,
    NormalizedEvent,
    OrderBook,
    Side,
    SourceMessageType,
    decode_itch_message,
)
from wire_to_decision.constants import MAX_U48
from wire_to_decision.types import FailureReason, FieldValidity, ModelStatus


ADD_VALID = FieldValidity(False, True, True, True, True)
EXEC_VALID = FieldValidity(True, False, True, False, False)


def add(ref: int, quantity: int, side: Side = Side.BUY, sequence: int = 1, timestamp: int = 2) -> NormalizedEvent:
    return NormalizedEvent(
        MutationKind.ADD, SourceMessageType.ADD_NO_MPID, sequence, timestamp, 3,
        ADD_VALID, new_order_reference=ref, quantity=quantity, price=100, side=side,
    )


def execute(ref: int, quantity: int, sequence: int = 1, timestamp: int = 2) -> NormalizedEvent:
    return NormalizedEvent(
        MutationKind.EXECUTE, SourceMessageType.EXECUTE, sequence, timestamp, 3,
        EXEC_VALID, old_order_reference=ref, quantity=quantity,
    )


def config(threshold: int = 10, budget: int = 2, enabled: bool = True) -> ModelConfig:
    return ModelConfig(0, 9000, 3, False, None, b"SESSION123", 1, threshold, budget, enabled)


class DecisionModelTests(unittest.TestCase):
    def test_buy_crossing_boundaries_and_no_repeat(self):
        model = DecisionModel(config(threshold=10))
        event = add(1, 9, sequence=11, timestamp=101)
        self.assertIsNone(model.evaluate_after_mutation(event, 9, 0, ModelStatus()))
        crossing = model.evaluate_after_mutation(add(2, 1, sequence=12, timestamp=102), 10, 0, ModelStatus())
        self.assertEqual(crossing.action, DecisionAction.BUY)
        self.assertEqual((crossing.trigger_mold_sequence, crossing.itch_timestamp, crossing.signed_imbalance), (12, 102, 10))
        self.assertIsNone(model.evaluate_after_mutation(add(3, 1), 11, 0, ModelStatus()))
        self.assertEqual((model.current_budget, model.decision_count, model.previous_imbalance), (1, 1, 11))

    def test_sell_crossing_boundaries_and_no_repeat(self):
        model = DecisionModel(config(threshold=10))
        event = add(1, 9, side=Side.SELL)
        self.assertIsNone(model.evaluate_after_mutation(event, 0, 9, ModelStatus()))
        crossing = model.evaluate_after_mutation(add(2, 1, side=Side.SELL, sequence=12), 0, 10, ModelStatus())
        self.assertEqual(crossing.action, DecisionAction.SELL)
        self.assertEqual(crossing.signed_imbalance, -10)
        self.assertIsNone(model.evaluate_after_mutation(add(3, 1, side=Side.SELL), 0, 11, ModelStatus()))

    def test_cross_back_and_recross_on_both_sides(self):
        model = DecisionModel(config(threshold=10, budget=4))
        self.assertIsNone(model.evaluate_after_mutation(add(1, 9), 9, 0, ModelStatus()))
        self.assertEqual(model.evaluate_after_mutation(add(2, 1), 10, 0, ModelStatus()).action, DecisionAction.BUY)
        self.assertIsNone(model.evaluate_after_mutation(add(3, 2, side=Side.SELL), 8, 0, ModelStatus()))
        self.assertEqual(model.evaluate_after_mutation(add(4, 20, side=Side.SELL), 0, 12, ModelStatus()).action, DecisionAction.SELL)
        self.assertIsNone(model.evaluate_after_mutation(add(5, 5), 0, 5, ModelStatus()))
        self.assertEqual(model.evaluate_after_mutation(add(6, 20), 20, 0, ModelStatus()).action, DecisionAction.BUY)
        self.assertEqual(model.decision_count, 3)

    def test_threshold_zero_uses_strict_previous_side(self):
        model = DecisionModel(config(threshold=0, budget=4))
        self.assertIsNone(model.evaluate_after_mutation(add(1, 1, side=Side.SELL), 0, 1, ModelStatus()))
        self.assertEqual(model.evaluate_after_mutation(add(2, 1), 1, 0, ModelStatus()).action, DecisionAction.BUY)
        self.assertEqual(model.evaluate_after_mutation(add(3, 2, side=Side.SELL), 0, 1, ModelStatus()).action, DecisionAction.SELL)
        self.assertIsNone(model.evaluate_after_mutation(add(4, 1, side=Side.SELL), 0, 1, ModelStatus()))

    def test_disable_and_zero_budget_still_advance_previous_imbalance(self):
        disabled = DecisionModel(config(threshold=10, enabled=True))
        self.assertIsNone(disabled.evaluate_after_mutation(add(1, 11), 11, 0, ModelStatus(), decision_enable=False))
        self.assertEqual(disabled.previous_imbalance, 11)
        self.assertIsNone(disabled.evaluate_after_mutation(add(2, 1), 12, 0, ModelStatus(), decision_enable=True))

        exhausted = DecisionModel(config(threshold=10, budget=1))
        self.assertEqual(exhausted.evaluate_after_mutation(add(1, 10), 10, 0, ModelStatus()).action, DecisionAction.BUY)
        self.assertIsNone(exhausted.evaluate_after_mutation(add(2, 10, side=Side.SELL), 0, 10, ModelStatus()))
        self.assertEqual(exhausted.previous_imbalance, -10)
        self.assertIsNone(exhausted.evaluate_after_mutation(add(3, 20), 20, 0, ModelStatus()))
        self.assertEqual((exhausted.current_budget, exhausted.decision_count), (0, 1))

    def test_failed_nonmutating_and_invalid_status_do_not_advance(self):
        model = DecisionModel(config(threshold=10))
        book = OrderBook()
        first = model.apply_and_evaluate(book, add(1, 9, sequence=20, timestamp=200))
        self.assertIsNone(first.decision_event)
        before = model.previous_imbalance
        failed = model.apply_and_evaluate(book, add(1, 2))
        self.assertFalse(failed.book_result.applied)
        self.assertIsNone(failed.decision_event)
        self.assertEqual((model.previous_imbalance, model.current_budget, model.decision_count), (before, 2, 0))
        self.assertIsNone(model.evaluate_after_mutation(add(2, 99), 99, 0, ModelStatus.failed(FailureReason.STATE_INTEGRITY)))
        self.assertEqual(model.previous_imbalance, before)

    def test_rearm_and_budget_invariant_stress(self):
        model = DecisionModel(config(threshold=5, budget=4))
        sequence = [(6, 0), (0, 6), (6, 0), (0, 6), (6, 0), (0, 6)]
        for index, (bid, ask) in enumerate(sequence):
            model.evaluate_after_mutation(add(index + 1, 1), bid, ask, ModelStatus())
            self.assertGreaterEqual(model.current_budget, 0)
            self.assertLessEqual(model.decision_count, 4)
            self.assertEqual(model.current_budget + model.decision_count, 4)
        model.reset()
        self.assertEqual((model.previous_imbalance, model.current_budget, model.decision_count), (0, 4, 0))

    def test_imbalance_extremes(self):
        model = DecisionModel(config(threshold=MAX_U48))
        self.assertIsNone(model.evaluate_after_mutation(add(1, 1), 0, 0, ModelStatus()))
        self.assertEqual(model.evaluate_after_mutation(add(2, 1), MAX_U48, 0, ModelStatus()).signed_imbalance, MAX_U48)
        event = model.evaluate_after_mutation(add(2, 1), 0, MAX_U48, ModelStatus())
        self.assertEqual(event.signed_imbalance, -MAX_U48)

    def test_book_and_itch_to_decision_integration(self):
        payload = bytearray(36)
        payload[0] = ord("A")
        payload[1:3] = (3).to_bytes(2, "big")
        payload[5:11] = (7).to_bytes(6, "big")
        payload[11:19] = (0x1122334455667788).to_bytes(8, "big")
        payload[19] = ord("B")
        payload[20:24] = (10).to_bytes(4, "big")
        payload[24:32] = b"        "
        payload[32:36] = (0x01020304).to_bytes(4, "big")
        cfg = config(threshold=10, budget=1)
        decoded = decode_itch_message(FramedMessage(77, bytes(payload)), cfg)
        book = OrderBook()
        model = DecisionModel(cfg)
        result = model.apply_and_evaluate(book, decoded.event)
        self.assertTrue(result.book_result.applied)
        self.assertEqual(result.decision_event.action, DecisionAction.BUY)
        self.assertEqual((result.decision_event.trigger_mold_sequence, result.decision_event.itch_timestamp, result.decision_event.signed_imbalance), (77, 7, 10))


if __name__ == "__main__":
    unittest.main()
