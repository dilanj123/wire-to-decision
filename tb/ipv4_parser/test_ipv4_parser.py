import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer


DEST = 0xC6336407
SRC = 0x0A0B0C0D
CODE = {
    "version": 0, "ihl": 1, "length": 2, "checksum": 3,
    "fragment": 4, "destination": 5, "protocol": 6,
    "header_truncated": 7, "empty": 8,
}


def checksum(data):
    if len(data) & 1:
        data += b"\0"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) | data[i + 1]
        total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def ipv4_packet(payload=b"PAYLOAD", *, version=4, ihl=5, destination=DEST,
                protocol=17, total_length=None, flags_fragment=0,
                corrupt_checksum=False):
    if total_length is None:
        total_length = 20 + len(payload)
    header = bytearray(20)
    header[0] = (version << 4) | ihl
    header[1] = 0x5A
    header[2:4] = total_length.to_bytes(2, "big")
    header[4:6] = (0x1234).to_bytes(2, "big")
    header[6:8] = flags_fragment.to_bytes(2, "big")
    header[8] = 64
    header[9] = protocol
    header[12:16] = SRC.to_bytes(4, "big")
    header[16:20] = destination.to_bytes(4, "big")
    header[10:12] = checksum(bytes(header)).to_bytes(2, "big")
    if corrupt_checksum:
        header[10] ^= 1
    return bytes(header) + payload


async def reset_dut(dut):
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.reject_ready.value = 1
    dut.cfg_destination_ipv4.value = DEST
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)


async def drive(dut, data, *, out_ready_fn=lambda c: 1,
                reject_ready_fn=lambda c: 1, max_cycles=10000):
    got = []
    rejects = []
    index = 0
    held = None
    stalled_out = None
    stalled_reject = None
    quiet = 0
    for cycle in range(max_cycles):
        await FallingEdge(dut.clk)
        dut.out_ready.value = int(out_ready_fn(cycle))
        dut.reject_ready.value = int(reject_ready_fn(cycle))
        if held is None and index < len(data):
            held = (data[index], index == len(data) - 1)
            dut.in_data.value = held[0]
            dut.in_last.value = int(held[1])
            dut.in_valid.value = 1
        await Timer(1, unit="ns")
        await ReadOnly()
        current_out = (int(dut.out_valid.value), int(dut.out_data.value), int(dut.out_last.value))
        current_reject = (int(dut.reject_valid.value), int(dut.reject_fatal.value), int(dut.reject_code.value))
        if stalled_out is not None:
            assert current_out == stalled_out
        if stalled_reject is not None:
            assert current_reject == stalled_reject
            assert int(dut.in_ready.value) == 0
        stalled_out = current_out if current_out[0] and not int(dut.out_ready.value) else None
        stalled_reject = current_reject if current_reject[0] and not int(dut.reject_ready.value) else None
        in_fire = int(dut.in_valid.value) and int(dut.in_ready.value)
        out_fire = int(dut.out_valid.value) and int(dut.out_ready.value)
        reject_fire = int(dut.reject_valid.value) and int(dut.reject_ready.value)
        if out_fire:
            got.append((int(dut.out_data.value), int(dut.out_last.value)))
        if reject_fire:
            rejects.append((int(dut.reject_fatal.value), int(dut.reject_code.value)))
        await RisingEdge(dut.clk)
        if in_fire:
            index += 1
            held = None
            dut.in_valid.value = 0
        if reject_fire:
            await FallingEdge(dut.clk)
            return got, rejects, index
        if index == len(data) and not int(dut.out_valid.value) and not int(dut.reject_valid.value):
            quiet += 1
            if quiet >= 3:
                await FallingEdge(dut.clk)
                return got, rejects, index
        else:
            quiet = 0
    raise AssertionError(f"timeout index={index}/{len(data)} got={got} rejects={rejects}")


def expected(data, declared_length):
    payload = data[20:declared_length]
    return [(b, i == len(payload) - 1) for i, b in enumerate(payload)]


@cocotb.test()
async def test_valid_checksum_length_and_padding(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    raw = ipv4_packet(b"0123456789AB") + b"PADPADPADPAD"
    got, rejects, index = await drive(dut, raw, out_ready_fn=lambda c: c % 5 != 2)
    assert index == len(raw)
    assert got == expected(raw, 32)
    assert rejects == []


@cocotb.test()
async def test_checksum_version_ihl_and_priority(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    cases = [
        (ipv4_packet(b"x", version=6, corrupt_checksum=True), (0, CODE["version"])),
        (ipv4_packet(b"x", ihl=4, corrupt_checksum=True), (0, CODE["ihl"])),
        (ipv4_packet(b"x", total_length=19, corrupt_checksum=True), (1, CODE["length"])),
        (ipv4_packet(b"x", destination=0x01020304, corrupt_checksum=True), (1, CODE["checksum"])),
        (ipv4_packet(b"x", flags_fragment=0x2000, destination=0x01020304), (1, CODE["fragment"])),
        (ipv4_packet(b"x", destination=0x01020304, protocol=6), (0, CODE["destination"])),
    ]
    for raw, expected_reject in cases:
        got, rejects, _ = await drive(dut, raw)
        assert got == []
        assert rejects == [expected_reject]


@cocotb.test()
async def test_truncation_empty_fragment_destination_protocol_and_df(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    for length in range(1, 20):
        raw = ipv4_packet(b"x")[:length]
        got, rejects, _ = await drive(dut, raw)
        assert got == [] and rejects == [(1, CODE["header_truncated"])]
    for total in (0, 1, 19):
        raw = ipv4_packet(b"x", total_length=total)
        got, rejects, _ = await drive(dut, raw)
        assert got == [] and rejects == [(1, CODE["length"])]
    raw = ipv4_packet(b"", total_length=20)
    got, rejects, _ = await drive(dut, raw)
    assert got == [] and rejects == [(1, CODE["empty"])]
    for flags in (0, 0x4000):
        raw = ipv4_packet(b"DF", flags_fragment=flags)
        got, rejects, _ = await drive(dut, raw)
        assert got == expected(raw, 22) and rejects == []
    for flags in (0x2000, 1, 0x2001):
        raw = ipv4_packet(b"x", flags_fragment=flags)
        got, rejects, _ = await drive(dut, raw)
        assert got == [] and rejects == [(1, CODE["fragment"])]
    for destination in (DEST, 0x01020304):
        raw = ipv4_packet(b"dst", destination=destination)
        got, rejects, _ = await drive(dut, raw)
        if destination == DEST:
            assert got == expected(raw, 23) and rejects == []
        else:
            assert got == [] and rejects == [(0, CODE["destination"])]
    for protocol in (17, 6, 1):
        raw = ipv4_packet(b"proto", protocol=protocol)
        got, rejects, _ = await drive(dut, raw)
        if protocol == 17:
            assert got == expected(raw, 25) and rejects == []
        else:
            assert got == [] and rejects == [(0, CODE["protocol"])]


@cocotb.test()
async def test_stall_rejection_and_back_to_back(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    raw = ipv4_packet(b"BACKPRESSURE")
    got, rejects, _ = await drive(dut, raw, out_ready_fn=lambda c: c % 4 != 1)
    assert got == expected(raw, len(raw)) and rejects == []
    bad = ipv4_packet(b"drop", destination=0x11111111)
    got, rejects, _ = await drive(dut, bad, reject_ready_fn=lambda c: c > 8)
    assert got == [] and rejects == [(0, CODE["destination"])]
    raw2 = ipv4_packet(b"NEXT")
    got, rejects, _ = await drive(dut, raw2)
    assert got == expected(raw2, len(raw2)) and rejects == []


@cocotb.test()
async def test_deterministic_random_cases(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    for seed in (1, 7, 19):
        await reset_dut(dut)
        rng = random.Random(seed)
        for _ in range(8):
            payload = bytes(rng.getrandbits(8) for _ in range(rng.randint(1, 20)))
            mode = rng.randrange(6)
            kwargs = {}
            expected_reject = None
            if mode == 1:
                kwargs["destination"] = 0x01020304
                expected_reject = (0, CODE["destination"])
            elif mode == 2:
                kwargs["protocol"] = 6
                expected_reject = (0, CODE["protocol"])
            elif mode == 3:
                kwargs["flags_fragment"] = 0x2000
                expected_reject = (1, CODE["fragment"])
            elif mode == 4:
                kwargs["corrupt_checksum"] = True
                expected_reject = (1, CODE["checksum"])
            raw = ipv4_packet(payload, **kwargs)
            got, rejects, _ = await drive(
                dut, raw,
                out_ready_fn=lambda c, s=seed: (c + s) % 5 != 0,
                reject_ready_fn=lambda c, s=seed: (c + s) % 7 != 0,
            )
            if expected_reject is None:
                assert got == expected(raw, len(raw)) and rejects == []
            else:
                assert got == [] and rejects == [expected_reject]
