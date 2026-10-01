# WIRE-023 — Bounded 512-Set × 2-Way Order-State and Aggregate RTL

## Status

PASS. Phase 3 remains ACTIVE; deterministic decision RTL is not started.

## Starting state and authority

- Repository: `/Users/Dilan/Projects/wire-to-decision`
- Branch: `main`
- Starting HEAD and origin/main: `ecacb89d26ce7b12acdc011bbefd9cdf08265836`
- Initial tree: clean
- Protected `kg-g0-env^{}`: `06f5643a940ac2c6fcfab0e377169b48ce700107`
- Authority: REQ-BOOK-001..008, REQ-DEC-001, REQ-ERR-001..004; WIRE-D006, D008, D009, D017, D018; WIRE-011 Python book model; WIRE-022 parser integration.

## Architecture and contract

Production default is exactly 512 sets × 2 ways (1,024 entries), no eviction. Each valid entry holds reference, price, nonzero remaining quantity, side, and valid. Set index is the frozen 9-bit WIRE-D006 XOR fold; way allocation is deterministic way 0 then way 1. Lookup is restricted to the selected set.

The input is the WIRE-D017 ready/valid normalized mutation event; the book validates event-kind/source/field-valid combinations and required nonzero quantities. One event is accepted at a time. A successful store+aggregate update is atomic at the clocked mutation edge and emits one stable successful-mutation commit carrying Mold sequence, ITCH timestamp, and post-update bid/ask totals. A failed mutation emits no successful commit.

`wire_arch_a_parser_book_top` composes the complete WIRE-022 parser top with the book. `upstream_recovery_required` prevents a new event handshake. An event already accepted before upstream fatal recovery may complete atomically and its commit is retained; the book then remains invalid/quarantined until reset/rearm. Reset/rearm clears entry-valid bits, totals, errors and pending transactions, and begins a valid empty epoch.

WIRE-D019 is recorded in `docs/DECISIONS.md`.

## Mutation semantics

- ADD: reject invalid contract, duplicate, or full selected set; otherwise allocate first free way, update the inherited-side aggregate, and commit.
- EXECUTE and EXECUTE_WITH_PRICE: require known reference and quantity no greater than remaining; reduce quantity/aggregate or remove at zero. C never changes resting price.
- CANCEL: same quantity reduction with `OVER_CANCEL` on excess.
- DELETE: remove the known entry and subtract its full remaining quantity; normalized quantity is ignored.
- REPLACE: old must exist; destination conflict/full fails without state/aggregate changes. Successful replacement inherits side and applies `new quantity - old remaining` atomically. Same-set, cross-set, and old==new are supported.
- Arithmetic uses widened signed candidates and explicit range checks before state writes. `1024 × (2^32−1) < 2^42 < 2^48`; the maximum is documented/tested, not an FPGA resource or timing claim.

Local error encodings: 0 EVENT_CONTRACT, 1 DUPLICATE_REFERENCE, 2 COLLISION_CAPACITY, 3 UNKNOWN_REFERENCE, 4 OVER_EXECUTE, 5 OVER_CANCEL, 6 NEW_REFERENCE_CONFLICT, 7 AGGREGATE_RANGE, 8 UPSTREAM_FATAL. First error is held until handshake and its code remains the quarantine reason until rearm/reset. There is no global decision/error arbiter in this task.

## Verification and tools

- Standalone cocotb/Verilator: **9/9 PASS**. Fixed hash vectors include `1`, `0x200`, and `0x40000` → set 1, plus high-bit and all-ones vectors. The production 512×2 store was filled with 1,024 maximum-quantity entries; aggregate was checked against the 48-bit limit. Other directed tests cover A/E/C/X/D/U, BUY/SELL, C-price preservation, full/duplicate/unknown/over-quantity, contract faults, U same/cross-set/same-reference/conflict/full-destination atomicity, commit stalls, upstream fatal ordering, rearm, and the independent dictionary scoreboard. Randomized model plans use seeds 1, 7, 19, 42, 97.
- Parser→book cocotb/Verilator: **4/4 PASS**. Five complete frames were processed across valid A/E/X/U/D mutations, late structural suffix, structurally valid Mold with unsupported ITCH, outer IPv4 fatal, and post-rearm traffic; a further frame attempt was blocked during recovery. Complete prefix mutations remained committed after later fatal outcomes. Mold sequence advances on structural Mold success even when later ITCH semantics quarantine the book.
- Python oracle comparison: valid mutation sequence and both late structural/ITCH-semantic failure outcomes were compared with `ReferenceOracle`; final aggregates/order state matched. Full Python suite: **71/71 PASS**.
- Verilator 5.053 strict lint: standalone and parser→book composition PASS, no meaningful warnings.
- Yosys 0.69+154 `hierarchy; proc; opt; check; stat`: standalone and parser→book composition PASS. Generic summaries: standalone 1,455 cells / 133,120 memory bits; composition 2,637 cells / 133,120 memory bits. Classification is component synthesis sanity only.
- Earlier simulation regressions rerun: WIRE-014 6/6; WIRE-015 5/5 + composition 1/1; WIRE-016 4/4 + composition 1/1; WIRE-017 5/5 + composition 3/3; WIRE-018 5/5 + composition 3/3; WIRE-019/019A 14/14 + composition 2/2; WIRE-020 10/10 + composition 2/2; WIRE-021 6/6 + composition 2/2; WIRE-022 6/6.
- Established formal regression suite: every job passed when invoked from its documented source root. Six initial gearbox/ingress invocations from the wrong working directory failed during source-file copy before elaboration; all six were rerun from repository root and passed. Historical solver-bound WIRE-017 monolithic and WIRE-022 depth-270 top jobs were intentionally not promoted or rerun as passing results.

## New formal evidence

All jobs use SBY 0.69 / `smtbmc yices` / Yices 2.7.0 and public DUT ports only; no DUT-private state is read. Public diagnostic lookup outputs are used in fixed-vector scenarios. Every result is bounded, not inductive/unbounded.

Harness refinement note: an initial one-set abstraction used `$clog2(1)`, creating an invalid zero-width slice; its failed vector run is retained as `formal_initial_one_set_harness_failure.log` and is not production-RTL counterexample evidence. The transaction vector was corrected to the two-set abstraction and passed at depth 28. An initial assertion that all commits disappear during recovery was also removed: WIRE-D019 allows a commit for an event accepted before upstream fatal to remain pending/stable. Safety closure is bounded, not inductive.

| Job | Result and scope |
|---|---|
| `order_book_safety` | BMC depth 12 PASS; reduced two-set instance. Arbitrary legal-source event stalls; unconstrained commit/error readiness. Checks commit/error tuple stall stability, recovery persistence/event blocking, upstream-fatal event blocking, and synchronous reset/rearm empty/valid state. |
| `order_book_hash_vectors` | Fixed-vector BMC depth 6 PASS; production 512-set default. Public hash diagnostic checks frozen low/high-bit fold vectors. |
| `order_book_add_vector` | Fixed-vector BMC depth 28 PASS; reduced two-set instance. Public lookup/aggregate/commit checks ADD, E, C, X, same-reference U, and D accounting; C preserves resting price; commit sequence/time and post-state totals match each transaction. |
| `order_book_collision_vector` | Fixed-vector BMC depth 20 PASS; reduced two-set instance. Two references occupy the selected destination set; a third colliding ADD fails without eviction; a cross-set U into that full set fails atomically, preserving old/destination entries and totals. |
| `order_book_duplicate_vector` | Fixed-vector BMC depth 12 PASS; reduced two-set instance. Duplicate ADD reports error, no second commit, original public entry/totals remain, and recovery blocks later input. |
| `order_book_unknown_vector` | Fixed-vector BMC depth 8 PASS; reduced two-set instance. Unknown E produces error/no commit/no aggregate mutation and quarantines further events. |
| `order_book_upstream_order` | Fixed-vector BMC depth 10 PASS; reduced two-set instance. Event handshakes before upstream fatal; it finishes atomically, commit remains stable under backpressure with exact metadata/post-total, and book invalid/recovery blocks new events. |

There are no separate formal cover jobs in WIRE-023; cover statements in harnesses are not counted as reachability results. The 1,024-entry capacity and maximum-quantity exercise is simulation evidence. Reduced formal instances do not prove all 512 sets or all possible event streams.

## Requirement traceability and limitations

RTL simulation plus bounded/fixed formal evidence supports REQ-BOOK-001..008 at the local store/aggregate/commit boundary, with full-scale capacity demonstrated in simulation. WIRE-D019/parser-fatal ordering supports local REQ-ERR-001..004 behavior at the book boundary. REQ-DEC-001 decision generation is not implemented; no order-state decision is claimed.

No end-to-end order rollback exists. Already-committed earlier messages remain in the book after a later parser fatal condition, and the book then quarantines. This is the WIRE-D018/D019 no-rollback contract, not a claim that events are transactionally undone.

Still unproven: deterministic decisions/risk budget; parser→book→decision complete integration; complete functional regression/verification gates; application P&R/timing/resources; L1/L2/L3 latency; measured throughput/initiation interval; Architecture-A bottleneck; Architecture B authorization; CDC/RDC; C++ checker; physical FPGA operation.

## Evidence and publication

- Raw logs: `results/raw/rtl/order_book/`
- Processed report: `results/processed/WIRE-023-order-book-rtl.md`
- Evidence index entry: EVID-023
- Working tree is expected clean after committing; publish to canonical GitHub only after all acceptance checks close.

## Exclusions

No deterministic BUY/SELL decision logic, risk-budget RTL, P&R, timing/throughput claim, Architecture B, or CDC work.
