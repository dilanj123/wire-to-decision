import unittest

from wire_to_decision import (
    DecodeKind,
    FramedMessage,
    FramingState,
    ModelConfig,
    MutationKind,
    SourceMessageType,
    decode_itch_message,
)
from wire_to_decision.itch import ItchErrorCode
from wire_to_decision.mold import MoldErrorCode, parse_mold_packet
from wire_to_decision.types import FailureReason, Side


LOCATE = 0x1234
OTHER_LOCATE = 0x4321
TIMESTAMP = 0x010203040506
ORDER_REF = 0x1122334455667788
NEW_ORDER_REF = 0x8877665544332211
QUANTITY = 0x01020304
PRICE = 0x0A0B0C0D
SESSION = b"SESSION123"


def _common(message_type: int, length: int, locate: int = LOCATE, timestamp: int = TIMESTAMP) -> bytearray:
    payload = bytearray(length)
    payload[0] = message_type
    payload[1:3] = locate.to_bytes(2, "big")
    payload[3:5] = (0x5678).to_bytes(2, "big")
    payload[5:11] = timestamp.to_bytes(6, "big")
    return payload


def _fixtures() -> dict[str, bytes]:
    add = _common(ord("A"), 36)
    add[11:19] = ORDER_REF.to_bytes(8, "big")
    add[19] = ord("B")
    add[20:24] = QUANTITY.to_bytes(4, "big")
    add[24:32] = b"ABC     "
    add[32:36] = PRICE.to_bytes(4, "big")

    add_mpid = _common(ord("F"), 40)
    add_mpid[11:19] = ORDER_REF.to_bytes(8, "big")
    add_mpid[19] = ord("S")
    add_mpid[20:24] = QUANTITY.to_bytes(4, "big")
    add_mpid[24:32] = b"ABC     "
    add_mpid[32:36] = PRICE.to_bytes(4, "big")
    add_mpid[36:40] = b"MPID"

    execute = _common(ord("E"), 31)
    execute[11:19] = ORDER_REF.to_bytes(8, "big")
    execute[19:23] = QUANTITY.to_bytes(4, "big")
    execute[23:31] = (0x1020304050607080).to_bytes(8, "big")

    execute_price = _common(ord("C"), 36)
    execute_price[11:19] = ORDER_REF.to_bytes(8, "big")
    execute_price[19:23] = QUANTITY.to_bytes(4, "big")
    execute_price[23:31] = (0x1020304050607080).to_bytes(8, "big")
    execute_price[31] = ord("Y")
    execute_price[32:36] = (0x0E0F1011).to_bytes(4, "big")

    cancel = _common(ord("X"), 23)
    cancel[11:19] = ORDER_REF.to_bytes(8, "big")
    cancel[19:23] = QUANTITY.to_bytes(4, "big")

    delete = _common(ord("D"), 19)
    delete[11:19] = ORDER_REF.to_bytes(8, "big")

    replace = _common(ord("U"), 35)
    replace[11:19] = ORDER_REF.to_bytes(8, "big")
    replace[19:27] = NEW_ORDER_REF.to_bytes(8, "big")
    replace[27:31] = QUANTITY.to_bytes(4, "big")
    replace[31:35] = PRICE.to_bytes(4, "big")

    trade = _common(ord("P"), 44)
    trade[11:] = bytes(range(33))
    return {"A": bytes(add), "F": bytes(add_mpid), "E": bytes(execute), "C": bytes(execute_price), "X": bytes(cancel), "D": bytes(delete), "U": bytes(replace), "P": bytes(trade)}


FIXTURES = _fixtures()


def _config(*, locate: int = LOCATE, symbol_check: bool = False, symbol: bytes | None = None) -> ModelConfig:
    return ModelConfig(0xC6336407, 9000, locate, symbol_check, symbol, SESSION, 100, 1, 1, True)


def _mold(sequence: int, messages: list[bytes], count: int | None = None) -> bytes:
    if count is None:
        count = len(messages)
    blocks = b"".join(len(message).to_bytes(2, "big") + message for message in messages)
    return SESSION + sequence.to_bytes(8, "big") + count.to_bytes(2, "big") + blocks


class ItchDecoderTests(unittest.TestCase):
    def decode(self, message_type: str, config: ModelConfig | None = None):
        return decode_itch_message(FramedMessage(0xABCDEF, FIXTURES[message_type]), config or _config())

    def test_a_and_f_use_distinct_source_types_with_equivalent_add_semantics(self):
        a = self.decode("A")
        f = self.decode("F", _config())
        self.assertEqual(a.kind, DecodeKind.MUTATION_EVENT)
        self.assertEqual(f.kind, DecodeKind.MUTATION_EVENT)
        self.assertEqual(a.event.kind, MutationKind.ADD)
        self.assertEqual(f.event.kind, MutationKind.ADD)
        self.assertEqual(a.event.source_type, SourceMessageType.ADD_NO_MPID)
        self.assertEqual(f.event.source_type, SourceMessageType.ADD_MPID)
        self.assertEqual(a.event.new_order_reference, ORDER_REF)
        self.assertEqual(f.event.new_order_reference, ORDER_REF)
        self.assertEqual(a.event.quantity, f.event.quantity)
        self.assertEqual(a.event.price, f.event.price)
        self.assertIsNone(a.event.old_order_reference)

    def test_all_mutating_messages_map_to_authoritative_kinds(self):
        expected = {
            "A": (MutationKind.ADD, SourceMessageType.ADD_NO_MPID),
            "F": (MutationKind.ADD, SourceMessageType.ADD_MPID),
            "E": (MutationKind.EXECUTE, SourceMessageType.EXECUTE),
            "C": (MutationKind.EXECUTE_WITH_PRICE, SourceMessageType.EXECUTE_WITH_PRICE),
            "X": (MutationKind.CANCEL, SourceMessageType.CANCEL),
            "D": (MutationKind.DELETE, SourceMessageType.DELETE),
            "U": (MutationKind.REPLACE, SourceMessageType.REPLACE),
        }
        for message_type, (kind, source_type) in expected.items():
            with self.subTest(message_type=message_type):
                result = self.decode(message_type)
                self.assertEqual(result.kind, DecodeKind.MUTATION_EVENT)
                self.assertEqual(result.event.kind, kind)
                self.assertEqual(result.event.source_type, source_type)
                self.assertEqual(result.event.mold_sequence, 0xABCDEF)
                self.assertEqual(result.event.itch_timestamp, TIMESTAMP)
                self.assertEqual(result.event.stock_locate, LOCATE)

    def test_e_c_distinction_does_not_use_execution_price_as_resting_price(self):
        execute = self.decode("E").event
        execute_price = self.decode("C").event
        self.assertEqual(execute.kind, MutationKind.EXECUTE)
        self.assertEqual(execute_price.kind, MutationKind.EXECUTE_WITH_PRICE)
        self.assertIsNone(execute.price)
        self.assertIsNone(execute_price.price)
        self.assertFalse(execute_price.field_valid.price)

    def test_u_old_new_fields_and_validity(self):
        event = self.decode("U").event
        self.assertEqual(event.old_order_reference, ORDER_REF)
        self.assertEqual(event.new_order_reference, NEW_ORDER_REF)
        self.assertEqual(event.quantity, QUANTITY)
        self.assertEqual(event.price, PRICE)
        self.assertTrue(event.field_valid.old_order_reference)
        self.assertTrue(event.field_valid.new_order_reference)
        self.assertFalse(event.field_valid.side)
        self.assertIsNone(event.side)

    def test_p_is_known_non_mutating(self):
        result = self.decode("P")
        self.assertEqual(result.kind, DecodeKind.KNOWN_NON_MUTATING)
        self.assertIsNone(result.event)
        self.assertEqual(result.source_type, SourceMessageType.TRADE)
        self.assertTrue(result.success)

    def test_unknown_type_fails_closed(self):
        payload = b"Z" + bytes(35)
        result = decode_itch_message(FramedMessage(1, payload), _config())
        self.assertEqual(result.kind, DecodeKind.FAIL_CLOSED)
        self.assertEqual(result.error, ItchErrorCode.UNSUPPORTED_MESSAGE)
        self.assertEqual(result.status.failure_reason, FailureReason.UNSUPPORTED_MESSAGE)

    def test_stock_locate_filtering(self):
        for message_type in FIXTURES:
            if message_type == "P":
                continue
            payload = bytearray(FIXTURES[message_type])
            payload[1:3] = OTHER_LOCATE.to_bytes(2, "big")
            result = decode_itch_message(FramedMessage(1, bytes(payload)), _config())
            with self.subTest(message_type=message_type):
                self.assertEqual(result.kind, DecodeKind.FILTERED_OTHER_INSTRUMENT)
                self.assertIsNone(result.event)

    def test_symbol_check_modes(self):
        mismatch = bytearray(FIXTURES["A"])
        mismatch[24:32] = b"XYZ     "
        disabled = decode_itch_message(FramedMessage(1, bytes(mismatch)), _config(symbol_check=False))
        self.assertEqual(disabled.kind, DecodeKind.MUTATION_EVENT)
        enabled = decode_itch_message(FramedMessage(1, FIXTURES["A"]), _config(symbol_check=True, symbol=b"ABC     "))
        self.assertEqual(enabled.kind, DecodeKind.MUTATION_EVENT)
        rejected = decode_itch_message(FramedMessage(1, bytes(mismatch)), _config(symbol_check=True, symbol=b"ABC     "))
        self.assertEqual(rejected.kind, DecodeKind.FAIL_CLOSED)
        self.assertEqual(rejected.error, ItchErrorCode.SYMBOL_MISMATCH)
        self.assertEqual(rejected.status.failure_reason, FailureReason.SYMBOL_MISMATCH)

    def test_invalid_side_fails_closed(self):
        payload = bytearray(FIXTURES["A"])
        payload[19] = ord("X")
        result = decode_itch_message(FramedMessage(1, bytes(payload)), _config())
        self.assertEqual(result.error, ItchErrorCode.INVALID_SIDE)
        self.assertEqual(result.status.failure_reason, FailureReason.MALFORMED)

    def test_exact_lengths_are_required_for_every_supported_type(self):
        for message_type, payload in FIXTURES.items():
            for altered in (payload[:-1], payload + b"\x00"):
                result = decode_itch_message(FramedMessage(1, altered), _config())
                with self.subTest(message_type=message_type, length=len(altered)):
                    self.assertEqual(result.kind, DecodeKind.FAIL_CLOSED)
                    self.assertEqual(result.error, ItchErrorCode.WRONG_LENGTH)

    def test_timestamp_and_numeric_boundaries(self):
        payload = bytearray(FIXTURES["A"])
        payload[5:11] = (0).to_bytes(6, "big")
        result = self.decode("A")
        zero_result = decode_itch_message(FramedMessage(1, bytes(payload)), _config())
        self.assertEqual(zero_result.event.itch_timestamp, 0)
        self.assertEqual(result.event.price, PRICE)
        self.assertEqual(result.event.quantity, QUANTITY)
        self.assertEqual(result.event.new_order_reference, ORDER_REF)

    def test_framed_message_and_late_suffix_integration(self):
        mold = _mold(100, [FIXTURES["A"], FIXTURES["E"]])
        parsed = parse_mold_packet(mold, FramingState(SESSION, 100))
        self.assertTrue(parsed.success)
        decoded = [decode_itch_message(message, _config()) for message in parsed.messages]
        self.assertEqual([result.kind for result in decoded], [DecodeKind.MUTATION_EVENT, DecodeKind.MUTATION_EVENT])
        self.assertEqual(decoded[0].event.kind, MutationKind.ADD)
        self.assertEqual(decoded[1].event.kind, MutationKind.EXECUTE)

        malformed = _mold(100, [FIXTURES["A"], FIXTURES["E"]], count=3) + b"\x00\x05x"
        malformed_result = parse_mold_packet(malformed, FramingState(SESSION, 100))
        self.assertEqual(malformed_result.error, MoldErrorCode.MESSAGE_TRUNCATED)
        prefix_results = [decode_itch_message(message, _config()) for message in malformed_result.messages]
        self.assertEqual([result.kind for result in prefix_results], [DecodeKind.MUTATION_EVENT, DecodeKind.MUTATION_EVENT])


if __name__ == "__main__":
    unittest.main()
