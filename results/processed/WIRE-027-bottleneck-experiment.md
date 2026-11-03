# WIRE-027 — Bottleneck isolation and timing experiment

## Result

**PASS.** The parser limits cycles per mutation/frame in the measured workloads; the order book limits routed clock frequency. A single registered write-plan change improved routed Fmax on every seed and reduced LUT use, but the design still misses the 156.25 MHz target. Evidence supports a small Architecture-B parser experiment; no B RTL was built.

## Measurements

Same qualified Cocotb/Verilator setup and representative legal traffic were used. Parser input was driven from complete post-MAC frames with event ready; the production 512 × 2 order book used direct normalized events with commit ready; the decision engine used direct successful commits. Full-top measurements reuse the WIRE-026A workload and signals. The wrapper serializer is not in the core cycle path.

| Workload | Parser cycles / events | Book event→commit / service interval | Decision commit→decision | Full top cycles |
|---|---:|---:|---:|---:|
| Single ADD→BUY | 111 / 1 | 4 / — | 1 / — | 116 |
| Two-message packet | 146 / 2, II 35 | 4 / — | — | 146 |
| Stateful A/F/E/C/X/U/D | 697 / 7, II 86–107 | 4–6 / 5 (cross-set U 7) | 1; output II 2, 5 | 697 |

The parser-only byte rate was 0.901, 0.911 and 0.958 accepted bytes/cycle respectively. The full-top runs accepted 100, 133 and 668 bytes over 116, 146 and 697 cycles (0.862–0.958 bytes/cycle) with natural input stalls. Decision L1/L2/L3 remained respectively 37/7/115 cycles for single ADD, 37/7/115 for the two-message case, and L1=37, L2=7/7/9, L3=115/131/131 for the stateful workload. Metrics use ready/valid transfer cycles as defined in WIRE-026; they are simulation cycles, not physical latency. Stage measurements overlap in the integrated top.

## Critical path and controlled change

The WIRE-026A seed-1 path was `order_row_mem.0.3:DOA15` → `order_row_mem.0.2:DIB14` at 22.000 ns. In the experiment, the seed-1 nextpnr JSON path is `core.parser_book.book.order_row_mem.0.6:DOB13` → `core.parser_book.book.write_row_q_TRELLIS_FF_Q_177:CE` at 21.180 ns. The path traverses selected-entry/valid comparison and 48-bit aggregate/update logic (RTL aggregate calculation at `wire_order_book.sv:298`); EBR clock-to-Q and routing also contribute. The endpoint moved from EBR write data to the registered write-plan control. The path remains inside the book. It is a clock-frequency bottleneck, distinct from the parser's larger service cycles per frame.

The one RTL change registers the validated row/valid-bit/aggregate write plan in evaluation, then writes from that plan. It leaves capacity, hash, allocation, no-eviction, mutation/error semantics and commit boundary unchanged. The normal book service interval did not change. The experiment was retained because all five routed Fmax values improved and LUT use fell.

## ECP5 synthesis and five-seed route

Frozen setup: LFE5U-85F-8BG381C, nextpnr `--85k --package CABGA381 --speed 8`, 156.25 MHz, seeds 1/7/19/42/97, unconstrained I/O, `--timing-allow-fail`. The complete production-capacity benchmark top was synthesized and routed. No package pinout validation was performed. Synthesis reports 16 DP16KD and 16 residual distributed DPR16X4 cells. nextpnr uses 113 I/O cells; this is distinct from the package document's 205 user-I/O figure.

| Seed | Route | Baseline Fmax | Experiment Fmax | Experiment critical delay | Slack vs 6.4 ns |
|---:|---|---:|---:|---:|---:|
| 1 | PASS | 45.45 MHz | 47.21 MHz | 21.180 ns | -14.780 ns |
| 7 | PASS | 44.84 MHz | 47.66 MHz | 20.982 ns | -14.582 ns |
| 19 | PASS | 43.63 MHz | 45.68 MHz | 21.891 ns | -15.491 ns |
| 42 | PASS | 42.81 MHz | 47.08 MHz | 21.240 ns | -14.840 ns |
| 97 | PASS | 42.70 MHz | 46.51 MHz | 21.500 ns | -15.100 ns |

| Resource | WIRE-026A baseline | WIRE-027 experiment |
|---|---:|---:|
| Yosys LUT4 | 7,876 | 7,376 |
| Yosys FF | 3,586 | 3,943 |
| DP16KD EBR | 16 | 16 |
| Distributed DPR16X4 | 16 | 16 |
| nextpnr combinational cells | 8,904 | 8,404 |

No seed meets the frequency objective. The experiment's five-seed median rose from 43.63 to 47.08 MHz (about 7.9%). This is still about 70% below the requested clock frequency. No timing closure is claimed.

## Verification and decision

Focused simulation passed: order book 9/9, parser-book 4/4, functional top 15/15, isolation 3/3. The full WIRE-025 suite passed: 110/110 Cocotb tests, 79/79 established SBY jobs, Python 71/71, and Verilator functional-top lint. The seven order-book formal jobs also passed at their existing depths. SBY/Yices scope remains bounded/fixed-vector; no whole-design proof is claimed. Historical solver-bound monolithic IPv4 and parser late-suffix jobs remain excluded and unchanged.

**Architecture decision: BUILD B (as a next controlled experiment, not implementation approval).** The seven-event parser intervals (86–107 cycles) are about 17–21× the ordinary book service interval (5 cycles). The decision engine takes one cycle to create an output. The byte-serial parser therefore dominates cycles per mutation/frame in these tests. A native-64 parser could plausibly improve this rate while retaining the common book/decision block. It will not address the measured book timing path or make 156.25 MHz achievable. Architecture B remains unauthorized until a narrow follow-up experiment is separately scoped. Recommend WIRE-028: compare a small native-64 supported-profile parser against the same event boundary and shared book using these frozen workloads and implementation target.

## Evidence paths

- Task: `tasks/WIRE-027.md`
- Raw service, full regression, formal, synthesis, route logs and JSON: `results/raw/implementation/wire027/`
- Comparison CSV: `results/raw/implementation/wire027/baseline_vs_experiment.csv`
- Per-seed routing/resource/path CSV: `results/raw/implementation/wire027/five_seed_results_027.csv`
- Original WIRE-026A seed reports and cycle measurements remain under `results/raw/implementation/arch_a/`.
