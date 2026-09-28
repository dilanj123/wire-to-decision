import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


DEST_PORT = 0x1234


def udp_packet(source, destination, payload=b"", length=None, checksum=0, physical_extra=b""):
    declared = 8 + len(payload) if length is None else length
    return (
        source.to_bytes(2, "big")
        + destination.to_bytes(2, "big")
        + declared.to_bytes(2, "big")
        + checksum.to_bytes(2, "big")
        + payload
        + physical_extra
    )


async def reset(dut):
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.in_data.value = 0
    dut.in_last.value = 0
    dut.out_ready.value = 1
    dut.reject_ready.value = 1
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst.value = 0


async def run_packet(dut, packet, *, expect_payload=b"", expect_reject=None,
                     stall_output=False, stall_reject=False):
    observed = bytearray()
    rejection = None
    index = 0
    quiet = 0
    previous_stall = None
    for cycle in range(400):
        await Timer(1, units="ns")
        if previous_stall is not None:
            assert int(dut.out_valid.value) == 1
            assert int(dut.out_data.value) == previous_stall[0]
            assert int(dut.out_last.value) == previous_stall[1]
        output_ready = not stall_output or (cycle % 5 != 1)
        reject_ready = not stall_reject or (cycle % 4 != 2)
        dut.out_ready.value = int(output_ready)
        dut.reject_ready.value = int(reject_ready)
        sending = index < len(packet)
        dut.in_valid.value = int(sending)
        if sending:
            dut.in_data.value = packet[index]
            dut.in_last.value = int(index == len(packet) - 1)
        else:
            dut.in_data.value = 0
            dut.in_last.value = 0
        # Allow combinational ready/valid signals to settle after driving the
        # current transaction before sampling the public interface.
        await Timer(1, units="ns")
        in_fire = sending and int(dut.in_ready.value)
        out_fire = int(dut.out_valid.value) and output_ready
        reject_fire = int(dut.reject_valid.value) and reject_ready
        if int(dut.out_valid.value) and not output_ready:
            previous_stall = (int(dut.out_data.value), int(dut.out_last.value))
        else:
            previous_stall = None
        if out_fire:
            observed.append(int(dut.out_data.value))
            if int(dut.out_last.value):
                assert len(observed) == len(expect_payload)
        if reject_fire:
            rejection = (int(dut.reject_fatal.value), int(dut.reject_code.value))
        await RisingEdge(dut.clk)
        if in_fire:
            index += 1
        active = sending or int(dut.out_valid.value) or int(dut.reject_valid.value)
        quiet = 0 if active else quiet + 1
        if index == len(packet) and quiet >= 5 and not int(dut.reject_valid.value):
            break
    else:
        raise AssertionError("packet did not drain")
    assert bytes(observed) == expect_payload
    assert rejection == expect_reject


@cocotb.test()
async def test_valid_source_independence_and_endianness(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.cfg_destination_udp_port.value = DEST_PORT
    for source in (0x0102, 0xA1B2):
        await reset(dut)
        await run_packet(dut, udp_packet(source, DEST_PORT, b"UDP!"), expect_payload=b"UDP!")
    await reset(dut)
    await run_packet(dut, udp_packet(1, 0x3412, b"bad"), expect_reject=(0, 2))


@cocotb.test()
async def test_header_truncation_and_lower_length(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.cfg_destination_udp_port.value = DEST_PORT
    for length in range(1, 8):
        await reset(dut)
        await run_packet(dut, bytes(range(length)), expect_reject=(1, 0))
    for declared in (0, 1, 7):
        await reset(dut)
        await run_packet(dut, udp_packet(1, DEST_PORT, b"", length=declared), expect_reject=(1, 1))


@cocotb.test()
async def test_length_priority_and_filters(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.cfg_destination_udp_port.value = DEST_PORT
    cases = [
        (udp_packet(1, 0x9999, b"abcd", length=20), (1, 1)),
        (udp_packet(1, DEST_PORT, b"abcd", length=20, checksum=1), (1, 1)),
        (udp_packet(1, 0x9999, b"abcd", checksum=0x1234), (0, 2)),
        (udp_packet(1, DEST_PORT, b"abcd", checksum=0xFFFF), (0, 3)),
        (udp_packet(1, 0x9999, b"abcd", checksum=0x1234), (0, 2)),
        (udp_packet(1, DEST_PORT, b"", length=8), (1, 4)),
        (udp_packet(1, 0x9999, b"", length=8), (0, 2)),
        (udp_packet(1, DEST_PORT, b"", length=8, checksum=1), (0, 3)),
        (udp_packet(1, DEST_PORT, b"abcd", length=20), (1, 1, b"abc")),
        (udp_packet(1, DEST_PORT, b"abcd", length=8, physical_extra=b"xx"), (1, 1)),
    ]
    for packet, expected in cases:
        await reset(dut)
        if len(expected) == 3:
            reject = expected[:2]
            payload = expected[2]
        else:
            reject = expected
            payload = b""
        await run_packet(dut, packet, expect_payload=payload, expect_reject=reject)


@cocotb.test()
async def test_stalls_and_back_to_back(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.cfg_destination_udp_port.value = DEST_PORT
    await reset(dut)
    await run_packet(dut, udp_packet(1, DEST_PORT, b"0123456789"), expect_payload=b"0123456789", stall_output=True)
    await run_packet(dut, udp_packet(2, 0x9999, b"x"), expect_reject=(0, 2), stall_reject=True)
    await run_packet(dut, udp_packet(3, DEST_PORT, b"ok"), expect_payload=b"ok")


@cocotb.test()
async def test_deterministic_random_cases(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.cfg_destination_udp_port.value = DEST_PORT
    for seed in (1, 7, 19):
        rng = random.Random(seed)
        for _ in range(12):
            payload = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 9)))
            destination = DEST_PORT if rng.randrange(3) else rng.randrange(65536)
            checksum = 0 if rng.randrange(3) else rng.choice((1, 0x1234, 0xFFFF))
            packet = udp_packet(rng.randrange(65536), destination, payload, checksum=checksum)
            expected_payload = payload if destination == DEST_PORT and checksum == 0 else b""
            expected = None if expected_payload else (0, 2 if destination != DEST_PORT else 3)
            await reset(dut)
            await run_packet(dut, packet, expect_payload=expected_payload, expect_reject=expected,
                             stall_output=True, stall_reject=True)
