import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model" / "python"))
from wire_to_decision.checksum import internet_checksum

DEST_IP = 0xC6336407
DEST_PORT = 0x1234
LOC = 0x2345
SESSION = b"W2DTEST001"
BASE_SEQ = 0x1020304050607080
SYMBOL = b"ALPH    "


def put(buf, off, width, value):
    buf[off:off + width] = int(value).to_bytes(width, "big")


def itch(kind, ref=0x2001, qty=10, price=100, side=b"B", salt=0):
    sizes = {"A": 36, "F": 40, "E": 31, "C": 36, "X": 23, "D": 19, "U": 35}
    data = bytearray(sizes[kind])
    data[0] = ord(kind)
    put(data, 1, 2, LOC)
    put(data, 3, 2, 0xA100 + salt)
    put(data, 5, 6, 0x010203040500 + salt)
    if kind in ("A", "F"):
        put(data, 11, 8, ref)
        data[19] = side[0]
        put(data, 20, 4, qty)
        data[24:32] = SYMBOL
        put(data, 32, 4, price)
        if kind == "F":
            data[36:40] = b"MPID"
    elif kind in ("E", "C", "X"):
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
        put(data, 19, 8, 0x8877665544332211 + salt)
        put(data, 27, 4, qty)
        put(data, 31, 4, price)
    return bytes(data)


def mold(messages, seq):
    body = b"".join(len(m).to_bytes(2, "big") + m for m in messages)
    return SESSION + seq.to_bytes(8, "big") + len(messages).to_bytes(2, "big") + body


def frame(mold_bytes):
    udp = bytearray(8)
    put(udp, 0, 2, 0xBEEF)
    put(udp, 2, 2, DEST_PORT)
    put(udp, 4, 2, 8 + len(mold_bytes))
    eth = bytes.fromhex("0201020304050A0B0C0D0E0F") + (0x0800).to_bytes(2, "big")
    ip_payload = bytes(udp) + mold_bytes
    ip = bytearray(20)
    ip[0] = 0x45
    put(ip, 2, 2, 20 + len(ip_payload))
    ip[8], ip[9] = 64, 17
    put(ip, 16, 4, DEST_IP)
    put(ip, 10, 2, internet_checksum(bytes(ip)))
    return eth + bytes(ip) + ip_payload


def make_beats(packet_list):
    result = []
    for packet in packet_list:
        for off in range(0, len(packet), 8):
            part = packet[off:off + 8]
            word = sum(b << (8 * i) for i, b in enumerate(part))
            result.append((word, (1 << len(part)) - 1, int(off + len(part) == len(packet))))
    return result


def stateful_frames():
    specs = [
        ("A", 0x2001, 10, 100, b"B"), ("F", 0x2002, 20, 101, b"S"),
        ("E", 0x2002, 5, 0, b"B"), ("C", 0x2002, 5, 0, b"B"),
        ("X", 0x2002, 5, 0, b"B"), ("U", 0x2001, 20, 105, b"B"),
        ("D", 0x8877665544332211 + 15, 0, 0, b"B"),
    ]
    return [frame(mold([itch(t, ref=r, qty=q, price=p, side=s, salt=10 + i)], BASE_SEQ + i))
            for i, (t, r, q, p, s) in enumerate(specs)]


def valid_mutations():
    return [
        dict(kind=0, source=ord("A"), seq=BASE_SEQ, ts=0x01020304050A,
             fields=0x0F, old=0, new=0x2001, qty=10, price=100, side=0),
        dict(kind=0, source=ord("F"), seq=BASE_SEQ+1, ts=0x01020304050B,
             fields=0x0F, old=0, new=0x2002, qty=20, price=101, side=1),
        dict(kind=1, source=ord("E"), seq=BASE_SEQ+2, ts=0x01020304050C,
             fields=0x14, old=0x2002, new=0, qty=5, price=0, side=0),
        dict(kind=2, source=ord("C"), seq=BASE_SEQ+3, ts=0x01020304050D,
             fields=0x14, old=0x2002, new=0, qty=5, price=0, side=0),
        dict(kind=3, source=ord("X"), seq=BASE_SEQ+4, ts=0x01020304050E,
             fields=0x14, old=0x2002, new=0, qty=5, price=0, side=0),
        dict(kind=5, source=ord("U"), seq=BASE_SEQ+5, ts=0x01020304050F,
             fields=0x1E, old=0x2001, new=0x8877665544332220, qty=20, price=105, side=0),
        dict(kind=4, source=ord("D"), seq=BASE_SEQ+6, ts=0x010203040510,
             fields=0x10, old=0x8877665544332220, new=0, qty=0, price=0, side=0),
    ]


def start_clock(d):
    cocotb.start_soon(Clock(d.clk, 10, unit="ns").start())


async def reset(d):
    d.rst.value = 1
    d.rearm.value = 0
    d.cfg_destination_ipv4.value = DEST_IP
    d.cfg_destination_udp_port.value = DEST_PORT
    d.cfg_active_session.value = int.from_bytes(SESSION, "big")
    d.cfg_expected_sequence.value = BASE_SEQ
    d.cfg_tracked_stock_locate.value = LOC
    d.cfg_symbol_check_enable.value = 1
    d.cfg_expected_stock_symbol.value = int.from_bytes(SYMBOL, "big")
    d.rx_data.value = 0
    d.rx_keep.value = 0
    d.rx_valid.value = 0
    d.rx_last.value = 0
    d.parser_event_ready.value = 1
    d.book_event_valid.value = 0
    d.book_event_kind.value = 0
    d.book_source_type.value = 0
    d.book_mold_sequence.value = 0
    d.book_itch_timestamp.value = 0
    d.book_fields_valid.value = 0
    d.book_old_reference.value = 0
    d.book_new_reference.value = 0
    d.book_quantity.value = 0
    d.book_price.value = 0
    d.book_side.value = 0
    d.book_upstream_recovery.value = 0
    d.book_commit_ready.value = 1
    d.book_error_ready.value = 1
    d.decision_commit_valid.value = 0
    d.decision_commit_sequence.value = 0
    d.decision_commit_timestamp.value = 0
    d.decision_commit_bid.value = 0
    d.decision_commit_ask.value = 0
    d.decision_ready.value = 1
    await RisingEdge(d.clk)
    await FallingEdge(d.clk)
    d.rst.value = 0
    await Timer(1, unit="ns")


async def run_parser_packets(d, packets, label):
    stream = make_beats(packets)
    idx = 0
    held = None
    cycle = 0
    first_input = None
    last_event = None
    event_cycles = []
    accepted_bytes = 0
    rx_stalls = 0
    while cycle < 30000:
        await FallingEdge(d.clk)
        if held is None and idx < len(stream):
            held = stream[idx]
            d.rx_data.value, d.rx_keep.value, d.rx_last.value = held
            d.rx_valid.value = 1
        await Timer(1, unit="ns")
        rx_fire = bool(int(d.rx_valid.value) and int(d.rx_ready.value))
        event_fire = bool(int(d.parser_event_valid.value) and int(d.parser_event_ready.value))
        if int(d.rx_valid.value) and not int(d.rx_ready.value):
            rx_stalls += 1
        if rx_fire:
            if first_input is None:
                first_input = cycle
            accepted_bytes += int(d.rx_keep.value).bit_count()
        if event_fire:
            event_cycles.append(cycle)
            last_event = cycle
        await RisingEdge(d.clk)
        if rx_fire:
            idx += 1
            held = None
            d.rx_valid.value = 0
        cycle += 1
        if idx == len(stream) and len(event_cycles) == sum(len(mold_messages) for mold_messages in packet_contents(label)):
            break
    else:
        raise AssertionError(f"parser service timed out at beat {idx}/{len(stream)}; events={len(event_cycles)}")
    elapsed = last_event - first_input + 1
    iis = [b-a for a, b in zip(event_cycles, event_cycles[1:])]
    result = dict(bytes=accepted_bytes, cycles=elapsed, events=len(event_cycles),
                  event_ii=iis, rx_stalls=rx_stalls,
                  bytes_per_cycle=accepted_bytes / elapsed)
    d._log.info("WIRE027_PARSER workload=%s bytes=%d cycles=%d events=%d event_ii=%s rx_stall_cycles=%d bytes_per_cycle=%.6f",
                label, result['bytes'], result['cycles'], result['events'], iis,
                rx_stalls, result['bytes_per_cycle'])
    return result


def packet_contents(label):
    a = itch("A", ref=0x1101, qty=10, price=101, salt=2)
    e = itch("E", ref=0x1101, qty=1, salt=3)
    if label == "single_ADD_BUY":
        return [[a]]
    if label == "multi_message":
        return [[a, e]]
    return [[itch(t, ref=r, qty=q, price=p, side=s, salt=10+i)]
            for i, (t, r, q, p, s) in enumerate([
                ("A",0x2001,10,100,b"B"),("F",0x2002,20,101,b"S"),
                ("E",0x2002,5,0,b"B"),("C",0x2002,5,0,b"B"),
                ("X",0x2002,5,0,b"B"),("U",0x2001,20,105,b"B"),
                ("D",0x8877665544332211+15,0,0,b"B")])]


@cocotb.test()
async def parser_service_comparison(d):
    start_clock(d)
    workloads = [
        ("single_ADD_BUY", [frame(mold([itch("A", ref=0x1101, qty=10, price=101, salt=2)], BASE_SEQ))]),
        ("multi_message", [frame(mold([itch("A", ref=0x1101, qty=10, price=101, salt=2),
                                      itch("E", ref=0x1101, qty=1, salt=3)], BASE_SEQ))]),
        ("stateful_frames_A_F_E_C_X_U_D", stateful_frames()),
    ]
    for label, packets in workloads:
        await reset(d)
        result = await run_parser_packets(d, packets, label)
        expected_events = sum(len(x) for x in packet_contents(label))
        assert result['events'] == expected_events
        assert int(d.parser_recovery_required.value) == 0


@cocotb.test()
async def book_service_comparison(d):
    start_clock(d)
    await reset(d)
    events = valid_mutations()
    idx = 0
    event_cycles = {}
    commit_cycles = {}
    cycle = 0
    stalls = 0
    while cycle < 3000:
        await FallingEdge(d.clk)
        d.book_event_valid.value = int(idx < len(events))
        if idx < len(events):
            e = events[idx]
            d.book_event_kind.value = e['kind']
            d.book_source_type.value = e['source']
            d.book_mold_sequence.value = e['seq']
            d.book_itch_timestamp.value = e['ts']
            d.book_fields_valid.value = e['fields']
            d.book_old_reference.value = e['old']
            d.book_new_reference.value = e['new']
            d.book_quantity.value = e['qty']
            d.book_price.value = e['price']
            d.book_side.value = e['side']
        await Timer(1, unit="ns")
        ev = bool(int(d.book_event_valid.value) and int(d.book_event_ready.value))
        cf = bool(int(d.book_commit_valid.value) and int(d.book_commit_ready.value))
        if int(d.book_event_valid.value) and not int(d.book_event_ready.value):
            stalls += 1
        if ev:
            event_cycles[events[idx]['seq']] = cycle
        if cf:
            commit_cycles[int(d.book_commit_sequence.value)] = cycle
        await RisingEdge(d.clk)
        if ev:
            idx += 1
        cycle += 1
        if idx == len(events) and len(commit_cycles) == len(events):
            break
    assert len(commit_cycles) == len(events), (idx, commit_cycles)
    latencies = [commit_cycles[e['seq']] - event_cycles[e['seq']] for e in events]
    service_ii = [b-a for a,b in zip([event_cycles[e['seq']] for e in events],
                                      [event_cycles[e['seq']] for e in events][1:])]
    assert int(d.book_recovery_required.value) == 0
    d._log.info("WIRE027_BOOK events=%d event_to_commit_cycles=%s service_ii=%s event_stall_cycles=%d final_bid=%d final_ask=%d",
                len(events), latencies, service_ii, stalls,
                int(d.book_commit_bid.value), int(d.book_commit_ask.value))


@cocotb.test()
async def decision_service_comparison(d):
    start_clock(d)
    await reset(d)
    trajectory = [(10,0),(10,20),(10,15),(10,10),(10,5),(20,5),(0,5)]
    events = valid_mutations()
    idx = 0
    commit_cycles = {}
    decision_cycles = {}
    cycle = 0
    commit_stalls = 0
    output_stalls = 0
    while cycle < 3000:
        await FallingEdge(d.clk)
        d.decision_commit_valid.value = int(idx < len(events))
        if idx < len(events):
            e = events[idx]
            bid, ask = trajectory[idx]
            d.decision_commit_sequence.value = e['seq']
            d.decision_commit_timestamp.value = e['ts']
            d.decision_commit_bid.value = bid
            d.decision_commit_ask.value = ask
        await Timer(1, unit="ns")
        cf = bool(int(d.decision_commit_valid.value) and int(d.decision_commit_ready.value))
        df = bool(int(d.decision_valid.value) and int(d.decision_ready.value))
        if int(d.decision_commit_valid.value) and not int(d.decision_commit_ready.value):
            commit_stalls += 1
        if int(d.decision_valid.value) and not int(d.decision_ready.value):
            output_stalls += 1
        if cf:
            commit_cycles[events[idx]['seq']] = cycle
        if df:
            decision_cycles[int(d.decision_sequence.value)] = cycle
        await RisingEdge(d.clk)
        if cf:
            idx += 1
        cycle += 1
        if idx == len(events) and not int(d.decision_valid.value):
            break
    latencies = [decision_cycles[s] - commit_cycles[s] for s in decision_cycles]
    iis = [b-a for a,b in zip(sorted(decision_cycles.values()), sorted(decision_cycles.values())[1:])]
    assert len(decision_cycles) == 3, decision_cycles
    assert int(d.decision_valid.value) == 0
    d._log.info("WIRE027_DECISION commits=%d decision_outputs=%d commit_to_decision_cycles=%s decision_ii=%s commit_stall_cycles=%d output_stall_cycles=%d",
                len(events), len(decision_cycles), latencies, iis, commit_stalls, output_stalls)
