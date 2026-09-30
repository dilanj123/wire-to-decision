import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

DEST_IP = 0xC6336407
DEST_PORT = 0x1234
SESSION = bytes.fromhex("4142434445464748494a")


def checksum(data):
    total = sum(int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2))
    while total >> 16:
        total = (total & 0xffff) + (total >> 16)
    return (~total) & 0xffff


def block(messages):
    return b"".join(len(m).to_bytes(2, "big") + m for m in messages)


def ethernet_ipv4_udp_mold(sequence, count, mold_body):
    mold = SESSION + sequence.to_bytes(8, "big") + count.to_bytes(2, "big") + mold_body
    udp = (0xCAFE).to_bytes(2, "big") + DEST_PORT.to_bytes(2, "big")
    udp += (8 + len(mold)).to_bytes(2, "big") + b"\0\0" + mold
    ip = bytearray(20)
    ip[0] = 0x45
    ip[2:4] = (20 + len(udp)).to_bytes(2, "big")
    ip[6:8] = (0x4000).to_bytes(2, "big")
    ip[8], ip[9] = 64, 17
    ip[12:16] = bytes.fromhex("c0000201")
    ip[16:20] = DEST_IP.to_bytes(4, "big")
    ip[10:12] = checksum(bytes(ip)).to_bytes(2, "big")
    return bytes.fromhex("00112233445566778899aabb0800") + bytes(ip) + udp


def beats(frame):
    out = []
    for start in range(0, len(frame), 8):
        chunk = frame[start:start + 8]
        out.append((sum(byte << (8 * i) for i, byte in enumerate(chunk)),
                    (1 << len(chunk)) - 1, int(start + len(chunk) == len(frame))))
    return out


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.cfg_destination_ipv4.value = DEST_IP
    dut.cfg_destination_udp_port.value = DEST_PORT
    dut.cfg_active_session.value = int.from_bytes(SESSION, "big")
    dut.cfg_expected_sequence.value = 0xFFFFFFFFFFFFFFFE
    for name in ("in_valid", "in_data", "in_keep", "in_last", "rearm"):
        getattr(dut, name).value = 0
    dut.message_ready.value = 1
    dut.out_ready.value = 1
    dut.framer_reject_ready.value = 1
    dut.mold_reject_ready.value = 1
    dut.eth_reject_ready.value = 1
    dut.ipv4_reject_ready.value = 1
    dut.udp_reject_ready.value = 1
    dut.rst.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0


async def run_frame(dut, frame, max_cycles=5000):
    q = beats(frame)
    idx = 0
    held = None
    metas, payload, result, rejects = [], [], [], []
    for cycle in range(max_cycles):
        await FallingEdge(dut.clk)
        if held is None and idx < len(q):
            held = q[idx]
        dut.in_valid.value = int(held is not None)
        if held is not None:
            dut.in_data.value, dut.in_keep.value, dut.in_last.value = held
        dut.out_ready.value = int(cycle % 9 not in (2, 3))
        await Timer(1, unit="ns")
        in_fire = held is not None and int(dut.in_ready.value)
        if int(dut.message_valid.value) and int(dut.message_ready.value):
            metas.append((int(dut.message_sequence.value), int(dut.message_length.value),
                          int(dut.message_empty.value)))
        if int(dut.out_valid.value) and int(dut.out_ready.value):
            payload.append((int(dut.out_data.value), int(dut.out_last.value)))
        if int(dut.packet_result_valid.value) and int(dut.packet_result_ready.value):
            result.append(int(dut.packet_result_success.value))
        if int(dut.framer_reject_valid.value) and int(dut.framer_reject_ready.value):
            rejects.append((int(dut.framer_reject_fatal.value), int(dut.framer_reject_code.value)))
        await RisingEdge(dut.clk)
        if in_fire:
            idx += 1
            held = None
        terminal = int(dut.recovery_required.value) or int(dut.current_expected_sequence.value) == 0
        if idx == len(q) and terminal and not int(dut.message_valid.value) and not int(dut.out_valid.value):
            # Let terminal status/recovery settle for one more edge.
            for _ in range(3):
                await FallingEdge(dut.clk)
                await RisingEdge(dut.clk)
            break
    else:
        raise AssertionError("seven-stage composition timed out")
    assert idx == len(q)
    return metas, payload, result, rejects


@cocotb.test()
async def test_seven_stage_valid_packet_sequence_commit(dut):
    await setup(dut)
    messages = [b"\xaa\x55", b"\x10\x20\x30"]
    frame = ethernet_ipv4_udp_mold(0xFFFFFFFFFFFFFFFE, 2, block(messages))
    metas, payload, result, rejects = await run_frame(dut, frame)
    assert metas == [(0xFFFFFFFFFFFFFFFE, 2, 0), (0xFFFFFFFFFFFFFFFF, 3, 0)]
    assert payload == [(x, int(i == len(m) - 1)) for m in messages for i, x in enumerate(m)]
    assert result == [1] and rejects == []
    assert int(dut.current_expected_sequence.value) == 0
    assert int(dut.controller_valid.value) == 1


@cocotb.test()
async def test_late_malformed_suffix_retains_complete_prefix(dut):
    await setup(dut)
    prefix = block([b"A", b"BC"])
    # Third declared message has length 5 but only two payload bytes physically.
    body = prefix + b"\x00\x05xy"
    frame = ethernet_ipv4_udp_mold(0xFFFFFFFFFFFFFFFE, 3, body)
    metas, payload, result, rejects = await run_frame(dut, frame)
    assert metas == [(0xFFFFFFFFFFFFFFFE, 1, 0),
                     (0xFFFFFFFFFFFFFFFF, 2, 0), (0, 5, 0)]
    assert payload[:3] == [(ord("A"), 1), (ord("B"), 0), (ord("C"), 1)]
    assert all(last == 0 for _, last in payload[3:])
    assert result == [0] and rejects == [(1, 1)]
    assert int(dut.current_expected_sequence.value) == 0xFFFFFFFFFFFFFFFE
    assert int(dut.controller_valid.value) == 0
    assert int(dut.recovery_required.value) == 1
