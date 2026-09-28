import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer


FILTERED = 0
TRUNCATED = 1
EMPTY = 2


def frame(ethertype, payload=b"", length_override=None):
    header = bytes(range(0xA0, 0xAC)) + bytes((ethertype >> 8, ethertype & 0xFF))
    result = header + payload
    return result if length_override is None else result[:length_override]


async def reset_dut(dut):
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.reject_ready.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)


async def drive_frame(dut, data, out_pattern=lambda _: True, reject_pattern=lambda _: True,
                      max_cycles=5000):
    received = []
    rejections = []
    index = 0
    held = None
    stalled_payload = None
    stalled_reject = None
    for cycle in range(max_cycles):
        await FallingEdge(dut.clk)
        dut.out_ready.value = int(out_pattern(cycle))
        dut.reject_ready.value = int(reject_pattern(cycle))
        if held is None and index < len(data):
            held = (data[index], index == len(data) - 1)
            dut.in_data.value = held[0]
            dut.in_last.value = int(held[1])
            dut.in_valid.value = 1
        await Timer(1, unit="ns")
        await ReadOnly()
        if stalled_payload is not None:
            assert (int(dut.out_valid.value), int(dut.out_data.value), int(dut.out_last.value)) == stalled_payload
        if stalled_reject is not None:
            assert (int(dut.reject_valid.value), int(dut.reject_fatal.value), int(dut.reject_code.value)) == stalled_reject
            assert int(dut.in_ready.value) == 0
        stalled_payload = None
        stalled_reject = None
        in_fire = int(dut.in_valid.value) and int(dut.in_ready.value)
        out_fire = int(dut.out_valid.value) and int(dut.out_ready.value)
        reject_fire = int(dut.reject_valid.value) and int(dut.reject_ready.value)
        final_out = out_fire and int(dut.out_last.value)
        if out_fire:
            received.append((int(dut.out_data.value), int(dut.out_last.value)))
        if reject_fire:
            rejections.append((int(dut.reject_fatal.value), int(dut.reject_code.value)))
        if int(dut.out_valid.value) and not int(dut.out_ready.value):
            stalled_payload = (1, int(dut.out_data.value), int(dut.out_last.value))
        if int(dut.reject_valid.value) and not int(dut.reject_ready.value):
            stalled_reject = (1, int(dut.reject_fatal.value), int(dut.reject_code.value))
        await RisingEdge(dut.clk)
        if in_fire:
            index += 1
            held = None
            dut.in_valid.value = 0
        if reject_fire or final_out:
            await FallingEdge(dut.clk)
            return received, rejections
        await Timer(1, unit="ns")
        await ReadOnly()
        if index == len(data) and not int(dut.out_valid.value) and not int(dut.reject_valid.value):
            if len(received) or len(data) == 0:
                await FallingEdge(dut.clk)
                return received, rejections
    raise AssertionError(f"timeout input={index}/{len(data)} out={received} rej={rejections}")


def expected_payload(raw):
    return [(byte, int(index == len(raw[14:]) - 1)) for index, byte in enumerate(raw[14:])]


@cocotb.test()
async def test_valid_and_endian_filter(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    raw = frame(0x0800, b"IPv4-PAYLOAD")
    received, rejected = await drive_frame(dut, raw, lambda c: c % 4 != 1)
    assert received == expected_payload(raw)
    assert rejected == []
    for ether, code in ((0x0806, FILTERED), (0x8100, FILTERED), (0x86DD, FILTERED),
                        (0x1234, FILTERED), (0x0008, FILTERED)):
        received, rejected = await drive_frame(dut, frame(ether, b"ignored"),
                                                reject_pattern=lambda c: c > 3)
        assert received == []
        assert rejected == [(0, code)]


@cocotb.test()
async def test_truncation_empty_and_minimal_payload(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    for length in range(1, 14):
        received, rejected = await drive_frame(dut, frame(0x0800, b"x", length_override=length))
        assert received == []
        assert rejected == [(1, TRUNCATED)]
    received, rejected = await drive_frame(dut, frame(0x0800, b""))
    assert received == [] and rejected == [(1, EMPTY)]
    raw = frame(0x0800, b"Z")
    received, rejected = await drive_frame(dut, raw)
    assert received == [(ord("Z"), 1)] and rejected == []


@cocotb.test()
async def test_rejection_stability_and_back_to_back(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    received, rejected = await drive_frame(dut, frame(0x8100, b"discard"),
                                            reject_pattern=lambda c: c >= 5)
    assert received == [] and rejected == [(0, FILTERED)]
    raw = frame(0x0800, b"AB")
    received, rejected = await drive_frame(dut, raw, out_pattern=lambda c: c != 2)
    assert received == expected_payload(raw) and rejected == []


@cocotb.test()
async def test_deterministic_random_frames(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    for seed in (1, 7, 19):
        await reset_dut(dut)
        rng = random.Random(seed)
        for _ in range(10):
            ether = rng.choice((0x0800, 0x8100, 0x0806, 0x1234))
            payload = bytes(rng.getrandbits(8) for _ in range(rng.randint(1, 24)))
            raw = frame(ether, payload)
            received, rejected = await drive_frame(
                dut, raw,
                out_pattern=lambda cycle, seed=seed: (cycle + seed) % 5 != 0,
                reject_pattern=lambda cycle, seed=seed: (cycle + seed) % 7 != 0,
            )
            if ether == 0x0800:
                assert received == expected_payload(raw) and rejected == []
            else:
                assert received == [] and rejected == [(0, FILTERED)]
