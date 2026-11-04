import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "functional_mvp"))
from test_functional_mvp import (
    BASE_SEQ, DEST_IP, DEST_PORT, LOC, SESSION, SYMBOL, beats, config, frame,
    itch, mold, oracle_decisions,
)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model" / "python"))
from wire_to_decision.oracle import ReferenceOracle


def oracle_outcome(data):
    oracle = ReferenceOracle(config(budget=4))
    result = oracle.process_frame(data)
    return (
        oracle_decisions(result),
        oracle.book.bid_total,
        oracle.book.ask_total,
        oracle.framing_state.expected_sequence,
    )


def start_clocks(dut):
    cocotb.start_soon(Clock(dut.rx_clk, 5, unit="ns").start())
    cocotb.start_soon(Clock(dut.proc_clk, 7, unit="ns").start())


def drive_config(d):
    d.cfg_destination_ipv4.value = DEST_IP
    d.cfg_destination_udp_port.value = DEST_PORT
    d.cfg_active_session.value = int.from_bytes(SESSION, "big")
    d.cfg_expected_sequence.value = BASE_SEQ
    d.cfg_tracked_stock_locate.value = LOC
    d.cfg_symbol_check_enable.value = 1
    d.cfg_expected_stock_symbol.value = int.from_bytes(SYMBOL, "big")
    d.cfg_decision_threshold.value = 10
    d.cfg_initial_budget.value = 4
    d.decision_enable.value = 1


async def rearm_epoch(d):
    d.rearm.value = 0
    await Timer(120, unit="ns")
    d.rearm.value = 1
    await Timer(160, unit="ns")
    d.rearm.value = 0
    for _ in range(100):
        await RisingEdge(d.proc_clk)
        if int(d.cdc_ready.value):
            return
    raise AssertionError("CDC epoch did not become ready after explicit rearm")


async def rearm_active_epoch(d):
    d.rearm.value = 0
    await Timer(100, unit="ns")
    d.rearm.value = 1
    saw_down = False
    saw_ready_after_down = False
    for _ in range(100):
        await RisingEdge(d.proc_clk)
        if not int(d.cdc_ready.value):
            saw_down = True
        elif saw_down:
            saw_ready_after_down = True
            break
    assert saw_down and saw_ready_after_down, "active rearm did not flush and reopen a new epoch"
    d.rearm.value = 0


async def send_frame(d, data, *, decision_stall=False, expect_recovery=False):
    stream = beats(data)
    decisions = []
    fifo_seen = []
    recovery_seen = []
    stalled_decision = None
    d.decision_ready.value = 0 if decision_stall else 1

    async def observe_fifo():
        nonlocal stalled_decision
        for _ in range(2000):
            await FallingEdge(d.proc_clk)
            await Timer(1, unit="ns")
            if (int(d.fifo_read_valid_observed.value) and
                    int(d.fifo_read_ready_observed.value)):
                fifo_seen.append(int(d.fifo_read_data_observed.value))
            if int(d.parser_recovery_required.value) or int(d.book_recovery_required.value):
                recovery_seen.append(1)
            decision_tuple = (
                int(d.decision_action.value),
                int(d.decision_mold_sequence.value),
                int(d.decision_itch_timestamp.value),
                int(d.decision_signed_imbalance.value),
            )
            if int(d.decision_valid.value) and not int(d.decision_ready.value):
                if stalled_decision is not None:
                    assert decision_tuple == stalled_decision, "stalled decision tuple changed"
                stalled_decision = decision_tuple
            else:
                stalled_decision = None
            if int(d.decision_valid.value) and int(d.decision_ready.value):
                imbalance = int(d.decision_signed_imbalance.value)
                if imbalance & (1 << 48):
                    imbalance -= 1 << 49
                decisions.append((int(d.decision_action.value),
                                  int(d.decision_mold_sequence.value),
                                  int(d.decision_itch_timestamp.value), imbalance))
            await RisingEdge(d.proc_clk)

    monitor = cocotb.start_soon(observe_fifo())

    idx = 0
    for _ in range(10000):
        await FallingEdge(d.rx_clk)
        if idx < len(stream):
            d.rx_data.value, d.rx_keep.value, d.rx_last.value = stream[idx]
            d.rx_valid.value = 1
        await Timer(1, unit="ns")
        fire = int(d.rx_valid.value) and int(d.rx_ready.value)
        await RisingEdge(d.rx_clk)
        if fire:
            idx += 1
        if expect_recovery and not int(d.cdc_ready.value):
            break
        if idx == len(stream):
            break
    else:
        raise AssertionError(f"RX timeout {idx}/{len(stream)}")
    d.rx_valid.value = 0
    if not expect_recovery:
        assert idx == len(stream), f"incomplete frame accepted {idx}/{len(stream)}"
    for _ in range(500):
        await FallingEdge(d.proc_clk)
        await RisingEdge(d.proc_clk)
    monitor.cancel()
    if expect_recovery:
        assert recovery_seen, "fatal parser/book recovery was not observed"
        assert int(d.cdc_ready.value) == 0
    else:
        expected_fifo = [((word << 9) | (keep << 1) | last) for word, keep, last in stream]
        assert fifo_seen == expected_fifo, f"FIFO beat mismatch {len(fifo_seen)}/{len(expected_fifo)}"
    return decisions


@cocotb.test()
async def cdc_full_architecture_frame_and_one_sided_reset(dut):
    start_clocks(dut)
    drive_config(dut)
    dut.rx_valid.value = 0
    dut.rx_data.value = 0
    dut.rx_keep.value = 0
    dut.rx_last.value = 0
    dut.decision_ready.value = 0
    dut.rearm.value = 0
    dut.rx_rst.value = 1
    dut.proc_rst.value = 1
    await Timer(50, unit="ns")
    dut.rx_rst.value = 0
    dut.proc_rst.value = 0
    await rearm_epoch(dut)
    assert int(dut.rx_epoch_ready.value) == 1
    assert int(dut.proc_epoch_ready.value) == 1

    test_frame = frame(mold([itch("A", ref=0x1122334455667788, qty=10, price=123, salt=1)]))
    expected, expected_bid, expected_ask, expected_sequence = oracle_outcome(test_frame)
    await send_frame(dut, test_frame, decision_stall=True)
    for _ in range(500):
        await RisingEdge(dut.proc_clk)
        if int(dut.decision_valid.value):
            break
    else:
        raise AssertionError(
            "expected decision did not become pending: "
            f"cdc={int(dut.cdc_ready.value)} parser_valid={int(dut.parser_valid.value)} "
            f"parser_recovery={int(dut.parser_recovery_required.value)} "
            f"book_valid={int(dut.book_valid.value)} book_recovery={int(dut.book_recovery_required.value)} "
            f"totals={int(dut.bid_total.value)}/{int(dut.ask_total.value)} "
            f"seq={int(dut.current_expected_sequence.value):x} "
            f"stage={int(dut.parser_recovery_stage.value)} rejects={int(dut.stage_reject_observed.value):x}/"
            f"{int(dut.stage_reject_fatal.value):x}/{int(dut.stage_reject_code.value):x} "
            f"bookerr={int(dut.error_valid.value)}/{int(dut.error_code.value)}"
        )
    pending = (int(dut.decision_action.value), int(dut.decision_mold_sequence.value),
               int(dut.decision_itch_timestamp.value), int(dut.decision_signed_imbalance.value))

    # A reset in the RX domain invalidates the epoch; the remote domain learns
    # after its two-flop peer-status synchronization delay.
    dut.rx_rst.value = 1
    await Timer(35, unit="ns")
    dut.rx_rst.value = 0
    saw_not_ready = False
    for _ in range(100):
        await RisingEdge(dut.proc_clk)
        if not int(dut.cdc_ready.value):
            saw_not_ready = True
            break
    assert saw_not_ready
    for _ in range(8):
        await RisingEdge(dut.proc_clk)
    assert int(dut.decision_valid.value) == 0
    assert int(dut.rx_ready.value) == 0

    # A fresh explicit low/high rearm establishes a clean epoch and clears
    # the pending old-epoch decision before any new frame is accepted.
    await rearm_epoch(dut)
    assert int(dut.decision_valid.value) == 0
    assert int(dut.bid_total.value) == 0 and int(dut.ask_total.value) == 0
    fresh_decisions = await send_frame(dut, test_frame, decision_stall=False)
    assert fresh_decisions == expected == [(0, BASE_SEQ, 0x010203040501, 10)]
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (expected_bid, expected_ask)
    assert int(dut.current_expected_sequence.value) == expected_sequence
    assert pending[0:3] == fresh_decisions[0][0:3]

    await rearm_active_epoch(dut)
    assert int(dut.bid_total.value) == 0 and int(dut.ask_total.value) == 0
    assert int(dut.decision_valid.value) == 0
    second_epoch = await send_frame(dut, test_frame)
    assert second_epoch == expected
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (expected_bid, expected_ask)
    assert int(dut.current_expected_sequence.value) == expected_sequence

    # A parser fatal also invalidates the CDC epoch. It cannot leave queued
    # tail beats to be interpreted as the first beat of a later packet.
    bad_session_frame = frame(mold(
        [itch("A", ref=0x9988776655443322, qty=10, price=44)],
        session=b"BADSESSION",
    ))
    await send_frame(dut, bad_session_frame, expect_recovery=True)
    dut.rx_valid.value = 1
    dut.rx_data.value = 0x12345678
    dut.rx_keep.value = 0xFF
    dut.rx_last.value = 0
    await Timer(1, unit="ns")
    assert int(dut.rx_ready.value) == 0
    dut.rx_valid.value = 0
    await rearm_epoch(dut)
    assert int(dut.bid_total.value) == 0 and int(dut.decision_valid.value) == 0
    after_fatal = await send_frame(dut, test_frame)
    assert after_fatal == expected
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (expected_bid, expected_ask)
    assert int(dut.current_expected_sequence.value) == expected_sequence


@cocotb.test()
async def processing_reset_discards_buffered_partial_frame(dut):
    start_clocks(dut)
    drive_config(dut)
    dut.rx_valid.value = 0
    dut.rx_data.value = 0
    dut.rx_keep.value = 0
    dut.rx_last.value = 0
    dut.decision_ready.value = 1
    dut.rearm.value = 0
    dut.rx_rst.value = 1
    dut.proc_rst.value = 1
    await Timer(50, unit="ns")
    dut.rx_rst.value = 0
    dut.proc_rst.value = 0
    await rearm_epoch(dut)

    partial_frame = frame(mold([itch("A", ref=0xAABBCCDDEEFF0011, qty=10, price=77, salt=2)]))
    stream = beats(partial_frame)
    accepted = 0
    for item in stream:
        await FallingEdge(dut.rx_clk)
        dut.rx_data.value, dut.rx_keep.value, dut.rx_last.value = item
        dut.rx_valid.value = 1
        await Timer(1, unit="ns")
        ready = int(dut.rx_ready.value)
        await RisingEdge(dut.rx_clk)
        if ready:
            accepted += 1
        if accepted == 1:
            # Read side reset immediately; the write domain learns the epoch
            # loss after its two-flop peer-ready synchronizer. Hold this beat
            # stable and count any transfers during that propagation window.
            dut.proc_rst.value = 1
            for _ in range(8):
                await FallingEdge(dut.rx_clk)
                await Timer(1, unit="ns")
                fire = int(dut.rx_ready.value)
                await RisingEdge(dut.rx_clk)
                if fire:
                    accepted += 1
                else:
                    break
            await Timer(20, unit="ns")
            dut.proc_rst.value = 0
        if not ready:
            break
    dut.rx_valid.value = 0
    assert accepted >= 2, "expected buffered old-epoch data during remote reset propagation"

    for _ in range(40):
        await RisingEdge(dut.proc_clk)
        if not int(dut.cdc_ready.value):
            break
    assert int(dut.cdc_ready.value) == 0
    assert int(dut.rx_ready.value) == 0
    await rearm_epoch(dut)
    assert int(dut.bid_total.value) == 0 and int(dut.ask_total.value) == 0
    assert int(dut.decision_valid.value) == 0

    fresh = frame(mold([itch("A", ref=0xAABBCCDDEEFF0022, qty=10, price=88, salt=3)]))
    expected, expected_bid, expected_ask, expected_sequence = oracle_outcome(fresh)
    decisions = await send_frame(dut, fresh)
    assert decisions == expected == [(0, BASE_SEQ, 0x010203040503, 10)]
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (expected_bid, expected_ask)
    assert int(dut.current_expected_sequence.value) == expected_sequence


@cocotb.test()
async def rx_reset_with_full_async_fifo_discards_old_epoch(dut):
    rx_task = cocotb.start_soon(Clock(dut.rx_clk, 5, unit="ns").start())
    proc_task = cocotb.start_soon(Clock(dut.proc_clk, 7, unit="ns").start())
    drive_config(dut)
    dut.rx_valid.value = 0
    dut.rx_data.value = 0
    dut.rx_keep.value = 0
    dut.rx_last.value = 0
    dut.decision_ready.value = 1
    dut.rearm.value = 0
    dut.rx_rst.value = 1
    dut.proc_rst.value = 1
    await Timer(50, unit="ns")
    dut.rx_rst.value = 0
    dut.proc_rst.value = 0
    await rearm_epoch(dut)

    # Stop only the processing clock. The RX side can fill the eight-entry
    # FIFO while its synchronized peer-ready remains high.
    await FallingEdge(dut.proc_clk)
    proc_task.cancel()
    raw = frame(mold([itch("A", ref=0x4455667788990011, qty=10, price=55)]))
    stream = beats(raw)
    accepted = 0
    for item in stream[:8]:
        await FallingEdge(dut.rx_clk)
        dut.rx_data.value, dut.rx_keep.value, dut.rx_last.value = item
        dut.rx_valid.value = 1
        await Timer(1, unit="ns")
        assert int(dut.rx_ready.value) == 1
        await RisingEdge(dut.rx_clk)
        accepted += 1
    assert accepted == 8
    await FallingEdge(dut.rx_clk)
    dut.rx_data.value, dut.rx_keep.value, dut.rx_last.value = stream[8]
    dut.rx_valid.value = 1
    await Timer(1, unit="ns")
    assert int(dut.rx_ready.value) == 0

    dut.rx_rst.value = 1
    await Timer(30, unit="ns")
    dut.rx_rst.value = 0
    dut.rx_valid.value = 0
    assert int(dut.rx_ready.value) == 0

    # Restart the remote clock so it can observe the synchronized epoch-down.
    proc_task = cocotb.start_soon(Clock(dut.proc_clk, 7, unit="ns").start())
    for _ in range(20):
        await RisingEdge(dut.proc_clk)
    assert int(dut.cdc_ready.value) == 0
    await rearm_epoch(dut)
    assert int(dut.bid_total.value) == 0 and int(dut.decision_valid.value) == 0

    fresh = frame(mold([itch("A", ref=0x4455667788990022, qty=10, price=66, salt=1)]))
    decisions = await send_frame(dut, fresh)
    expected, expected_bid, expected_ask, expected_sequence = oracle_outcome(fresh)
    assert decisions == expected == [(0, BASE_SEQ, 0x010203040501, 10)]
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (expected_bid, expected_ask)
    assert int(dut.current_expected_sequence.value) == expected_sequence
    rx_task.cancel()
    proc_task.cancel()
