# WIRE-026A — ECP5 order-store memory mapping and implementation rerun

## Status

**PASS for the combined WIRE-026 implementation/measurement campaign, with the 156.25 MHz timing objective missed.** All five fixed seeds placed and routed. Phase 5 implementation evidence is complete; timing closure is not.

## Starting state and preserved work

- Workspace: `/Users/Dilan/Projects/wire-to-decision`
- Starting `main` / `origin/main`: `e2527db38f126288c5c31b021dc607938e717bb8`
- The working tree contained only the authorized, uncommitted WIRE-026 benchmark, tests, raw results, reports and state/checklist updates. Those changes were preserved and completed here.
- Protected Gate-0 peeled SHA: `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## Cause and correction

The original `wire_order_book` used asynchronous/dynamically indexed multi-address order-row reads and multiple update branches. Yosys mapped the large order store into FFs/distributed LUT RAM rather than EBR, leading to 138,733 LUT4, 68,997 FF, 2,128 distributed `TRELLIS_DPR16X4`, no `DP16KD`, and a 182% pre-placement LUT estimate.

`rtl/common/wire_order_book.sv` now holds the two ways for each of 512 sets in one packed row RAM, uses synchronous registered reads, a single row write path and a short FSM for reads/evaluation/writes. Resettable valid bits are separate; debug lookup is registered/idle-only. Cross-set REPLACE validates both sides before writes, serializes invalidation/insertion, and publishes aggregate/commit only after the final write. Production capacity, WIRE-D006 hash, WIRE-D009 allocation, mutation semantics, error/recovery and commit contract remain unchanged. The production-size table now maps to 16 EBRs and the design routes.

## Verification and tool results

- WIRE-023 order book 9/9, parser→book 4/4, functional top 15/15.
- WIRE-014..024 aggregate cocotb regression: 110/110 PASS; Python 71/71 PASS.
- Benchmark wrapper tuple reconstruction: 1/1 PASS.
- Verilator full benchmark hierarchy: PASS, no warnings.
- All seven order-book formal jobs PASS with SBY 0.69 / Yices 2.7.0. The synchronous RAM FSM adds latency; existing fixed-vector checks were updated to sample the same public outcomes at the new cycles. First stale-cycle ADD/collision failures and traces are retained. Revised depths include ADD 20, collision 40, duplicate 18; all other jobs/depths remain in their `.sby` files and raw logs. Other established WIRE-025 formal jobs passed before the first stale order-book vector stopped the original aggregate driver. Fresh full regression logs are under `results/raw/implementation/arch_a/wire025_regression_rerun/`; historical tracked WIRE-025 logs were restored unchanged after copying.
- Yosys `synth_ecp5`: 7,876 LUT4, 3,586 FF, 16 DP16KD EBR, 16 small distributed DPR16X4; hierarchy/check found zero design problems.
- nextpnr: all seeds placed/routed; Fmax 42.70–45.45 MHz, timing objective 156.25 MHz missed in every seed. Resource and timing details are in the processed report and CSV.
- Latency/throughput measurements were repeated on the full unwrapped functional top after the RAM access change; results are recorded in `latency_throughput_026a.csv`.

## Constraints and architecture conclusion

Top-level width is 113 bits; frozen device documentation lists 205 package user I/Os, and nextpnr reports 365 `TRELLIS_IO` cells available. No physical pinout was assigned or validated. Serializer output is lossless but may backpressure decision readout; canonical cycle measurements bypass it.

**MODIFY HYPOTHESIS.** The measured routed critical path is the book's EBR read/compare/aggregate/write path. The parser accepts about 0.86–0.96 bytes/cycle on measured workloads with natural ingress stalls, but these workloads do not isolate parser serialization from book/decision service. First isolate those cycle costs and investigate the measured book path before deciding whether a parser alternative helps. Do not build Architecture B here.

No P&R timing closure, physical hardware operation, board I/O timing, application formal proof, or physical throughput claim is made. No production protocol behavior or Python reference behavior changed.

## Evidence

- Task: `tasks/WIRE-026A.md`
- Combined implementation report: `results/processed/WIRE-026-arch-a-implementation.md`
- Raw synthesis, five routed seed logs/JSON reports, CSVs, regression, formal and wrapper evidence: `results/raw/implementation/arch_a/`
- EVID-026A: `docs/EVIDENCE_INDEX.md`
