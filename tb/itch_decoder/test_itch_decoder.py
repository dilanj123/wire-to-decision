import random
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model" / "python"))
from wire_to_decision.itch import DecodeKind, decode_itch_message
from wire_to_decision.mold import FramedMessage
from wire_to_decision.types import ModelConfig


LOC = 0x1234
SEQ = 0xFEDCBA9876543210
SYMBOL = b"ABCD    "
LENGTHS = {"A": 36, "F": 40, "E": 31, "C": 36, "X": 23, "D": 19, "U": 35, "P": 44}


def put(buf, offset, width, value):
    buf[offset:offset + width] = value.to_bytes(width, "big")


def itch_message(kind, locate=LOC, symbol=SYMBOL, side=b"S"):
    data = bytearray(LENGTHS[kind])
    data[0] = ord(kind)
    put(data, 1, 2, locate)
    put(data, 3, 2, 0xA1B2)
    put(data, 5, 6, 0x010203040506)
    if kind in "AF":
        put(data, 11, 8, 0x1122334455667788)
        data[19:20] = side
        put(data, 20, 4, 0x10203040)
        data[24:32] = symbol
        put(data, 32, 4, 0x50607080)
    elif kind in "ECX":
        put(data, 11, 8, 0x8877665544332211)
        put(data, 19, 4, 0x20304050)
    elif kind == "D":
        put(data, 11, 8, 0x8877665544332211)
    elif kind == "U":
        put(data, 11, 8, 0x0102030405060708)
        put(data, 19, 8, 0x1112131415161718)
        put(data, 27, 4, 0x31415926)
        put(data, 31, 4, 0x27182818)
    return bytes(data)


class Driver:
    def __init__(self, dut):
        self.d = dut
        self.events = []
        self.rejects = []

    async def tick(self, **values):
        d = self.d
        await FallingEdge(d.clk)
        defaults = dict(rst=0, rearm=0, cfg_tracked_stock_locate=LOC,
                        cfg_symbol_check_enable=1,
                        cfg_expected_stock_symbol=int.from_bytes(SYMBOL, "big"),
                        message_valid=0, message_ready=1, message_sequence=SEQ, message_length=0,
                        message_empty=0, in_data=0, in_valid=0, in_last=0,
                        event_ready=1, reject_ready=1)
        defaults.update(values)
        for name, value in defaults.items():
            getattr(d, name).value = value
        await Timer(1, unit="ns")
        event = None
        if int(d.event_valid.value):
            event = tuple(int(getattr(d, name).value) for name in (
                "event_kind", "source_type", "mold_sequence", "itch_timestamp", "stock_locate",
                "old_order_reference", "new_order_reference", "quantity", "price", "side",
                "old_reference_valid", "new_reference_valid", "quantity_valid", "price_valid", "side_valid"))
            if int(d.event_ready.value):
                self.events.append(event)
        if int(d.reject_valid.value) and int(d.reject_ready.value):
            self.rejects.append((int(d.reject_fatal.value), int(d.reject_code.value)))
        result = {"msg": int(d.message_valid.value) and int(d.message_ready.value),
                  "byte": int(d.in_valid.value) and int(d.in_ready.value),
                  "event": event if event is not None and int(d.event_ready.value) else None}
        await RisingEdge(d.clk)
        return result

    async def reset(self):
        for _ in range(3):
            await self.tick(rst=1)
        await self.tick()
        self.events.clear()
        self.rejects.clear()

    async def send(self, payload, sequence=SEQ, declared=None, empty=False,
                   event_ready=1, reject_ready=1):
        length = len(payload) if declared is None else declared
        for _ in range(10):
            r = await self.tick(message_valid=1, message_sequence=sequence,
                                message_length=length, message_empty=int(empty),
                                event_ready=event_ready, reject_ready=reject_ready)
            if r["msg"]:
                break
        else:
            raise AssertionError("decoder did not accept message metadata")
        for i, byte in enumerate(payload):
            for _ in range(10):
                r = await self.tick(in_valid=1, in_data=byte, in_last=int(i == len(payload) - 1),
                                    event_ready=event_ready, reject_ready=reject_ready)
                if r["byte"]:
                    break
            else:
                raise AssertionError("decoder did not accept message byte")
        for _ in range(4):
            await self.tick(event_ready=event_ready, reject_ready=reject_ready)


def expected(kind, seq=SEQ):
    kinds = {"A": 0, "F": 0, "E": 1, "C": 2, "X": 3, "D": 4, "U": 5}
    a = itch_message(kind)
    old, new, qty, price, side = 0, 0, 0, 0, 0
    ov = nv = qv = pv = sv = 0
    if kind in "AF":
        new, qty, price, side = 0x1122334455667788, 0x10203040, 0x50607080, 1
        nv = qv = pv = sv = 1
    elif kind in "ECX":
        old, qty = 0x8877665544332211, 0x20304050
        ov = qv = 1
    elif kind == "D":
        old, ov = 0x8877665544332211, 1
    elif kind == "U":
        old, new, qty, price = 0x0102030405060708, 0x1112131415161718, 0x31415926, 0x27182818
        ov = nv = qv = pv = 1
    return (kinds[kind], ord(kind), seq, 0x010203040506, LOC, old, new, qty, price, side,
            ov, nv, qv, pv, sv)


@cocotb.test()
async def test_all_supported_event_mappings_and_p(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Driver(dut)
    await b.reset()
    config = ModelConfig(destination_ipv4=0, destination_udp_port=0,
                         tracked_stock_locate=LOC, symbol_check_enable=True,
                         expected_stock_symbol=SYMBOL, active_session=b"0123456789",
                         expected_sequence=SEQ, decision_threshold=0, initial_budget=0,
                         decision_enable=False)
    for kind in "AFECXDU":
        await b.send(itch_message(kind))
        assert b.events[-1] == expected(kind)
        assert int(dut.recovery_required.value) == 0
        oracle = decode_itch_message(FramedMessage(SEQ, itch_message(kind)), config)
        assert oracle.kind is DecodeKind.MUTATION_EVENT
        event = oracle.event
        rtl = b.events[-1]
        kind_code = {"ADD": 0, "EXECUTE": 1, "EXECUTE_WITH_PRICE": 2,
                     "CANCEL": 3, "DELETE": 4, "REPLACE": 5}[event.kind.value]
        assert rtl[0] == kind_code
        assert rtl[1:5] == (ord(event.source_type.value), event.mold_sequence,
                            event.itch_timestamp, event.stock_locate)
        assert rtl[5:10] == (event.old_order_reference or 0,
                             event.new_order_reference or 0,
                             event.quantity or 0, event.price or 0,
                             int(event.side is not None and event.side.value == "S"))
        assert rtl[10:] == (int(event.field_valid.old_order_reference),
                            int(event.field_valid.new_order_reference),
                            int(event.field_valid.quantity), int(event.field_valid.price),
                            int(event.field_valid.side))
    count = len(b.events)
    await b.send(itch_message("P"))
    assert len(b.events) == count
    assert not b.rejects


@cocotb.test()
async def test_filters_and_symbol_configuration(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Driver(dut)
    await b.reset()
    await b.send(itch_message("A", locate=LOC + 1))
    assert not b.events and not b.rejects
    await b.send(itch_message("A", symbol=b"XXXXXXXX"), event_ready=1)
    # Enabled mismatch fails closed; then explicitly rearm with symbol check disabled.
    assert not b.events and b.rejects[-1] == (1, 4)
    await b.tick(rearm=1, cfg_symbol_check_enable=0)
    await b.send(itch_message("A", symbol=b"XXXXXXXX"))
    assert b.events[-1] == expected("A")


@cocotb.test()
async def test_fail_closed_side_length_unknown_empty_and_drain(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Driver(dut)
    await b.reset()
    bad_side = itch_message("A", side=b"?")
    await b.send(bad_side)
    assert not b.events and b.rejects[-1] == (1, 3)
    for kind in "AFECXDUP":
        await b.tick(rearm=1)
        await b.send(itch_message(kind), declared=LENGTHS[kind] - 1)
        assert b.rejects[-1] == (1, 2), kind
    await b.tick(rearm=1)
    await b.send(itch_message("E"), declared=30)
    assert not b.events and b.rejects[-1] == (1, 2)
    await b.tick(rearm=1)
    await b.send(b"Zopaque", declared=7)
    assert not b.events and b.rejects[-1] == (1, 1)
    # Following complete messages are consumed in quarantine, not decoded.
    await b.send(itch_message("E"))
    assert not b.events
    await b.tick(rearm=1)
    await b.send(b"", declared=0, empty=True)
    assert b.rejects[-1] == (1, 0)


@cocotb.test()
async def test_complete_boundary_and_event_stability(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Driver(dut)
    await b.reset()
    msg = itch_message("A")
    for _ in range(4):
        r = await b.tick(message_valid=1, message_sequence=SEQ,
                         message_length=len(msg), event_ready=0)
        if r["msg"]:
            break
    for byte in msg[:-1]:
        await b.tick(in_valid=1, in_data=byte, in_last=0, event_ready=0)
    assert not int(dut.event_valid.value)
    # Finish only after providing the final byte; event becomes pending and holds.
    r = await b.tick(in_valid=1, in_data=msg[-1], in_last=1, event_ready=0)
    assert r["byte"]
    for _ in range(3):
        await b.tick(event_ready=0)
        if int(dut.event_valid.value):
            break
    assert int(dut.event_valid.value)
    held = tuple(int(getattr(dut, n).value) for n in ("event_kind", "source_type", "mold_sequence", "itch_timestamp", "stock_locate", "new_order_reference"))
    for _ in range(3):
        await b.tick(event_ready=0)
        assert int(dut.event_valid.value)
        assert held == tuple(int(getattr(dut, n).value) for n in ("event_kind", "source_type", "mold_sequence", "itch_timestamp", "stock_locate", "new_order_reference"))
    await b.tick(event_ready=1)
    assert len(b.events) == 1


@cocotb.test()
async def test_rejection_stall_and_rearm_discards_partial_message(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Driver(dut)
    await b.reset()
    for _ in range(4):
        r = await b.tick(message_valid=1, message_sequence=SEQ,
                         message_length=36, message_empty=0)
        if r["msg"]:
            break
    for i, byte in enumerate(itch_message("A")[:2]):
        r = await b.tick(in_valid=1, in_data=byte, in_last=0)
        assert r["byte"]
    await b.tick(rearm=1)
    assert int(dut.decoder_valid.value) == 1
    assert not int(dut.event_valid.value)
    await b.send(b"Zbad", declared=4, reject_ready=0)
    assert int(dut.reject_valid.value)
    held = (int(dut.reject_code.value), int(dut.reject_fatal.value))
    for _ in range(3):
        await b.tick(reject_ready=0)
        assert int(dut.reject_valid.value)
        assert (int(dut.reject_code.value), int(dut.reject_fatal.value)) == held
        assert int(dut.recovery_required.value)
    await b.tick(rearm=1)
    await b.tick()
    assert not int(dut.reject_valid.value) and int(dut.decoder_valid.value)


@cocotb.test()
async def test_deterministic_random_types_and_sequences(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Driver(dut)
    await b.reset()
    for seed in (1, 7, 19):
        rng = random.Random(seed)
        for kind in "AFECXDU":
            await b.tick(rearm=1)
            seq = rng.getrandbits(64)
            await b.send(itch_message(kind), sequence=seq)
            assert b.events[-1] == expected(kind, seq)
