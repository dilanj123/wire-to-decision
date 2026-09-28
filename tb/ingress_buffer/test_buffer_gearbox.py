import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer


def byte_expected(beats):
    result = []
    for data, keep, last in beats:
        count = keep.bit_count()
        for lane in range(count):
            result.append(((data >> (lane * 8)) & 0xFF, bool(last and lane == count - 1)))
    return result


async def reset_dut(dut):
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)


@cocotb.test()
async def test_buffer_to_gearbox_stream_and_backpressure(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    beats = [
        (0x1716151413121110, 0xFF, False),
        (0x2726252423222120, 0xFF, False),
        (0x3736353433323120, 0x07, True),
        (0x4746454443424140, 0x03, True),
    ]
    expected = byte_expected(beats)
    received = []
    sent = 0
    held = None

    for cycle in range(2000):
        await FallingEdge(dut.clk)
        dut.out_ready.value = int(cycle % 7 not in (1, 2, 3))
        if held is None and sent < len(beats):
            held = beats[sent]
            dut.in_data.value, dut.in_keep.value, dut.in_last.value = held
            dut.in_valid.value = 1
        elif held is None:
            dut.in_valid.value = 0
        await Timer(1, unit="ns")
        await ReadOnly()

        if int(dut.out_valid.value) and int(dut.out_ready.value):
            received.append((int(dut.out_data.value), bool(int(dut.out_last.value))))

        push = bool(int(dut.in_valid.value) and int(dut.in_ready.value))
        await RisingEdge(dut.clk)
        if push:
            sent += 1
            held = None
            dut.in_valid.value = 0

        if sent == len(beats) and len(received) == len(expected):
            assert received == expected
            return

    raise AssertionError(f"timeout sent={sent} received={len(received)} expected={len(expected)}")
