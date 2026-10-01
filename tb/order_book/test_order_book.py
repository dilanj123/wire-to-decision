import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer


BUY, SELL = 0, 1
ADD, EXEC, EXEC_PRICE, CANCEL, DELETE, REPLACE = range(6)
SRC = {ADD: ord("A"), EXEC: ord("E"), EXEC_PRICE: ord("C"),
       CANCEL: ord("X"), DELETE: ord("D"), REPLACE: ord("U")}
ERR = {"contract": 0, "duplicate": 1, "capacity": 2, "unknown": 3,
       "execute": 4, "cancel": 5, "conflict": 6, "aggregate": 7, "upstream": 8}


def fold(ref):
    value = 0
    for shift in range(0, 64, 9):
        value ^= (ref >> shift) & 0x1FF
    return value & 0x1FF


def ev(kind, *, old=0, new=0, qty=0, price=0, side=BUY, seq=0x1234, ts=0x102030405060):
    valid = {
        ADD: (0, 1, 1, 1, 1), EXEC: (1, 0, 1, 0, 0),
        EXEC_PRICE: (1, 0, 1, 0, 0), CANCEL: (1, 0, 1, 0, 0),
        DELETE: (1, 0, 0, 0, 0), REPLACE: (1, 1, 1, 1, 0),
    }[kind]
    return dict(kind=kind, source=SRC[kind], seq=seq, ts=ts,
                old=old, new=new, qty=qty, price=price, side=side, valid=valid)


def model_apply(book, e):
    k, old, new, qty, price, side = (e[x] for x in ("kind", "old", "new", "qty", "price", "side"))
    idx = fold(new if k == ADD else old)
    occupants = [r for r in book if fold(r) == idx]
    bid = sum(q for p, q, s in book.values() if s == BUY)
    ask = sum(q for p, q, s in book.values() if s == SELL)
    target_side = side
    delta = 0
    action = None
    if k == ADD:
        if new in book:
            return False, ERR["duplicate"], book, bid, ask
        if len(occupants) == 2:
            return False, ERR["capacity"], book, bid, ask
        book = dict(book)
        book[new] = (price, qty, side)
        delta, action = qty, "add"
    elif k in (EXEC, EXEC_PRICE, CANCEL, DELETE, REPLACE):
        if old not in book:
            return False, ERR["unknown"], book, bid, ask
        op, oq, oside = book[old]
        target_side = oside
        if k in (EXEC, EXEC_PRICE, CANCEL) and qty > oq:
            return False, ERR["cancel" if k == CANCEL else "execute"], book, bid, ask
        if k == REPLACE:
            if new in book and new != old:
                return False, ERR["conflict"], book, bid, ask
            dest = [r for r in book if fold(r) == fold(new) and r != old]
            if len(dest) >= 2:
                return False, ERR["capacity"], book, bid, ask
            book = dict(book)
            del book[old]
            book[new] = (price, qty, oside)
            delta, action = qty - oq, "replace"
        elif k == DELETE:
            book = dict(book)
            del book[old]
            delta, action = -oq, "delete"
        else:
            remaining = oq - qty
            book = dict(book)
            if remaining:
                book[old] = (op, remaining, oside)
            else:
                del book[old]
            delta, action = -qty, "reduce"
    else:
        return False, ERR["contract"], book, bid, ask
    nbid, nask = bid, ask
    if target_side == BUY:
        nbid += delta
    else:
        nask += delta
    if not (0 <= nbid < (1 << 48) and 0 <= nask < (1 << 48)):
        return False, ERR["aggregate"], book, bid, ask
    return True, None, book, nbid, nask


class Bench:
    def __init__(self, dut):
        self.d = dut

    async def reset(self):
        d = self.d
        await FallingEdge(d.clk)
        d.rst.value = 1
        d.rearm.value = 0
        d.upstream_recovery_required.value = 0
        d.event_valid.value = 0
        d.commit_ready.value = 1
        d.error_ready.value = 1
        d.debug_reference.value = 0
        for name in ("event_kind", "source_type", "mold_sequence", "itch_timestamp", "stock_locate",
                     "old_order_reference", "new_order_reference", "quantity", "price", "side",
                     "old_reference_valid", "new_reference_valid", "quantity_valid", "price_valid", "side_valid"):
            getattr(d, name).value = 0
        await RisingEdge(d.clk)
        await FallingEdge(d.clk)
        d.rst.value = 0

    async def accept(self, e):
        d = self.d
        pins = {"event_kind": e["kind"], "source_type": e["source"],
                "mold_sequence": e["seq"], "itch_timestamp": e["ts"], "stock_locate": 0x2345,
                "old_order_reference": e["old"], "new_order_reference": e["new"],
                "quantity": e["qty"], "price": e["price"], "side": e["side"],
                "old_reference_valid": e["valid"][0], "new_reference_valid": e["valid"][1],
                "quantity_valid": e["valid"][2], "price_valid": e["valid"][3], "side_valid": e["valid"][4]}
        await FallingEdge(d.clk)
        for name, value in pins.items():
            getattr(d, name).value = value
        d.event_valid.value = 1
        for _ in range(100):
            await Timer(1, unit="ns")
            ready = int(d.event_ready.value)
            await RisingEdge(d.clk)
            if ready:
                await FallingEdge(d.clk)
                d.event_valid.value = 0
                return
        raise AssertionError("event was not accepted")

    async def result(self, timeout=100):
        d = self.d
        for _ in range(timeout):
            await RisingEdge(d.clk)
            await Timer(1, unit="ns")
            if int(d.commit_valid.value):
                got = (int(d.commit_mold_sequence.value), int(d.commit_itch_timestamp.value),
                       int(d.commit_bid_total.value), int(d.commit_ask_total.value))
                await RisingEdge(d.clk)
                await Timer(1, unit="ns")
                return ("commit", got)
            if int(d.error_valid.value):
                code = int(d.error_code.value)
                await RisingEdge(d.clk)
                await Timer(1, unit="ns")
                return ("error", code)
        raise AssertionError("no commit/error response")

    async def submit(self, e, expect_error=None):
        await self.accept(e)
        result = await self.result()
        if expect_error is None:
            assert result[0] == "commit", result
        else:
            assert result == ("error", expect_error), result
        return result

    async def query(self, ref):
        d = self.d
        await FallingEdge(d.clk)
        d.debug_reference.value = ref
        await Timer(1, unit="ns")
        if not int(d.debug_found.value):
            return None
        return (int(d.debug_price.value), int(d.debug_remaining_quantity.value),
                int(d.debug_side.value), int(d.debug_set_index.value), int(d.debug_way.value))


@cocotb.test()
async def test_hash_vectors_way_allocation_collision_and_no_eviction(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    refs = (1, 0x200, 0x40000)
    assert tuple(fold(r) for r in refs) == (1, 1, 1)
    assert tuple(fold(r) for r in (0x8000000000000000, 0xFFFFFFFFFFFFFFFF)) == (1, 0x1FE)
    for i, ref in enumerate(refs[:2]):
        await b.submit(ev(ADD, new=ref, qty=10 + i, price=100 + i, side=BUY))
        found = await b.query(ref)
        assert found == (100 + i, 10 + i, BUY, 1, i)
    await b.submit(ev(ADD, new=refs[2], qty=1, price=1), ERR["capacity"])
    assert await b.query(refs[2]) is None
    assert int(dut.bid_total.value) == 21
    assert int(dut.book_valid.value) == 0


@cocotb.test()
async def test_full_512_by_2_capacity_and_48_bit_bound(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    max_q = 0xFFFFFFFF
    for set_index in range(512):
        ref0 = set_index
        ref1 = set_index + 0x40200  # Add two equal folded lanes; same set, distinct ref.
        assert fold(ref0) == set_index and fold(ref1) == set_index
        await b.submit(ev(ADD, new=ref0, qty=max_q, price=set_index, side=BUY,
                          seq=set_index * 2, ts=set_index * 2))
        await b.submit(ev(ADD, new=ref1, qty=max_q, price=set_index ^ 0xFFFF, side=BUY,
                          seq=set_index * 2 + 1, ts=set_index * 2 + 1))
    expected = 1024 * max_q
    assert expected < (1 << 42) < (1 << 48)
    assert int(dut.bid_total.value) == expected
    assert int(dut.ask_total.value) == 0
    assert int(dut.book_valid.value) == 1
    assert await b.query(511) is not None
    assert await b.query(511 + 0x40200) is not None


@cocotb.test()
async def test_add_duplicates_buy_sell_and_contract_quarantine(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    await b.submit(ev(ADD, new=0xABCDEF, qty=7, price=0x12345678, side=BUY, seq=11))
    await b.submit(ev(ADD, new=0x123456789, qty=9, price=0x87654321, side=SELL, seq=12))
    assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (7, 9)
    await b.submit(ev(ADD, new=0xABCDEF, qty=1, price=2), ERR["duplicate"])
    await b.reset()
    bad = ev(ADD, new=44, qty=1, price=2)
    bad["valid"] = (1, 1, 1, 1, 1)
    await b.submit(bad, ERR["contract"])
    assert int(dut.book_valid.value) == 0
    assert int(dut.bid_total.value) == 0


@cocotb.test()
async def test_execute_c_price_cancel_delete_and_errors(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    ref = 0x1020304050607080
    await b.submit(ev(ADD, new=ref, qty=20, price=0x55667788, side=BUY))
    await b.submit(ev(EXEC_PRICE, old=ref, qty=3, price=0xDEADBEEF))
    assert await b.query(ref) == (0x55667788, 17, BUY, fold(ref), 0)
    await b.submit(ev(EXEC, old=ref, qty=17))
    assert await b.query(ref) is None
    await b.reset()
    await b.submit(ev(ADD, new=ref, qty=20, price=2, side=SELL))
    await b.submit(ev(CANCEL, old=ref, qty=5))
    assert (await b.query(ref))[:3] == (2, 15, SELL)
    await b.submit(ev(DELETE, old=ref))
    assert await b.query(ref) is None
    await b.reset()
    await b.submit(ev(EXEC, old=ref, qty=1), ERR["unknown"])
    await b.reset()
    await b.submit(ev(ADD, new=ref, qty=2, price=3))
    await b.submit(ev(EXEC, old=ref, qty=3), ERR["execute"])


@cocotb.test()
async def test_replace_same_cross_set_same_reference_and_inherited_side(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    old = 0x21
    same_set_new = 0x40221  # Two matching XOR-fold lanes cancel.
    assert fold(old) == fold(same_set_new)
    await b.submit(ev(ADD, new=old, qty=10, price=100, side=SELL))
    await b.submit(ev(REPLACE, old=old, new=same_set_new, qty=13, price=150))
    assert await b.query(old) is None
    assert (await b.query(same_set_new))[:3] == (150, 13, SELL)
    assert int(dut.ask_total.value) == 13
    await b.submit(ev(REPLACE, old=same_set_new, new=same_set_new, qty=8, price=200))
    assert (await b.query(same_set_new))[:3] == (200, 8, SELL)
    cross_new = 0x10000
    assert fold(cross_new) != fold(same_set_new)
    await b.submit(ev(REPLACE, old=same_set_new, new=cross_new, qty=5, price=250))
    assert await b.query(same_set_new) is None
    assert (await b.query(cross_new))[:3] == (250, 5, SELL)
    assert int(dut.ask_total.value) == 5


@cocotb.test()
async def test_replace_conflict_and_full_destination_are_atomic(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    old, conflict = 0x11, 0x12
    await b.submit(ev(ADD, new=old, qty=8, price=88, side=BUY))
    await b.submit(ev(ADD, new=conflict, qty=4, price=44, side=SELL))
    before = (int(dut.bid_total.value), int(dut.ask_total.value),
              await b.query(old), await b.query(conflict))
    await b.submit(ev(REPLACE, old=old, new=conflict, qty=9, price=99), ERR["conflict"])
    after = (int(dut.bid_total.value), int(dut.ask_total.value),
             await b.query(old), await b.query(conflict))
    assert after == before

    await b.reset()
    colliders = [1, 0x200, 0x40000]
    await b.submit(ev(ADD, new=old, qty=3, price=33, side=SELL))
    await b.submit(ev(ADD, new=colliders[0], qty=5, price=55))
    await b.submit(ev(ADD, new=colliders[1], qty=6, price=66))
    before = (int(dut.bid_total.value), int(dut.ask_total.value), await b.query(old),
              await b.query(colliders[0]), await b.query(colliders[1]))
    await b.submit(ev(REPLACE, old=old, new=colliders[2], qty=7, price=77), ERR["capacity"])
    after = (int(dut.bid_total.value), int(dut.ask_total.value), await b.query(old),
             await b.query(colliders[0]), await b.query(colliders[1]))
    assert after == before


@cocotb.test()
async def test_commit_stall_and_upstream_fatal_ordering(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    dut.commit_ready.value = 0
    dut.error_ready.value = 0
    e = ev(ADD, new=0x900, qty=12, price=321, side=BUY, seq=0x1122334455667788, ts=0x123456789ABC)
    await b.accept(e)
    dut.upstream_recovery_required.value = 1
    for _ in range(4):
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")
        assert int(dut.commit_valid.value)
        assert (int(dut.commit_mold_sequence.value), int(dut.commit_itch_timestamp.value),
                int(dut.commit_bid_total.value), int(dut.commit_ask_total.value)) == (e["seq"], e["ts"], 12, 0)
    assert (await b.query(e["new"]))[:3] == (321, 12, BUY)
    assert int(dut.book_valid.value) == 0
    assert int(dut.recovery_required.value) == 1
    assert int(dut.event_ready.value) == 0
    dut.commit_ready.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.upstream_recovery_required.value = 0
    assert int(dut.commit_valid.value) == 0
    assert int(dut.error_valid.value) == 1
    assert int(dut.error_code.value) == ERR["upstream"]
    await b.reset()
    assert (int(dut.book_valid.value), int(dut.recovery_required.value),
            int(dut.bid_total.value), int(dut.ask_total.value)) == (1, 0, 0, 0)


@cocotb.test()
async def test_bad_contract_zero_and_upstream_idle_quarantine(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    await b.reset()
    bad = ev(ADD, new=7, qty=0, price=1)
    await b.submit(bad, ERR["contract"])
    await b.reset()
    dut.upstream_recovery_required.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert int(dut.book_valid.value) == 0
    assert int(dut.recovery_required.value) == 1
    assert int(dut.event_ready.value) == 0
    assert int(dut.error_valid.value) == 1
    await b.reset()
    assert int(dut.error_valid.value) == 0
    assert int(dut.event_ready.value) == 1


@cocotb.test()
async def test_deterministic_randomized_model_sequences(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    b = Bench(dut)
    for seed in (1, 7, 19, 42, 97):
        await b.reset()
        rng = random.Random(seed)
        model = {}
        for step in range(50):
            choice = rng.randrange(100)
            if not model or choice < 35:
                ref = (rng.getrandbits(32) << 12) | (seed << 4) | (step & 0xF)
                while ref in model:
                    ref += 1
                e = ev(ADD, new=ref, qty=rng.randint(1, 1000), price=rng.getrandbits(32),
                       side=rng.randrange(2), seq=(seed << 32) | step, ts=step)
            else:
                ref = rng.choice(list(model))
                p, q, s = model[ref]
                kind = rng.choice((EXEC, EXEC_PRICE, CANCEL, DELETE, REPLACE))
                qty = rng.randint(1, q) if kind != DELETE else 0
                new = ref
                if kind == REPLACE:
                    new = (rng.getrandbits(32) << 12) | (step + 1)
                    while new in model and new != ref:
                        new += 1
                e = ev(kind, old=ref, new=new, qty=qty,
                       price=rng.getrandbits(32), seq=(seed << 32) | step, ts=step)
            success, err, updated, bid, ask = model_apply(model, e)
            if success:
                result = await b.submit(e)
                model = updated
                assert result == ("commit", (e["seq"], e["ts"], bid, ask))
                assert (int(dut.bid_total.value), int(dut.ask_total.value)) == (bid, ask)
                assert (bid, ask) == (
                    sum(q for p, q, s in model.values() if s == BUY),
                    sum(q for p, q, s in model.values() if s == SELL))
            else:
                await b.submit(e, err)
                break
