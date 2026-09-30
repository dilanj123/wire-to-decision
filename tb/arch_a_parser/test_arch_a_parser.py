import random
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model" / "python"))
from wire_to_decision.checksum import internet_checksum
from wire_to_decision.framing import frame_packet
from wire_to_decision.itch import decode_itch_message
from wire_to_decision.mold import FramedMessage
from wire_to_decision.types import ModelConfig


DEST_IP = 0xC6336407
DEST_PORT = 0x1234
LOC = 0x2345
SESSION = b"W2DTEST001"
SEQ0 = 0x1020304050607080
SYMBOL = b"ALPH    "
LENGTHS = {"A": 36, "F": 40, "E": 31, "C": 36, "X": 23, "D": 19, "U": 35, "P": 44}
KINDS = {"ADD": 0, "EXECUTE": 1, "EXECUTE_WITH_PRICE": 2,
         "CANCEL": 3, "DELETE": 4, "REPLACE": 5}


def put(buf, off, width, value):
    buf[off:off + width] = value.to_bytes(width, "big")


def itch(kind, locate=LOC, symbol=SYMBOL, side=b"B", salt=0):
    b = bytearray(LENGTHS[kind])
    b[0] = ord(kind)
    put(b, 1, 2, locate)
    put(b, 3, 2, (0xAB00 + salt) & 0xFFFF)
    put(b, 5, 6, (0x010203040500 + salt) & ((1 << 48) - 1))
    if kind in "AF":
        put(b, 11, 8, 0x1122334455667700 + salt)
        b[19] = side[0]
        put(b, 20, 4, 0x10203040 + salt)
        b[24:32] = symbol
        put(b, 32, 4, 0x50607080 + salt)
        if kind == "F":
            b[36:40] = b"MPID"
    elif kind in "ECX":
        put(b, 11, 8, 0x8877665544332200 + salt)
        put(b, 19, 4, 0x20304050 + salt)
        if kind == "C":
            b[23] = 1
            put(b, 24, 4, 0x31415926 + salt)
            b[28:36] = b"XYZ12345"
    elif kind == "D":
        put(b, 11, 8, 0x8877665544332200 + salt)
    elif kind == "U":
        put(b, 11, 8, 0x0102030405060700 + salt)
        put(b, 19, 8, 0x1112131415161700 + salt)
        put(b, 27, 4, 0x31415926 + salt)
        put(b, 31, 4, 0x27182818 + salt)
    elif kind == "P":
        b[11:] = bytes((i * 13 + salt) & 0xFF for i in range(len(b) - 11))
    return bytes(b)


def mold_packet(messages, seq, session=SESSION, count=None, raw_body=None):
    body = bytearray()
    for msg in messages:
        body.extend(len(msg).to_bytes(2, "big"))
        body.extend(msg)
    if raw_body is not None:
        body = bytearray(raw_body)
    n = len(messages) if count is None else count
    return session + seq.to_bytes(8, "big") + n.to_bytes(2, "big") + bytes(body)


def ipv4(payload, dst=DEST_IP):
    h = bytearray(20)
    h[0] = 0x45
    h[1] = 0x10
    put(h, 2, 2, 20 + len(payload))
    put(h, 4, 2, 0x4567)
    put(h, 6, 2, 0x4000)
    h[8] = 64
    h[9] = 17
    h[12:16] = b"\xC0\x00\x02\x21"
    put(h, 16, 4, dst)
    put(h, 10, 2, internet_checksum(bytes(h)))
    return bytes(h) + payload


def frame(payload, *, dst=DEST_IP, port=DEST_PORT, ethertype=0x0800):
    udp = bytearray(8)
    put(udp, 0, 2, 0xBEEF)
    put(udp, 2, 2, port)
    put(udp, 4, 2, 8 + len(payload))
    put(udp, 6, 2, 0)
    eth = bytes.fromhex("0201020304050A0B0C0D0E0F") + ethertype.to_bytes(2, "big")
    return eth + ipv4(bytes(udp) + payload, dst)


def ethernet_ip(ip_bytes):
    return bytes.fromhex("0201020304050A0B0C0D0E0F0800") + ip_bytes


def beats(data):
    result = []
    for off in range(0, len(data), 8):
        chunk = data[off:off + 8]
        word = sum(v << (8 * lane) for lane, v in enumerate(chunk))
        result.append((word, (1 << len(chunk)) - 1, int(off + len(chunk) == len(data))))
    return result


def config(seq=SEQ0, *, session=SESSION, locate=LOC, symbol_check=True, symbol=SYMBOL):
    return ModelConfig(destination_ipv4=DEST_IP, destination_udp_port=DEST_PORT,
                       tracked_stock_locate=locate, symbol_check_enable=symbol_check,
                       expected_stock_symbol=symbol, active_session=session,
                       expected_sequence=seq, decision_threshold=0, initial_budget=0,
                       decision_enable=False)


def event_tuple(d):
    names = ("event_kind", "source_type", "mold_sequence", "itch_timestamp", "stock_locate",
             "old_order_reference", "new_order_reference", "quantity", "price", "side",
             "old_reference_valid", "new_reference_valid", "quantity_valid", "price_valid", "side_valid")
    return tuple(int(getattr(d, n).value) for n in names)


def expected_event(msg, sequence, cfg):
    decoded = decode_itch_message(FramedMessage(sequence, msg), cfg)
    if decoded.event is None:
        return None
    e = decoded.event
    return (KINDS[e.kind.value], ord(e.source_type.value), e.mold_sequence, e.itch_timestamp,
            e.stock_locate, e.old_order_reference or 0, e.new_order_reference or 0,
            e.quantity or 0, e.price or 0,
            int(e.side is not None and e.side.value == "S"),
            int(e.field_valid.old_order_reference), int(e.field_valid.new_order_reference),
            int(e.field_valid.quantity), int(e.field_valid.price), int(e.field_valid.side))


class Driver:
    def __init__(self, dut):
        self.d = dut
        self.events = []
        self.diag = []
        self.accepted_beats = 0
        self.recovery_before_end = False
        self.drained_beats_after_recovery = 0

    async def setup(self, *, seq=SEQ0, session=SESSION, locate=LOC, symbol_check=True, symbol=SYMBOL,
                    rearm=False, rst=False):
        d = self.d
        await FallingEdge(d.clk)
        for name, value in {
            "rst": int(rst), "rearm": int(rearm), "cfg_destination_ipv4": DEST_IP,
            "cfg_destination_udp_port": DEST_PORT,
            "cfg_active_session": int.from_bytes(session, "big"), "cfg_expected_sequence": seq,
            "cfg_tracked_stock_locate": locate, "cfg_symbol_check_enable": int(symbol_check),
            "cfg_expected_stock_symbol": int.from_bytes(symbol, "big"),
            "rx_valid": 0, "rx_data": 0, "rx_keep": 0, "rx_last": 0,
            "event_ready": 1,
        }.items():
            getattr(d, name).value = value
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        d.rst.value = 0
        d.rearm.value = 0
        if rst or rearm:
            self.events.clear()
            self.diag.clear()
            self.accepted_beats = 0
            self.recovery_before_end = False
            self.drained_beats_after_recovery = 0

    async def send_frame(self, data, *, seed=None, max_cycles=12000):
        d = self.d
        stream = beats(data)
        index = 0
        held = None
        quiet = 0
        rng = random.Random(seed) if seed is not None else None
        start_events = len(self.events)
        for cycle in range(max_cycles):
            await FallingEdge(d.clk)
            d.event_ready.value = 1 if rng is None else int(rng.randrange(4) != 0)
            if held is None and index < len(stream):
                held = stream[index]
                d.rx_data.value, d.rx_keep.value, d.rx_last.value = held
                d.rx_valid.value = 1
            await Timer(1, unit="ns")
            in_fire = int(d.rx_valid.value) and int(d.rx_ready.value)
            if int(d.event_valid.value) and int(d.event_ready.value):
                self.events.append(event_tuple(d))
            if int(d.recovery_required.value) and index < len(stream):
                self.recovery_before_end = True
            for prefix in ("eth", "ipv4", "udp", "mold", "framer", "itch"):
                valid_name = f"{prefix}_reject_observed"
                if int(getattr(d, valid_name).value):
                    code_name = f"{prefix}_reject_code"
                    self.diag.append((prefix, int(getattr(d, code_name).value)))
            await RisingEdge(d.clk)
            if in_fire:
                if int(d.recovery_required.value):
                    self.drained_beats_after_recovery += 1
                index += 1
                held = None
                d.rx_valid.value = 0
                self.accepted_beats += 1
            if index == len(stream) and not int(d.event_valid.value):
                quiet += 1
                if quiet >= 80:
                    return self.events[start_events:]
            else:
                quiet = 0
        raise AssertionError(f"timeout accepted={index}/{len(stream)}, events={self.events[start_events:]}, recovery={int(d.recovery_required.value)}")


@cocotb.test()
async def test_full_ingress_all_mutation_mappings_and_python_crosscheck(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    d = Driver(dut)
    await d.setup(rst=True)
    cfg = config()
    seq = SEQ0
    for i, typ in enumerate("AFECXDU"):
        msg = itch(typ, side=b"S", salt=i)
        packet = frame(mold_packet([msg], seq))
        parsed = frame_packet(packet, config(seq))
        assert parsed.success and len(parsed.messages) == 1
        got = await d.send_frame(packet, seed=i + 1)
        assert got == [expected_event(msg, seq, cfg)], (typ, got)
        seq = (seq + 1) & ((1 << 64) - 1)
    assert int(dut.current_expected_sequence.value) == seq


@cocotb.test()
async def test_filters_heartbeat_multi_message_and_reuse(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    d = Driver(dut)
    await d.setup(rst=True)
    cfg = config()
    seq = SEQ0
    batch = [itch("A", salt=1), itch("P", salt=2), itch("E", locate=LOC + 1, salt=3), itch("U", salt=4)]
    packet = frame(mold_packet(batch, seq))
    parsed = frame_packet(packet, cfg)
    assert parsed.success and len(parsed.messages) == 4
    got = await d.send_frame(packet, seed=19)
    exp = [expected_event(batch[0], seq, cfg), expected_event(batch[3], seq + 3, cfg)]
    assert got == exp
    seq += len(batch)
    heartbeat = frame(SESSION + seq.to_bytes(8, "big") + b"\x00\x00")
    assert frame_packet(heartbeat, config(seq)).success
    assert await d.send_frame(heartbeat) == []
    assert int(dut.current_expected_sequence.value) == seq
    # Nonfatal outer profile filters must not quarantine later valid traffic.
    vlan = frame(mold_packet([itch("A")], seq), ethertype=0x8100)
    assert frame_packet(vlan, config(seq)).error is not None
    assert await d.send_frame(vlan) == []
    assert not int(dut.recovery_required.value)
    wrong_ip = frame(mold_packet([itch("A")], seq), dst=DEST_IP ^ 1)
    assert frame_packet(wrong_ip, config(seq)).error is not None
    assert await d.send_frame(wrong_ip) == []
    assert not int(dut.recovery_required.value)
    wrong_port = frame(mold_packet([itch("A")], seq), port=DEST_PORT ^ 1)
    assert frame_packet(wrong_port, config(seq)).error is not None
    assert await d.send_frame(wrong_port) == []
    assert not int(dut.recovery_required.value)
    good = itch("D", salt=5)
    assert await d.send_frame(frame(mold_packet([good], seq))) == [expected_event(good, seq, cfg)]


@cocotb.test()
async def test_late_structural_suffix_and_itch_quarantine(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    d = Driver(dut)
    await d.setup(rst=True)
    a, e, u = itch("A", salt=1), itch("E", salt=2), itch("U", salt=3)
    body = len(a).to_bytes(2, "big") + a + len(e).to_bytes(2, "big") + e + b"\x00\x05ab"
    pkt = frame(mold_packet([], SEQ0, count=3, raw_body=body))
    cfg = config()
    oracle = frame_packet(pkt, cfg)
    assert not oracle.success and len(oracle.messages) == 2
    got = await d.send_frame(pkt, seed=7)
    assert got == [expected_event(a, SEQ0, cfg), expected_event(e, SEQ0 + 1, cfg)]
    assert int(dut.recovery_required.value) == 1
    assert int(dut.current_expected_sequence.value) == SEQ0
    assert d.diag and any(x[0] == "framer" for x in d.diag)
    old_events = len(d.events)
    # New frame is held by an upstream producer throughout recovery.
    blocked_beats = beats(frame(mold_packet([u], SEQ0)))
    await FallingEdge(dut.clk)
    dut.rx_data.value, dut.rx_keep.value, dut.rx_last.value = blocked_beats[0]
    dut.rx_valid.value = 1
    for _ in range(12):
        await Timer(1, unit="ns")
        assert int(dut.rx_ready.value) == 0
        assert int(dut.event_valid.value) == 0
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
    dut.rx_valid.value = 0
    assert len(d.events) == old_events
    await d.setup(rearm=True, seq=SEQ0, session=SESSION)
    assert not int(dut.recovery_required.value)
    assert await d.send_frame(frame(mold_packet([u], SEQ0))) == [expected_event(u, SEQ0, cfg)]

    await d.setup(rearm=True, seq=SEQ0)
    valid = itch("A", salt=9)
    bad = b"Zunsupported"
    final = itch("U", salt=10)
    pkt = frame(mold_packet([valid, bad, final], SEQ0))
    oracle = frame_packet(pkt, cfg)
    assert oracle.success and len(oracle.messages) == 3
    got = await d.send_frame(pkt, seed=42)
    assert got == [expected_event(valid, SEQ0, cfg)]
    assert int(dut.recovery_required.value) == 1
    assert int(dut.current_expected_sequence.value) == SEQ0 + 3
    assert d.recovery_before_end
    assert d.drained_beats_after_recovery > 0


@cocotb.test()
async def test_semantic_and_outer_fatal_recovery_rearm(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    d = Driver(dut)
    await d.setup(rst=True)
    cases = [
        (b"Zunsupported", "itch"),
        (itch("A")[:-1], "itch"),
        (itch("A", side=b"?"), "itch"),
        (itch("A", symbol=b"WRONG   "), "itch"),
    ]
    for msg, expected_stage in cases:
        await d.setup(rearm=True, seq=SEQ0)
        await d.send_frame(frame(mold_packet([msg], SEQ0)), seed=len(msg))
        assert int(dut.recovery_required.value) == 1
        assert int(dut.parser_valid.value) == 0
        assert int(dut.recovery_stage.value) == 6
        assert d.diag and any(s == expected_stage for s, _ in d.diag)

    # Fatal Ethernet header truncation is latched globally.
    await d.setup(rearm=True, seq=SEQ0)
    await d.send_frame(bytes.fromhex("0201020304050a0b0c0d"))
    assert int(dut.recovery_required.value) == 1
    assert int(dut.recovery_stage.value) == 1

    # UDP physical length mismatch is fatal after valid Ethernet and IPv4.
    await d.setup(rearm=True, seq=SEQ0)
    bad_udp = bytes.fromhex("beef1234000a0000") + b"x"
    await d.send_frame(ethernet_ip(ipv4(bad_udp)))
    assert int(dut.recovery_required.value) == 1
    assert int(dut.recovery_stage.value) == 3

    await d.setup(rearm=True, seq=SEQ0)
    bad_ip = bytearray(ipv4(bytes.fromhex("beef123400080000") +
                            mold_packet([itch("D")], SEQ0)))
    bad_ip[10] ^= 0x80
    # The next configuration is installed only on this explicit new epoch.
    await d.send_frame(bytes.fromhex("0201020304050a0b0c0d0e0f0800") + bytes(bad_ip))
    assert int(dut.recovery_required.value) == 1
    assert int(dut.recovery_stage.value) == 2
    new_session = b"NEWEPOCH01"
    new_seq = 0xAABBCCDDEEFF0011
    await d.setup(rearm=True, seq=new_seq, session=new_session)
    good = itch("D", salt=21)
    got = await d.send_frame(frame(mold_packet([good], new_seq, session=new_session)))
    assert got == [expected_event(good, new_seq, config(new_seq, session=new_session))]
    assert int(dut.recovery_required.value) == 0


@cocotb.test()
async def test_mold_header_eos_and_trailing_recovery(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    d = Driver(dut)
    await d.setup(rst=True)
    # A physically truncated Mold header is fatal at the Mold controller.
    await d.send_frame(frame(SESSION + SEQ0.to_bytes(8, "big") + b"\x00"))
    assert int(dut.recovery_required.value) == 1
    assert int(dut.recovery_stage.value) == 4

    await d.setup(rearm=True, seq=SEQ0)
    # Exact EOS is a local fatal control outcome and never advances sequence.
    eos = SESSION + SEQ0.to_bytes(8, "big") + b"\xff\xff"
    assert await d.send_frame(frame(eos)) == []
    assert int(dut.recovery_required.value) == 1
    assert int(dut.current_expected_sequence.value) == SEQ0

    await d.setup(rearm=True, seq=SEQ0)
    msg = itch("D", salt=33)
    block = len(msg).to_bytes(2, "big") + msg
    raw_body = block + b"EXTRA"
    raw_mold = mold_packet([], SEQ0, count=1, raw_body=raw_body)
    oracle = frame_packet(frame(raw_mold), config())
    assert not oracle.success and len(oracle.messages) == 1
    got = await d.send_frame(frame(raw_mold), seed=97)
    assert got == [expected_event(msg, SEQ0, config())]
    assert int(dut.recovery_required.value) == 1
    assert int(dut.current_expected_sequence.value) == SEQ0


@cocotb.test()
async def test_random_replayable_frames_and_fail_closed_rearm(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    d = Driver(dut)
    for seed in (1, 7, 19, 42, 97):
        await d.setup(rst=True)
        rng = random.Random(seed)
        seq = SEQ0
        for n in range(4):
            kind = rng.choice("AFECXDUP")
            msg = itch(kind, salt=(seed + n) & 0x3F)
            if kind == "P":
                expected = []
            else:
                one = expected_event(msg, seq, config())
                expected = [] if one is None else [one]
            raw = frame(mold_packet([msg], seq))
            model = frame_packet(raw, config(seq))
            assert model.success
            got = await d.send_frame(raw, seed=seed * 100 + n)
            assert got == expected, (seed, n, kind)
            seq += 1
        # Known-length semantic error is structurally valid but quarantines ITCH.
        wrong = itch("A", salt=seed)[:-1]
        raw = frame(mold_packet([wrong], seq))
        assert frame_packet(raw, config(seq)).success
        assert await d.send_frame(raw, seed=seed + 1000) == []
        assert int(dut.recovery_required.value)
        print(f"WIRE022_VECTOR seed={seed} messages=4 malformed=wrong_length frame_hex={raw.hex()}")
