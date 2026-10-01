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


def put(buf, off, width, val):
    buf[off:off + width] = val.to_bytes(width, "big")


def itch(kind, *, ref=0x1122334455667788, qty=20, price=0x12345678,
         side=b"B", salt=0, length_override=None):
    lengths = {"A": 36, "E": 31, "C": 36, "X": 23, "D": 19, "U": 35, "Z": 12}
    data = bytearray(length_override or lengths[kind])
    data[0] = ord(kind)
    if len(data) >= 11:
        put(data, 1, 2, LOC)
        put(data, 3, 2, 0xA100 + salt)
        put(data, 5, 6, 0x010203040500 + salt)
    if kind == "A" and len(data) >= 36:
        put(data, 11, 8, ref)
        data[19] = side[0]
        put(data, 20, 4, qty)
        data[24:32] = SYMBOL
        put(data, 32, 4, price)
    elif kind in "ECX" and len(data) >= lengths.get(kind, 0):
        put(data, 11, 8, ref)
        put(data, 19, 4, qty)
        if kind == "C":
            data[23] = 1
            put(data, 24, 4, 0xDEADBEEF)
            data[28:36] = b"XYZ12345"
    elif kind == "D" and len(data) >= 19:
        put(data, 11, 8, ref)
    elif kind == "U" and len(data) >= 35:
        put(data, 11, 8, ref)
        put(data, 19, 8, 0x8877665544332211 + salt)
        put(data, 27, 4, qty)
        put(data, 31, 4, price)
    return bytes(data)


def mold(messages, sequence=BASE_SEQ, *, body=None, count=None):
    if body is None:
        body = b"".join(len(m).to_bytes(2, "big") + m for m in messages)
    n = len(messages) if count is None else count
    return SESSION + sequence.to_bytes(8, "big") + n.to_bytes(2, "big") + body


def frame(mold_bytes, *, bad_ip_checksum=False):
    udp = bytearray(8)
    put(udp, 0, 2, 0xBEEF)
    put(udp, 2, 2, DEST_PORT)
    put(udp, 4, 2, len(udp) + len(mold_bytes))
    eth = bytes.fromhex("0201020304050A0B0C0D0E0F0800")
    ip_payload = bytes(udp) + mold_bytes
    iph = bytearray(20)
    iph[0] = 0x45
    put(iph, 2, 2, 20 + len(ip_payload))
    iph[8] = 64
    iph[9] = 17
    put(iph, 16, 4, DEST_IP)
    put(iph, 10, 2, internet_checksum(bytes(iph)))
    if bad_ip_checksum:
        iph[10] ^= 0x01
    return eth + bytes(iph) + ip_payload


def beats(data):
    result = []
    for off in range(0, len(data), 8):
        part = data[off:off + 8]
        word = sum(byte << (8 * i) for i, byte in enumerate(part))
        result.append((word, (1 << len(part)) - 1, int(off + len(part) == len(data))))
    return result


def model_config(seq=BASE_SEQ, session=SESSION):
    return ModelConfig(DEST_IP, DEST_PORT, LOC, True, SYMBOL, session, seq,
                       decision_threshold=0, initial_budget=0, decision_enable=False)


class Bench:
    def __init__(self, d):
        self.d = d
        self.commits = []
        self.events = []
        self.errors = []
        self.accepted_beats = 0

    async def setup(self, *, seq=BASE_SEQ, session=SESSION, rearm=False):
        d = self.d
        await FallingEdge(d.clk)
        for name, value in {
            "rst": 1, "rearm": int(rearm), "cfg_destination_ipv4": DEST_IP,
            "cfg_destination_udp_port": DEST_PORT,
            "cfg_active_session": int.from_bytes(session, "big"),
            "cfg_expected_sequence": seq, "cfg_tracked_stock_locate": LOC,
            "cfg_symbol_check_enable": 1, "cfg_expected_stock_symbol": int.from_bytes(SYMBOL, "big"),
            "rx_data": 0, "rx_keep": 0, "rx_valid": 0, "rx_last": 0,
            "commit_ready": 1, "error_ready": 1, "debug_reference": 0,
        }.items():
            getattr(d, name).value = value
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        d.rst.value = 0
        d.rearm.value = 0
        self.commits.clear()
        self.events.clear()
        self.errors.clear()
        self.accepted_beats = 0

    async def send_frame(self, raw, *, stall_seed=0, max_cycles=6000):
        d = self.d
        stream = beats(raw)
        index, held, idle = 0, None, 0
        for cycle in range(max_cycles):
            await FallingEdge(d.clk)
            if held is None and index < len(stream):
                held = stream[index]
                d.rx_data.value, d.rx_keep.value, d.rx_last.value = held
                d.rx_valid.value = 1
            # Deterministic consumer stalls exercise commit backpressure.
            d.commit_ready.value = int((cycle + stall_seed) % 5 != 1)
            await Timer(1, unit="ns")
            rx_fire = int(d.rx_valid.value) and int(d.rx_ready.value)
            if int(d.event_valid_observed.value) and int(d.event_ready_observed.value):
                self.events.append((int(d.event_kind_observed.value),
                                    int(d.event_mold_sequence_observed.value)))
            if int(d.commit_valid.value) and int(d.commit_ready.value):
                self.commits.append((int(d.commit_mold_sequence.value),
                                     int(d.commit_itch_timestamp.value),
                                     int(d.commit_bid_total.value), int(d.commit_ask_total.value)))
            if int(d.error_valid.value) and int(d.error_ready.value):
                self.errors.append(int(d.error_code.value))
            await RisingEdge(d.clk)
            if rx_fire:
                index += 1
                held = None
                d.rx_valid.value = 0
                self.accepted_beats += 1
            if index == len(stream) and not int(d.commit_valid.value) and not int(d.event_valid_observed.value):
                idle += 1
                if idle >= 80:
                    d.commit_ready.value = 1
                    return
            else:
                idle = 0
        raise AssertionError(f"frame timeout accepted {index}/{len(stream)} recovery={int(d.parser_recovery_required.value)}")

    async def lookup(self, ref):
        await FallingEdge(self.d.clk)
        self.d.debug_reference.value = ref
        await Timer(1, unit="ns")
        if not int(self.d.debug_found.value):
            return None
        return (int(self.d.debug_price.value), int(self.d.debug_remaining_quantity.value),
                int(self.d.debug_side.value))


def make_clock(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())


@cocotb.test()
async def test_valid_parser_to_book_mutation_sequence_against_oracle(dut):
    make_clock(dut)
    b = Bench(dut)
    await b.setup()
    a_ref, u_ref = 0x1001, 0x2002
    messages = [
        itch("A", ref=a_ref, qty=20, price=100),
        itch("E", ref=a_ref, qty=5, price=0),
        itch("X", ref=a_ref, qty=5, price=0),
        itch("U", ref=a_ref, qty=8, price=120),
        itch("D", ref=u_ref, qty=0, price=0),
    ]
    # Delete must target the replacement reference.
    messages[-1] = itch("D", ref=0x8877665544332211, qty=0, price=0)
    packet = mold(messages)
    raw = frame(packet)
    oracle = ReferenceOracle(model_config())
    expected = oracle.process_frame(raw)
    assert expected.accepted and expected.terminal_error is None
    await b.send_frame(raw, stall_seed=2)
    assert [kind for kind, seq in b.events] == [0, 1, 3, 5, 4]
    assert [seq for kind, seq in b.events] == [BASE_SEQ + i for i in range(5)]
    assert [entry[0] for entry in b.commits] == [BASE_SEQ + i for i in range(5)]
    assert [entry[2:] for entry in b.commits] == [(20, 0), (15, 0), (10, 0), (8, 0), (0, 0)]
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (
        oracle.book.bid_total, oracle.book.ask_total)
    assert (await b.lookup(a_ref)) is None
    assert (await b.lookup(0x8877665544332211)) is None
    assert int(dut.book_valid.value) == 1
    assert int(dut.parser_recovery_required.value) == 0
    assert int(dut.current_expected_sequence.value) == BASE_SEQ + 5


@cocotb.test()
async def test_late_structural_suffix_commits_only_complete_prefix(dut):
    make_clock(dut)
    b = Bench(dut)
    await b.setup()
    ref = 0x4001
    m0 = itch("A", ref=ref, qty=30, price=77)
    m1 = itch("E", ref=ref, qty=8, price=0)
    raw_body = len(m0).to_bytes(2, "big") + m0 + len(m1).to_bytes(2, "big") + m1 + b"\x00\x05\xAA\xBB"
    packet = mold([m0, m1], body=raw_body, count=3)
    raw = frame(packet)
    oracle = ReferenceOracle(model_config())
    expected = oracle.process_frame(raw)
    assert not expected.accepted and expected.quarantined
    await b.send_frame(raw, stall_seed=1)
    assert len(b.commits) == 2
    assert [commit[2:] for commit in b.commits] == [(30, 0), (22, 0)]
    assert (await b.lookup(ref)) == (77, 22, 0)
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (
        oracle.book.bid_total, oracle.book.ask_total)
    assert int(dut.book_valid.value) == 0
    assert int(dut.book_recovery_required.value) == 1
    assert int(dut.parser_recovery_required.value) == 1
    assert int(dut.current_expected_sequence.value) == BASE_SEQ
    assert b.errors and b.errors[-1] == 8  # ERR_UPSTREAM_FATAL

    # Later frame cannot enter until the shared parser/book rearm epoch.
    await FallingEdge(dut.clk)
    d = dut
    next_frame = beats(frame(mold([itch("A", ref=0x4002, qty=1, price=9)])))
    d.rx_data.value, d.rx_keep.value, d.rx_last.value = next_frame[0]
    d.rx_valid.value = 1
    await Timer(1, unit="ns")
    assert int(d.rx_ready.value) == 0
    d.rx_valid.value = 0
    await b.setup(seq=BASE_SEQ + 3, rearm=True)
    await b.send_frame(frame(mold([itch("A", ref=0x4002, qty=1, price=9)], BASE_SEQ + 3)))
    assert int(dut.book_valid.value) == 1
    assert int(dut.parser_recovery_required.value) == 0
    assert int(dut.bid_total.value) == 1


@cocotb.test()
async def test_structural_success_with_itch_failure_preserves_sequence_commit(dut):
    make_clock(dut)
    b = Bench(dut)
    await b.setup()
    ref = 0x5001
    valid = itch("A", ref=ref, qty=6, price=12)
    unsupported = itch("Z")
    later = itch("A", ref=0x5002, qty=3, price=13)
    packet = mold([valid, unsupported, later])
    raw = frame(packet)
    oracle = ReferenceOracle(model_config())
    expected = oracle.process_frame(raw)
    # Structural Mold framing succeeds; ITCH semantics quarantine separately.
    assert expected.quarantined and expected.accepted
    await b.send_frame(raw, stall_seed=3)
    assert len(b.commits) == 1
    assert b.commits[0][2:] == (6, 0)
    assert (await b.lookup(ref)) == (12, 6, 0)
    assert await b.lookup(0x5002) is None
    assert int(dut.current_expected_sequence.value) == BASE_SEQ + 3
    assert int(dut.book_valid.value) == 0
    assert int(dut.book_recovery_required.value) == 1
    assert int(dut.parser_recovery_required.value) == 1
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (
        oracle.book.bid_total, oracle.book.ask_total)


@cocotb.test()
async def test_outer_fatal_before_event_invalidates_empty_book_and_rearms(dut):
    make_clock(dut)
    b = Bench(dut)
    await b.setup()
    raw = frame(mold([itch("A", ref=0x6001, qty=9, price=99)]), bad_ip_checksum=True)
    await b.send_frame(raw)
    assert not b.commits
    assert int(dut.book_valid.value) == 0
    assert int(dut.book_recovery_required.value) == 1
    assert int(dut.bid_total.value) == 0
    assert await b.lookup(0x6001) is None
    await b.setup(seq=BASE_SEQ + 10, rearm=True)
    await b.send_frame(frame(mold([itch("A", ref=0x6001, qty=9, price=99)], BASE_SEQ + 10)))
    assert int(dut.book_valid.value) == 1
    assert int(dut.bid_total.value) == 9
