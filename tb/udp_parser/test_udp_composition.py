import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer


DEST_IP = 0xC6336407
DEST_PORT = 0x1234


def checksum(data):
    total = 0
    for i in range(0, len(data), 2):
        total += int.from_bytes(data[i:i + 2], "big")
        total = (total & 0xFFFF) + (total >> 16)
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def frame(payload, *, destination=DEST_PORT, checksum_value=0, length=None,
          physical_extra=b""):
    udp_length = 8 + len(payload) if length is None else length
    udp = (0xCAFE).to_bytes(2, "big") + destination.to_bytes(2, "big")
    udp += udp_length.to_bytes(2, "big") + checksum_value.to_bytes(2, "big") + payload + physical_extra
    total = 20 + len(udp)
    ip = bytearray(20)
    ip[0] = 0x45
    ip[2:4] = total.to_bytes(2, "big")
    ip[6:8] = (0x4000).to_bytes(2, "big")
    ip[8] = 64
    ip[9] = 17
    ip[12:16] = (0xC0000201).to_bytes(4, "big")
    ip[16:20] = DEST_IP.to_bytes(4, "big")
    ip[10:12] = checksum(bytes(ip)).to_bytes(2, "big")
    eth = bytes.fromhex("00112233445566778899AABB0800")
    return eth + bytes(ip) + udp


def beats(data):
    result = []
    for start in range(0, len(data), 8):
        chunk = data[start:start + 8]
        value = sum(byte << (8 * lane) for lane, byte in enumerate(chunk))
        keep = (1 << len(chunk)) - 1
        result.append((value, keep, int(start + len(chunk) == len(data))))
    return result


async def reset(dut):
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.eth_reject_ready.value = 1
    dut.ipv4_reject_ready.value = 1
    dut.udp_reject_ready.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst.value = 0


async def send_frame(dut, data, expected, expected_reject=None, stalls=True):
    queue = beats(data)
    bi = 0
    observed = bytearray()
    rejection = None
    quiet = 0
    held = None
    terminal_seen = False
    for cycle in range(1200):
        await FallingEdge(dut.clk)
        out_ready = (not stalls) or (cycle % 7 != 2)
        dut.out_ready.value = int(out_ready)
        dut.udp_reject_ready.value = int(cycle % 5 != 3)
        if held is None and bi < len(queue):
            held = queue[bi]
            data_word, keep, last = held
            dut.in_valid.value = 1
            dut.in_data.value = data_word
            dut.in_keep.value = keep
            dut.in_last.value = last
        elif held is None:
            dut.in_valid.value = 0
            dut.in_data.value = 0
            dut.in_keep.value = 0
            dut.in_last.value = 0
        await Timer(1, unit="ns")
        await ReadOnly()
        in_fire = bi < len(queue) and int(dut.in_ready.value)
        out_fire = int(dut.out_valid.value) and out_ready
        reject_fire = int(dut.udp_reject_valid.value) and int(dut.udp_reject_ready.value)
        if out_fire:
            observed.append(int(dut.out_data.value))
            terminal_seen |= bool(int(dut.out_last.value))
        if reject_fire:
            rejection = (int(dut.udp_reject_fatal.value), int(dut.udp_reject_code.value))
            terminal_seen = True
        await RisingEdge(dut.clk)
        if in_fire:
            bi += 1
            held = None
            dut.in_valid.value = 0
        active = int(dut.out_valid.value) or int(dut.udp_reject_valid.value)
        if bi == len(queue) and terminal_seen and not active:
            quiet += 1
            if quiet >= 4:
                await FallingEdge(dut.clk)
                break
        else:
            quiet = 0
    else:
        raise AssertionError("composition frame did not drain")
    assert bytes(observed) == expected
    assert rejection == expected_reject


@cocotb.test()
async def test_five_stage_valid_path(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.cfg_destination_ipv4.value = DEST_IP
    dut.cfg_destination_udp_port.value = DEST_PORT
    await reset(dut)
    payload = b"MOLD-PAYLOAD"
    await send_frame(dut, frame(payload), payload)


@cocotb.test()
async def test_udp_invalid_paths_are_localized(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.cfg_destination_ipv4.value = DEST_IP
    dut.cfg_destination_udp_port.value = DEST_PORT
    cases = [
        (frame(b"x", destination=0x9999), b"", (0, 2)),
        (frame(b"x", checksum_value=1), b"", (0, 3)),
        # The IPv4 stage can emit a prefix before the UDP stage discovers
        # the late physical-short mismatch; WIRE-018 records that prefix as
        # speculative parser data and still requires the fatal rejection.
        (frame(b"1234", length=20), b"123", (1, 1)),
        (frame(b"1234", length=8, physical_extra=b"xx"), b"", (1, 1)),
    ]
    for packet, expected, rejection in cases:
        await reset(dut)
        await send_frame(dut, packet, expected, rejection)


@cocotb.test()
async def test_five_stage_random_valid_frames(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.cfg_destination_ipv4.value = DEST_IP
    dut.cfg_destination_udp_port.value = DEST_PORT
    for seed in (1, 7, 19):
        rng = random.Random(seed)
        for _ in range(8):
            payload = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 13)))
            await reset(dut)
            await send_frame(dut, frame(payload), payload)
