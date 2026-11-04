import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


def beat(i):
    payload = (0x1020304050607080 ^ (i * 0x0101010101010101)) & ((1 << 64) - 1)
    return (payload << 9) | (((i * 37) & 0xFF) << 1) | (i & 1)


async def reset_fifo(dut):
    dut.wr_rst.value = 1
    dut.rd_rst.value = 1
    dut.wr_valid.value = 0
    dut.rd_ready.value = 0
    dut.wr_data.value = 0
    await Timer(30, unit="ns")
    dut.wr_rst.value = 0
    dut.rd_rst.value = 0
    await Timer(30, unit="ns")


@cocotb.test()
async def fifo_full_empty_order_wrap_and_random_stalls(dut):
    cocotb.start_soon(Clock(dut.wr_clk, 5, unit="ns").start())
    cocotb.start_soon(Clock(dut.rd_clk, 7, unit="ns").start())
    await reset_fifo(dut)

    assert int(dut.rd_valid.value) == 0
    for i in range(8):
        await FallingEdge(dut.wr_clk)
        dut.wr_data.value = beat(i)
        dut.wr_valid.value = 1
        await Timer(1, unit="ns")
        assert int(dut.wr_ready.value) == 1
        await RisingEdge(dut.wr_clk)
    await FallingEdge(dut.wr_clk)
    dut.wr_data.value = beat(8)
    dut.wr_valid.value = 1
    await Timer(1, unit="ns")
    assert int(dut.wr_ready.value) == 0
    dut.wr_valid.value = 0
    dut.rd_ready.value = 0
    await Timer(1, unit="ns")
    stalled_word = int(dut.rd_data.value)
    for _ in range(4):
        await RisingEdge(dut.rd_clk)
        await Timer(1, unit="ns")
        assert int(dut.rd_valid.value) == 1
        assert int(dut.rd_data.value) == stalled_word

    observed = []
    for _ in range(30):
        await FallingEdge(dut.rd_clk)
        dut.rd_ready.value = 1
        await Timer(1, unit="ns")
        if int(dut.rd_valid.value):
            observed.append(int(dut.rd_data.value))
        await RisingEdge(dut.rd_clk)
        if len(observed) == 8:
            break
    assert observed == [beat(i) for i in range(8)]

    rng = random.Random(19)
    total, got = 64, []

    async def producer():
        sent = 0
        while sent < total:
            await FallingEdge(dut.wr_clk)
            dut.wr_valid.value = 1
            dut.wr_data.value = beat(100 + sent)
            await Timer(1, unit="ns")
            fire = int(dut.wr_ready.value)
            await RisingEdge(dut.wr_clk)
            sent += fire
        dut.wr_valid.value = 0

    async def consumer():
        while len(got) < total:
            await FallingEdge(dut.rd_clk)
            dut.rd_ready.value = int(rng.random() > 0.3)
            await Timer(1, unit="ns")
            fire = int(dut.rd_valid.value) and int(dut.rd_ready.value)
            if fire:
                got.append(int(dut.rd_data.value))
            await RisingEdge(dut.rd_clk)

    p = cocotb.start_soon(producer())
    c = cocotb.start_soon(consumer())
    await p
    await c
    assert got == [beat(100 + i) for i in range(total)]


@cocotb.test()
async def fifo_read_clock_faster_than_write_clock(dut):
    cocotb.start_soon(Clock(dut.wr_clk, 11, unit="ns").start())
    cocotb.start_soon(Clock(dut.rd_clk, 4, unit="ns").start())
    await reset_fifo(dut)
    rng = random.Random(7)
    total, got = 32, []

    async def producer():
        sent = 0
        while sent < total:
            await FallingEdge(dut.wr_clk)
            dut.wr_valid.value = 1
            dut.wr_data.value = beat(500 + sent)
            await Timer(1, unit="ns")
            fire = int(dut.wr_ready.value)
            await RisingEdge(dut.wr_clk)
            sent += fire
        dut.wr_valid.value = 0

    async def consumer():
        while len(got) < total:
            await FallingEdge(dut.rd_clk)
            dut.rd_ready.value = int(rng.random() > 0.15)
            await Timer(1, unit="ns")
            fire = int(dut.rd_valid.value) and int(dut.rd_ready.value)
            if fire:
                got.append(int(dut.rd_data.value))
            await RisingEdge(dut.rd_clk)

    p = cocotb.start_soon(producer())
    c = cocotb.start_soon(consumer())
    await p
    await c
    assert got == [beat(500 + i) for i in range(total)]
