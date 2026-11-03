import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

SEQ = 0x1020304050607080
SESSION = b"W2DTEST001"


def checksum(data):
    if len(data) & 1:
        data += b"\x00"
    total = sum(int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def put(buf, off, width, value):
    buf[off:off + width] = value.to_bytes(width, "big")


def add_itch(ref, qty, price, side, salt):
    msg = bytearray(36)
    msg[0] = ord("A")
    put(msg, 1, 2, 0x2345)
    put(msg, 3, 2, 0xA100 + salt)
    put(msg, 5, 6, 0x010203040500 + salt)
    put(msg, 11, 8, ref)
    msg[19] = side
    put(msg, 20, 4, qty)
    msg[24:32] = b"ALPH    "
    put(msg, 32, 4, price)
    return bytes(msg)


def make_frame(msg, sequence):
    mold = SESSION + sequence.to_bytes(8, "big") + b"\x00\x01" + len(msg).to_bytes(2, "big") + msg
    udp = bytearray(8)
    put(udp, 0, 2, 0xBEEF)
    put(udp, 2, 2, 0x1234)
    put(udp, 4, 2, 8 + len(mold))
    ip_payload = bytes(udp) + mold
    ip = bytearray(20)
    ip[0] = 0x45
    put(ip, 2, 2, 20 + len(ip_payload))
    ip[8], ip[9] = 64, 17
    put(ip, 16, 4, 0xC6336407)
    put(ip, 10, 2, checksum(bytes(ip)))
    eth = bytes.fromhex("0201020304050A0B0C0D0E0F") + b"\x08\x00"
    return eth + bytes(ip) + ip_payload


def pack_beats(packet):
    beats = []
    for offset in range(0, len(packet), 8):
        chunk = packet[offset:offset + 8]
        data = sum(value << (8 * lane) for lane, value in enumerate(chunk))
        beats.append((data, (1 << len(chunk)) - 1, int(offset + len(chunk) == len(packet))))
    return beats


def decode(words):
    assert len(words) == 6 and words[-1][1]
    seq = (words[0][0] << 32) | words[1][0]
    action = (words[2][0] >> 16) & 1
    timestamp = ((words[2][0] & 0xFFFF) << 32) | words[3][0]
    raw_imbalance = (words[4][0] << 17) | (words[5][0] & 0x1FFFF)
    imbalance = raw_imbalance - (1 << 49) if raw_imbalance & (1 << 48) else raw_imbalance
    return action, seq, timestamp, imbalance


async def send_one(dut, side, packet):
    beats = pack_beats(packet)
    index = 0
    decision = None
    words = []
    accepted = 0
    for _ in range(12000):
        await FallingEdge(dut.clk)
        if index < len(beats):
            data, keep, last = beats[index]
            if side == "wrap":
                dut.wrap_rx_data.value, dut.wrap_rx_keep.value = data, keep
                dut.wrap_rx_last.value, dut.wrap_rx_valid.value = last, 1
            else:
                dut.ref_rx_data.value, dut.ref_rx_keep.value = data, keep
                dut.ref_rx_last.value, dut.ref_rx_valid.value = last, 1
        else:
            if side == "wrap": dut.wrap_rx_valid.value = 0
            else: dut.ref_rx_valid.value = 0
        await Timer(1, unit="ns")
        if side == "wrap":
            fire = index < len(beats) and int(dut.wrap_rx_ready.value)
            if int(dut.readout_valid.value) and int(dut.readout_ready.value):
                words.append((int(dut.readout_data.value), int(dut.readout_last.value)))
        else:
            fire = index < len(beats) and int(dut.ref_rx_ready.value)
            if int(dut.ref_decision_valid.value) and int(dut.ref_decision_ready.value):
                decision = (int(dut.ref_decision_action.value),
                            int(dut.ref_decision_sequence.value),
                            int(dut.ref_decision_timestamp.value),
                            dut.ref_decision_imbalance.value.to_signed())
        await RisingEdge(dut.clk)
        if fire:
            index += 1
            accepted += 1
        if index == len(beats) and ((side == "wrap" and words and words[-1][1]) or
                                    (side == "ref" and decision is not None)):
            return decode(words) if side == "wrap" else decision
    raise AssertionError(f"timeout sending {side} frame accepted={accepted}/{len(beats)} words={len(words)} ref_decision={decision} recovery={int(dut.ref_parser_recovery.value)} stage={int(dut.ref_recovery_stage.value)} reject={int(dut.ref_stage_reject.value)} fatal={int(dut.ref_stage_reject_fatal.value)} code={int(dut.ref_stage_reject_code.value)}")


@cocotb.test()
async def wrapper_reconstructs_complete_functional_top_decisions(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst.value = 1
    dut.rearm.value = 0
    dut.wrap_rx_valid.value = 0
    dut.ref_rx_valid.value = 0
    dut.readout_ready.value = 1
    dut.ref_decision_ready.value = 1
    for _ in range(3):
        await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    dut.rst.value = 0

    vectors = [
        (add_itch(0x1001, 10, 0x10203040, ord("B"), 1), SEQ,
         (0, SEQ, 0x010203040501, 10)),
        (add_itch(0x1002, 20, 0x50607080, ord("S"), 2), SEQ + 1,
         (1, SEQ + 1, 0x010203040502, -10)),
    ]
    for msg, sequence, hand_result in vectors:
        packet = make_frame(msg, sequence)
        reference_tuple = await send_one(dut, "ref", packet)
        wrapper_tuple = await send_one(dut, "wrap", packet)
        assert wrapper_tuple == reference_tuple == hand_result
