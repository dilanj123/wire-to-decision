# WIRE-024 — Decision RTL and Single-Clock Functional MVP Evidence

## A. Starting state and authority

Authorized start was local `main` at `4e9a98c9b7d2e0b78eb4dc4b000c44c96df970e4`, with `origin/main` at `50a5e7c68bc383ef719862966dc675ba6c61a79e`. The authorized preparatory commit was preserved. Gate-0 peeled SHA remained `06f5643a940ac2c6fcfab0e377169b48ce700107`. Relevant decision, error, aggregate and recovery requirements, WIRE-D010/D018/D019, WIRE-012/013/023 evidence, and Python decision/oracle were reviewed; no conflict was found.

## B. WIRE-D020

A successful book commit handshake is the only decision-evaluation boundary. The threshold and initial budget are captured on synchronous reset/rearm; `decision_enable` is sampled live on the commit handshake. Previous imbalance advances on every accepted commit, including disabled and exhausted-budget commits. A generated decision consumes budget immediately and is held stable until accepted. An earlier generated decision is not cancelled by later recovery. Rearm/reset clears it and establishes a new configured epoch.

## C. RTL architecture and interface

`wire_decision_engine` accepts commit valid/ready, Mold sequence, ITCH timestamp, and post-mutation 48-bit bid/ask totals. It outputs decision valid/ready, action (`0 BUY`, `1 SELL`), triggering sequence/timestamp, signed 49-bit imbalance, previous imbalance, remaining 32-bit budget, and 32-bit decision count. `wire_arch_a_functional_top` composes `wire_arch_a_parser_top` through `wire_order_book` and the decision engine, and exposes parser/book/decision status and diagnostic observability.

Current imbalance is computed as signed 49-bit `signed({1'b0,bid}) - signed({1'b0,ask})`, representing the full range `-(2^48−1)..+(2^48−1)`. Threshold is unsigned 48-bit and negative threshold is formed in 49-bit signed arithmetic. BUY is `previous < +T && current >= +T`; SELL is `previous > -T && current <= -T`. Threshold zero is not special-cased. There is no decision optimization or performance claim.

## D. Simulation

Toolchain: Verilator 5.053; Cocotb 2.1.0.dev0+41564633; Python 3.11.6.

- Standalone decision engine: 7/7 PASS. Directed boundaries, no-repeat, recross, threshold zero, enable suppression/no stale event, budget zero/one/multiple, maximum aggregate/threshold values, metadata, stalled output, rearm/capture, and deterministic random trajectories seeds 1, 7, 19, 42, 97.
- Full external 64-bit ingress functional top: 10/10 PASS. Tests cover all supported mutation mappings A/F/E/C/X/U/D, P, heartbeat, tracked-locate and outer filters, BUY/SELL, no-repeat/recross, live enable, budget exhaustion, parser and book fatal cases, explicit rearm, late malformed Mold suffix, structurally valid Mold with unsupported ITCH, pending decision under later recovery, and random replay seeds 1, 7, 19, 42, 97.
- Full-top outputs and state were cross-checked against `ReferenceOracle`; no Python production changes.

An initial randomized vector put a malformed next-block length immediately after a single complete ITCH message and failed to create a Python-expected decision before recovery; the event had not yet crossed the book commit boundary when the suffix error became known. The vector was revised to the task-required late-suffix shape with two complete prefix messages followed by a truncated third message. This is consistent with WIRE-D018/D019 handshake-based no-rollback semantics. The revised 10/10 integration run passes. The original investigation log is retained as test-development evidence.

## E. Prefix/no-rollback behavior

The directed full-top late-suffix regression observes complete prefix mutations and any qualifying prefix decision remain committed; the incomplete suffix creates no mutation or decision, the book/parser enter recovery, and new frames block until rearm. A separate full-top stall test holds a qualifying decision while a later unsupported ITCH message asserts recovery; the decision tuple stays stable and is delivered exactly once after release, with no later decision.

## F. Formal

SBY 0.69, `smtbmc yices`, Yices 2.7.0.

1. `decision_reference.sby`: BMC depth 16, PASS against a public-input shadow transaction model. Checks 49-bit signed arithmetic, crossing/output correspondence, metadata, previous trajectory, credit/count conservation, reset/rearm state, no spontaneous/repeated pending decisions, and stall stability. Initial synchronous reset and stable upstream commit tuple while stalled are assumed. Decision readiness and commit payload otherwise remain symbolic. This is bounded, not inductive.
2. `prefix_recovery.sby`: fixed-vector/reduced-model BMC depth 8, PASS. `wire_order_book` uses `NUM_SETS=2`; one fixed ADD creates a BUY decision held stalled, then a later upstream fatal quarantines the book while the prior decision remains valid/stable and new event/commit acceptance is blocked. No DUT-private state is read by the assertions. This is not proof for all book states or the full parser top.

No formal covers are claimed; these are assertion BMC jobs. Detailed assumptions are in `results/raw/rtl/decision_engine/formal_property_inventory.txt`.

## G. Tool checks

Verilator strict lint/build passed for standalone decision engine and complete functional top with no meaningful warnings. Yosys 0.69+154 hierarchy/process/opt/check/stat passed for both; zero check problems. Classification: `SYNTHESISED COMPONENT SANITY`. No nextpnr/P&R.

## H. Regression preservation

The fresh sequential Verilator regression log records PASS for WIRE-014 through WIRE-023 suites: gearbox 6; ingress buffer 5 plus composition 1; Ethernet 4 plus composition 1; IPv4 standalone 5 plus composition 3; UDP standalone 5 plus composition 3; Mold controller 14 plus composition 2; Mold framer 10 plus composition 2; ITCH decoder 6 plus composition 2; WIRE-022 parser 6; WIRE-023 book 9; parser→book 4. WIRE-023's seven formal jobs were rerun and PASS. Decision engine 7 and functional top 10 passed separately with final retained logs. Python full suite: 71/71 PASS.

## I. Requirement traceability and classification

- REQ-DEC-001: aggregate interface/representation originated in WIRE-023; decision uses its post-mutation totals.
- REQ-DEC-002..007 and WIRE-D010 behavior: decision functional behavior `RTL-SIMULATED`; named local properties `FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS` at BMC depth 16 plus the fixed-vector depth-8 composition check.
- REQ-ERR-002..004: book/parser recovery and committed-prefix behavior `RTL-SIMULATED`; prefix pending-decision retention also fixed-vector checked at depth 8. No complete-application formal proof.
- Complete parser→book→decision MVP: `RTL-SIMULATED`.
- Yosys: `SYNTHESISED COMPONENT SANITY` only.

## J. WIRE-023 documentation correction

The WIRE-023 traceability now states REQ-DEC-001 aggregate representation was implemented and simulated there, while REQ-DEC-002..006 decision behavior remained unimplemented at WIRE-023.

## K. Still unproven

Phase-4 deep functional regression, comprehensive application formal proof, ECP5 application synthesis/P&R and multi-seed routing, timing closure, L1/L2/L3 latency, measured initiation interval/throughput, Architecture-A bottleneck, Architecture-B authorization, CDC/RDC, independent C++ checker, physical FPGA operation.

## L. Conclusion

WIRE-024 PASS. Phase 3 is complete; Phase 4 is next. Functional regression and verification-gate checklist items remain open. No P&R or application performance claims are made.
