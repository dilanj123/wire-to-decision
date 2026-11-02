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


def mold(messages, sequence=BASE_SEQ, *, body=None, count=None):
    body = (b"".join(len(m).to_bytes(2, "big") + m for m in messages)
            if body is None else body)
    return SESSION + sequence.to_bytes(8, "big") + \
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
        self.accepted_beats = 0
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
        self.accepted_beats = 0

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
        for cycle in range(max_cycles):
            await FallingEdge(d.clk)
            if held is None and index < len(stream):
                held = stream[index]
                d.rx_data.value, d.rx_keep.value, d.rx_last.value = held
                d.rx_valid.value = 1
            d.decision_ready.value = 0 if hold_decision else int((cycle + stall_seed) % 5 != 2)
            await Timer(1, unit="ns")
            rx_fire = int(d.rx_valid.value) and int(d.rx_ready.value)
            if int(d.decision_valid.value) and int(d.decision_ready.value):
                self.decisions.append(self.sample_decision())
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
            if int(d.decision_valid.value) and int(d.decision_ready.value):
                self.decisions.append(self.sample_decision())
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
