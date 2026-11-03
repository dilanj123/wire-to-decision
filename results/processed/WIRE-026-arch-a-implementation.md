# WIRE-026 — Architecture-A implementation and measurement

## Result

**PASS for the WIRE-026 implementation/measurement stage, with a recorded timing miss.** The full 512-set × 2-way functional design maps into the frozen ECP5-85K, and all five fixed seeds place and route. None meets the 156.25 MHz objective. The best routed Fmax is 45.45 MHz; the five-seed range is 42.70–45.45 MHz. This closes the requested implementation evidence campaign; it does not claim timing closure or physical FPGA operation.

WIRE-026 originally stopped PARTIAL because the order table mapped to distributed LUT RAM and exceeded LUT capacity. WIRE-026A made one order-store access refinement, reran the functional/formal regressions, inferred EBRs, and completed the same frozen five-seed P&R campaign. The historical failed WIRE-026 synthesis and placement logs remain intact.

## Setup and wrapper

Target: LFE5U-85F-8BG381C, nextpnr `--85k --package CABGA381 --speed 8`, 156.25 MHz / 6.4 ns. P&R used the same synthesized netlist and settings for seeds 1, 7, 19, 42, 97, `--lpf-allow-unconstrained`, and `--timing-allow-fail`. Tools: Yosys 0.69+154; nextpnr-ECP5 0.11.1-34-gc4f4bb55; Verilator 5.053 devel; Cocotb 2.1.0.dev0+41564633; Python 3.11.6; SBY 0.69; Yices 2.7.0.

`rtl/arch_a/wire_arch_a_benchmark_top.sv` instantiates the actual complete functional top and production-size 512 × 2 book, preserving its full 64-bit post-MAC interface. Fixed legal configuration is recorded in `tasks/WIRE-026.md`. The top has 113 port bits. This is below the frozen package's 205 user-I/O figure by bit count; nextpnr separately reports 365 available `TRELLIS_IO` cells and uses 113. No pin assignment or physical package-pin validation was performed. A six-word 32-bit ready/valid serializer losslessly reconstructs the complete decision tuple. Wrapper equivalence is 1/1 PASS. The serializer may backpressure decision acceptance if its readout stalls. It is absent from the canonical cycle measurements, which use the core with `decision_ready=1`; it is not on the reported critical path.

## Order-store mapping and resources

The original failure came from asynchronous/dynamic multi-address order-entry access and multiple update cases that prevented the large order data from becoming a synchronous EBR memory. The store was represented largely as FFs and distributed LUT RAM. WIRE-026A packs both ways into one row per set, uses synchronous registered row reads and a single write path, sequences lookups and cross-set replacement through a small FSM, and keeps resettable valid bits separate from packed row data. The diagnostic lookup is idle-only and registered. No entry capacity, hash, way-selection, mutation, aggregate, commit, or no-eviction semantics changed. Replacement writes are serialized; totals and successful commit become visible only after the final required row write.

| Mapping | Yosys LUT4 | FF | DP16KD EBR | distributed DPR16X4 | P&R LUT/COMB | Result |
|---|---:|---:|---:|---:|---:|---|
| Original WIRE-026 | 138,733 | 68,997 | 0 | 2,128 | 152,295 estimated | did not fit |
| WIRE-026A | 7,876 | 3,586 | 16 | 16 | 8,904 | placed/routed |

The packed order rows are inferred as 16 EBRs configured with 36-bit data ports; the 258-bit row width is split across EBRs and read/write ports. The remaining 16 small distributed RAM cells are not the large order table. `synth_ecp5` completed hierarchy/process/check with zero design problems. P&R uses 8,904/83,640 combinational cells (10.65%), 3,586/83,640 FFs (4.29%), 16/208 EBRs (7.69%), 0/156 multipliers, and 113/365 nextpnr I/O cells (31.0%). The 365 `TRELLIS_IO` availability is a nextpnr device-cell count; the package reference separately lists 205 user I/Os. Yosys logged its experimental `write_xaiger2` feature warning and ABC informational carry/AIG warnings.

## Five-seed placement and routing

The routed critical path in every seed is an order-book read/update path: an EBR row output feeds selected-entry/valid comparison and aggregate/update logic, then returns to order-store write or valid state. The 6.4 ns target slack is computed from the routed critical-path delay. Each route completed normally, but timing failed.

| Seed | Placement | Routing | Target MHz | Routed Fmax MHz | Critical delay ns | Slack vs 6.4 ns |
|---:|---|---|---:|---:|---:|---:|
| 1 | PASS | PASS | 156.25 | 45.45 | 22.000 | -15.600 |
| 7 | PASS | PASS | 156.25 | 44.84 | 22.304 | -15.904 |
| 19 | PASS | PASS | 156.25 | 43.63 | 22.922 | -16.522 |
| 42 | PASS | PASS | 156.25 | 42.81 | 23.361 | -16.961 |
| 97 | PASS | PASS | 156.25 | 42.70 | 23.421 | -17.021 |

The paths begin at an `order_row_mem` EBR output and terminate at an order-row memory input or `order_valid_mem` update. Per-seed reports/logs are retained; `five_seed_results_026a.csv` is the compact result table. This identifies a clock-frequency limiter in the book read/modify/write path, not in the benchmark serializer. Unconstrained I/O is a board-independent experiment setting, not I/O timing closure.

## Cycle measurements

Measurements use Cocotb/Verilator on the unwrapped complete functional top, `decision_ready=1`, legal held-beat source behavior, and actual accepted ready/valid transfers. L1 is first accepted ITCH message payload byte to normalized-event transfer. L2 is final ITCH message payload byte (`in_last`) accepted at that byte-stage boundary to decision-valid observation. L3 is first accepted post-MAC 64-bit beat of the decision's frame to decision-valid observation. Accepted bytes count set bits in accepted `keep` masks. Elapsed cycles run from the first accepted frame beat through the expected event/decision observations; RX stall cycles are sampled valid-but-not-ready input cycles.

| Workload | Bytes | Cycles | L1 | L2 | L3 | Event II | Decision II | Bytes/cycle | RX stall cycles |
|---|---:|---:|---:|---|---|---|---|---:|---:|
| Single ADD → BUY | 100 | 116 | 37 | 7 | 115 | — | — | 0.862069 | 71 |
| Two-message Mold packet | 133 | 146 | 37 | 7 | 115 | 35 | — | 0.910959 | 101 |
| Stateful A/F/E/C/X/U/D frames | 668 | 697 | 37 | 7, 7, 9 | 115, 131, 131 | 107, 98, 103, 90, 102, 86 | 107, 395 | 0.958393 | 583 |

These are simulation cycles and accepted-byte rates, not measured physical throughput. At the nominal 156.25 MHz only, cycles would correspond to 6.4 ns each; those derived times are not supported by routed timing because the achieved clock is much slower. No external wire latency is claimed. The core sees natural input backpressure in these workloads. The benchmark serializer does not affect these no-stall decision measurements.

## Verification and formal evidence

- Wrapper decision tuple equivalence: 1/1 Cocotb PASS.
- Full WIRE-026 measurement test: included in WIRE-024 functional-top 15/15 Cocotb PASS.
- Regression Cocotb totals across WIRE-014..024: 110/110 PASS (the WIRE-025 baseline 109 plus the WIRE-026 measurement case). Per-suite counts are in `wire026a_regression_complete.log`.
- Python: 71/71 PASS.
- Verilator full benchmark hierarchy lint: PASS, no warnings.
- WIRE-023 production book simulation: 9/9, including the full 1,024-entry capacity fill; parser→book: 4/4; functional top: 15/15.
- The memory-access FSM made old fixed-cycle formal vectors assert too early. The first stale ADD/collision vector failures and traces are retained. The vectors were updated to observe the same public behavior at the new legitimate latency, not weakened; all seven order-book SBY jobs then passed. SBY 0.69 / Yices 2.7.0, `smtbmc` bounded/fixed-vector jobs. Revised ADD depth 20, collision depth 40, duplicate depth 18; hash, safety, unknown-reference and upstream-order jobs also PASS at their recorded configuration. The other established WIRE-025 formal jobs passed in the regression run before it reached the stale order-book vectors. Fresh order-book results are in `wire025_regression_rerun/order_book_formal/` and individual `wire026a_formal_*.log` files. The two historical large monolithic solver-bound jobs remain solver-bound, not PASS.
- The first Cocotb rerun found only a stale same-cycle debug-read test assumption; the diagnostic lookup is now tested after its registered idle read. All functional tests passed without weakening semantic assertions.

## Bottleneck decision and limits

**MODIFY HYPOTHESIS.** The store now fits and routes, so the original resource-fit blocker is resolved. The routed clock-frequency limiter is the sequential EBR book read/compare/aggregate/write path (42.70–45.45 MHz), while the measured end-to-end workloads accept about 0.86–0.96 external bytes/cycle and show large natural ingress backpressure. Parser byte serialization contributes cycles, but the current evidence does not isolate its share from multi-cycle book processing enough to justify Architecture B. First isolate parser-only versus book/decision cycle contribution and investigate the measured book path; then decide whether parser parallelism would improve the bottleneck. Architecture B remains unauthorized.

No timing closure at 156.25 MHz, routed physical throughput, board pinout/timing, P&R-derived latency in ns, application-wide formal proof, CDC/RDC, C++ checker, or physical FPGA operation is claimed. Evidence labels: functional/cycle behavior `RTL-SIMULATED`; named local formal jobs `FORMALLY CHECKED UNDER DOCUMENTED BOUNDED/FIXED-VECTOR SCOPES`; ECP5 mapping/P&R `SYNTHESISED COMPONENT SANITY` and routed implementation evidence with timing failure.
