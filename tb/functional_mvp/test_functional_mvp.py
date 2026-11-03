import random
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model" / "python"))
from wire_to_decision.oracle import ReferenceOracle
from wire_to_decision.types import ModelConfig
from wire_to_decision.checksum import internet_checksum

DEST_IP = 0xC6336407
DEST_PORT = 0x1234
LOC = 0x2345
SESSION = b"W2DTEST001"
BASE_SEQ = 0x1020304050607080
SYMBOL = b"ALPH    "


def put(buf, offset, width, value):
    buf[offset:offset + width] = value.to_bytes(width, "big")


def itch(kind, *, ref=0x1122334455667788, qty=10, price=0x12345678,
         side=b"B", salt=0, locate=LOC, length_override=None,
         symbol=SYMBOL):
    sizes = {"A": 36, "F": 40, "E": 31, "C": 36, "X": 23, "D": 19,
             "U": 35, "P": 44, "Z": 12}
    size = length_override if length_override is not None else sizes[kind]
    data = bytearray(size)
    if size:
        data[0] = ord(kind)
    if size >= 11:
        put(data, 1, 2, locate)
        put(data, 3, 2, 0xA100 + salt)
        put(data, 5, 6, 0x010203040500 + salt)
    if kind in ("A", "F") and size >= sizes[kind]:
        put(data, 11, 8, ref)
        data[19] = side[0]
        put(data, 20, 4, qty)
        data[24:32] = symbol
        put(data, 32, 4, price)
        if kind == "F":
            data[36:40] = b"MPID"
    elif kind in ("E", "C", "X") and size >= sizes[kind]:
        put(data, 11, 8, ref)
        put(data, 19, 4, qty)
        if kind == "C":
            data[23] = 1
            put(data, 24, 4, 0xDEADBEEF)
            data[28:36] = b"XYZ12345"
    elif kind == "D" and size >= 19:
        put(data, 11, 8, ref)
    elif kind == "U" and size >= 35:
        put(data, 11, 8, ref)
        put(data, 19, 8, 0x8877665544332211 + salt)
        put(data, 27, 4, qty)
        put(data, 31, 4, price)
    return bytes(data)


def mold(messages, sequence=BASE_SEQ, *, body=None, count=None, session=SESSION):
    body = (b"".join(len(m).to_bytes(2, "big") + m for m in messages)
            if body is None else body)
    return session + sequence.to_bytes(8, "big") + \
        (len(messages) if count is None else count).to_bytes(2, "big") + body


def frame(mold_bytes, *, bad_ip_checksum=False, ether_type=0x0800,
          destination_port=DEST_PORT, destination_ip=DEST_IP):
    udp = bytearray(8)
    put(udp, 0, 2, 0xBEEF)
    put(udp, 2, 2, destination_port)
    put(udp, 4, 2, len(udp) + len(mold_bytes))
    eth = bytes.fromhex("0201020304050A0B0C0D0E0F") + ether_type.to_bytes(2, "big")
    ip_payload = bytes(udp) + mold_bytes
    iph = bytearray(20)
    iph[0] = 0x45
    put(iph, 2, 2, 20 + len(ip_payload))
    iph[8], iph[9] = 64, 17
    put(iph, 16, 4, destination_ip)
    put(iph, 10, 2, internet_checksum(bytes(iph)))
    if bad_ip_checksum:
        iph[10] ^= 1
    return eth + bytes(iph) + ip_payload


def beats(data):
    result = []
    for off in range(0, len(data), 8):
        part = data[off:off + 8]
        word = sum(byte << (8 * lane) for lane, byte in enumerate(part))
        result.append((word, (1 << len(part)) - 1, int(off + len(part) == len(data))))
    return result


def config(seq=BASE_SEQ, *, threshold=10, budget=20, enabled=True):
    return ModelConfig(DEST_IP, DEST_PORT, LOC, True, SYMBOL, SESSION, seq,
                       threshold, budget, enabled)


class Bench:
    def __init__(self, dut):
        self.d = dut
        self.decisions = []
        self.commits = []
        self.accepted_beats = 0
        self.rx_stall_cycles = 0
        self.config = None

    async def setup(self, *, seq=BASE_SEQ, threshold=10, budget=20,
                    enabled=True, rearm=False):
        d = self.d
        self.config = config(seq, threshold=threshold, budget=budget, enabled=enabled)
        await FallingEdge(d.clk)
        pins = {
            "rst": 1, "rearm": int(rearm),
            "cfg_destination_ipv4": DEST_IP, "cfg_destination_udp_port": DEST_PORT,
            "cfg_active_session": int.from_bytes(SESSION, "big"),
            "cfg_expected_sequence": seq, "cfg_tracked_stock_locate": LOC,
            "cfg_symbol_check_enable": 1,
            "cfg_expected_stock_symbol": int.from_bytes(SYMBOL, "big"),
            "cfg_decision_threshold": threshold, "cfg_initial_budget": budget,
            "decision_enable": int(enabled), "rx_data": 0, "rx_keep": 0,
            "rx_valid": 0, "rx_last": 0, "decision_ready": 1,
            "error_ready": 1, "debug_reference": 0,
        }
        for name, value in pins.items():
            getattr(d, name).value = value
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        d.rst.value = 0
        d.rearm.value = 0
        self.decisions.clear()
        self.commits.clear()
        self.accepted_beats = 0
        self.rx_stall_cycles = 0

    def sample_decision(self):
        d = self.d
        return (int(d.decision_action.value), int(d.decision_mold_sequence.value),
                int(d.decision_itch_timestamp.value), self.signed49(d.decision_signed_imbalance.value))

    @staticmethod
    def signed49(signal):
        value = int(signal)
        return value - (1 << 49) if value & (1 << 48) else value

    async def send_frame(self, data, *, stall_seed=0, max_cycles=12000,
                         hold_decision=False):
        d = self.d
        stream = beats(data)
        index = 0
        held = None
        prev_rx_stall = None
        prev_decision_stall = None
        for cycle in range(max_cycles):
            await FallingEdge(d.clk)
            if held is None and index < len(stream):
                held = stream[index]
                d.rx_data.value, d.rx_keep.value, d.rx_last.value = held
                d.rx_valid.value = 1
            d.decision_ready.value = 0 if hold_decision else int((cycle + stall_seed) % 5 != 2)
            await Timer(1, unit="ns")
            rx_tuple = (int(d.rx_valid.value), int(d.rx_data.value),
                        int(d.rx_keep.value), int(d.rx_last.value))
            decision_tuple = self.sample_decision()
            if prev_rx_stall is not None:
                assert rx_tuple == prev_rx_stall, "external input changed while stalled"
            if prev_decision_stall is not None:
                assert int(d.decision_valid.value) == 1
                assert decision_tuple == prev_decision_stall, "decision changed while stalled"
            rx_fire = int(d.rx_valid.value) and int(d.rx_ready.value)
            if int(d.rx_valid.value) and not int(d.rx_ready.value):
                self.rx_stall_cycles += 1
            if int(d.decision_valid.value) and int(d.decision_ready.value):
                self.decisions.append(self.sample_decision())
            if int(d.commit_valid_observed.value) and int(d.commit_ready_observed.value):
                self.commits.append((int(d.commit_mold_sequence_observed.value),
                                     int(d.commit_bid_total_observed.value),
                                     int(d.commit_ask_total_observed.value),
                                     int(d.parser_recovery_required.value)))
            prev_rx_stall = rx_tuple if int(d.rx_valid.value) and not int(d.rx_ready.value) else None
            prev_decision_stall = (decision_tuple if int(d.decision_valid.value) and
                                   not int(d.decision_ready.value) else None)
            await RisingEdge(d.clk)
            if rx_fire:
                index += 1
                held = None
                d.rx_valid.value = 0
                self.accepted_beats += 1
            if index == len(stream):
                break
        else:
            raise AssertionError(f"RX timeout {index}/{len(stream)}; recovery={int(d.parser_recovery_required.value)}")

        # Drain pipeline and decision backpressure deterministically.
        d.rx_valid.value = 0
        for cycle in range(400):
            await FallingEdge(d.clk)
            d.decision_ready.value = 0 if hold_decision else int(cycle % 5 != 1)
            await Timer(1, unit="ns")
            decision_tuple = self.sample_decision()
            if prev_decision_stall is not None:
                assert int(d.decision_valid.value) == 1
                assert decision_tuple == prev_decision_stall, "decision changed during drain stall"
            if int(d.decision_valid.value) and int(d.decision_ready.value):
                self.decisions.append(self.sample_decision())
            if int(d.commit_valid_observed.value) and int(d.commit_ready_observed.value):
                self.commits.append((int(d.commit_mold_sequence_observed.value),
                                     int(d.commit_bid_total_observed.value),
                                     int(d.commit_ask_total_observed.value),
                                     int(d.parser_recovery_required.value)))
            prev_decision_stall = (decision_tuple if int(d.decision_valid.value) and
                                   not int(d.decision_ready.value) else None)
            await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        d.decision_ready.value = 0 if hold_decision else 1
        await RisingEdge(d.clk)


def clock(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())


def oracle_decisions(result):
    return [(int(item.action.value == "SELL"), item.trigger_mold_sequence,
             item.itch_timestamp, item.signed_imbalance) for item in result.decisions]


@cocotb.test()
async def test_full_chain_buy_sell_and_oracle(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=10, budget=8)
    oracle = ReferenceOracle(b.config)
    ref_buy, ref_sell = 0x1001, 0x2002
    first = frame(mold([itch("A", ref=ref_buy, qty=10, price=100, salt=1)]))
    second = frame(mold([itch("F", ref=ref_sell, qty=20, price=101, side=b"S", salt=2)], BASE_SEQ + 1))
    expected = oracle.process_frame(first)
    await b.send_frame(first, stall_seed=3)
    assert b.decisions == oracle_decisions(expected) == [(0, BASE_SEQ, 0x010203040501, 10)]
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (10, 0)
    expected = oracle.process_frame(second)
    await b.send_frame(second, stall_seed=7)
    assert b.decisions[-len(expected.decisions):] == oracle_decisions(expected)
    assert b.decisions[-1] == (1, BASE_SEQ + 1, 0x010203040502, -10)
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (10, 20)
    assert int(dut.remaining_budget.value) == 6
    assert int(dut.decision_count.value) == 2
    assert int(dut.current_expected_sequence.value) == BASE_SEQ + 2
    assert int(dut.book_valid.value) == 1 and int(dut.parser_recovery_required.value) == 0


@cocotb.test()
async def test_nonmutating_heartbeat_filter_and_no_repeat(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=5, budget=5)
    oracle = ReferenceOracle(b.config)
    a = frame(mold([itch("A", ref=0x3001, qty=7, price=90)]))
    await b.send_frame(a)
    assert len(b.decisions) == 1
    start = len(b.decisions)
    p_frame = frame(mold([itch("P", salt=3)], BASE_SEQ + 1))
    heartbeat = frame(mold([], BASE_SEQ + 2, count=0))
    filtered = frame(mold([itch("A", ref=0x3002, qty=2, price=91,
                                locate=LOC + 1)], BASE_SEQ + 2))
    vlan = frame(mold([itch("A", ref=0x3FFF)], BASE_SEQ + 3), ether_type=0x8100)
    wrong_port = frame(mold([itch("A", ref=0x3FFE)], BASE_SEQ + 3),
                       destination_port=DEST_PORT + 1)
    await b.send_frame(p_frame)
    await b.send_frame(heartbeat)
    await b.send_frame(filtered)
    await b.send_frame(vlan)
    await b.send_frame(wrong_port)
    above = frame(mold([itch("A", ref=0x3003, qty=1, price=92)], BASE_SEQ + 3))
    exp = []
    for packet in (a, p_frame, heartbeat, filtered, vlan, wrong_port, above):
        exp.extend(oracle_decisions(oracle.process_frame(packet)))
    await b.send_frame(above)
    assert b.decisions == exp and len(b.decisions) == start
    assert int(dut.parser_recovery_required.value) == 0
    assert int(dut.bid_total.value) == 8
    assert int(dut.current_expected_sequence.value) == BASE_SEQ + 4


@cocotb.test()
async def test_all_mutation_message_types_through_full_parser(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=30, budget=4)
    oracle = ReferenceOracle(b.config)
    old_ref, new_ref = 0x7101, 0x8877665544332211 + 5
    messages = [
        itch("A", ref=old_ref, qty=30, price=100, side=b"B", salt=1),
        itch("E", ref=old_ref, qty=5, salt=2),
        itch("C", ref=old_ref, qty=5, salt=3),
        itch("X", ref=old_ref, qty=5, salt=4),
        itch("U", ref=old_ref, qty=8, price=120, salt=5),
        itch("D", ref=new_ref, salt=6),
    ]
    packet = frame(mold(messages))
    expected = oracle.process_frame(packet)
    await b.send_frame(packet, stall_seed=4)
    assert b.decisions == oracle_decisions(expected)
    assert b.decisions == [(0, BASE_SEQ, 0x010203040501, 30)]
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (0, 0)
    assert int(dut.book_valid.value) == 1
    assert int(dut.current_expected_sequence.value) == BASE_SEQ + len(messages)


@cocotb.test()
async def test_live_enable_no_stale_crossing_and_budget_exhaustion(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=5, budget=4, enabled=True)
    dut.decision_enable.value = 0
    await b.send_frame(frame(mold([itch("A", ref=0x7301, qty=8, price=1)])))
    assert b.decisions == [] and int(dut.previous_imbalance.value) == 8

    dut.decision_enable.value = 1
    await b.send_frame(frame(mold([itch("A", ref=0x7302, qty=1, price=1)], BASE_SEQ + 1)))
    assert b.decisions == []  # re-enable above threshold does not replay crossing
    await b.send_frame(frame(mold([itch("A", ref=0x7303, qty=5, price=1, side=b"S")], BASE_SEQ + 2)))
    assert b.decisions == [] and int(dut.previous_imbalance.value) == 4
    await b.send_frame(frame(mold([itch("A", ref=0x7304, qty=2, price=1)], BASE_SEQ + 3)))
    assert b.decisions == [(0, BASE_SEQ + 3, 0x010203040500, 6)]

    # Re-arm a one-credit epoch. Subsequent crossings still mutate the book.
    await b.setup(seq=BASE_SEQ + 10, threshold=5, budget=1, rearm=True)
    await b.send_frame(frame(mold([itch("A", ref=0x7311, qty=5, price=1)], BASE_SEQ + 10)))
    await b.send_frame(frame(mold([itch("A", ref=0x7312, qty=10, price=1, side=b"S")], BASE_SEQ + 11)))
    await b.send_frame(frame(mold([itch("A", ref=0x7313, qty=10, price=1)], BASE_SEQ + 12)))
    assert b.decisions == [(0, BASE_SEQ + 10, 0x010203040500, 5)]
    assert int(dut.remaining_budget.value) == 0
    assert int(dut.decision_count.value) == 1
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (15, 10)


@cocotb.test()
async def test_itch_semantic_failures_suppress_event_and_rearm(dut):
    clock(dut)
    cases = (
        itch("Z"),
        itch("A", ref=0x7401, length_override=35),
        itch("A", ref=0x7402, side=b"Q"),
        itch("A", ref=0x7403, symbol=b"WRONG   "),
    )
    b = Bench(dut)
    for index, message in enumerate(cases):
        await b.setup(threshold=1, budget=3, rearm=index > 0)
        raw = frame(mold([message]))
        expected = ReferenceOracle(b.config).process_frame(raw)
        assert expected.quarantined and not expected.decisions
        await b.send_frame(raw)
        assert not b.decisions
        assert int(dut.parser_recovery_required.value) == 1
        assert int(dut.book_valid.value) == 0
        assert int(dut.bid_total.value) == 0
        await b.setup(seq=BASE_SEQ + 20, threshold=1, budget=2, rearm=True)
        await b.send_frame(frame(mold([itch("A", ref=0x7500 + index, qty=1, price=1)], BASE_SEQ + 20)))
        assert b.decisions == [(0, BASE_SEQ + 20, 0x010203040500, 1)]


@cocotb.test()
async def test_book_failure_produces_no_decision_and_rearm(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=5, budget=5)
    oracle = ReferenceOracle(b.config)
    first = frame(mold([itch("A", ref=0x4001, qty=5, price=10)]))
    oracle.process_frame(first)
    await b.send_frame(first)
    assert len(b.decisions) == 1
    duplicate = frame(mold([itch("A", ref=0x4001, qty=100, price=20)], BASE_SEQ + 1))
    failure_expected = oracle.process_frame(duplicate)
    assert failure_expected.quarantined and not failure_expected.decisions
    before = len(b.decisions)
    previous_before = int(dut.previous_imbalance.value)
    await b.send_frame(duplicate)
    assert len(b.decisions) == before
    assert int(dut.book_valid.value) == 0 and int(dut.book_recovery_required.value) == 1
    assert int(dut.previous_imbalance.value) == previous_before
    await b.setup(seq=BASE_SEQ + 50, threshold=3, budget=2, rearm=True)
    assert int(dut.bid_total.value) == 0 and int(dut.ask_total.value) == 0
    assert int(dut.previous_imbalance.value) == 0
    await b.send_frame(frame(mold([itch("A", ref=0x4002, qty=3, price=10)], BASE_SEQ + 50)))
    assert b.decisions == [(0, BASE_SEQ + 50, 0x010203040500, 3)]


@cocotb.test()
async def test_late_mold_suffix_retains_prefix_decision_and_state(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=10, budget=5)
    m0 = itch("A", ref=0x5001, qty=12, price=77)
    m1 = itch("E", ref=0x5001, qty=2)
    raw_body = len(m0).to_bytes(2, "big") + m0 + len(m1).to_bytes(2, "big") + m1 + b"\x00\x05\xAA\xBB"
    malformed = frame(mold([m0, m1], body=raw_body, count=3))
    oracle = ReferenceOracle(b.config)
    expected = oracle.process_frame(malformed)
    assert expected.quarantined and len(expected.decisions) == 1
    await b.send_frame(malformed, stall_seed=1)
    assert b.decisions == oracle_decisions(expected)
    assert [item[0] for item in b.commits] == [BASE_SEQ, BASE_SEQ + 1]
    assert all(recovery == 0 for _, _, _, recovery in b.commits)
    assert int(dut.bid_total.value) == 10
    assert int(dut.book_valid.value) == 0 and int(dut.parser_recovery_required.value) == 1
    assert int(dut.current_expected_sequence.value) == BASE_SEQ
    assert int(dut.decision_count.value) == 1
    # Following frame is blocked until the common epoch rearm.
    await FallingEdge(dut.clk)
    next_beat = beats(frame(mold([itch("A", ref=0x5002, qty=1, price=1)])))[0]
    dut.rx_data.value, dut.rx_keep.value, dut.rx_last.value = next_beat
    dut.rx_valid.value = 1
    await Timer(1, unit="ns")
    assert int(dut.rx_ready.value) == 0
    dut.rx_valid.value = 0


@cocotb.test()
async def test_structural_success_itch_failure_keeps_prefix_and_advances_sequence(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=6, budget=5)
    m0 = itch("A", ref=0x6001, qty=8, price=100)
    packet = frame(mold([m0, itch("Z"), itch("A", ref=0x6002, qty=10)]))
    oracle = ReferenceOracle(b.config)
    expected = oracle.process_frame(packet)
    assert expected.quarantined and expected.accepted
    await b.send_frame(packet)
    assert b.decisions == oracle_decisions(expected)
    assert int(dut.bid_total.value) == 8
    assert int(dut.current_expected_sequence.value) == BASE_SEQ + 3
    assert int(dut.parser_recovery_required.value) == 1
    assert int(dut.book_valid.value) == 0


@cocotb.test()
async def test_stalled_prefix_decision_survives_later_itch_recovery(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=6, budget=3)
    packet = frame(mold([
        itch("A", ref=0x6101, qty=8, price=100),
        itch("Z"),
    ]))
    oracle = ReferenceOracle(b.config)
    expected = oracle.process_frame(packet)
    assert expected.quarantined and expected.decisions
    await b.send_frame(packet, hold_decision=True)
    assert int(dut.decision_valid.value) == 1
    assert int(dut.parser_recovery_required.value) == 1
    assert int(dut.book_valid.value) == 0
    held = b.sample_decision()
    assert held == oracle_decisions(expected)[0]
    for _ in range(5):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.decision_valid.value) == 1
        assert b.sample_decision() == held
    await FallingEdge(dut.clk)
    dut.decision_ready.value = 1
    await Timer(1, unit="ns")
    assert int(dut.decision_valid.value) == 1
    b.decisions.append(b.sample_decision())
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.decision_valid.value) == 0
    assert b.decisions == oracle_decisions(expected)
    for _ in range(20):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.decision_valid.value) == 0


@cocotb.test()
async def test_long_valid_multiframe_mutation_stream_against_oracle(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=6, budget=8)
    oracle = ReferenceOracle(b.config)
    buy_ref, sell_ref = 0x8101, 0x8202
    replacement_ref = 0x8877665544332211 + 6
    messages = [
        itch("A", ref=buy_ref, qty=10, price=100, side=b"B", salt=1),
        itch("F", ref=sell_ref, qty=8, price=101, side=b"S", salt=2),
        itch("E", ref=buy_ref, qty=3, salt=3),
        itch("C", ref=sell_ref, qty=2, salt=4),
        itch("X", ref=buy_ref, qty=2, salt=5),
        itch("U", ref=sell_ref, qty=9, price=120, salt=6),
        itch("D", ref=buy_ref, salt=7),
    ]
    expected_decisions = []
    for index, message in enumerate(messages):
        packet = frame(mold([message], BASE_SEQ + index))
        expected_decisions.extend(oracle_decisions(oracle.process_frame(packet)))
        await b.send_frame(packet, stall_seed=index + 1)

    assert b.decisions == expected_decisions == [
        (0, BASE_SEQ, 0x010203040501, 10),
        (1, BASE_SEQ + 6, 0x010203040507, -9),
    ]
    assert len(b.commits) == 7
    assert [row[0] for row in b.commits] == [BASE_SEQ + i for i in range(7)]
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (
        oracle.book.bid_total, oracle.book.ask_total) == (0, 9)
    assert int(dut.current_expected_sequence.value) == BASE_SEQ + 7
    assert int(dut.remaining_budget.value) == oracle.decision_model.current_budget == 6
    assert int(dut.decision_count.value) == oracle.decision_model.decision_count == 2
    await FallingEdge(dut.clk)
    dut.debug_reference.value = replacement_ref
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.debug_found.value) == 1
    assert int(dut.debug_price.value) == 120
    assert int(dut.debug_remaining_quantity.value) == 9
    assert int(dut.debug_side.value) == 1
    assert b.rx_stall_cycles > 0, "long stream did not exercise external ingress backpressure"


@cocotb.test()
async def test_mixed_outer_mold_book_failures_and_rearm(dut):
    clock(dut)
    b = Bench(dut)

    # A nonfatal filter is followed by usable traffic in the same epoch.
    await b.setup(threshold=100, budget=10)
    first = frame(mold([itch("A", ref=0x9101, qty=4, price=20)]))
    await b.send_frame(first)
    nonfatal = frame(mold([itch("A", ref=0x9102, locate=LOC + 1)], BASE_SEQ + 1))
    await b.send_frame(nonfatal)
    assert int(dut.parser_recovery_required.value) == 0
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (4, 0)

    fatal_cases = [
        frame(mold([itch("A")], session=b"BADSESSION")),
        frame(mold([itch("A")], BASE_SEQ + 1)),
        frame(mold([], body=b"\x00", count=1)),
        frame(mold([itch("A", ref=0x9103, qty=20)]), bad_ip_checksum=True),
        frame(mold([itch("Z")])),
        frame(mold([itch("A", ref=1, qty=4), itch("A", ref=1, qty=8)])),
        frame(mold([itch("A", ref=1), itch("A", ref=0x200),
                    itch("A", ref=0x40000)])),
    ]
    for index, packet in enumerate(fatal_cases):
        await b.setup(seq=BASE_SEQ, threshold=100, budget=10, rearm=True)
        model = ReferenceOracle(b.config)
        expected = model.process_frame(packet)
        assert expected.quarantined
        await b.send_frame(packet, stall_seed=index + 1)
        if index < 5:
            assert int(dut.parser_recovery_required.value) == 1
        else:
            # Duplicate/collision are book state-integrity errors, distinct
            # from parser-stage recovery, but both quarantine the functional path.
            assert int(dut.parser_recovery_required.value) == 0
        assert int(dut.book_recovery_required.value) == 1
        assert int(dut.book_valid.value) == 0
        assert not b.commits or all(row[3] == 0 for row in b.commits)
        # Explicit rearm establishes a clean, usable configuration epoch.
        await b.setup(seq=BASE_SEQ + 20, threshold=100, budget=2, rearm=True)
        clean = frame(mold([itch("A", ref=0xA000 + index, qty=2)], BASE_SEQ + 20))
        clean_expected = ReferenceOracle(b.config).process_frame(clean)
        await b.send_frame(clean)
        assert b.decisions == oracle_decisions(clean_expected) == []
        assert int(dut.book_valid.value) == 1
        assert int(dut.parser_recovery_required.value) == 0
        assert int(dut.bid_total.value) == 2


@cocotb.test()
async def test_suffix_ordering_commit_before_and_fatal_before_commit(dut):
    clock(dut)
    b = Bench(dut)

    # First ordering: two message commits handshake before malformed suffix recovery.
    await b.setup(threshold=5, budget=4)
    good = itch("A", ref=0xB001, qty=8, price=100)
    later = itch("E", ref=0xB001, qty=1)
    body = (len(good).to_bytes(2, "big") + good +
            len(later).to_bytes(2, "big") + later + b"\x00\x05\xAA")
    packet = frame(mold([], body=body, count=3))
    await b.send_frame(packet, stall_seed=7)
    assert [item[0] for item in b.commits] == [BASE_SEQ, BASE_SEQ + 1]
    assert all(item[3] == 0 for item in b.commits)
    assert b.decisions == [(0, BASE_SEQ, 0x010203040500, 8)]
    assert int(dut.bid_total.value) == 7
    assert int(dut.book_valid.value) == 0
    assert int(dut.parser_recovery_required.value) == 1

    # Second ordering: the final-byte-truncated next length makes recovery
    # visible before the complete first ITCH message reaches book commit.
    await b.setup(threshold=5, budget=4, rearm=True)
    one = itch("A", ref=0xB101, qty=8, price=100)
    too_early = frame(mold([], body=len(one).to_bytes(2, "big") + one + b"\x00",
                           count=2))
    model = ReferenceOracle(b.config)
    expected = model.process_frame(too_early)
    assert expected.quarantined and len(expected.decisions) == 1
    await b.send_frame(too_early)
    assert int(dut.parser_recovery_required.value) == 1
    assert b.commits == [] and b.decisions == []
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (0, 0)


@cocotb.test()
async def test_single_edge_rearm_discards_pending_decision_epoch(dut):
    clock(dut)
    b = Bench(dut)
    await b.setup(threshold=3, budget=2)
    old_packet = frame(mold([itch("A", ref=0xC001, qty=5, price=50)]))
    await b.send_frame(old_packet, hold_decision=True)
    assert int(dut.decision_valid.value) == 1
    old_decision = b.sample_decision()

    new_seq, new_threshold, new_budget = BASE_SEQ + 100, 4, 3
    await FallingEdge(dut.clk)
    dut.cfg_expected_sequence.value = new_seq
    dut.cfg_decision_threshold.value = new_threshold
    dut.cfg_initial_budget.value = new_budget
    dut.rearm.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.decision_valid.value) == 0
    assert int(dut.previous_imbalance.value) == 0
    assert int(dut.remaining_budget.value) == new_budget
    assert int(dut.decision_count.value) == 0
    assert int(dut.bid_total.value) == 0
    assert int(dut.book_valid.value) == 1
    assert int(dut.parser_recovery_required.value) == 0
    await FallingEdge(dut.clk)
    dut.rearm.value = 0

    b.config = config(new_seq, threshold=new_threshold, budget=new_budget)
    b.decisions.clear()
    b.commits.clear()
    new_packet = frame(mold([itch("A", ref=0xC002, qty=4, price=60)], new_seq))
    await b.send_frame(new_packet)
    assert b.decisions == [(0, new_seq, 0x010203040500, 4)]
    assert b.sample_decision() != old_decision
    assert int(dut.current_expected_sequence.value) == new_seq + 1


@cocotb.test()
async def test_random_full_frame_seed_set(dut):
    clock(dut)
    for seed in (1, 7, 19, 42, 97):
        b = Bench(dut)
        await b.setup(seq=BASE_SEQ, threshold=15, budget=30)
        oracle = ReferenceOracle(b.config)
        rng = random.Random(seed)
        messages = []
        for i in range(6):
            kind = rng.choice(("A", "F", "P"))
            if kind == "P":
                messages.append(itch("P", salt=i))
            else:
                messages.append(itch(kind, ref=(seed << 32) + i + 1,
                                     qty=rng.randrange(1, 15), price=rng.randrange(1, 100),
                                     side=rng.choice((b"B", b"S")), salt=i))
        packet = frame(mold(messages))
        expected = oracle.process_frame(packet)
        await b.send_frame(packet, stall_seed=seed)
        assert b.decisions == oracle_decisions(expected)
        assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (
            oracle.book.bid_total, oracle.book.ask_total)
        assert int(dut.remaining_budget.value) == oracle.decision_model.current_budget
        assert int(dut.decision_count.value) == oracle.decision_model.decision_count

        # Replay one seeded malformed or filtered case in a fresh epoch.
        await b.setup(seq=BASE_SEQ, threshold=15, budget=30, rearm=True)
        oracle = ReferenceOracle(b.config)
        if seed % 4 == 0:
            bad = frame(mold([itch("A", ref=(seed << 32) + 99, qty=20)]),
                        bad_ip_checksum=True)
        elif seed % 4 == 1:
            bad = frame(mold([itch("A", ref=(seed << 32) + 99, qty=20)]),
                        ether_type=0x8100)
        elif seed % 4 == 2:
            bad = frame(mold([itch("Z")]))
        else:
            prefix0 = itch("A", ref=(seed << 32) + 99, qty=20)
            prefix1 = itch("A", ref=(seed << 32) + 100, qty=3)
            raw_body = (len(prefix0).to_bytes(2, "big") + prefix0 +
                        len(prefix1).to_bytes(2, "big") + prefix1 +
                        b"\x00\x05\xAA\xBB")
            bad = frame(mold([], body=raw_body, count=3))
        expected_bad = oracle.process_frame(bad)
        await b.send_frame(bad, stall_seed=seed)
        assert b.decisions == oracle_decisions(expected_bad), (
            f"seed={seed} bad_case decisions={b.decisions} expected={oracle_decisions(expected_bad)} "
            f"bid={int(dut.bid_total.value)} ask={int(dut.ask_total.value)} "
            f"book_recovery={int(dut.book_recovery_required.value)} "
            f"parser_recovery={int(dut.parser_recovery_required.value)} "
            f"decision_count={int(dut.decision_count.value)}"
        )
        assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (
            oracle.book.bid_total, oracle.book.ask_total)
        assert int(dut.parser_recovery_required.value) == int(expected_bad.quarantined)

@cocotb.test()
async def wire026_cycle_performance_workloads(dut):
    """Cycle counts from accepted byte/event handshakes; simulation only."""
    clock(dut)
    base = Bench(dut)
    await base.setup(threshold=10, budget=20, enabled=True)

    async def run(frames, expected_event_count, expected_decisions):
        stream = []
        frame_first = {}
        frame_bytes = 0
        for frame_seq, packet in frames:
            packed = beats(packet)
            frame_first[frame_seq] = len(stream)
            stream.extend((frame_seq, beat) for beat in packed)
            frame_bytes += len(packet)

        dut.decision_ready.value = 1
        idx = 0
        held = None
        cyc = 0
        first_rx = {}
        msg_first = {}
        msg_last = {}
        events = []
        decisions = []
        rx_stalls = 0
        # Public top input/output plus named parser-stage stream boundary.
        msg_valid = dut.parser_book.parser.msg_valid
        msg_ready = dut.parser_book.parser.msg_ready
        msg_last_sig = dut.parser_book.parser.msg_last
        msg_seq = dut.parser_book.parser.message_sequence
        meta_valid = dut.parser_book.parser.message_valid
        meta_ready = dut.parser_book.parser.message_ready
        active_msg_seq = None
        for _ in range(20000):
            await FallingEdge(dut.clk)
            if held is None and idx < len(stream):
                held = stream[idx]
                _, (data, keep, last) = held
                dut.rx_data.value, dut.rx_keep.value, dut.rx_last.value = data, keep, last
                dut.rx_valid.value = 1
            await Timer(1, unit="ns")
            rx_fire = idx < len(stream) and int(dut.rx_valid.value) and int(dut.rx_ready.value)
            if int(dut.rx_valid.value) and not int(dut.rx_ready.value):
                rx_stalls += 1
            if rx_fire:
                seq = stream[idx][0]
                first_rx.setdefault(seq, cyc)
            if int(meta_valid.value) and int(meta_ready.value):
                active_msg_seq = int(msg_seq.value)
            if int(msg_valid.value) and int(msg_ready.value):
                if active_msg_seq is None:
                    raise AssertionError("ITCH payload byte accepted without message metadata")
                msg_first.setdefault(active_msg_seq, cyc)
                if int(msg_last_sig.value):
                    msg_last[active_msg_seq] = cyc
            if int(dut.event_valid_observed.value) and int(dut.event_ready_observed.value):
                events.append((cyc, int(dut.event_mold_sequence_observed.value)))
            if int(dut.decision_valid.value):
                decisions.append((cyc, (int(dut.decision_action.value),
                                        int(dut.decision_mold_sequence.value),
                                        int(dut.decision_itch_timestamp.value),
                                        Bench.signed49(dut.decision_signed_imbalance))))
            await RisingEdge(dut.clk)
            if rx_fire:
                idx += 1
                held = None
                dut.rx_valid.value = 0
            cyc += 1
            if idx == len(stream) and len(decisions) >= len(expected_decisions) and len(events) >= expected_event_count:
                break
        else:
            raise AssertionError(f"performance workload timed out: beats {idx}/{len(stream)}, decisions {len(decisions)}")
        assert len(events) == expected_event_count, (events, expected_event_count)
        assert [item[1] for item in decisions] == expected_decisions, decisions
        elapsed = cyc - first_rx[frames[0][0]]
        l1 = events[0][0] - msg_first[events[0][1]]
        l2 = [(cycle - msg_last[decision[1]]) for cycle, decision in decisions]
        l3 = [(cycle - first_rx[decision[1]]) for cycle, decision in decisions]
        event_ii = [b[0] - a[0] for a, b in zip(events, events[1:])]
        decision_ii = [b[0] - a[0] for a, b in zip(decisions, decisions[1:])]
        # Count actual valid bytes from accepted beat keep masks.
        accepted_bytes = sum(sum((int(beat[1]) >> lane) & 1 for lane in range(8))
                             for _, beat in stream)
        return {
            "bytes": accepted_bytes, "cycles": elapsed, "L1": l1, "L2": l2,
            "L3": l3, "event_ii": event_ii, "decision_ii": decision_ii,
            "throughput_bytes_per_cycle": accepted_bytes / elapsed,
            "rx_stall_cycles": rx_stalls, "events": events, "decisions": decisions,
        }

    workloads = []
    # W1: one ADD, first threshold crossing.
    await base.setup(threshold=10, budget=20, enabled=True, rearm=True)
    workloads.append(("single_ADD_BUY", [(BASE_SEQ, frame(mold([itch("A", ref=0x1001, qty=10, price=100, salt=1)])) )], 1, [(0, BASE_SEQ, 0x010203040501, 10)]))
    # W2: two complete messages in one Mold packet; only the ADD crosses.
    await base.setup(threshold=10, budget=20, enabled=True, rearm=True)
    workloads.append(("multi_message", [(BASE_SEQ, frame(mold([
        itch("A", ref=0x1101, qty=10, price=101, salt=2),
        itch("E", ref=0x1101, qty=1, salt=3)
    ])))], 2, [(0, BASE_SEQ, 0x010203040502, 10)]))
    # W3: repeated separate frames exercise A/F/E/C/X/U/D and three crossings.
    await base.setup(threshold=10, budget=20, enabled=True, rearm=True)
    specs = [
        ("A", 0x2001, 10, 100, b"B"), ("F", 0x2002, 20, 101, b"S"),
        ("E", 0x2002, 5, 0, b"B"), ("C", 0x2002, 5, 0, b"B"),
        ("X", 0x2002, 5, 0, b"B"), ("U", 0x2001, 20, 105, b"B"),
        ("D", 0x8877665544332211 + 5, 0, 0, b"B"),
    ]
    packets = []
    for i, (kind, ref, qty, price, side) in enumerate(specs):
        packets.append((BASE_SEQ + i, frame(mold([itch(kind, ref=ref, qty=qty, price=price,
                                                       side=side, salt=10 + i)], BASE_SEQ + i))))
    workloads.append(("stateful_frames_A_F_E_C_X_U_D", packets, 7, [
        (0, BASE_SEQ, 0x01020304050A, 10),
        (1, BASE_SEQ + 1, 0x01020304050B, -10),
        (0, BASE_SEQ + 5, 0x01020304050F, 15),
    ]))

    for name, frame_list, event_count, expected_decision_tuples in workloads:
        # Re-arm before each independent workload, loading the same known config.
        if name != "single_ADD_BUY":
            await base.setup(threshold=10, budget=20, enabled=True, rearm=True)
        result = await run(frame_list, event_count, expected_decision_tuples)
        dut._log.info("WIRE026_METRIC workload=%s bytes=%d cycles=%d L1=%d L2=%s L3=%s event_ii=%s decision_ii=%s bytes_per_cycle=%.6f rx_stall_cycles=%d decisions=%s",
                      name, result["bytes"], result["cycles"], result["L1"], result["L2"], result["L3"],
                      result["event_ii"], result["decision_ii"], result["throughput_bytes_per_cycle"],
                      result["rx_stall_cycles"], result["decisions"])
