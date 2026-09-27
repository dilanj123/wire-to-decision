import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer


LEGAL_KEEPS = (0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF)


def expected_bytes(beats):
    expected = []
    for data, keep, last in beats:
        count = keep.bit_count()
        for lane in range(count):
            expected.append(((data >> (lane * 8)) & 0xFF, bool(last and lane == count - 1)))
    return expected


async def reset_dut(dut):
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)


async def run_beats(dut, beats, ready_pattern, input_pattern=None, max_cycles=4000):
    expected = expected_bytes(beats)
    received = []
    input_index = 0
    held = None
    previous_stall = None

    for cycle in range(max_cycles):
        await FallingEdge(dut.clk)
        dut.out_ready.value = int(ready_pattern(cycle))
        if (held is None and input_index < len(beats) and
                (input_pattern is None or input_pattern(cycle))):
            held = beats[input_index]
            data, keep, last = held
            dut.in_data.value = data
            dut.in_keep.value = keep
            dut.in_last.value = int(last)
            dut.in_valid.value = 1
        await Timer(1, unit="ns")
        await ReadOnly()

        if previous_stall is not None:
            assert int(dut.out_valid.value) == 1
            assert int(dut.out_data.value) == previous_stall[0]
            assert int(dut.out_last.value) == previous_stall[1]
        stalled_now = int(dut.out_valid.value) and not int(dut.out_ready.value)
        if stalled_now:
            previous_stall = (int(dut.out_data.value), int(dut.out_last.value))
        else:
            previous_stall = None

        input_transfer = bool(int(dut.in_valid.value) and int(dut.in_ready.value))
        output_transfer = bool(int(dut.out_valid.value) and int(dut.out_ready.value))
        if output_transfer:
            assert len(received) < len(expected)
            received.append((int(dut.out_data.value), bool(int(dut.out_last.value))))

        await RisingEdge(dut.clk)
        if input_transfer:
            input_index += 1
            held = None
            dut.in_valid.value = 0

        if input_index == len(beats) and len(received) == len(expected):
            await FallingEdge(dut.clk)
            await Timer(1, unit="ns")
            await ReadOnly()
            assert int(dut.out_valid.value) == 0
            assert received == expected
            return received

    raise AssertionError(f"timeout: inputs={input_index}/{len(beats)} outputs={len(received)}/{len(expected)}")


@cocotb.test()
async def test_all_legal_final_keep_masks(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    for index, keep in enumerate(LEGAL_KEEPS):
        await reset_dut(dut)
        data = int.from_bytes(bytes((0x10 + index * 8 + lane for lane in range(8))), "little")
        await run_beats(dut, [(data, keep, True)], lambda _cycle: True)


@cocotb.test()
async def test_multibeat_and_back_to_back_frames(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    beats = [
        (0x1716151413121110, 0xFF, False),
        (0x2726252423222120, 0xFF, False),
        (0x3736353433323120, 0x07, True),
        (0x4746454443424140, 0x03, True),
    ]
    await run_beats(dut, beats, lambda _cycle: True)


@cocotb.test()
async def test_output_backpressure_and_input_pressure(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    beats = [(0x0706050403020100 + index * 0x1111111111111111, 0xFF, False) for index in range(4)]
    beats.append((0x8786858483828180, 0x1F, True))
    await run_beats(dut, beats, lambda cycle: (cycle % 7 not in (1, 2, 3)))


@cocotb.test()
async def test_same_cycle_retire_refill(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    beats = [(0x1716151413121110, 0xFF, False), (0x2726252423222120, 0xFF, True)]
    await run_beats(dut, beats, lambda _cycle: True)


@cocotb.test()
async def test_reset_idle_stalled_and_partial(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    dut.in_data.value = 0x1716151413121110
    dut.in_keep.value = 0xFF
    dut.in_last.value = 1
    dut.in_valid.value = 1
    while True:
        await FallingEdge(dut.clk)
        await Timer(1, unit="ns")
        await ReadOnly()
        if int(dut.in_ready.value):
            break
        await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    dut.out_ready.value = 0
    await FallingEdge(dut.clk)
    await Timer(1, unit="ns")
    await ReadOnly()
    assert int(dut.out_valid.value) == 1
    stalled_byte = int(dut.out_data.value)
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)
    await Timer(1, unit="ns")
    await ReadOnly()
    assert int(dut.out_valid.value) == 0
    await run_beats(dut, [(0xA7A6A5A4A3A2A1A0, 0x03, True)], lambda _cycle: True)
    assert stalled_byte == 0x10


@cocotb.test()
async def test_fixed_random_legal_frames(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    for seed in (1, 7, 19):
        await reset_dut(dut)
        rng = random.Random(seed)
        beats = []
        for frame in range(5):
            beat_count = rng.randint(1, 4)
            for beat in range(beat_count):
                last = beat == beat_count - 1
                keep = rng.choice(LEGAL_KEEPS) if last else 0xFF
                data = rng.getrandbits(64)
                beats.append((data, keep, last))
        await run_beats(
            dut,
            beats,
            lambda cycle: ((cycle + seed) % 5 != 0),
            lambda cycle: ((cycle + seed) % 7 != 0),
        )
