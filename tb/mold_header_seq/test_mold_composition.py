import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge, Timer

DEST_IP = 0xC6336407
DEST_PORT = 0x1234
SESSION = bytes([0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A])


def checksum(data):
    total = 0
    for i in range(0, len(data), 2):
        total += int.from_bytes(data[i:i + 2], "big")
        total = (total & 0xffff) + (total >> 16)
    while total >> 16:
        total = (total & 0xffff) + (total >> 16)
    return (~total) & 0xffff


def packet(session, sequence, count, body=b""):
    mold = session + sequence.to_bytes(8, "big") + count.to_bytes(2, "big") + body
    udp = (0xCAFE).to_bytes(2, "big") + DEST_PORT.to_bytes(2, "big")
    udp += (8 + len(mold)).to_bytes(2, "big") + b"\x00\x00" + mold
    ip = bytearray(20)
    ip[0] = 0x45
    ip[2:4] = (20 + len(udp)).to_bytes(2, "big")
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
        result.append((sum(x << (8 * i) for i, x in enumerate(chunk)),
                       (1 << len(chunk)) - 1,
                       int(start + len(chunk) == len(data))))
    return result


async def reset(dut):
    dut.rst.value = 1
    dut.rearm.value = 0
    dut.in_valid.value = 0
    dut.packet_ready.value = 1
    dut.mold_out_ready.value = 1
    dut.packet_result_valid.value = 0
    dut.packet_result_success.value = 0
    dut.mold_reject_ready.value = 1
    dut.eth_reject_ready.value = 1
    dut.ipv4_reject_ready.value = 1
    dut.udp_reject_ready.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0


async def send(dut, data, expect_body=b"", expect_packet=None, expect_reject=None):
    q = beats(data)
    index = 0
    held = None
    body = bytearray()
    packet_meta = []
    rejects = []
    for cycle in range(1600):
        await FallingEdge(dut.clk)
        dut.mold_out_ready.value = int(cycle % 11 != 4)
        dut.udp_reject_ready.value = 1
        if held is None and index < len(q):
            held = q[index]
        if held is not None:
            dut.in_valid.value, dut.in_data.value, dut.in_keep.value, dut.in_last.value = 1, held[0], held[1], held[2]
        else:
            dut.in_valid.value = 0
        await Timer(1, unit="ns")
        await ReadOnly()
        in_fire = held is not None and int(dut.in_ready.value)
        if int(dut.packet_valid.value) and int(dut.packet_ready.value):
            packet_meta.append((int(dut.packet_sequence.value), int(dut.packet_message_count.value), int(dut.packet_body_empty.value)))
        out_fire = int(dut.mold_out_valid.value) and int(dut.mold_out_ready.value)
        if out_fire:
            body.append(int(dut.mold_out_data.value))
        reject_fire = int(dut.mold_reject_valid.value) and int(dut.mold_reject_ready.value)
        if reject_fire:
            rejects.append((int(dut.mold_reject_fatal.value), int(dut.mold_reject_code.value)))
        await RisingEdge(dut.clk)
        if in_fire:
            index += 1
            held = None
        body_done = len(body) >= len(expect_body)
        if index == len(q) and body_done and (packet_meta or rejects or (not expect_packet and not expect_reject)):
            if not int(dut.mold_out_valid.value) and not int(dut.mold_reject_valid.value) and not int(dut.packet_valid.value):
                break
    else:
        raise AssertionError("six-stage composition did not drain")
    assert bytes(body) == expect_body
    assert packet_meta == ([] if expect_packet is None else [expect_packet])
    assert rejects == ([] if expect_reject is None else [expect_reject])


async def commit(dut, success=True):
    await FallingEdge(dut.clk)
    dut.packet_result_valid.value = 1
    dut.packet_result_success.value = int(success)
    await Timer(1, unit="ns")
    ready = int(dut.packet_result_ready.value)
    await RisingEdge(dut.clk)
    assert ready == 1
    await FallingEdge(dut.clk)
    dut.packet_result_valid.value = 0


@cocotb.test()
async def test_six_stage_normal_and_heartbeat(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.cfg_destination_ipv4.value = DEST_IP
    dut.cfg_destination_udp_port.value = DEST_PORT
    dut.cfg_active_session.value = int.from_bytes(SESSION, "big")
    dut.cfg_expected_sequence.value = 100
    await reset(dut)
    raw = b"RAW-MSG-BLOCK"
    await send(dut, packet(SESSION, 100, 2, raw), raw, (100, 2, 0), None)
    await commit(dut, True)
    assert int(dut.current_expected_sequence.value) == 102
    dut.cfg_expected_sequence.value = 102
    await reset(dut)
    await send(dut, packet(SESSION, 102, 0), b"", None, None)
    assert int(dut.current_expected_sequence.value) == 102


@cocotb.test()
async def test_six_stage_mold_errors_are_local(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.cfg_destination_ipv4.value = DEST_IP
    dut.cfg_destination_udp_port.value = DEST_PORT
    dut.cfg_active_session.value = int.from_bytes(SESSION, "big")
    dut.cfg_expected_sequence.value = 100
    await reset(dut)
    wrong = bytes([0x51 + i for i in range(10)])
    await send(dut, packet(wrong, 100, 1, b"x"), b"", None, (1, 1))
