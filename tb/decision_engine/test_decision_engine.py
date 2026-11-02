import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


MAX48 = (1 << 48) - 1
MAX49 = (1 << 48) - 1


def signed49(signal):
    value = int(signal.value)
    return value - (1 << 49) if value & (1 << 48) else value


class Bench:
    def __init__(self, dut):
        self.d = dut
        self.previous = 0
        self.threshold = 0
        self.initial = 0
        self.budget = 0
        self.count = 0

    async def reset(self, threshold=0, budget=0, rearm=False):
        d = self.d
        await FallingEdge(d.clk)
        for name, value in {
            "rst": 1, "rearm": int(rearm),
            "cfg_decision_threshold": threshold,
            "cfg_initial_budget": budget, "decision_enable": 1,
            "commit_valid": 0, "commit_mold_sequence": 0,
            "commit_itch_timestamp": 0, "commit_bid_total": 0,
            "commit_ask_total": 0, "decision_ready": 1,
        }.items():
            getattr(d, name).value = value
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        d.rst.value = 0
        d.rearm.value = 0
        await Timer(1, unit="ns")
        self.previous, self.threshold = 0, threshold
        self.initial = self.budget = budget
        self.count = 0
        assert int(d.commit_ready.value) == 1
        assert int(d.decision_valid.value) == 0
        self.check_state()

    def check_state(self):
        d = self.d
        assert signed49(d.previous_imbalance) == self.previous
        assert int(d.remaining_budget.value) == self.budget
        assert int(d.decision_count.value) == self.count
        assert self.count <= self.initial
        assert self.budget + self.count == self.initial

    async def commit(self, bid, ask, *, seq=0x1020304050607080,
                     ts=0x123456789ABC, enable=True, stall=True):
        d = self.d
        current = bid - ask
        expected = None
        if enable and self.budget:
            if self.previous < self.threshold <= current:
                expected = (0, current)
            elif self.previous > -self.threshold >= current:
                expected = (1, current)

        await FallingEdge(d.clk)
        d.decision_enable.value = int(enable)
        d.decision_ready.value = int(not stall)
        d.commit_mold_sequence.value = seq
        d.commit_itch_timestamp.value = ts
        d.commit_bid_total.value = bid
        d.commit_ask_total.value = ask
        d.commit_valid.value = 1
        for _ in range(10):
            await Timer(1, unit="ns")
            ready = int(d.commit_ready.value)
            await RisingEdge(d.clk)
            if ready:
                break
            await FallingEdge(d.clk)
        else:
            raise AssertionError("commit not accepted")
        await FallingEdge(d.clk)
        d.commit_valid.value = 0
        self.previous = current
        if expected is not None:
            self.budget -= 1
            self.count += 1
        await Timer(1, unit="ns")
        assert int(d.decision_valid.value) == int(expected is not None)
        if expected is not None:
            action, imbalance = expected
            assert int(d.decision_action.value) == action
            assert int(d.decision_mold_sequence.value) == seq
            assert int(d.decision_itch_timestamp.value) == ts
            assert signed49(d.decision_signed_imbalance) == imbalance
        self.check_state()
        if expected is not None and not stall:
            await RisingEdge(d.clk)
            await Timer(1, unit="ns")
            assert int(d.decision_valid.value) == 0
        return expected

    async def release(self):
        await FallingEdge(self.d.clk)
        self.d.decision_ready.value = 1
        await RisingEdge(self.d.clk)
        await Timer(1, unit="ns")
        assert int(self.d.decision_valid.value) == 0


def start_clock(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())


@cocotb.test()
async def test_buy_sell_exact_boundaries_and_no_repeat(dut):
    start_clock(dut)
    b = Bench(dut)
    await b.reset(threshold=10, budget=8)
    assert await b.commit(9, 0, seq=10) is None
    assert await b.commit(10, 0, seq=11) == (0, 10)
    await b.release()
    assert await b.commit(15, 0, seq=12) is None
    assert await b.commit(9, 0, seq=13) is None
    assert await b.commit(10, 0, seq=14) == (0, 10)
    await b.release()
    assert await b.commit(0, 9, seq=15) is None
    assert await b.commit(0, 10, seq=16) == (1, -10)
    await b.release()
    assert await b.commit(0, 11, seq=17) is None
    assert await b.commit(10, 0, seq=18) == (0, 10)
    await b.release()
    assert await b.commit(0, 10, seq=19) == (1, -10)
    await b.release()


@cocotb.test()
async def test_threshold_zero_enable_and_previous_trajectory(dut):
    start_clock(dut)
    b = Bench(dut)
    await b.reset(threshold=0, budget=4)
    assert await b.commit(0, 0) is None
    assert await b.commit(1, 0) is None
    assert await b.commit(0, 0) == (1, 0)
    await b.release()
    await b.reset(threshold=5, budget=4)
    assert await b.commit(7, 0, enable=False) is None
    assert b.previous == 7
    assert await b.commit(8, 0, enable=True) is None
    assert await b.commit(4, 0, enable=True) is None
    assert await b.commit(5, 0, enable=True) == (0, 5)
    await b.release()


@cocotb.test()
async def test_budget_zero_one_and_multi_credit(dut):
    start_clock(dut)
    b = Bench(dut)
    await b.reset(threshold=3, budget=0)
    assert await b.commit(3, 0) is None
    assert b.previous == 3
    await b.reset(threshold=3, budget=1)
    assert await b.commit(4, 0) == (0, 4)
    await b.release()
    assert await b.commit(0, 4) is None
    assert b.budget == 0 and b.count == 1
    await b.reset(threshold=3, budget=3)
    for bid, ask, action, target in ((3, 0, 0, 3), (0, 3, 1, -3), (3, 0, 0, 3)):
        assert await b.commit(bid, ask) == (action, target)
        await b.release()
    assert b.count == 3 and b.budget == 0


@cocotb.test()
async def test_maximum_imbalance_and_threshold(dut):
    start_clock(dut)
    b = Bench(dut)
    await b.reset(threshold=MAX48, budget=2)
    assert await b.commit(MAX48, 0) == (0, MAX48)
    assert signed49(dut.decision_signed_imbalance) == MAX49
    await b.release()
    await b.reset(threshold=MAX48, budget=2)
    assert await b.commit(0, MAX48) == (1, -MAX49)
    assert signed49(dut.decision_signed_imbalance) == -MAX49


@cocotb.test()
async def test_decision_stability_and_rearm_discards_pending(dut):
    start_clock(dut)
    b = Bench(dut)
    await b.reset(threshold=5, budget=2)
    result = await b.commit(7, 0, seq=0xDEADBEEF, ts=0xABCDEF, stall=True)
    assert result == (0, 7)
    snap = (int(dut.decision_action.value), int(dut.decision_mold_sequence.value),
            int(dut.decision_itch_timestamp.value), signed49(dut.decision_signed_imbalance),
            int(dut.remaining_budget.value), int(dut.decision_count.value))
    for _ in range(5):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.decision_valid.value) == 1
        assert snap == (int(dut.decision_action.value), int(dut.decision_mold_sequence.value),
                        int(dut.decision_itch_timestamp.value), signed49(dut.decision_signed_imbalance),
                        int(dut.remaining_budget.value), int(dut.decision_count.value))
        assert int(dut.commit_ready.value) == 0
    # A later parser/book fatal does not connect to this boundary and cannot
    # cancel a decision already generated by an earlier successful commit.
    await b.release()
    await b.reset(threshold=9, budget=6, rearm=True)
    assert signed49(dut.previous_imbalance) == 0
    assert int(dut.remaining_budget.value) == 6
    assert int(dut.decision_count.value) == 0
    assert int(dut.decision_valid.value) == 0


@cocotb.test()
async def test_rearm_captures_threshold_and_initial_budget(dut):
    start_clock(dut)
    b = Bench(dut)
    await b.reset(threshold=4, budget=1)
    await b.commit(4, 0)
    await b.release()
    await b.reset(threshold=20, budget=7, rearm=True)
    assert await b.commit(10, 0) is None
    assert b.previous == 10 and b.budget == 7


@cocotb.test()
async def test_random_commit_trajectories_seed_1_7_19_42_97(dut):
    start_clock(dut)
    for seed in (1, 7, 19, 42, 97):
        rng = random.Random(seed)
        b = Bench(dut)
        await b.reset(threshold=rng.randrange(0, 100), budget=25)
        for i in range(80):
            bid, ask = rng.randrange(0, 200), rng.randrange(0, 200)
            expected = await b.commit(bid, ask, seq=(seed << 32) | i,
                                      ts=(seed << 24) | i,
                                      enable=rng.choice((True, False)), stall=True)
            if expected is not None:
                await b.release()
            assert b.budget + b.count == b.initial
