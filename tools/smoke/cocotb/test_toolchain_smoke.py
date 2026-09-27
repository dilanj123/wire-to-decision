"""WIRE-004 TOOLCHAIN SMOKE ONLY; not project verification."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


@cocotb.test()
async def registered_sum_smoke(dut):
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    dut.rst_n.value = 0
    dut.a.value = 0
    dut.b.value = 0
    await RisingEdge(dut.clk)
    assert int(dut.sum_q.value) == 0

    dut.rst_n.value = 1
    vectors = [(0, 0), (1, 2), (0xFF, 1), (0xFF, 0xFF)]
    for a, b in vectors:
        dut.a.value = a
        dut.b.value = b
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        assert int(dut.sum_q.value) == a + b, f"{a:#x} + {b:#x}"
