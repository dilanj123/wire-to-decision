# WIRE-027 — Isolate Bottlenecks and Run One Small Timing Experiment

## Result

**PASS.** The isolated measurements show the byte-serial parser is the throughput limiter for the tested mutation workloads; the EBR-backed book is the routed clock-frequency limiter. One register-stage write-plan experiment reduced LUT use and improved all five routed Fmax results, while preserving the production store and functional behavior. Timing still misses the 156.25 MHz objective. Evidence supports a small controlled Architecture-B parser experiment as the next task; no B RTL was implemented here.

## Starting state and scope

- Starting HEAD: `3190269da9b8e8c276f47d947ed43989add3c3ca`; branch `main`, clean and equal to `origin/main`.
- Gate-0 peeled commit: `06f5643a940ac2c6fcfab0e377169b48ce700107`.
- WIRE-026/026A reports and original five-seed results were retained.
- Only production RTL changed: `rtl/common/wire_order_book.sv`. The 512 × 2 store, 1,024-entry capacity, EBR mapping, hash, allocation, mutation semantics and interfaces are unchanged.

## Isolated service measurements

The new public-interface Cocotb harness compares the complete parser with a ready event consumer, the production-size book with a ready commit consumer, and the decision engine with direct commits. Across the seven-mutation workload, parser event intervals were 86–107 cycles (about 0.96 input bytes/cycle); ordinary book service interval was 5 cycles/event (7 for cross-set replacement); direct decision latency was 1 cycle. The functional-top canonical measurements remained 116, 146 and 697 cycles for the single, two-message and stateful workloads. Stage latencies overlap in the top and are not summed.

## Timing experiment

At successful evaluation, the RTL now registers a validated write plan: replacement row/valid bits, post-mutation aggregates and old-way selection. The subsequent write state consumes those registered values. Cross-set replacement remains serialized; commit is published after its final write. No extra service cycle was observed.

Production-size `synth_ecp5` still infers 16 DP16KD EBRs and fits. Yosys LUT4 changed from 7,876 to 7,376; FFs from 3,586 to 3,943; distributed DPR16X4 remains 16. nextpnr combinational cells changed from 8,904 to 8,404. All five fixed seeds placed and routed at the original constraint. Fmax improved from 42.70–45.45 MHz to 45.68–47.66 MHz; none meets 156.25 MHz. Median Fmax improved from 43.63 to 47.08 MHz. The critical path remains an order-row EBR output through selected-entry/valid checks and aggregate/update logic to the registered write-plan register control. This is a modest timing improvement, not timing closure.

## Verification

- Focused suites: order book 9/9, parser-book 4/4, functional top 15/15; isolation harness 3/3.
- Full WIRE-025 campaign: 110/110 Cocotb tests, 79/79 established SBY jobs, Python 71/71; the two historically solver-bound monolithic jobs remain excluded and retain their historical status.
- All seven WIRE-023 order-book formal jobs passed at their unchanged configured depths; SBY 0.69, Yices 2.7.0. No formal assumptions or properties were weakened.
- Verilator functional-top lint and the isolation-top Verilator/Cocotb build passed.
- The full-top L1/L2/L3 and workload cycle metrics are unchanged from WIRE-026A. The canonical wrapper is excluded from those core measurements.

## Architecture decision and limits

**BUILD B is justified as a narrow experiment.** For the tested frames, the parser emits mutation events roughly 17–20× less frequently than the book can service them. Decision service is faster still. Parser serialization therefore dominates cycles per mutation/frame, while the book dominates achievable clock frequency. A native-64 parser experiment can plausibly improve workload throughput by feeding the unchanged shared book more efficiently; it is not expected to repair the book-limited Fmax. Keep Architecture B unauthorized until its separately scoped experiment is reviewed. No B implementation, CDC, P&R beyond the frozen A rerun, physical measurement, or application performance claim is part of WIRE-027.

See [processed report](../results/processed/WIRE-027-bottleneck-experiment.md) and raw logs/JSON/CSV under `results/raw/implementation/wire027/`.
