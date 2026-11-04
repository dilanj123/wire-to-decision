# WIRE-028 — Architecture-A/B parser experiment

## Result

**PASS as a completed controlled experiment; REJECT B for this project baseline.** Architecture B is functionally demonstrated at the tested profile and routed for five seeds. It remains experimental; Architecture A remains the production baseline. B roughly halves workload cycles, but routes at less than half A's conservative estimated clock rate, uses about 1.97× LUT4, and has lower derived end-to-end byte rates at each architecture's conservative routed-frequency estimate. Neither design meets 156.25 MHz.

## Synthesis diagnosis and final implementation

Yosys 0.69+154 first completed `PROC_MEMWR`; the expensive stage was downstream control-graph/FSM processing of eight ordered byte-lane state transitions. An eight-lane `fsm_encoding="none"` diagnostic completed but remained slow and large (full-top 41,823 LUT4; a diagnostic route reached 4.25 MHz). The final source retains the attribute and limits the lane walk to at most **two consecutive bytes per cycle**, preserving the 64-bit beat/cursor and bounded protocol/message state. The cursor monitor observes two-byte advances. Because both the attribute and lane width differ from the original run, this evidence does not isolate each change's contribution. No Architecture-A, book, or decision RTL changed. Yosys documents that `fsm_encoding="none"` prevents automatic FSM detection for the marked state signal; the experiment treated this as a synthesis control, not an efficiency guarantee ([Yosys FSM handling](https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/index_passes_fsm.html)).

With the two-lane parser, parser-only ECP5 synthesis completed in 32.70 s (9,431 LUT4, 1,539 FF, 16 distributed DPR16X4). Full benchmark synthesis completed in 45.79 s: 14,559 LUT4, 3,700 FF, 16 DP16KD EBR, 16 distributed DPR16X4. The production 512×2 book remains EBR-backed and the complete benchmark fits the device's mapped resource capacities.

## Functional and formal evidence

- A/B parser comparison: **8/8 Cocotb PASS**, including all supported mutation types, P/filtering, lane/final-keep boundaries, malformed traffic, recovery/rearm, stalls, deterministic seeds 1, 7, 19, 42, 97, and byte-cursor conservation/progress.
- B parser→book→decision: **2/2 Cocotb PASS**, including ReferenceOracle comparisons for decision tuples, aggregates, sequence and budget across the measured workloads.
- Python model: **71/71 PASS**.
- Verilator 5.053 benchmark-top lint: **PASS**.
- SBY 0.69/Yices 2.7.0 public-interface safety BMC: **PASS, depth 12**; assumptions are reset initialization and stable input valid/data/keep/last while stalled. It checks recovery suppression, event tuple stability and rearm observations. It is bounded evidence, not an unbounded parser proof; cover statements were not separately run in cover mode.

## Matched full-top simulation measurements

The first three rows use the same WIRE-027 frames and configuration. Cycles are simulation cycles at the existing 10 ns test clock, starting with the first accepted external beat and ending after the pipeline drains. L1 is first relevant ITCH byte consumed to event handshake; for B this is instrumented at its byte cursor. WIRE-027 reports the first-event L1 only, while B logs each event. L2 is final required ITCH byte to decision handshake. L3 is first accepted external frame beat to decision handshake. B's internal byte cursor was observed for width; external accepted byte counts use `rx_keep`. Natural input stalls are included. Detailed values and definitions are in `results/raw/implementation/arch_b/ab_comparison_028b.csv`.

| Workload | Bytes | A cycles / B cycles | A bytes/cycle / B bytes/cycle | A L1/L2/L3 | B L1/L2/L3 | A/B event II | A/B decision II | A/B ingress stalls |
|---|---:|---:|---:|---|---|---|---|---|
| Single ADD→BUY | 100 | 116 / 58 | 0.862 / 1.724 | 37 / 7 / 115 | 18 / 6 / 57 | — / — | — / — | 71 / 29 |
| Two-message A+E | 133 | 146 / 75 | 0.911 / 1.773 | 37 / 7 / 115 | 18,16 / 6 / 57 | 35 / 17 | — / — | 101 / 41 |
| Stateful A/F/E/C/X/U/D | 668 | 697 / 350 | 0.958 / 1.909 | 37 (first) / 7,7,9 / 115,131,131 | 18,20,16,18,12,18,10 / 6,6,8 / 57,65,67 | 107,98,103,90,102,86 / 53,49,51,45,51,43 | 107,395 / 53,198 | 583 / 248 |

A separate five-frame B workload accepted 500 bytes in 262 cycles (1.908 bytes/cycle); it has no matched WIRE-027 A measurement and is not used to claim paired improvement. At a common **derived** 19 MHz clock, the paired workloads correspond to 16.38/17.31/18.21 MB/s for A and 32.76/33.69/36.26 MB/s for B. At each architecture's conservative minimum seed estimate (A 45.68 MHz, B 19.997 MHz), derived rates are A 39.38/41.61/43.78 MB/s and B 34.48/35.46/38.17 MB/s. These calculations multiply simulated byte/cycle by nextpnr estimated Fmax; they are not physical throughput measurements. B's L3 estimate is 2.85 μs at 19.997 MHz versus A's 2.52 μs at 45.68 MHz for the single-frame case; this is likewise derived, not measured hardware latency.

## ECP5 routing

Frozen target and controls: LFE5U-85F-8BG381C, nextpnr `--85k --package CABGA381 --speed 8`, 156.25 MHz, unconstrained I/O, `--timing-allow-fail`, seeds 1/7/19/42/97. All B seeds placed and routed successfully. The benchmark wrapper uses 113 of nextpnr's 365 available I/O cells for this selected device model; no package pinout validation was performed.

| Seed | Route | Fmax MHz | Critical delay ns | Slack vs 6.4 ns |
|---:|---|---:|---:|---:|
| 1 | PASS | 21.047 | 47.512 | -41.112 |
| 7 | PASS | 19.997 | 50.007 | -43.607 |
| 19 | PASS | 20.572 | 48.610 | -42.210 |
| 42 | PASS | 20.589 | 48.569 | -42.169 |
| 97 | PASS | 20.159 | 49.606 | -43.206 |

A's frozen WIRE-027 Fmax values are 47.21, 47.66, 45.68, 47.08 and 46.51 MHz. The B seed-1 critical path starts at the ingress FIFO `read_ptr_q`/data EBR output and ends at the parser `ip_index_q` register (47.512 ns). It traverses ingress data selection and parser state/index logic. The clock limiter therefore moved from A's order-book EBR/update path to B's parser path. The benchmark decision readout is outside this internal register-to-register critical path; no physical output timing claim is made.

| Full-top resource | A, WIRE-027 | B, WIRE-028B |
|---|---:|---:|
| Yosys LUT4 | 7,376 | 14,559 |
| FF | 3,943 | 3,700 |
| DP16KD EBR | 16 | 16 |
| Distributed DPR16X4 | 16 | 16 |
| DSP | 0 | 0 |

The exact routed netlists used for the seed runs are retained as lossless gzip files beside the raw reports to avoid committing oversized intermediate JSON. The clock target is missed for every seed. B's doubled parser work width does improve simulation cycles, but the clock estimate falls from A's 45.68 MHz conservative value to B's 19.997 MHz. The combined rate and LUT cost do not justify retaining B in the current project. No claim is made that two-byte parsing is the only possible B architecture or that another design could not improve the result.

## Evidence and limitations

Raw synthesis, all five route logs/reports, simulation, Python, formal and lint evidence are under `results/raw/implementation/arch_b/`. The final task record is `tasks/WIRE-028B.md`; the baseline and earlier failed synthesis logs remain retained. Architecture-B production use, timing closure, physical throughput/latency, package pinout, CDC/RDC, C++ checking and hardware operation remain unproven. The next project task is WIRE-029, minimal CDC/RDC extension; it is not started here.
