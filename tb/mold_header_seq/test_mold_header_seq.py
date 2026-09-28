import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly, Timer

SESSION = bytes([0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A])
OTHER_SESSION = bytes([0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A])


def mold(session, sequence, count, body=b""):
    return session + sequence.to_bytes(8, "big") + count.to_bytes(2, "big") + body


class MoldTB:
    def __init__(self, dut):
        self.dut = dut
        self.packets = []
        self.body = []
        self.rejects = []

    async def start(self):
        cocotb.start_soon(Clock(self.dut.clk, 10, units="ns").start())
        self.dut.cfg_active_session.value = int.from_bytes(SESSION, "big")
        self.dut.cfg_expected_sequence.value = 100
        self.dut.rearm.value = 0
        self.dut.in_valid.value = 0
        self.dut.in_data.value = 0
        self.dut.in_last.value = 0
        self.dut.packet_ready.value = 1
        self.dut.out_ready.value = 1
        self.dut.packet_result_valid.value = 0
        self.dut.packet_result_success.value = 0
        self.dut.reject_ready.value = 1
        self.dut.rst.value = 1
        await RisingEdge(self.dut.clk)
        await ReadOnly()
        await FallingEdge(self.dut.clk)
        self.dut.rst.value = 0

    async def observe(self):
        await ReadOnly()
        if int(self.dut.packet_valid.value) and int(self.dut.packet_ready.value):
            self.packets.append((int(self.dut.packet_sequence.value),
                                 int(self.dut.packet_message_count.value),
                                 int(self.dut.packet_body_empty.value)))
        if int(self.dut.out_valid.value) and int(self.dut.out_ready.value):
            self.body.append((int(self.dut.out_data.value), int(self.dut.out_last.value)))
        if int(self.dut.reject_valid.value) and int(self.dut.reject_ready.value):
            self.rejects.append((int(self.dut.reject_fatal.value), int(self.dut.reject_code.value)))

    async def cycle(self):
        await RisingEdge(self.dut.clk)
        await self.observe()

    async def send(self, data, final_last=True):
        for i, byte in enumerate(data):
            loops = 0
            while True:
                loops += 1
                if loops > 100:
                    raise AssertionError(f"input byte {i} did not transfer; ready={int(self.dut.in_ready.value)}")
                await FallingEdge(self.dut.clk)
                self.dut.in_valid.value = 1
                self.dut.in_data.value = byte
                self.dut.in_last.value = int(final_last and i == len(data) - 1)
                await Timer(1, unit="ns")
                accepted = int(self.dut.in_ready.value)
                await RisingEdge(self.dut.clk)
                await self.observe()
                if accepted:
                    break
        await FallingEdge(self.dut.clk)
        self.dut.in_valid.value = 0
        self.dut.in_last.value = 0

    async def wait_cycles(self, n=4):
        for _ in range(n):
            await self.cycle()

    async def result(self, success):
        while True:
            await FallingEdge(self.dut.clk)
            self.dut.packet_result_valid.value = 1
            self.dut.packet_result_success.value = int(success)
            await Timer(1, unit="ns")
            accepted = int(self.dut.packet_result_ready.value)
            await RisingEdge(self.dut.clk)
            await self.observe()
            if accepted:
                break
        await FallingEdge(self.dut.clk)
        self.dut.packet_result_valid.value = 0

    async def rearm_now(self):
        await FallingEdge(self.dut.clk)
        self.dut.rearm.value = 1
        await RisingEdge(self.dut.clk)
        await self.observe()
        await FallingEdge(self.dut.clk)
        self.dut.rearm.value = 0


@cocotb.test()
async def test_normal_metadata_body_and_deferred_commit(dut):
    tb = MoldTB(dut)
    await tb.start()
    body = bytes([0xD1, 0xE2, 0xF3])
    await tb.send(mold(SESSION, 100, 2, body))
    await tb.wait_cycles(2)
    assert tb.packets == [(100, 2, 0)]
    assert tb.body == [(x, i == len(body) - 1) for i, x in enumerate(body)]
    assert int(dut.current_expected_sequence.value) == 100
    await tb.result(True)
    await tb.wait_cycles(1)
    assert int(dut.current_expected_sequence.value) == 102
    assert int(dut.controller_valid.value) == 1


@cocotb.test()
async def test_empty_normal_body_failed_result_and_rearm(dut):
    tb = MoldTB(dut)
    await tb.start()
    await tb.send(mold(SESSION, 100, 1))
    await tb.wait_cycles(2)
    assert tb.packets == [(100, 1, 1)]
    assert tb.body == []
    await tb.result(False)
    await tb.wait_cycles(1)
    assert int(dut.recovery_required.value) == 1
    assert int(dut.current_expected_sequence.value) == 100
    await FallingEdge(dut.clk)
    dut.cfg_active_session.value = int.from_bytes(OTHER_SESSION, "big")
    dut.cfg_expected_sequence.value = 900
    await tb.rearm_now()
    await tb.send(mold(OTHER_SESSION, 900, 1, b"Z"))
    await tb.wait_cycles(2)
    assert tb.packets[-1] == (900, 1, 0)


@cocotb.test()
async def test_heartbeat_and_sequence_wrap(dut):
    tb = MoldTB(dut)
    await tb.start()
    await tb.send(mold(SESSION, 100, 0))
    await tb.wait_cycles(1)
    assert tb.packets == [] and tb.rejects == []
    await tb.send(mold(SESSION, 100, 1, b"Q"))
    await tb.wait_cycles(1)
    assert tb.packets[-1] == (100, 1, 0)
    await tb.result(True)
    await FallingEdge(dut.clk)
    dut.cfg_expected_sequence.value = 0xFFFFFFFFFFFFFFFE
    await tb.rearm_now()
    await tb.send(mold(SESSION, 0xFFFFFFFFFFFFFFFE, 2, b"XY"))
    await tb.wait_cycles(1)
    await tb.result(True)
    assert int(dut.current_expected_sequence.value) == 0


@cocotb.test()
async def test_heartbeat_and_eos_trailing_precedence(dut):
    tb = MoldTB(dut)
    await tb.start()
    await tb.send(mold(SESSION, 100, 0, b"X"))
    await tb.wait_cycles(1)
    assert tb.rejects[-1] == (1, 3)
    assert int(dut.recovery_required.value) == 1
    await tb.rearm_now()
    await tb.send(mold(SESSION, 100, 0xFFFF, b"Y"))
    await tb.wait_cycles(1)
    assert tb.rejects[-1] == (1, 3)


@cocotb.test()
async def test_eos_exact_and_recovery_blocks_input(dut):
    tb = MoldTB(dut)
    await tb.start()
    await tb.send(mold(SESSION, 100, 0xFFFF))
    await tb.wait_cycles(1)
    assert tb.rejects[-1] == (1, 4)
    assert int(dut.in_ready.value) == 0
    await tb.rearm_now()
    assert int(dut.recovery_required.value) == 0


@cocotb.test()
async def test_session_sequence_priority_and_drop(dut):
    tb = MoldTB(dut)
    await tb.start()
    await tb.send(mold(OTHER_SESSION, 999, 1, b"DROP"))
    await tb.wait_cycles(1)
    assert tb.rejects[-1] == (1, 1)
    await tb.rearm_now()
    await tb.send(mold(SESSION, 999, 1, b"DROP"))
    await tb.wait_cycles(1)
    assert tb.rejects[-1] == (1, 2)


@cocotb.test()
async def test_header_truncation_and_reject_stall(dut):
    tb = MoldTB(dut)
    await tb.start()
    await FallingEdge(dut.clk)
    dut.reject_ready.value = 0
    await tb.send(bytes([0xA0, 0xB1, 0xC2]))
    await tb.wait_cycles(2)
    assert int(dut.reject_valid.value) == 1
    assert int(dut.reject_code.value) == 0
    assert int(dut.in_ready.value) == 0
    assert int(dut.controller_valid.value) == 0
    await FallingEdge(dut.clk)
    dut.reject_ready.value = 1
    await tb.cycle()
    assert int(dut.recovery_required.value) == 1


@cocotb.test()
async def test_metadata_and_body_stalls(dut):
    tb = MoldTB(dut)
    await tb.start()
    await FallingEdge(dut.clk)
    dut.packet_ready.value = 0
    await tb.send(mold(SESSION, 100, 1), final_last=False)
    await tb.wait_cycles(2)
    assert int(dut.packet_valid.value) == 1
    assert int(dut.in_ready.value) == 0
    assert tb.body == []
    await FallingEdge(dut.clk)
    dut.packet_ready.value = 1
    dut.out_ready.value = 0
    await tb.cycle()
    await tb.send(b"A", final_last=False)
    await tb.cycle()
    assert int(dut.out_valid.value) == 1
    held = (int(dut.out_data.value), int(dut.out_last.value))
    await tb.cycle()
    assert (int(dut.out_data.value), int(dut.out_last.value)) == held
    await FallingEdge(dut.clk)
    dut.out_ready.value = 1
    await tb.send(b"B")
    await tb.cycle()
    assert held == (ord("A"), 0)
    assert tb.body == [(ord("B"), 1)]


@cocotb.test()
async def test_deterministic_random_opaque_bodies(dut):
    for seed in (1, 7, 19):
        tb = MoldTB(dut)
        await tb.start()
        expected = 100
        rng = random.Random(seed)
        for _ in range(4):
            count = rng.randrange(1, 5)
            body = bytes(rng.randrange(256) for _ in range(rng.randrange(1, 7)))
            await tb.send(mold(SESSION, expected, count, body))
            await tb.wait_cycles(2)
            assert tb.packets[-1] == (expected, count, 0)
            await tb.result(True)
            expected = (expected + count) & ((1 << 64) - 1)
        assert int(dut.current_expected_sequence.value) == expected
