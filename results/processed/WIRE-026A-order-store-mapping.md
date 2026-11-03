# WIRE-026A — Order-store EBR mapping and routed rerun

## Result

The targeted order-store memory-access refinement resolved the original ECP5 LUT fit failure. The production store remains 512 sets × 2 ways / 1,024 entries. The complete benchmark top now places and routes for seeds 1, 7, 19, 42 and 97. All routed seeds miss the frozen 156.25 MHz objective, with Fmax 42.70–45.45 MHz.

## Change

`rtl/common/wire_order_book.sv` packs both ways into one 258-bit row per set and uses synchronous registered reads, a single write path and a small FSM to sequence lookup/evaluation/write, including cross-set REPLACE. Valid bits are reset separately. Diagnostic lookup is registered and idle-only. Aggregate/commit publication occurs only after the last required memory write. Mutation behavior, hash/way selection, no-eviction rule and externally visible interfaces remain unchanged.

## Mapping and route

| Metric | Original WIRE-026 | WIRE-026A |
|---|---:|---:|
| Yosys LUT4 | 138,733 | 7,876 |
| FF | 68,997 | 3,586 |
| DP16KD EBR | 0 | 16 |
| Distributed DPR16X4 | 2,128 | 16 |
| nextpnr combinational cells | 152,295 estimated; over capacity | 8,904 |

All five seeds route. The critical paths start at `order_row_mem` EBR outputs and end at row-memory write inputs or valid-bit updates after selected-entry checks and aggregate/update logic. Slack against 6.4 ns ranges from -15.600 to -17.021 ns. Detailed per-seed data is in `results/raw/implementation/arch_a/five_seed_results_026a.csv` and corresponding JSON/logs.

The wrapper has 113 top-level bits. The frozen package specification lists 205 user I/Os; nextpnr reports 365 available `TRELLIS_IO` cells and uses 113. No package pin assignment or board I/O timing validation was done. Serializer readout can backpressure the wrapped decision output, but the canonical cycle measurements bypass the serializer.

## Verification and performance

- WIRE-014..024 cocotb: 110/110 PASS; full WIRE-023 order-book fill and full-top tests included.
- Python: 71/71 PASS.
- Wrapper tuple reconstruction: 1/1 PASS.
- Verilator full benchmark hierarchy lint: PASS.
- All seven WIRE-023 order-book SBY jobs: PASS after updating old fixed-cycle observation points for the synchronous RAM FSM; mode/depths are in `formal/order_book/*.sby`. SBY 0.69, Yices 2.7.0. First stale-cycle failures remain retained as historical harness-latency findings, not RTL semantic counterexamples.
- ECP5 `synth_ecp5`: PASS; 16 EBR blocks inferred. Five-seed placement/routing: 5/5 PASS; timing target: 0/5 met.

The unwrapped full-top cycle tests measured 0.862–0.958 accepted external bytes/cycle, with natural RX stalls. L1/L2/L3 and event/decision intervals are tabulated in `results/raw/implementation/arch_a/latency_throughput_026a.csv` and the combined WIRE-026 report.

## Architecture decision

**MODIFY HYPOTHESIS.** The routed clock path is the sequential book EBR read/compare/aggregate/write path. The end-to-end tests also show byte-serial processing, but do not isolate parser cycles from book service cycles enough to justify a parser alternative. First measure parser-only versus book/decision cycle contribution and investigate the book path. Architecture B remains unauthorized.
