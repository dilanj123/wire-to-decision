#!/usr/bin/env python3
"""Small hand-calculated replay tests for the independent C++ checker."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / "tools" / "cpp" / "build" / "w2d_checker"
BASE = 0x1020304050607080
SESSION = b"W2DTEST001"
SYMBOL = b"ALPH    "
LOCATE = 0x2345
DEST_IP = 0xC6336407
DEST_PORT = 0x1234


def put(data, offset, width, value):
    data[offset:offset + width] = value.to_bytes(width, "big")


def itch(kind, *, ref=0x1122334455667788, new_ref=0x8877665544332211,
         qty=10, price=100, side=b"B", locate=LOCATE, salt=0):
    size = {"A": 36, "F": 40, "E": 31, "C": 36, "X": 23,
            "D": 19, "U": 35, "P": 44}[kind]
    data = bytearray(size)
    data[0] = ord(kind)
    put(data, 1, 2, locate)
    put(data, 3, 2, 0xA100 + salt)
    put(data, 5, 6, 0x010203040500 + salt)
    if kind in "AF":
        put(data, 11, 8, ref)
        data[19] = side[0]
        put(data, 20, 4, qty)
        data[24:32] = SYMBOL
        put(data, 32, 4, price)
        if kind == "F": data[36:40] = b"MPID"
    elif kind in "ECX":
        put(data, 11, 8, ref)
        put(data, 19, 4, qty)
        if kind == "C":
            data[23] = 1
            put(data, 24, 4, 0xDEADBEEF)
            data[28:36] = b"XYZ12345"
    elif kind == "D":
        put(data, 11, 8, ref)
    elif kind == "U":
        put(data, 11, 8, ref)
        put(data, 19, 8, new_ref)
        put(data, 27, 4, qty)
        put(data, 31, 4, price)
    return bytes(data)


def mold(messages, sequence, *, session=SESSION, count=None, body=None):
    body = b"".join(len(msg).to_bytes(2, "big") + msg for msg in messages) if body is None else body
    n = len(messages) if count is None else count
    return session + sequence.to_bytes(8, "big") + n.to_bytes(2, "big") + body


def checksum(data):
    if len(data) % 2: data += b"\0"
    total = sum(int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2))
    while total >> 16: total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def frame(payload, *, session=SESSION, destination=DEST_IP, port=DEST_PORT,
          udp_checksum=0, ether_type=0x0800):
    del session  # Session is encoded by the supplied Mold payload.
    udp = bytearray(8)
    put(udp, 0, 2, 0xBEEF)
    put(udp, 2, 2, port)
    put(udp, 4, 2, 8 + len(payload))
    put(udp, 6, 2, udp_checksum)
    ip = bytearray(20)
    ip[0] = 0x45
    put(ip, 2, 2, 20 + len(udp) + len(payload))
    ip[8], ip[9] = 64, 17
    put(ip, 16, 4, destination)
    put(ip, 10, 2, checksum(bytes(ip)))
    eth = bytes.fromhex("0201020304050A0B0C0D0E0F") + ether_type.to_bytes(2, "big")
    return eth + bytes(ip) + bytes(udp) + payload


def config(*, threshold=10, budget=4, enable=1, sequence=BASE):
    return (f"CONFIG destination_ip=0x{DEST_IP:08x} destination_port=0x{DEST_PORT:04x} "
            f"session={SESSION.hex()} expected_sequence=0x{sequence:016x} "
            f"tracked_locate=0x{LOCATE:04x} symbol={SYMBOL.hex()} symbol_check=1 "
            f"threshold={threshold} budget={budget} enable={enable}")


def rtl_log(decisions, *, bid, ask, sequence, quarantined, latency=True):
    rows = ["WIRE_RTL_LOG_V1"]
    for cycle, action, seq, timestamp, imbalance in decisions:
        rows.append(f"DECISION cycle={cycle} action={action} mold_sequence={seq} "
                    f"itch_timestamp={timestamp} imbalance={imbalance}")
    if latency:
        for cycle, *_ in decisions:
            rows.append(f"LATENCY cycle={cycle} l1=80 l2=2 l3=100")
    rows.append(f"STATE bid_total={bid} ask_total={ask} expected_sequence={sequence} "
                f"quarantined={int(quarantined)}")
    return "\n".join(rows) + "\n"


class CheckerTests(unittest.TestCase):
    def run_case(self, commands, actual, *, pass_expected=True, summary_extra=None,
                 config_line=None):
        with tempfile.TemporaryDirectory() as temp:
            replay_path = Path(temp) / "case.w2d"
            actual_path = Path(temp) / "actual.log"
            summary_path = Path(temp) / "summary.json"
            replay_path.write_text("\n".join(["WIRE_REPLAY_V1", config_line or config(), *commands]) + "\n")
            actual_path.write_text(actual)
            result = subprocess.run([str(CHECKER), "compare", str(replay_path),
                                     str(actual_path), str(summary_path)],
                                    text=True, capture_output=True)
            summary = json.loads(summary_path.read_text())
            self.assertEqual(result.returncode == 0, pass_expected, result.stderr + result.stdout)
            self.assertEqual(summary["replay_pass"], pass_expected)
            if summary_extra:
                for key, value in summary_extra.items():
                    self.assertEqual(summary[key], value)
            return result, summary

    def test_add_buy_sell_and_budget_exhaustion(self):
        a = itch("A", ref=0x101, qty=10, salt=1)
        s = itch("A", ref=0x202, qty=20, side=b"S", salt=2)
        commands = [f"FRAME {frame(mold([a], BASE)).hex()}",
                    f"FRAME {frame(mold([s], BASE + 1)).hex()}"]
        self.run_case(commands, rtl_log([(20, "BUY", BASE, 0x010203040501, 10)],
            bid=10, ask=20, sequence=BASE + 2, quarantined=False),
            summary_extra={"frames_checked": 2, "messages_checked": 2, "decisions_compared": 1},
            config_line=config(budget=1))

    def test_sell_crossing(self):
        sell = itch("A", ref=0x303, qty=5, side=b"S", salt=3)
        self.run_case([f"FRAME {frame(mold([sell], BASE)).hex()}"],
            rtl_log([(14, "SELL", BASE, 0x010203040503, -5)], bid=0, ask=5,
                    sequence=BASE + 1, quarantined=False), config_line=config(threshold=5))

    def test_mpid_add_and_execute(self):
        messages = [itch("F", ref=0x333, qty=10, side=b"S", salt=23),
                    itch("E", ref=0x333, qty=4, salt=24)]
        self.run_case([f"FRAME {frame(mold(messages, BASE)).hex()}"],
            rtl_log([], bid=0, ask=6, sequence=BASE + 2, quarantined=False, latency=False),
            config_line=config(threshold=100))

    def test_live_enable_advances_imbalance_without_stale_decision(self):
        first = itch("A", ref=0x3333, qty=10, salt=25)
        second = itch("A", ref=0x4444, qty=1, salt=26)
        commands = ["ENABLE 0", f"FRAME {frame(mold([first], BASE)).hex()}",
                    "ENABLE 1", f"FRAME {frame(mold([second], BASE + 1)).hex()}"]
        self.run_case(commands,
            rtl_log([], bid=11, ask=0, sequence=BASE + 2, quarantined=False, latency=False))

    def test_partial_execution_and_full_cancel(self):
        messages = [itch("A", ref=0x404, qty=12, salt=4),
                    itch("C", ref=0x404, qty=2, salt=5),
                    itch("X", ref=0x404, qty=10, salt=6)]
        self.run_case([f"FRAME {frame(mold(messages, BASE)).hex()}"],
            rtl_log([], bid=0, ask=0, sequence=BASE + 3, quarantined=False, latency=False),
            config_line=config(threshold=100))

    def test_replace_and_delete(self):
        old, new = 0x505, 0x606
        packets = [frame(mold([itch("A", ref=old, qty=10, salt=7)], BASE)),
                   frame(mold([itch("U", ref=old, new_ref=new, qty=15, price=777, salt=8)], BASE + 1)),
                   frame(mold([itch("D", ref=new, salt=9)], BASE + 2))]
        self.run_case([f"FRAME {packet.hex()}" for packet in packets],
            rtl_log([], bid=0, ask=0, sequence=BASE + 3, quarantined=False, latency=False),
            config_line=config(threshold=100))

    def test_p_other_locate_and_multi_message_sequence(self):
        messages = [itch("P", salt=10), itch("A", ref=0x707, qty=2, locate=LOCATE + 1, salt=11),
                    itch("A", ref=0x808, qty=10, salt=12)]
        self.run_case([f"FRAME {frame(mold(messages, BASE)).hex()}"],
            rtl_log([(30, "BUY", BASE + 2, 0x01020304050C, 10)], bid=10, ask=0,
                    sequence=BASE + 3, quarantined=False))

    def test_duplicate_failure_quarantines_until_rearm(self):
        order = itch("A", ref=0x909, qty=4, salt=13)
        commands = [f"FRAME {frame(mold([order], BASE)).hex()}",
                    f"FRAME {frame(mold([order], BASE + 1)).hex()}", "REARM",
                    f"FRAME {frame(mold([itch('E', ref=0x999, qty=1, salt=14)], BASE)).hex()}"]
        self.run_case(commands,
            rtl_log([(20, "BUY", BASE, 0x01020304050D, 4)], bid=0, ask=0,
                    sequence=BASE + 1, quarantined=True), config_line=config(threshold=4))

    def test_bad_session_then_explicit_rearm(self):
        wrong = frame(mold([itch("A", ref=0xA0A, qty=10, salt=15)], BASE,
                           session=b"BADSESSION"))
        good = frame(mold([itch("A", ref=0xB0B, qty=10, salt=16)], BASE))
        self.run_case([f"FRAME {wrong.hex()}", "REARM", f"FRAME {good.hex()}"],
            rtl_log([(40, "BUY", BASE, 0x010203040510, 10)], bid=10, ask=0,
                    sequence=BASE + 1, quarantined=False))

    def test_unsupported_itch_quarantines_until_rearm(self):
        unsupported = b"Z" + bytes(11)
        bad = frame(mold([unsupported], BASE))
        blocked = frame(mold([itch("A", ref=0xAB0, qty=10, salt=27)], BASE + 1))
        fresh = frame(mold([itch("A", ref=0xAC0, qty=10, salt=28)], BASE))
        commands = [f"FRAME {bad.hex()}", f"FRAME {blocked.hex()}", "REARM",
                    f"FRAME {fresh.hex()}"]
        self.run_case(commands,
            rtl_log([(48, "BUY", BASE, 0x01020304051C, 10)], bid=10, ask=0,
                    sequence=BASE + 1, quarantined=False))

    def test_malformed_suffix_keeps_only_complete_prefix(self):
        prefix = itch("A", ref=0xC0C, qty=10, salt=17)
        body = len(prefix).to_bytes(2, "big") + prefix + b"\x00\x05\xaa\xbb"
        malformed = mold([], BASE, count=2, body=body)
        self.run_case([f"FRAME {frame(malformed).hex()}"],
            rtl_log([(23, "BUY", BASE, 0x010203040511, 10)], bid=10, ask=0,
                    sequence=BASE, quarantined=True))

    def test_corrupt_actual_decision_is_detected(self):
        order = itch("A", ref=0xD0D, qty=10, salt=18)
        self.run_case([f"FRAME {frame(mold([order], BASE)).hex()}"],
            rtl_log([(20, "BUY", BASE, 0x010203040512, 9)], bid=10, ask=0,
                    sequence=BASE + 1, quarantined=False), pass_expected=False)

    def test_hash_vectors_and_full_set_collision(self):
        # These frozen vectors all select set 1. The third ADD must fail with
        # both occupied ways unchanged and no eviction.
        messages = [itch("A", ref=1, qty=1, salt=19),
                    itch("A", ref=0x200, qty=1, salt=20),
                    itch("A", ref=0x40000, qty=1, salt=21)]
        self.run_case([f"FRAME {frame(mold(messages, BASE)).hex()}"],
            rtl_log([], bid=2, ask=0, sequence=BASE + 3, quarantined=True, latency=False),
            config_line=config(threshold=100))

    def test_mold_sequence_wrap(self):
        sequence = (1 << 64) - 1
        order = itch("A", ref=0xE0E, qty=10, salt=22)
        self.run_case([f"FRAME {frame(mold([order], sequence)).hex()}"],
            rtl_log([(22, "BUY", sequence, 0x010203040516, 10)], bid=10, ask=0,
                    sequence=0, quarantined=False),
            config_line=config(sequence=sequence))

    def test_python_oracle_additional_crosscheck(self):
        sys.path.insert(0, str(ROOT / "model" / "python"))
        from wire_to_decision.oracle import ReferenceOracle
        from wire_to_decision.types import ModelConfig

        replay_path = ROOT / "tools" / "cpp" / "replays" / "canonical.w2d"
        config_fields = next(line for line in replay_path.read_text().splitlines()
                             if line.startswith("CONFIG "))
        cfg = dict(field.split("=", 1) for field in config_fields.split()[1:])
        model_config = ModelConfig(
            int(cfg["destination_ip"], 0), int(cfg["destination_port"], 0),
            int(cfg["tracked_locate"], 0), bool(int(cfg["symbol_check"])),
            bytes.fromhex(cfg["symbol"]), bytes.fromhex(cfg["session"]),
            int(cfg["expected_sequence"], 0), int(cfg["threshold"], 0),
            int(cfg["budget"], 0), bool(int(cfg["enable"])),
        )
        oracle = ReferenceOracle(model_config)
        expected = []
        for line in replay_path.read_text().splitlines():
            if line.startswith("FRAME "):
                result = oracle.process_frame(bytes.fromhex(line.split(maxsplit=1)[1]))
                expected.extend((d.action.value, d.trigger_mold_sequence,
                                 d.itch_timestamp, d.signed_imbalance)
                                for d in result.decisions)

        output = subprocess.run([str(CHECKER), "run", str(replay_path)],
                                check=True, capture_output=True, text=True).stdout
        actual = []
        for line in output.splitlines():
            parts = line.split()
            if parts and parts[0] in ("BUY", "SELL"):
                fields = dict(part.split("=", 1) for part in parts[1:])
                actual.append((parts[0], int(fields["seq"]), int(fields["timestamp"]),
                               int(fields["imbalance"])))
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
