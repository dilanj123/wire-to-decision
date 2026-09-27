import unittest

from wire_to_decision import (
    BookErrorCode,
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
from wire_to_decision.types import FailureReason, FieldValidity


ADD_VALID = FieldValidity(False, True, True, True, True)
EXEC_VALID = FieldValidity(True, False, True, False, False)
DELETE_VALID = FieldValidity(True, False, False, False, False)
REPLACE_VALID = FieldValidity(True, True, True, True, False)


def add(reference: int, quantity: int, price: int, side: Side = Side.BUY) -> NormalizedEvent:
    return NormalizedEvent(
        MutationKind.ADD, SourceMessageType.ADD_NO_MPID, 1, 2, 3, ADD_VALID,
        new_order_reference=reference, quantity=quantity, price=price, side=side,
    )


def execute(reference: int, quantity: int, with_price: bool = False) -> NormalizedEvent:
    source = SourceMessageType.EXECUTE_WITH_PRICE if with_price else SourceMessageType.EXECUTE
    kind = MutationKind.EXECUTE_WITH_PRICE if with_price else MutationKind.EXECUTE
    return NormalizedEvent(kind, source, 1, 2, 3, EXEC_VALID, old_order_reference=reference, quantity=quantity)


def cancel(reference: int, quantity: int) -> NormalizedEvent:
    return NormalizedEvent(MutationKind.CANCEL, SourceMessageType.CANCEL, 1, 2, 3, EXEC_VALID, old_order_reference=reference, quantity=quantity)


def delete(reference: int) -> NormalizedEvent:
    return NormalizedEvent(MutationKind.DELETE, SourceMessageType.DELETE, 1, 2, 3, DELETE_VALID, old_order_reference=reference)


def replace(old_reference: int, new_reference: int, quantity: int, price: int) -> NormalizedEvent:
    return NormalizedEvent(MutationKind.REPLACE, SourceMessageType.REPLACE, 1, 2, 3, REPLACE_VALID, old_order_reference=old_reference, new_order_reference=new_reference, quantity=quantity, price=price)


def assert_aggregates(test_case: unittest.TestCase, book: OrderBook, bid: int, ask: int) -> None:
    test_case.assertEqual((book.bid_total, book.ask_total), (bid, ask))
    test_case.assertEqual(book.recompute_aggregates(), (bid, ask))


class OrderBookTests(unittest.TestCase):
    def test_bounded_storage_hash_and_deterministic_ways(self):
        book = OrderBook()
        self.assertEqual(book.apply(add(1, 10, 100)).applied, True)
        self.assertEqual(book.apply(add(0x200, 20, 200, Side.SELL)).applied, True)
        self.assertEqual(book.set_ways(1)[0].order_reference, 1)
        self.assertEqual(book.set_ways(1)[1].order_reference, 0x200)
        self.assertEqual(book.order_count, 2)
        assert_aggregates(self, book, 10, 20)

    def test_third_collision_and_duplicate_fail_closed_without_eviction(self):
        book = OrderBook()
        book.apply(add(1, 1, 1))
        book.apply(add(0x200, 2, 2))
        duplicate = book.apply(add(1, 3, 3))
        self.assertFalse(duplicate.applied)
        self.assertEqual(duplicate.error, BookErrorCode.DUPLICATE_REFERENCE)
        self.assertEqual(duplicate.status.failure_reason, FailureReason.STATE_INTEGRITY)
        book.reset()
        book.apply(add(1, 1, 1))
        book.apply(add(0x200, 2, 2))
        collision = book.apply(add(0x40000, 4, 4))
        self.assertFalse(collision.applied)
        self.assertEqual(collision.error, BookErrorCode.COLLISION_CAPACITY)
        self.assertEqual(book.order_count, 2)
        self.assertEqual(book.lookup(1).price, 1)
        self.assertFalse(book.book_valid)
        self.assertTrue(book.recovery_required)

    def test_execute_partial_full_over_and_unknown(self):
        book = OrderBook()
        book.apply(add(10, 10, 0xAABBCCDD, Side.BUY))
        self.assertTrue(book.apply(execute(10, 4)).applied)
        self.assertEqual(book.lookup(10).remaining_quantity, 6)
        self.assertEqual(book.lookup(10).price, 0xAABBCCDD)
        assert_aggregates(self, book, 6, 0)
        self.assertTrue(book.apply(execute(10, 6)).applied)
        self.assertIsNone(book.lookup(10))
        assert_aggregates(self, book, 0, 0)
        book.reset()
        book.apply(add(10, 10, 1))
        over = book.apply(execute(10, 11))
        self.assertEqual(over.error, BookErrorCode.OVER_EXECUTE)
        book.reset()
        unknown = book.apply(execute(99, 1))
        self.assertEqual(unknown.error, BookErrorCode.UNKNOWN_REFERENCE)

    def test_execute_with_price_does_not_change_resting_price(self):
        book = OrderBook()
        book.apply(add(10, 10, 0x01020304, Side.SELL))
        result = book.apply(execute(10, 3, with_price=True))
        self.assertTrue(result.applied)
        self.assertEqual(book.lookup(10).price, 0x01020304)
        self.assertEqual(book.lookup(10).remaining_quantity, 7)
        assert_aggregates(self, book, 0, 7)

    def test_cancel_partial_full_over_and_unknown(self):
        book = OrderBook()
        book.apply(add(10, 9, 1, Side.SELL))
        self.assertTrue(book.apply(cancel(10, 4)).applied)
        self.assertEqual(book.lookup(10).remaining_quantity, 5)
        assert_aggregates(self, book, 0, 5)
        self.assertTrue(book.apply(cancel(10, 5)).applied)
        self.assertIsNone(book.lookup(10))
        book.reset()
        book.apply(add(10, 9, 1))
        self.assertEqual(book.apply(cancel(10, 10)).error, BookErrorCode.OVER_CANCEL)
        book.reset()
        self.assertEqual(book.apply(cancel(10, 1)).error, BookErrorCode.UNKNOWN_REFERENCE)

    def test_delete_buy_and_sell(self):
        book = OrderBook()
        book.apply(add(1, 7, 1, Side.BUY))
        book.apply(add(2, 8, 2, Side.SELL))
        self.assertTrue(book.apply(delete(1)).applied)
        assert_aggregates(self, book, 0, 8)
        self.assertTrue(book.apply(delete(2)).applied)
        assert_aggregates(self, book, 0, 0)
        self.assertEqual(book.apply(delete(2)).error, BookErrorCode.UNKNOWN_REFERENCE)

    def test_replace_same_set_and_different_set(self):
        book = OrderBook()
        book.apply(add(1, 10, 100, Side.SELL))
        same_set = book.apply(replace(1, 0x200, 6, 600))
        self.assertTrue(same_set.applied)
        self.assertIsNone(book.lookup(1))
        self.assertEqual(book.lookup(0x200).remaining_quantity, 6)
        self.assertEqual(book.lookup(0x200).price, 600)
        self.assertEqual(book.lookup(0x200).side, Side.SELL)
        assert_aggregates(self, book, 0, 6)
        different_set = book.apply(replace(0x200, 3, 12, 1200))
        self.assertTrue(different_set.applied)
        self.assertIsNone(book.lookup(0x200))
        self.assertEqual(book.lookup(3).remaining_quantity, 12)
        assert_aggregates(self, book, 0, 12)

    def test_replace_unknown_conflict_and_destination_capacity(self):
        book = OrderBook()
        book.apply(add(1, 10, 1))
        self.assertEqual(book.apply(replace(99, 2, 1, 2)).error, BookErrorCode.UNKNOWN_REFERENCE)
        book.reset()
        book.apply(add(1, 10, 1))
        book.apply(add(2, 2, 2))
        conflict = book.apply(replace(1, 2, 3, 3))
        self.assertEqual(conflict.error, BookErrorCode.NEW_REFERENCE_CONFLICT)
        self.assertIsNotNone(book.lookup(1))
        book.reset()
        book.apply(add(1, 10, 1))
        book.apply(add(2, 1, 2))
        book.apply(add(0x400, 1, 3))
        collision = book.apply(replace(1, 0x80000, 4, 4))
        self.assertEqual(collision.error, BookErrorCode.COLLISION_CAPACITY)
        self.assertIsNotNone(book.lookup(1))
        assert_aggregates(self, book, 12, 0)

    def test_invalid_book_quarantine_and_reset(self):
        book = OrderBook()
        book.apply(add(1, 1, 1))
        book.apply(add(1, 1, 1))
        blocked = book.apply(add(2, 1, 2))
        self.assertEqual(blocked.error, BookErrorCode.RECOVERY_REQUIRED)
        book.reset()
        self.assertTrue(book.book_valid)
        self.assertFalse(book.recovery_required)
        self.assertEqual(book.order_count, 0)
        self.assertTrue(book.apply(add(2, 1, 2)).applied)

    def test_aggregate_range_guard(self):
        book = OrderBook()
        book.bid_total = MAX_U48
        result = book.apply(add(1, 1, 1))
        self.assertEqual(result.error, BookErrorCode.AGGREGATE_RANGE)
        self.assertFalse(book.book_valid)

    def test_decoder_to_book_integration(self):
        payload = bytearray(36)
        payload[0] = ord("A")
        payload[1:3] = (3).to_bytes(2, "big")
        payload[5:11] = (7).to_bytes(6, "big")
        payload[11:19] = (0x1122334455667788).to_bytes(8, "big")
        payload[19] = ord("B")
        payload[20:24] = (9).to_bytes(4, "big")
        payload[24:32] = b"        "
        payload[32:36] = (0x01020304).to_bytes(4, "big")
        config = ModelConfig(0, 9000, 3, False, None, b"SESSION123", 1, 1, 1, True)
        decoded = decode_itch_message(FramedMessage(77, bytes(payload)), config)
        self.assertEqual(decoded.kind.value, "MUTATION_EVENT")
        book = OrderBook()
        result = book.apply(decoded.event)
        self.assertTrue(result.applied)
        assert_aggregates(self, book, 9, 0)


if __name__ == "__main__":
    unittest.main()
