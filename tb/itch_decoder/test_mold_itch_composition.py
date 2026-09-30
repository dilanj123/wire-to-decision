import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

from test_itch_decoder import LOC, SEQ, SYMBOL, itch_message

SESSION = b"MOLD000021"


class Bench:
    def __init__(self, d):
        self.d = d
        self.events = []
        self.results = []
        self.rejects = []

    async def tick(self, **v):
        d = self.d
        await FallingEdge(d.clk)
        values = dict(rst=0, rearm=0,
                      cfg_active_session=int.from_bytes(SESSION, "big"),
                      cfg_expected_sequence=SEQ,
                      cfg_tracked_stock_locate=LOC, cfg_symbol_check_enable=1,
                      cfg_expected_stock_symbol=int.from_bytes(SYMBOL, "big"),
                      in_data=0, in_valid=0, in_last=0,
                      event_ready=1, decoder_reject_ready=1,
                      mold_reject_ready=1, framer_reject_ready=1)
        values.update(v)
        for k, x in values.items():
            getattr(d, k).value = x
        await Timer(1, unit="ns")
        fire = int(d.in_valid.value) and int(d.in_ready.value)
        if int(d.event_valid.value) and int(d.event_ready.value):
            self.events.append((int(d.event_kind.value), int(d.source_type.value),
                                int(d.mold_sequence.value), int(d.itch_timestamp.value),
                                int(d.stock_locate.value)))
        if int(d.structural_result_valid.value):
            self.results.append(int(d.structural_result_success.value))
        if int(d.decoder_reject_valid.value) and int(d.decoder_reject_ready.value):
            self.rejects.append((int(d.decoder_reject_fatal.value), int(d.decoder_reject_code.value)))
        await RisingEdge(d.clk)
        return fire

    async def reset(self):
        for _ in range(3):
            await self.tick(rst=1)
        await self.tick()

    async def packet(self, seq, messages):
        raw = SESSION + seq.to_bytes(8, "big") + len(messages).to_bytes(2, "big")
        for m in messages:
            raw += len(m).to_bytes(2, "big") + m
        for i, byte in enumerate(raw):
            for _ in range(30):
                if await self.tick(in_data=byte, in_valid=1, in_last=int(i == len(raw) - 1)):
                    break
            else:
                raise AssertionError("Mold→ITCH composition stopped accepting bytes")
        for _ in range(20):
            await self.tick()


async def start(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    return b


@cocotb.test()
async def test_valid_multimessage_p_filter_and_locate_filter(dut):
    b = await start(dut)
    msgs = [itch_message("A"), itch_message("P"), itch_message("E", locate=LOC + 1), itch_message("U")]
    await b.packet(SEQ, msgs)
    assert b.results == [1]
    assert [e[0:3] for e in b.events] == [(0, ord("A"), SEQ), (5, ord("U"), SEQ + 3)]
    assert not b.rejects
    assert int(dut.decoder_valid.value) == 1
    assert int(dut.current_expected_sequence.value) == SEQ + 4


@cocotb.test()
async def test_itch_failure_does_not_change_structural_mold_success(dut):
    b = await start(dut)
    msgs = [itch_message("A"), b"Z" + bytes(7), itch_message("U")]
    await b.packet(SEQ, msgs)
    assert b.results == [1], "ITCH semantic failure must not feed Mold structural result"
    assert [e[1] for e in b.events] == [ord("A")]
    assert int(dut.decoder_valid.value) == 0
    assert int(dut.recovery_required.value) == 1
    assert int(dut.current_expected_sequence.value) == SEQ + 3
    assert b.rejects == [(1, 1)]
