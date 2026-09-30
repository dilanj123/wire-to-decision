import random
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model" / "python"))
from wire_to_decision.mold import FramingState, MoldErrorCode, parse_mold_packet


def body_of(messages):
    return b"".join(len(m).to_bytes(2, "big") + m for m in messages)


class Bench:
    def __init__(self, dut):
        self.d = dut
        self.metas = []
        self.payload = []
        self.results = []
        self.rejects = []
        self.cycle_no = 0
        self.stalled = None

    async def tick(self, **drive):
        d = self.d
        await FallingEdge(d.clk)
        defaults = dict(rst=0, rearm=0, packet_valid=0, packet_sequence=0,
                        packet_message_count=0, packet_body_empty=0,
                        in_valid=0, in_data=0, in_last=0, message_ready=1,
                        out_ready=1, packet_result_ready=1, reject_ready=1)
        defaults.update(drive)
        for name, value in defaults.items():
            getattr(d, name).value = value
        await Timer(1, unit="ns")
        if self.stalled and not defaults["rst"] and not defaults["rearm"]:
            kind, prior = self.stalled
            if kind == "message":
                assert int(d.message_valid.value) == prior[0]
                assert (int(d.message_sequence.value), int(d.message_length.value),
                        int(d.message_empty.value)) == prior[1:]
                assert not int(d.in_ready.value) and not int(d.out_valid.value)
            elif kind == "payload":
                assert int(d.out_valid.value) == prior[0]
                assert (int(d.out_data.value), int(d.out_last.value)) == prior[1:]
            elif kind == "result":
                assert int(d.packet_result_valid.value) == prior[0]
                assert int(d.packet_result_success.value) == prior[1]
            elif kind == "reject":
                assert int(d.reject_valid.value) == prior[0]
                assert (int(d.reject_fatal.value), int(d.reject_code.value)) == prior[1:]
                assert not int(d.in_ready.value) and not int(d.out_valid.value)
        if int(d.packet_valid.value) and int(d.packet_ready.value):
            packet_fire = True
        else:
            packet_fire = False
        if int(d.message_valid.value) and int(d.message_ready.value):
            self.metas.append((int(d.message_sequence.value), int(d.message_length.value),
                               int(d.message_empty.value)))
        if int(d.out_valid.value) and int(d.out_ready.value):
            self.payload.append((int(d.out_data.value), int(d.out_last.value)))
        if int(d.packet_result_valid.value) and int(d.packet_result_ready.value):
            self.results.append(int(d.packet_result_success.value))
        if int(d.reject_valid.value) and int(d.reject_ready.value):
            self.rejects.append((int(d.reject_fatal.value), int(d.reject_code.value)))
        input_fire = int(d.in_valid.value) and int(d.in_ready.value)
        self.stalled = None
        if int(d.message_valid.value) and not int(d.message_ready.value):
            self.stalled = ("message", (int(d.message_valid.value),
                                          int(d.message_sequence.value), int(d.message_length.value),
                                          int(d.message_empty.value)))
        elif int(d.out_valid.value) and not int(d.out_ready.value):
            self.stalled = ("payload", (int(d.out_valid.value), int(d.out_data.value), int(d.out_last.value)))
        elif int(d.packet_result_valid.value) and not int(d.packet_result_ready.value):
            self.stalled = ("result", (int(d.packet_result_valid.value),
                                         int(d.packet_result_success.value)))
        elif int(d.reject_valid.value) and not int(d.reject_ready.value):
            self.stalled = ("reject", (int(d.reject_valid.value), int(d.reject_fatal.value),
                                        int(d.reject_code.value)))
        await RisingEdge(d.clk)
        self.cycle_no += 1
        return {"packet_fire": packet_fire, "input_fire": input_fire}

    async def reset(self):
        for _ in range(3):
            await self.tick(rst=1)
        await self.tick(rst=0)

    async def packet(self, sequence, count, body, body_empty=False, stall=False,
                     result_stall_cycles=0, reject_stall_cycles=0):
        accepted = False
        for _ in range(20):
            hs = await self.tick(packet_valid=1, packet_sequence=sequence,
                                 packet_message_count=count, packet_body_empty=int(body_empty))
            if hs["packet_fire"]:
                accepted = True
                break
        assert accepted, "framer did not accept packet metadata"
        # packet metadata transfers at the sampling edge of the final tick.
        if body:
            for i, byte in enumerate(body):
                while True:
                    hs = await self.tick(in_valid=1, in_data=byte,
                                         in_last=int(i == len(body) - 1),
                                         out_ready=int(not stall or self.cycle_no % 4 != 1),
                                         message_ready=int(not stall or self.cycle_no % 4 != 0))
                    if hs["input_fire"]:
                        break
        for cycle in range(12):
            await self.tick(out_ready=1, message_ready=1,
                            packet_result_ready=int(cycle >= result_stall_cycles),
                            reject_ready=int(cycle >= reject_stall_cycles))


async def initialized(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    return b


@cocotb.test()
async def test_single_and_multiple_message_boundaries(dut):
    b = await initialized(dut)
    msgs = [b"A", b"BC", b"longer"]
    await b.packet(0xFFFFFFFFFFFFFFFE, len(msgs), body_of(msgs), stall=True)
    assert b.metas == [(0xFFFFFFFFFFFFFFFE, 1, 0),
                       (0xFFFFFFFFFFFFFFFF, 2, 0), (0, 6, 0)]
    expected = []
    for m in msgs:
        expected.extend((x, int(i == len(m) - 1)) for i, x in enumerate(m))
    assert b.payload == expected
    assert b.results == [1]
    assert b.rejects == []


@cocotb.test()
async def test_zero_length_messages_are_structural(dut):
    b = await initialized(dut)
    msgs = [b"xy", b"", b"z"]
    await b.packet(33, 3, body_of(msgs))
    assert b.metas == [(33, 2, 0), (34, 0, 1), (35, 1, 0)]
    assert b.payload == [(ord("x"), 0), (ord("y"), 1), (ord("z"), 1)]
    assert b.results == [1] and b.rejects == []


@cocotb.test()
async def test_body_empty_and_length_field_truncations(dut):
    b = await initialized(dut)
    await b.packet(4, 2, b"", body_empty=True)
    assert b.results == [0] and b.rejects == [(1, 0)]
    await b.tick(rearm=1)
    b.metas.clear(); b.payload.clear(); b.results.clear(); b.rejects.clear()
    await b.packet(5, 1, b"\x00", body_empty=False)
    assert b.metas == [] and b.payload == []
    assert b.results == [0] and b.rejects == [(1, 0)]


@cocotb.test()
async def test_positive_payload_truncation_and_short_message_count(dut):
    b = await initialized(dut)
    await b.packet(8, 1, b"\x00\x03ab")
    assert b.metas == [(8, 3, 0)]
    assert b.payload == [(ord("a"), 0), (ord("b"), 0)]
    assert b.results == [0] and b.rejects == [(1, 1)]
    await b.tick(rearm=1)
    b.metas.clear(); b.payload.clear(); b.results.clear(); b.rejects.clear()
    # Positive length is known, but the physical body ends at the low length byte.
    await b.packet(10, 1, b"\x00\x02")
    assert b.metas == [(10, 2, 0)] and b.payload == []
    assert b.results == [0] and b.rejects == [(1, 1)]
    await b.tick(rearm=1)
    b.metas.clear(); b.payload.clear(); b.results.clear(); b.rejects.clear()
    # One complete block but packet count requires a second length field.
    await b.packet(9, 2, b"\x00\x01q")
    assert b.metas == [(9, 1, 0)]
    assert b.payload == [(ord("q"), 1)]
    assert b.results == [0] and b.rejects == [(1, 0)]


@cocotb.test()
async def test_trailing_bytes_after_exact_message_count(dut):
    b = await initialized(dut)
    # Exact first block plus unclaimed byte: message stays complete, packet fails.
    await b.packet(10, 1, b"\x00\x01x\x99")
    assert b.metas == [(10, 1, 0)]
    assert b.payload == [(ord("x"), 1)]
    assert b.results == [0] and b.rejects == [(1, 2)]


@cocotb.test()
async def test_deterministic_random_blocks(dut):
    b = await initialized(dut)
    for seed in (1, 7, 19):
        rng = random.Random(seed)
        messages = [bytes(rng.randrange(256) for _ in range(rng.randrange(0, 10)))
                    for _ in range(rng.randrange(1, 7))]
        start = len(b.metas)
        pstart = len(b.payload)
        rstart = len(b.results)
        await b.packet(seed * 100, len(messages), body_of(messages), stall=True)
        got_meta = b.metas[start:]
        assert got_meta == [(seed * 100 + i, len(m), int(len(m) == 0))
                            for i, m in enumerate(messages)]
        got = b.payload[pstart:]
        exp = [(v, int(j == len(m) - 1)) for m in messages
               for j, v in enumerate(m)]
        assert got == exp
        assert b.results[rstart:] == [1]


@cocotb.test()
async def test_result_and_rejection_stalls(dut):
    b = await initialized(dut)
    await b.packet(0x123, 1, body_of([b"stall"]), result_stall_cycles=4)
    assert b.results == [1]
    assert b.rejects == []
    await b.tick(rearm=1)
    b.metas.clear(); b.payload.clear(); b.results.clear(); b.rejects.clear()
    await b.packet(0x124, 1, b"\x00\x01z\x99", reject_stall_cycles=5,
                   result_stall_cycles=5)
    assert b.results == [0]
    assert b.rejects == [(1, 2)]


@cocotb.test()
async def test_rearm_discards_partial_packet_state(dut):
    b = await initialized(dut)
    await b.tick(packet_valid=1, packet_sequence=7, packet_message_count=1)
    await b.tick(in_valid=1, in_data=0, in_last=0)
    await b.tick(rearm=1)
    b.metas.clear(); b.payload.clear(); b.results.clear(); b.rejects.clear()
    await b.packet(8, 1, body_of([b"fresh"]))
    assert b.metas == [(8, 5, 0)]
    assert bytes(x for x, _ in b.payload) == b"fresh"
    assert b.payload[-1][1] == 1
    assert b.results == [1] and b.rejects == []
    await b.tick(rearm=1)
    b.metas.clear(); b.payload.clear(); b.results.clear(); b.rejects.clear()
    # Keep a terminal rejection pending, then prove re-arm discards it.
    await b.packet(9, 1, b"\x00", reject_stall_cycles=20,
                   result_stall_cycles=20)
    assert int(dut.reject_valid.value) == 1
    assert int(dut.packet_result_valid.value) == 1
    await b.tick(rearm=1)
    await Timer(1, unit="ns")
    assert int(dut.reject_valid.value) == 0
    assert int(dut.packet_result_valid.value) == 0
    b.metas.clear(); b.payload.clear(); b.results.clear(); b.rejects.clear()
    await b.packet(10, 1, body_of([b"after-rearm"]))
    assert b.results == [1] and b.rejects == []


@cocotb.test()
async def test_synchronous_reset_discards_held_payload(dut):
    b = await initialized(dut)
    await b.tick(packet_valid=1, packet_sequence=20, packet_message_count=1)
    await b.tick(in_valid=1, in_data=0, in_last=0)
    await b.tick(in_valid=1, in_data=3, in_last=0)
    await b.tick(message_ready=1)
    await b.tick(in_valid=1, in_data=0xA5, in_last=0, out_ready=0)
    await Timer(1, unit="ns")
    assert int(dut.out_valid.value) == 1
    await b.tick(rst=1)
    await Timer(1, unit="ns")
    assert int(dut.packet_ready.value) == 1
    assert not int(dut.message_valid.value) and not int(dut.out_valid.value)
    assert not int(dut.packet_result_valid.value) and not int(dut.reject_valid.value)
    b.metas.clear(); b.payload.clear(); b.results.clear(); b.rejects.clear()
    await b.packet(21, 1, body_of([b"reset-fresh"]))
    assert bytes(x for x, _ in b.payload) == b"reset-fresh"
    assert b.payload[-1][1] == 1 and b.results == [1]


@cocotb.test()
async def test_python_mold_framing_crosscheck(dut):
    b = await initialized(dut)
    session = bytes.fromhex("4142434445464748494a")
    vectors = [
        (0xFFFFFFFFFFFFFFFE, 2, body_of([b"ok", b"yes"]), False, None),
        (0xFFFFFFFFFFFFFFFE, 2, body_of([b"abc", b"z"]), False, None),
        (9, 1, b"\x00", False, MoldErrorCode.MESSAGE_LENGTH_TRUNCATED),
        (9, 1, b"\x00\x03ab", False, MoldErrorCode.MESSAGE_TRUNCATED),
        (9, 2, body_of([b"q"]), False, MoldErrorCode.MESSAGE_LENGTH_TRUNCATED),
        (9, 1, b"\x00\x01q!", False, MoldErrorCode.TRAILING_BYTES),
        (9, 1, b"", True, MoldErrorCode.MESSAGE_LENGTH_TRUNCATED),
    ]
    for sequence, count, body, empty, expected_error in vectors:
        mold_packet = session + sequence.to_bytes(8, "big") + count.to_bytes(2, "big") + body
        reference = parse_mold_packet(mold_packet,
                                      FramingState(session, sequence))
        assert reference.error == expected_error
        m0, p0, r0, e0 = len(b.metas), len(b.payload), len(b.results), len(b.rejects)
        await b.packet(sequence, count, body, body_empty=empty)
        actual_metas = b.metas[m0:]
        actual_payload = b.payload[p0:]
        actual_result = b.results[r0:]
        actual_reject = b.rejects[e0:]
        complete_metas = actual_metas[:-1] if expected_error == MoldErrorCode.MESSAGE_TRUNCATED else actual_metas
        assert [x[0] for x in complete_metas] == [m.mold_sequence for m in reference.messages]
        assert [x[1] for x in complete_metas] == [len(m.payload) for m in reference.messages]
        reference_bytes = b"".join(m.payload for m in reference.messages)
        assert bytes(x for x, _ in actual_payload[:len(reference_bytes)]) == reference_bytes
        if expected_error == MoldErrorCode.MESSAGE_TRUNCATED:
            assert all(last == 0 for _, last in actual_payload[len(reference_bytes):])
        else:
            assert len(actual_payload) == len(reference_bytes)
        assert actual_result == [int(reference.success)]
        if expected_error is not None:
            code = {MoldErrorCode.MESSAGE_LENGTH_TRUNCATED: 0,
                    MoldErrorCode.MESSAGE_TRUNCATED: 1,
                    MoldErrorCode.TRAILING_BYTES: 2}[expected_error]
            assert actual_reject == [(1, code)]
        else:
            assert actual_reject == []
        await b.tick(rearm=1)
