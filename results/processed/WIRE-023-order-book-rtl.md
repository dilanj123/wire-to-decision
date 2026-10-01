# WIRE-023 — Bounded Order-State and Aggregate RTL

## A. Starting state and authority

Started on clean `main` at `ecacb89d26ce7b12acdc011bbefd9cdf08265836`, equal to `origin/main`; Gate-0 peeled commit remained `06f5643a940ac2c6fcfab0e377169b48ce700107`. Phase 1 and Phase 2 were complete, Architecture-A parser was checked in the master checklist, bounded order state/decision remained unchecked, and Architecture B remained unauthorized.

Authority was REQ-BOOK-001..008, REQ-DEC-001, REQ-ERR-001..004, WIRE-D006/D008/D009/D017/D018, WIRE-011 book-model evidence, WIRE-022 parser integration, Python book/hash, canonical event types, and the Architecture-A parser top. No authority conflict was found.

## B. WIRE-D019

The normalized mutation input accepts one transaction at a time. Store and corresponding side aggregate are updated atomically; only a successful update emits a ready/valid commit containing input Mold sequence, ITCH timestamp, and post-update aggregate values. Failed mutation emits no successful commit. Upstream fatal blocks new input. If the event handshook before fatal became known, that event can complete and its commit remains; then the book is invalid/recovery-required. Reset/rearm clears to an empty, valid epoch. This is a no-rollback boundary.

## C. Architecture and mutation semantics

`rtl/common/wire_order_book.sv` defaults to 512 sets × 2 ways, 1,024 entries, with reference[63:0], price[31:0], remaining quantity[31:0], side, and valid. Hash is the exact WIRE-D006 nine-bit XOR fold. Search is limited to the selected set. Empty set allocation is way 0 then way 1. Full sets fail closed; there is no eviction.

ADD, E, C, X, D and U implement the WIRE-011 semantics with the contract-validity checks from WIRE-D017. C does not modify the resting price. REPLACE inherits old side and supports same-set, cross-set, and same-reference replacement; conflict/full destination errors leave all selected entries and aggregates unchanged. Invalid event kind/validity patterns and zero quantities where prohibited fail closed.

Bid/ask totals are unsigned 48-bit. Widened signed candidate arithmetic detects underflow/overflow before any store write. A bounded maximum is `1024 × (2^32 − 1) < 2^42 < 2^48`. Explicit guards remain in RTL despite the valid-state bound.

## D. Interfaces and status

Book input is the complete WIRE-D017 event tuple plus `upstream_recovery_required`. Outputs include event ready, successful commit valid/ready and `{mold_sequence, itch_timestamp, bid_total, ask_total}`, `book_valid`, `recovery_required`, bid/ask totals, stable error valid/ready/code, and read-only diagnostic lookup. Error codes 0..8 are respectively event contract, duplicate, collision capacity, unknown reference, over-execute, over-cancel, new-reference conflict, aggregate range, and upstream fatal.

`rtl/arch_a/wire_arch_a_parser_book_top.sv` exposes the frozen parser configuration/external beat ingress, book status/commit/error, stage rejection diagnostics, event observation, and diagnostic lookup. Decision configuration/output is not present.

## E. Cocotb simulation

Verilator 5.053; cocotb 2.1.0.dev0+41564633. Standalone order-book test module: **9/9 PASS**. Five deterministic random seeds: 1, 7, 19, 42, 97. The production default was filled with 1,024 entries at maximum 32-bit quantity; no eviction occurred and aggregate remained below 2^42. Directed/model tests include D006 exact vectors, way selection, ADD, E/C/X/D/U, all specified fail-closed cases, C-price preservation, cross-set U atomic failures, commit stability, upstream-fatal ordering, rearm, and independent dictionary recomputation.

Parser→book full-ingress composition: **4/4 PASS**. Five complete Ethernet frames were accepted across the four tests (one further new-frame attempt was blocked during recovery). Expected/observed successful commits total 9: five A/E/X/U/D updates; two complete-prefix updates before late Mold truncation; one ADD before unsupported ITCH semantic recovery; and one fresh ADD after outer-fatal rearm. No malformed message mutated state. The late suffix preserved earlier aggregate/state but did not advance expected Mold sequence; the structurally valid Mold/unsupported ITCH case preserved structural sequence advancement and quarantined the book. Outer IPv4 checksum fatal produced no mutation and rearm restored operation.

`ReferenceOracle` was used for the valid, structural-late-suffix and semantic-failure scenarios; final book totals matched. Standalone expected mutation behavior uses an independent dictionary scoreboard. Python suite: **71/71 PASS**.

## F. Formal jobs

SBY 0.69, `smtbmc yices`, Yices 2.7.0. All new order-book jobs are BMC/fixed-vector, no unbounded proof is claimed. References use only public DUT inputs/outputs, including public read-only diagnostics; no private state.

Harness refinement is retained honestly: the first one-set vector abstraction hit a zero-width `$clog2(1)` slice and failed its public debug assertions; it was replaced with a valid two-set abstraction and the mutation vector passed at depth 28. This was an invalid formal abstraction, not an RTL counterexample. A proposed assertion that no commit can remain while recovery is active was also rejected because WIRE-D019 explicitly allows an already-accepted mutation commit to remain pending. The final safety result is bounded BMC; no induction result is claimed.

- Safety BMC depth 12, reduced two-set instance: commit/error stability during stall; recovery persistence; event-ready suppression under local/upstream recovery; reset/rearm empty/valid state.
- Hash fixed-vector BMC depth 6, production 512-set default: D006 low/high-bit vectors.
- Mutation fixed-vector BMC depth 28, reduced two-set instance: ADD, E, C, X, same-reference U, D; exact public entry/aggregate/commit metadata; C leaves price unchanged.
- Collision/U atomicity fixed-vector BMC depth 20, reduced two-set instance: no-eviction at full selected set; full-destination cross-set U fails with old/destination state and totals preserved.
- Duplicate fixed-vector BMC depth 12 and unknown-reference E fixed-vector BMC depth 8, reduced two-set instances: no silent successful commit; error/quarantine/public state checks.
- Upstream fatal ordering fixed-vector BMC depth 10, reduced two-set instance: accepted event completes under a later fatal; commit tuple is held while stalled and new event input remains blocked.

The standalone 1,024-entry fill is simulation, not formal. Reduced two-set jobs do not establish properties for all 512 sets. Formal harness cover statements were not run as separate cover jobs.

## G. Verilator and Yosys

`verilator --lint-only --Wall` passed for the standalone book and parser→book top with no meaningful warnings. Yosys 0.69+154 completed `hierarchy; proc; opt; check; stat` for both hierarchies. Generic statistics were 1,455 cells / 133,120 memory bits standalone and 2,637 cells / 133,618 memory bits for the full composition hierarchy (including parser state; the book submodule accounts for 133,120 bits). Classification: `SYNTHESISED COMPONENT SANITY`; no target mapping/P&R claim.

## H. Regression preservation

Fresh simulation regressions: WIRE-014 6/6; WIRE-015 5/5 + 1/1 composition; WIRE-016 4/4 + 1/1; WIRE-017 5/5 + 3/3; WIRE-018 5/5 + 3/3; WIRE-019/019A 14/14 + 2/2; WIRE-020 10/10 + 2/2; WIRE-021 6/6 + 2/2; WIRE-022 6/6; Python 71/71.

Prior formal suites through WIRE-022 were rerun from their established source roots. Six initial gearbox/ingress invocations from the wrong working directory failed during SBY file staging; the same six jobs were rerun from repository root and passed. Historical solver-bound WIRE-017 monolithic correspondence and WIRE-022 depth-270 full-top suffix jobs remain historical limitations and were not relabeled.

## I. Requirement traceability and evidence classification

- REQ-BOOK-001..008: bounded architecture, event mutation semantics, no eviction, aggregates and local integrity failures are RTL-simulated; named properties are bounded/fixed-vector checked at the scopes above.
- REQ-ERR-001..004: book local invalid/recovery and parser fatal ordering are simulated/formally checked within fixed/reduced local scope. Prior committed events are retained; no rollback is implemented.
- REQ-DEC-001: decision behavior is not implemented or verified.

Classification: bounded store/aggregates `RTL-SIMULATED`; named local properties `FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS` at bounded/fixed/reduced scopes; parser→book `RTL-SIMULATED`; Yosys `SYNTHESISED COMPONENT SANITY`.

## J. Remaining work

Deterministic decision/risk-budget RTL and parser→book→decision integration; complete functional regression and verification gates; application synthesis/P&R/timing; L1/L2/L3 latency; measured throughput/initiation interval; Architecture-A bottleneck; Architecture B authorization; CDC/RDC; C++ checker; and physical FPGA operation remain unproven. Phase 3 remains active. Next task is WIRE-024; it was not started here.
