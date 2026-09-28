import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

from test_ipv4_parser import DEST, CODE, ipv4_packet


def ethernet_ipv4(ip_bytes, ethertype=0x0800):
    return bytes(range(0xA0, 0xAC)) + ethertype.to_bytes(2, "big") + ip_bytes


def pack_beats(data):
    beats = []
    for start in range(0, len(data), 8):
        chunk = data[start:start + 8]
        word = sum(byte << (8 * lane) for lane, byte in enumerate(chunk))
        keep = (1 << len(chunk)) - 1
        beats.append((word, keep, len(start.to_bytes(1, "big")) and start + len(chunk) == len(data)))
    return beats


async def reset_dut(dut):
    await FallingEdge(dut.clk)
    dut.rst.value = 1
    dut.in_valid.value = 0
    dut.out_ready.value = 1
    dut.eth_reject_ready.value = 1
    dut.ipv4_reject_ready.value = 1
    dut.cfg_destination_ipv4.value = DEST
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await FallingEdge(dut.clk)


async def drive(dut, beats, *, out_ready_fn=lambda c: 1, max_cycles=30000):
    outputs = []
    eth_rejects = []
    ip_rejects = []
    index = 0
    held = None
    quiet = 0
    terminal_seen = False
    for cycle in range(max_cycles):
        await FallingEdge(dut.clk)
        dut.out_ready.value = int(out_ready_fn(cycle))
        dut.eth_reject_ready.value = 1
        dut.ipv4_reject_ready.value = 1
        if held is None and index < len(beats):
            held = beats[index]
            dut.in_data.value = held[0]
            dut.in_keep.value = held[1]
            dut.in_last.value = int(held[2])
            dut.in_valid.value = 1
        await Timer(1, unit="ns")
        await ReadOnly()
        in_fire = int(dut.in_valid.value) and int(dut.in_ready.value)
        out_fire = int(dut.out_valid.value) and int(dut.out_ready.value)
        eth_fire = int(dut.eth_reject_valid.value) and int(dut.eth_reject_ready.value)
        ip_fire = int(dut.ipv4_reject_valid.value) and int(dut.ipv4_reject_ready.value)
        if out_fire:
            outputs.append((int(dut.out_data.value), int(dut.out_last.value)))
            terminal_seen |= bool(int(dut.out_last.value))
        if eth_fire:
            eth_rejects.append((int(dut.eth_reject_fatal.value), int(dut.eth_reject_code.value)))
            terminal_seen = True
        if ip_fire:
            ip_rejects.append((int(dut.ipv4_reject_fatal.value), int(dut.ipv4_reject_code.value)))
            terminal_seen = True
        await RisingEdge(dut.clk)
        if in_fire:
            index += 1
            held = None
            dut.in_valid.value = 0
        active = int(dut.out_valid.value) or int(dut.eth_reject_valid.value) or int(dut.ipv4_reject_valid.value)
        if index == len(beats) and terminal_seen and not active:
            quiet += 1
            if quiet >= 4:
                await FallingEdge(dut.clk)
                return outputs, eth_rejects, ip_rejects
        else:
            quiet = 0
    raise AssertionError(f"timeout beats={index}/{len(beats)} outputs={outputs} ip={ip_rejects} eth={eth_rejects}")


def expected_payload(ip):
    return [(byte, i == len(ip[20:]) - 1) for i, byte in enumerate(ip[20:])]


@cocotb.test()
async def test_buffer_gearbox_eth_ipv4_accepted_and_padding(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    ip = ipv4_packet(b"UDP-DATA-012")
    raw = ethernet_ipv4(ip + b"ETHERNETPAD")
    outputs, eth_rejects, ip_rejects = await drive(dut, pack_beats(raw), out_ready_fn=lambda c: c % 6 != 2)
    assert outputs == expected_payload(ip)
    assert eth_rejects == [] and ip_rejects == []


@cocotb.test()
async def test_composition_filters_and_fatals(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    await reset_dut(dut)
    cases = [
        (ethernet_ipv4(ipv4_packet(b"x", destination=0x01020304)), (0, CODE["destination"])),
        (ethernet_ipv4(ipv4_packet(b"x", corrupt_checksum=True)), (1, CODE["checksum"])),
        (ethernet_ipv4(ipv4_packet(b"x", flags_fragment=0x2000)), (1, CODE["fragment"])),
        (ethernet_ipv4(ipv4_packet(b"x" * 15, total_length=40)), (1, CODE["length"])),
    ]
    for case_index, (raw, expected_reject) in enumerate(cases):
        outputs, eth_rejects, ip_rejects = await drive(dut, pack_beats(raw))
        if case_index == 3:
            assert outputs == [(ord("x"), 0)] * 14, (len(outputs), outputs, ip_rejects)
        else:
            assert outputs == [], (case_index, outputs, eth_rejects, ip_rejects)
        assert eth_rejects == [] and ip_rejects == [expected_reject]
    filtered = ethernet_ipv4(ipv4_packet(b"x"), ethertype=0x8100)
    outputs, eth_rejects, ip_rejects = await drive(dut, pack_beats(filtered))
    assert outputs == [] and eth_rejects == [(0, 0)] and ip_rejects == []


@cocotb.test()
async def test_composition_random_frames(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    for seed in (1, 7, 19):
        await reset_dut(dut)
        rng = random.Random(seed)
        for _ in range(4):
            payload = bytes(rng.getrandbits(8) for _ in range(rng.randint(1, 18)))
            ip = ipv4_packet(payload)
            raw = ethernet_ipv4(ip)
            outputs, eth_rejects, ip_rejects = await drive(
                dut, pack_beats(raw), out_ready_fn=lambda c, s=seed: (c + s) % 7 != 0)
            assert outputs == expected_payload(ip)
            assert eth_rejects == [] and ip_rejects == []
