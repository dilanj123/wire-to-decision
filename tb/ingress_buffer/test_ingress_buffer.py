import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer


LEGAL_KEEPS = (0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF)


def tuple_expected(beats):
    return list(beats)


def byte_expected(beats):
    result = []
    for data, keep, last in beats:
        for lane in range(keep.bit_count()):
            result.append(((data >> (lane * 8)) & 0xFF, bool(last and lane == keep.bit_count() - 1)))
    return result


async def reset_dut(dut):
    await FallingEdge(dut.clk)
    dut.rst.value = 0
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)


async def drive_fifo(dut, beats, ready_fn=lambda _cycle: True, seed=1, max_cycles=5000):
    rng = random.Random(seed)
    queue = []
    sent = 0
    received = []
    held = None
    stall_snapshot = None

    for cycle in range(max_cycles):
        await FallingEdge(dut.clk)
        dut.out_ready.value = int(ready_fn(cycle))
        if held is None and sent < len(beats):
            held = beats[sent]
            dut.in_data.value, dut.in_keep.value, dut.in_last.value = held
            dut.in_valid.value = 1
        elif held is None:
            dut.in_valid.value = 0
        await Timer(1, unit="ns")
        await ReadOnly()

        out_valid = bool(int(dut.out_valid.value))
        out_ready = bool(int(dut.out_ready.value))
        if out_valid and not out_ready:
            snapshot = (
                int(dut.out_data.value), int(dut.out_keep.value), int(dut.out_last.value)
            )
            if stall_snapshot is not None:
                assert snapshot == stall_snapshot
            stall_snapshot = snapshot
        else:
            stall_snapshot = None

        push = bool(int(dut.in_valid.value) and int(dut.in_ready.value))
        pop = bool(int(dut.out_valid.value) and int(dut.out_ready.value))
        if push:
            queue.append(held)
        if pop:
            assert queue
            expected = queue.pop(0)
            actual = (int(dut.out_data.value), int(dut.out_keep.value), int(dut.out_last.value))
            assert actual == expected
            received.append(actual)

        await RisingEdge(dut.clk)
        if push:
            sent += 1
            held = None

        if sent == len(beats) and not queue and held is None:
            await FallingEdge(dut.clk)
            await Timer(1, unit="ns")
            await ReadOnly()
            assert int(dut.out_valid.value) == 0
            return received

    raise AssertionError(f"timeout sent={sent}/{len(beats)} queued={len(queue)} received={len(received)}")


@cocotb.test()
async def test_empty_single_and_stall(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    beats = [(0x1122334455667788, 0x7F, True)]
    received = await drive_fifo(dut, beats, lambda cycle: cycle >= 4)
    assert received == beats


@cocotb.test()
async def test_fill_full_and_backpressure(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    beats = [(0x1000 + i, 0xFF, False) for i in range(3)]
    received = await drive_fifo(dut, beats, lambda cycle: cycle >= 5)
    assert received == beats


@cocotb.test()
async def test_simultaneous_pop_push_occupancy_one_and_two(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    beats = [(0x2000 + i, 0xFF, False) for i in range(8)]
    received = await drive_fifo(dut, beats, lambda _cycle: True)
    assert received == beats


@cocotb.test()
async def test_frame_shaped_and_reset_flush(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    dut.in_data.value = 0xABCDEF0123456789
    dut.in_keep.value = 0x03
    dut.in_last.value = 1
    dut.in_valid.value = 1
    dut.out_ready.value = 0
    await FallingEdge(dut.clk)
    await Timer(1, unit="ns")
    await ReadOnly()
    assert int(dut.in_ready.value) == 1
    await RisingEdge(dut.clk)
    dut.rst.value = 1
    dut.in_valid.value = 0
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)
    await Timer(1, unit="ns")
    await ReadOnly()
    assert int(dut.out_valid.value) == 0
    received = await drive_fifo(
        dut,
        [(0x3736353433323130, 0x07, True), (0x4746454443424140, 0x03, True)],
        lambda _cycle: True,
    )
    assert received == [(0x3736353433323130, 0x07, True), (0x4746454443424140, 0x03, True)]


@cocotb.test()
async def test_fixed_random_fifo_traffic(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    for seed in (1, 7, 19):
        await reset_dut(dut)
        rng = random.Random(seed)
        beats = []
        for index in range(80):
            beats.append((rng.getrandbits(64), rng.getrandbits(8), bool(rng.getrandbits(1))))
        received = await drive_fifo(dut, beats, lambda cycle: (cycle + seed) % 4 != 0, seed)
        assert received == beats
