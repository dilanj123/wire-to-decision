import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer


def make_frame(ether, payload):
    return bytes(range(0x40, 0x4C)) + bytes((ether >> 8, ether & 0xFF)) + payload


def pack(frame):
    beats = []
    for start in range(0, len(frame), 8):
        chunk = frame[start:start + 8]
        data = int.from_bytes(chunk + bytes(8 - len(chunk)), "little")
        beats.append((data, (1 << len(chunk)) - 1, start + 8 >= len(frame)))
    return beats


async def reset_dut(dut):
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.reject_ready.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0


async def run_beats(dut, beats, out_ready=lambda c: True):
    expected = []
    for data, keep, last in beats:
        count = keep.bit_count()
        expected.extend((data >> (8 * lane)) & 0xFF for lane in range(count))
    got = []
    lasts = []
    index = 0
    held = None
    rejects = []
    for cycle in range(4000):
        await FallingEdge(dut.clk)
        dut.out_ready.value = int(out_ready(cycle))
        dut.reject_ready.value = 1
        if held is None and index < len(beats):
            held = beats[index]
            dut.in_data.value, dut.in_keep.value, dut.in_last.value = held
            dut.in_valid.value = 1
        await Timer(1, unit="ns")
        await ReadOnly()
        in_fire = int(dut.in_valid.value) and int(dut.in_ready.value)
        out_fire = int(dut.out_valid.value) and int(dut.out_ready.value)
        reject_fire = int(dut.reject_valid.value) and int(dut.reject_ready.value)
        final_out = out_fire and int(dut.out_last.value)
        if out_fire:
            got.append(int(dut.out_data.value)); lasts.append(int(dut.out_last.value))
        if reject_fire:
            rejects.append((int(dut.reject_fatal.value), int(dut.reject_code.value)))
        await RisingEdge(dut.clk)
        if in_fire:
            index += 1; held = None; dut.in_valid.value = 0
        if reject_fire or final_out:
            await FallingEdge(dut.clk)
            return got, lasts, rejects
        if index == len(beats) and len(got) == len(expected) and not int(dut.out_valid.value):
            return got, lasts, rejects
    raise AssertionError("composition timeout")


@cocotb.test()
async def test_buffer_gearbox_eth_composition(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    accepted = make_frame(0x0800, b"IPv4-through-chain")
    filtered = make_frame(0x8100, b"discarded")
    for raw, payload, rejection in ((accepted, accepted[14:], []),
                                    (filtered, b"", [(0, 0)])):
        got, lasts, rejects = await run_beats(dut, pack(raw), lambda c: c % 6 not in (1, 2))
        assert got == list(payload)
        assert lasts == ([0] * (len(payload) - 1) + [1] if payload else [])
        assert rejects == rejection
