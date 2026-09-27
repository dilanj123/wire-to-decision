import unittest

from wire_to_decision import (
    CanonicalDataError,
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


ADD_VALID = FieldValidity(False, True, True, True, True)
EXECUTION_VALID = FieldValidity(True, False, True, False, False)
DELETE_VALID = FieldValidity(True, False, False, False, False)
REPLACE_VALID = FieldValidity(True, True, True, True, False)


class TypePrimitiveTests(unittest.TestCase):
    def test_side_round_trip(self):
        self.assertEqual(Side.from_source_encoding("B"), Side.BUY)
        self.assertEqual(Side.from_source_encoding(b"S"), Side.SELL)
        self.assertEqual(Side.BUY.to_source_encoding(), "B")
        self.assertEqual(Side.SELL.to_source_encoding(), "S")

    def test_invalid_side(self):
        for value in ("X", b"", b"BS"):
            with self.subTest(value=value), self.assertRaises(CanonicalDataError):
                Side.from_source_encoding(value)

    def test_source_message_types(self):
        self.assertEqual(SourceMessageType.from_encoding("A"), SourceMessageType.ADD_NO_MPID)
        self.assertEqual(SourceMessageType.from_encoding(b"P"), SourceMessageType.TRADE)
        with self.assertRaises(CanonicalDataError):
            SourceMessageType.from_encoding("Z")

    def test_valid_add_events_use_new_reference(self):
        for source in (SourceMessageType.ADD_NO_MPID, SourceMessageType.ADD_MPID):
            event = NormalizedEvent(
                MutationKind.ADD, source, 7, 9, 11, ADD_VALID,
                new_order_reference=13, quantity=17, price=19, side=Side.BUY,
            )
            self.assertIsNone(event.old_order_reference)
            self.assertEqual(event.new_order_reference, 13)

    def test_valid_execute_event(self):
        event = NormalizedEvent(
            MutationKind.EXECUTE, SourceMessageType.EXECUTE, 1, 2, 3,
            EXECUTION_VALID, old_order_reference=4, quantity=5,
        )
        self.assertEqual(event.old_order_reference, 4)
        self.assertFalse(event.field_valid.price)

    def test_valid_execute_with_price_event(self):
        event = NormalizedEvent(
            MutationKind.EXECUTE_WITH_PRICE, SourceMessageType.EXECUTE_WITH_PRICE,
            1, 2, 3, EXECUTION_VALID, old_order_reference=4, quantity=5,
        )
        self.assertEqual(event.kind, MutationKind.EXECUTE_WITH_PRICE)
        self.assertIsNone(event.price)
        self.assertFalse(event.field_valid.price)

    def test_valid_cancel_delete_replace_events(self):
        cancel = NormalizedEvent(
            MutationKind.CANCEL, SourceMessageType.CANCEL, 1, 2, 3,
            EXECUTION_VALID, old_order_reference=4, quantity=5,
        )
        delete = NormalizedEvent(
            MutationKind.DELETE, SourceMessageType.DELETE, 1, 2, 3,
            DELETE_VALID, old_order_reference=4,
        )
        replace = NormalizedEvent(
            MutationKind.REPLACE, SourceMessageType.REPLACE, 1, 2, 3,
            REPLACE_VALID, old_order_reference=4, new_order_reference=5,
            quantity=6, price=7,
        )
        self.assertEqual(cancel.quantity, 5)
        self.assertIsNone(delete.quantity)
        self.assertEqual(replace.new_order_reference, 5)

    def test_event_source_and_fields_are_checked(self):
        cases = [
            dict(kind=MutationKind.ADD, source_type=SourceMessageType.EXECUTE, field_valid=ADD_VALID, new_order_reference=1, quantity=1, price=1, side=Side.BUY),
            dict(kind=MutationKind.ADD, source_type=SourceMessageType.ADD_NO_MPID, field_valid=ADD_VALID, new_order_reference=1, quantity=0, price=1, side=Side.BUY),
            dict(kind=MutationKind.EXECUTE, source_type=SourceMessageType.EXECUTE, field_valid=EXECUTION_VALID, old_order_reference=1, quantity=1, price=1),
            dict(kind=MutationKind.REPLACE, source_type=SourceMessageType.REPLACE, field_valid=REPLACE_VALID, old_order_reference=1, new_order_reference=2, quantity=1, price=1, side=Side.SELL),
        ]
        for fields in cases:
            with self.subTest(fields=fields), self.assertRaises(CanonicalDataError):
                NormalizedEvent(mold_sequence=1, itch_timestamp=1, stock_locate=1, **fields)

    def test_event_validity_flags_are_exact(self):
        with self.assertRaises(CanonicalDataError):
            NormalizedEvent(
                MutationKind.ADD, SourceMessageType.ADD_NO_MPID,
                1, 2, 3, FieldValidity(True, True, True, True, True),
                new_order_reference=4, quantity=1, price=1, side=Side.BUY,
            )
        with self.assertRaises(CanonicalDataError):
            NormalizedEvent(
                MutationKind.EXECUTE_WITH_PRICE, SourceMessageType.EXECUTE_WITH_PRICE,
                1, 2, 3, FieldValidity(True, False, True, True, False),
                old_order_reference=4, quantity=1,
            )

    def test_event_widths_and_negative_values(self):
        base = dict(kind=MutationKind.DELETE, source_type=SourceMessageType.DELETE, mold_sequence=0, itch_timestamp=0, stock_locate=0, field_valid=DELETE_VALID, old_order_reference=0)
        NormalizedEvent(**base)
        for field, value in (("mold_sequence", 1 << 64), ("itch_timestamp", 1 << 48), ("stock_locate", 1 << 16), ("old_order_reference", -1)):
            with self.subTest(field=field), self.assertRaises(CanonicalDataError):
                NormalizedEvent(**{**base, field: value})

    def test_model_config(self):
        config = ModelConfig(0xC0000201, 9000, 12, True, b"ABC     ", b"SESSION123", 8, 100, 3, True)
        self.assertEqual(config.destination_ipv4, 0xC0000201)
        with self.assertRaises(CanonicalDataError):
            ModelConfig(0, 1, 1, True, None, b"SESSION123", 0, 1, 1, True)
        with self.assertRaises(CanonicalDataError):
            ModelConfig(0, 1, 1, False, b"short", b"SESSION123", 0, 1, 1, True)

    def test_model_config_ranges(self):
        valid = dict(destination_ipv4=0, destination_udp_port=0, tracked_stock_locate=0, symbol_check_enable=False, expected_stock_symbol=None, active_session=b"0123456789", expected_sequence=0, decision_threshold=0, initial_budget=0, decision_enable=False)
        ModelConfig(**valid)
        for field, value in (("destination_ipv4", 1 << 32), ("destination_udp_port", 1 << 16), ("tracked_stock_locate", 1 << 16), ("expected_sequence", 1 << 64), ("decision_threshold", -1), ("initial_budget", -1)):
            with self.subTest(field=field), self.assertRaises((CanonicalDataError, TypeError)):
                ModelConfig(**{**valid, field: value})

    def test_order_entry(self):
        entry = OrderEntry(1, 2, 3, Side.SELL)
        self.assertEqual(entry.remaining_quantity, 3)
        with self.assertRaises(CanonicalDataError):
            OrderEntry(1, 2, 0, Side.SELL)
        with self.assertRaises(CanonicalDataError):
            OrderEntry(1 << 64, 2, 3, Side.SELL)

    def test_decision_event(self):
        event = DecisionEvent(DecisionAction.BUY, 1, 2, -3)
        self.assertEqual(event.signed_imbalance, -3)
        with self.assertRaises(CanonicalDataError):
            DecisionEvent(DecisionAction.SELL, 1, 2, 1 << 48)

    def test_model_status(self):
        self.assertTrue(ModelStatus().book_valid)
        failed = ModelStatus.failed(FailureReason.SEQUENCE_ERROR)
        self.assertFalse(failed.book_valid)
        self.assertTrue(failed.recovery_required)
        with self.assertRaises(CanonicalDataError):
            ModelStatus(book_valid=True, recovery_required=True)


if __name__ == "__main__":
    unittest.main()
