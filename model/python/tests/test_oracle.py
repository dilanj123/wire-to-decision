import struct
import unittest

from wire_to_decision import (
    DecisionAction,
    FramingErrorCode,
    ModelConfig,
    MoldErrorCode,
    OracleErrorCode,
    ReferenceOracle,
)
from wire_to_decision.mold import MOLD_END_OF_SESSION
from wire_to_decision.types import FailureReason


SESSION = b"SESSION123"
OTHER_SESSION = b"OTHER_____"
DEST_IP = 0xC6336407
DEST_PORT = 9000
LOCATE = 1
OTHER_LOCATE = 2


def _checksum(data: bytes) -> int:
    total = 0
    for offset in range(0, len(data), 2):
        total += int.from_bytes(data[offset : offset + 2], "big")
        total = (total & 0xFFFF) + (total >> 16)
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def _frame(mold: bytes, *, destination_ip: int = DEST_IP) -> bytes:
    udp = struct.pack("!HHHH", 40000, DEST_PORT, 8 + len(mold), 0) + mold
    total_length = 20 + len(udp)
    header = bytearray(struct.pack("!BBHHHBBHII", 0x45, 0, total_length, 0x1234, 0x4000, 64, 17, 0, 0xC0000201, destination_ip))
    header[10:12] = _checksum(header).to_bytes(2, "big")
    ethernet = b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\x08\x00"
    return ethernet + bytes(header) + udp


def _mold(sequence: int, messages: list[bytes], *, session: bytes = SESSION, count: int | None = None) -> bytes:
    if count is None:
        count = len(messages)
    body = b"".join(len(message).to_bytes(2, "big") + message for message in messages)
    return session + sequence.to_bytes(8, "big") + count.to_bytes(2, "big") + body


def _common(message_type: str, *, locate: int = LOCATE, timestamp: int = 7, length: int = 36) -> bytearray:
    payload = bytearray(length)
    payload[0] = ord(message_type)
    payload[1:3] = locate.to_bytes(2, "big")
    payload[5:11] = timestamp.to_bytes(6, "big")
    return payload


def _add(reference: int, quantity: int, *, locate: int = LOCATE, timestamp: int = 7) -> bytes:
    payload = _common("A", locate=locate, timestamp=timestamp)
    payload[11:19] = reference.to_bytes(8, "big")
    payload[19] = ord("B")
    payload[20:24] = quantity.to_bytes(4, "big")
    payload[24:32] = b"        "
    payload[32:36] = (0x01020304).to_bytes(4, "big")
    return bytes(payload)


def _execute(reference: int, quantity: int, *, timestamp: int = 8) -> bytes:
    payload = _common("E", timestamp=timestamp, length=31)
    payload[11:19] = reference.to_bytes(8, "big")
    payload[19:23] = quantity.to_bytes(4, "big")
    return bytes(payload)


def _trade() -> bytes:
    payload = _common("P", length=44)
    payload[11:] = bytes(range(33))
    return bytes(payload)


def _config(sequence: int = 100, session: bytes = SESSION, threshold: int = 9, budget: int = 2) -> ModelConfig:
    return ModelConfig(DEST_IP, DEST_PORT, LOCATE, False, None, session, sequence, threshold, budget, True)


class OracleTests(unittest.TestCase):
    def test_complete_frame_reaches_decision_and_persists_state(self):
        oracle = ReferenceOracle(_config(threshold=9, budget=1))
        result = oracle.process_frame(_frame(_mold(100, [_add(1, 10)])))
        self.assertTrue(result.accepted)
        self.assertFalse(result.quarantined)
        self.assertEqual(len(result.messages), 1)
        self.assertEqual(result.decisions[0].action, DecisionAction.BUY)
        self.assertEqual((result.decisions[0].trigger_mold_sequence, result.decisions[0].itch_timestamp, result.decisions[0].signed_imbalance), (100, 7, 10))
        self.assertEqual((oracle.book.bid_total, oracle.book.ask_total, oracle.framing_state.expected_sequence), (10, 0, 101))
        self.assertEqual(oracle.decision_model.current_budget, 0)

    def test_multi_message_and_multi_frame_lifecycle(self):
        oracle = ReferenceOracle(_config(threshold=100))
        first = oracle.process_frame(_frame(_mold(100, [_add(10, 10), _execute(10, 4)])))
        self.assertTrue(first.accepted)
        self.assertEqual(oracle.book.lookup(10).remaining_quantity, 6)
        second = oracle.process_frame(_frame(_mold(102, [_add(11, 5)])))
        self.assertTrue(second.accepted)
        self.assertEqual((oracle.book.bid_total, oracle.book.recompute_aggregates(), oracle.framing_state.expected_sequence), (11, (11, 0), 103))

    def test_heartbeat_and_p_are_noops_for_book_and_decision(self):
        oracle = ReferenceOracle(_config(threshold=9))
        oracle.process_frame(_frame(_mold(100, [_add(1, 10)])))
        prior = (oracle.book.bid_total, oracle.decision_model.previous_imbalance, oracle.decision_model.current_budget, oracle.decision_model.decision_count)
        heartbeat = oracle.process_frame(_frame(_mold(101, [])))
        trade = oracle.process_frame(_frame(_mold(101, [_trade()])))
        self.assertTrue(heartbeat.accepted and trade.accepted)
        self.assertEqual(heartbeat.messages, ())
        self.assertEqual((oracle.book.bid_total, oracle.decision_model.previous_imbalance, oracle.decision_model.current_budget, oracle.decision_model.decision_count), prior)
        self.assertEqual(oracle.framing_state.expected_sequence, 102)

    def test_other_locate_and_nonfatal_profile_filter_do_not_quarantine(self):
        oracle = ReferenceOracle(_config())
        other = oracle.process_frame(_frame(_mold(100, [_add(1, 10, locate=OTHER_LOCATE)])))
        self.assertTrue(other.accepted)
        self.assertEqual(other.messages[0].decode_result.kind.value, "FILTERED_OTHER_INSTRUMENT")
        self.assertTrue(oracle.book.book_valid)
        filtered = oracle.process_frame(_frame(_mold(100, [_add(1, 10)]), destination_ip=1))
        self.assertFalse(filtered.accepted)
        self.assertTrue(filtered.filtered)
        self.assertFalse(filtered.quarantined)
        self.assertTrue(oracle.book.book_valid)
        self.assertEqual(oracle.framing_state.expected_sequence, 101)

    def test_sequence_failure_quarantines_and_rearm_accepts_new_state(self):
        oracle = ReferenceOracle(_config(sequence=100))
        self.assertTrue(oracle.process_frame(_frame(_mold(100, [_add(1, 1)]))).accepted)
        failed = oracle.process_frame(_frame(_mold(102, [_add(2, 1)])))
        self.assertEqual(failed.terminal_error, MoldErrorCode.SEQUENCE_ERROR)
        self.assertTrue(failed.quarantined)
        blocked = oracle.process_frame(_frame(_mold(100, [_add(3, 1)])))
        self.assertEqual(blocked.terminal_error, OracleErrorCode.RECOVERY_REQUIRED)
        oracle.rearm(_config(sequence=7, session=OTHER_SESSION))
        recovered = oracle.process_frame(_frame(_mold(7, [_add(4, 2)], session=OTHER_SESSION)))
        self.assertTrue(recovered.accepted)
        self.assertTrue(oracle.book.book_valid)
        self.assertIsNotNone(oracle.book.lookup(4))

    def test_end_of_session_quarantine_and_rearm(self):
        oracle = ReferenceOracle(_config())
        result = oracle.process_frame(_frame(_mold(100, [], count=MOLD_END_OF_SESSION)))
        self.assertEqual(result.terminal_error, MoldErrorCode.END_OF_SESSION)
        self.assertTrue(result.quarantined)
        oracle.rearm(_config(sequence=55))
        self.assertTrue(oracle.process_frame(_frame(_mold(55, [_add(5, 1)]))).accepted)

    def test_unsupported_itch_quarantines(self):
        oracle = ReferenceOracle(_config())
        result = oracle.process_frame(_frame(_mold(100, [b"Z"])))
        self.assertTrue(result.quarantined)
        self.assertFalse(result.messages[0].decode_result.success)
        self.assertEqual(result.messages[0].decode_result.status.failure_reason, FailureReason.UNSUPPORTED_MESSAGE)
        self.assertEqual(result.decisions, ())

    def test_duplicate_and_unknown_reference_fail_through_frames(self):
        oracle = ReferenceOracle(_config(threshold=100))
        self.assertTrue(oracle.process_frame(_frame(_mold(100, [_add(9, 3)]))).accepted)
        duplicate = oracle.process_frame(_frame(_mold(101, [_add(9, 2)])))
        self.assertTrue(duplicate.quarantined)
        self.assertEqual(duplicate.messages[0].book_result.error.value, "DUPLICATE_REFERENCE")

        oracle.rearm(_config(sequence=200, threshold=100))
        unknown = _frame(_mold(200, [_execute(99, 1)]))
        result = oracle.process_frame(unknown)
        self.assertTrue(result.quarantined)
        self.assertEqual(result.messages[0].book_result.error.value, "UNKNOWN_REFERENCE")

    def test_late_malformed_suffix_commits_prefix_then_quarantines(self):
        oracle = ReferenceOracle(_config(threshold=9, budget=2))
        payload = _mold(100, [_add(20, 10), _execute(20, 4)]) + b"\x00\x05D"
        payload = SESSION + (100).to_bytes(8, "big") + (3).to_bytes(2, "big")
        payload += len(_add(20, 10)).to_bytes(2, "big") + _add(20, 10)
        payload += len(_execute(20, 4)).to_bytes(2, "big") + _execute(20, 4)
        payload += b"\x00\x05D"
        result = oracle.process_frame(_frame(payload))
        self.assertEqual(len(result.messages), 2)
        self.assertEqual(result.terminal_error, MoldErrorCode.MESSAGE_TRUNCATED)
        self.assertEqual(len(result.decisions), 1)
        self.assertEqual(oracle.book.lookup(20).remaining_quantity, 6)
        self.assertEqual((oracle.book.bid_total, oracle.book.recompute_aggregates()), (6, (6, 0)))
        self.assertFalse(oracle.book.book_valid)
        self.assertTrue(oracle.book.recovery_required)
        self.assertEqual(result.framing_result.messages[0].mold_sequence, 100)
        blocked = oracle.process_frame(_frame(_mold(100, [_add(21, 1)])))
        self.assertEqual(blocked.terminal_error, OracleErrorCode.RECOVERY_REQUIRED)

    def test_rearm_clears_prefix_state_and_allows_normal_processing(self):
        oracle = ReferenceOracle(_config(threshold=9, budget=1))
        payload = SESSION + (100).to_bytes(8, "big") + (2).to_bytes(2, "big")
        payload += len(_add(30, 10)).to_bytes(2, "big") + _add(30, 10) + b"\x00\x05D"
        self.assertTrue(oracle.process_frame(_frame(payload)).quarantined)
        oracle.rearm(_config(sequence=300, session=OTHER_SESSION, threshold=2, budget=1))
        self.assertEqual((oracle.book.order_count, oracle.book.bid_total, oracle.decision_model.previous_imbalance, oracle.decision_model.current_budget), (0, 0, 0, 1))
        result = oracle.process_frame(_frame(_mold(300, [_add(31, 3)], session=OTHER_SESSION)))
        self.assertTrue(result.accepted)
        self.assertEqual(result.decisions[0].action, DecisionAction.BUY)


if __name__ == "__main__":
    unittest.main()
