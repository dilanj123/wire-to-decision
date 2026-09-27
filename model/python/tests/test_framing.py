import struct
import unittest

from wire_to_decision import (
    FramingErrorCode,
    FramingState,
    ModelConfig,
    MoldErrorCode,
    frame_packet,
)
from wire_to_decision.checksum import ipv4_header_checksum_valid
from wire_to_decision.mold import MOLD_END_OF_SESSION, MOLD_HEADER_BYTES, parse_mold_packet
from wire_to_decision.types import FailureReason, ModelStatus


SESSION = b"SESSION123"
DEST_IP = 0xC6336407
DEST_PORT = 9000


def _checksum_for_test(data: bytes) -> int:
    total = 0
    for offset in range(0, len(data), 2):
        total += int.from_bytes(data[offset : offset + 2], "big")
        total = (total & 0xFFFF) + (total >> 16)
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def _mold(sequence: int, messages: list[bytes], session: bytes = SESSION, count: int | None = None) -> bytes:
    if count is None:
        count = len(messages)
    body = b"".join(len(message).to_bytes(2, "big") + message for message in messages)
    return session + sequence.to_bytes(8, "big") + count.to_bytes(2, "big") + body


def _frame(mold: bytes, *, destination_ip: int = DEST_IP, destination_port: int = DEST_PORT, protocol: int = 17, udp_checksum: int = 0, total_length_adjust: int = 0, flags_fragment: int = 0x4000) -> bytes:
    udp_length = 8 + len(mold)
    udp = struct.pack("!HHHH", 40000, destination_port, udp_length, udp_checksum) + mold
    total_length = 20 + len(udp) + total_length_adjust
    header = bytearray(struct.pack("!BBHHHBBHII", 0x45, 0, total_length, 0x1234, flags_fragment, 64, protocol, 0, 0xC0000201, destination_ip))
    header[10:12] = _checksum_for_test(header).to_bytes(2, "big")
    ethernet = b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb" + b"\x08\x00"
    return ethernet + bytes(header) + udp


def _config(sequence: int = 100) -> ModelConfig:
    return ModelConfig(DEST_IP, DEST_PORT, 1, False, None, SESSION, sequence, 1, 1, True)


class ChecksumTests(unittest.TestCase):
    def test_fixed_ipv4_checksum_vector(self):
        header = bytes.fromhex("450000341234400040113c49c0000201c6336407")
        self.assertTrue(ipv4_header_checksum_valid(header))
        corrupted = bytearray(header)
        corrupted[8] ^= 1
        self.assertFalse(ipv4_header_checksum_valid(bytes(corrupted)))
        corrupted = bytearray(header)
        corrupted[10] ^= 1
        self.assertFalse(ipv4_header_checksum_valid(bytes(corrupted)))


class FramingTests(unittest.TestCase):
    def test_one_and_multi_message_progression(self):
        state = FramingState.from_config(_config())
        first = frame_packet(_frame(_mold(100, [b"A"])), _config(), state)
        self.assertTrue(first.success)
        self.assertEqual([(m.mold_sequence, m.payload) for m in first.messages], [(100, b"A")])
        second = frame_packet(_frame(_mold(101, [b"B", b"C"])), _config(), first.next_state)
        self.assertTrue(second.success)
        self.assertEqual([m.mold_sequence for m in second.messages], [101, 102])
        self.assertEqual(second.next_state.expected_sequence, 103)

    def test_ethernet_padding_after_ipv4_datagram_is_ignored(self):
        result = frame_packet(_frame(_mold(100, [b"A"])) + b"\x00\x00\x00", _config())
        self.assertTrue(result.success)
        self.assertEqual(result.messages[0].payload, b"A")

    def test_valid_heartbeat_does_not_advance(self):
        result = frame_packet(_frame(_mold(100, [])), _config())
        self.assertTrue(result.success)
        self.assertEqual(result.messages, ())
        self.assertEqual(result.next_state.expected_sequence, 100)

    def test_end_of_session_requires_recovery(self):
        result = frame_packet(_frame(_mold(100, [], count=MOLD_END_OF_SESSION)), _config())
        self.assertEqual(result.error, MoldErrorCode.END_OF_SESSION)
        self.assertEqual(result.messages, ())
        self.assertFalse(result.next_state.status.book_valid)
        self.assertTrue(result.next_state.status.recovery_required)

    def test_sequence_regression_gap_and_heartbeat_error(self):
        for sequence in (99, 101):
            result = frame_packet(_frame(_mold(sequence, [b"X"])), _config())
            self.assertEqual(result.error, MoldErrorCode.SEQUENCE_ERROR)
            self.assertEqual(result.next_state.status.failure_reason, FailureReason.SEQUENCE_ERROR)
        result = frame_packet(_frame(_mold(99, [])), _config())
        self.assertEqual(result.error, MoldErrorCode.SEQUENCE_ERROR)

    def test_mold_prefix_is_retained_on_late_truncation(self):
        payload = SESSION + (100).to_bytes(8, "big") + (3).to_bytes(2, "big")
        payload += b"\x00\x01A\x00\x02BC\x00\x05D"
        result = frame_packet(_frame(payload), _config())
        self.assertEqual(result.error, MoldErrorCode.MESSAGE_TRUNCATED)
        self.assertEqual([(m.mold_sequence, m.payload) for m in result.messages], [(100, b"A"), (101, b"BC")])
        self.assertFalse(result.next_state.status.book_valid)
        self.assertTrue(result.next_state.status.recovery_required)

    def test_mold_truncation_and_trailing_bytes(self):
        result = frame_packet(_frame(SESSION + (100).to_bytes(8, "big")), _config())
        self.assertEqual(result.error, MoldErrorCode.HEADER_TRUNCATED)
        result = frame_packet(_frame(_mold(100, [b"A"]) + b"\x00"), _config())
        self.assertEqual(result.error, MoldErrorCode.TRAILING_BYTES)

    def test_session_mismatch(self):
        result = frame_packet(_frame(_mold(100, [b"A"], session=b"OTHER_____")), _config())
        self.assertEqual(result.error, MoldErrorCode.SESSION_MISMATCH)
        self.assertEqual(result.next_state.status.failure_reason, FailureReason.SESSION_MISMATCH)

    def test_ethernet_and_ipv4_rejections(self):
        base = _frame(_mold(100, [b"A"]))
        self.assertEqual(frame_packet(base[:13], _config()).error, FramingErrorCode.FRAME_TRUNCATED)
        self.assertFalse(frame_packet(base[:13], _config()).next_state.status.book_valid)
        self.assertEqual(frame_packet(base[:12] + b"\x08\x06" + base[14:], _config()).error, FramingErrorCode.UNSUPPORTED_ETHERTYPE)
        bad_version = bytearray(base)
        bad_version[14] = 0x65
        self.assertEqual(frame_packet(bytes(bad_version), _config()).error, FramingErrorCode.INVALID_IPV4_VERSION)
        bad_ihl = bytearray(base)
        bad_ihl[14] = 0x46
        self.assertEqual(frame_packet(bytes(bad_ihl), _config()).error, FramingErrorCode.UNSUPPORTED_IPV4_IHL)
        bad_checksum = bytearray(base)
        bad_checksum[24] ^= 1
        checksum_result = frame_packet(bytes(bad_checksum), _config())
        self.assertEqual(checksum_result.error, FramingErrorCode.IPV4_CHECKSUM)
        self.assertFalse(checksum_result.next_state.status.book_valid)
        bad_total = bytearray(base)
        bad_total[16:18] = (19).to_bytes(2, "big")
        self.assertEqual(frame_packet(bytes(bad_total), _config()).error, FramingErrorCode.IPV4_LENGTH)
        fragmented = _frame(_mold(100, [b"A"]), flags_fragment=0x2000)
        self.assertEqual(frame_packet(fragmented, _config()).error, FramingErrorCode.IPV4_FRAGMENTED)
        self.assertEqual(frame_packet(_frame(_mold(100, [b"A"]), destination_ip=1), _config()).error, FramingErrorCode.WRONG_DESTINATION_IP)
        self.assertEqual(frame_packet(_frame(_mold(100, [b"A"]), protocol=6), _config()).error, FramingErrorCode.NON_UDP_PROTOCOL)

    def test_udp_rejections(self):
        base = _frame(_mold(100, [b"A"]))
        truncated_udp = bytearray(base[:14 + 20 + 7])
        truncated_udp[16:18] = (27).to_bytes(2, "big")
        truncated_udp[24:26] = b"\x00\x00"
        truncated_udp[24:26] = _checksum_for_test(bytes(truncated_udp[14:34])).to_bytes(2, "big")
        self.assertEqual(frame_packet(bytes(truncated_udp), _config()).error, FramingErrorCode.UDP_HEADER_TRUNCATED)
        wrong_port = _frame(_mold(100, [b"A"]), destination_port=9001)
        self.assertEqual(frame_packet(wrong_port, _config()).error, FramingErrorCode.WRONG_DESTINATION_PORT)
        nonzero_checksum = _frame(_mold(100, [b"A"]), udp_checksum=1)
        self.assertEqual(frame_packet(nonzero_checksum, _config()).error, FramingErrorCode.UDP_CHECKSUM_UNSUPPORTED)
        bad_length = bytearray(base)
        bad_length[14 + 20 + 4:14 + 20 + 6] = (7).to_bytes(2, "big")
        self.assertEqual(frame_packet(bytes(bad_length), _config()).error, FramingErrorCode.UDP_LENGTH)


if __name__ == "__main__":
    unittest.main()
