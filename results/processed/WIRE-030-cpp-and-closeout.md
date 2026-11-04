# WIRE-030 — C++ replay checker and portfolio closeout

**Result: PASS.** A standard-library C++20 checker parses canonical packet bytes and independently applies the frozen parser, Mold, ITCH, bounded-book and decision profile. The C++ executable does not call Python.

The hand-calculated C++ fixture suite passed **15/15**. A real Architecture-A functional-top Cocotb run processed four replay frames and exported two actual decisions. C++ compared those decisions and final state: **4 frames, 3 Mold messages, 2 decisions, 0 mismatches**. It also detected an intentionally corrupted copy of the RTL decision log (exit 1, one mismatch). A separate Python oracle cross-check agreed.

Actual simulation-cycle latency samples (min / median / nearest-rank p95 / max):

| Metric | Cycles |
|---|---:|
| L1: first ITCH payload byte to normalized-event valid | 37 / 37 / 37 / 37 |
| L2: final ITCH payload byte to decision valid | 7 / 7 / 7 / 7 |
| L3: first accepted external beat to decision valid | 115 / 121 / 127 / 127 |

These are simulation-cycle measurements. They are not physical FPGA latency. Median averages the middle pair for even sample counts; p95 uses nearest rank (`ceil(0.95 × n)`).

Additional reruns: Python **71/71**, functional-top Cocotb **15/15**, decision-reference SBY/Yices **BMC depth 16 PASS**, and Verilator functional-top lint PASS. A fresh clone at commit `ad801db3d1d5d23ce3cae44ead06ee35afb3ee9e` reran the documented Python, C++, RTL replay/C++ comparison, functional-top simulation, and bounded formal commands successfully; full output: `results/raw/cpp/clean_clone_validation.log`.

Final implementation status remains as previously measured: Architecture A routes for five seeds at 45.68–47.66 MHz and misses 156.25 MHz; B was rejected on its measured resource/clock trade-off. Formal checks remain bounded/fixed/reduced where documented; historical solver-bound jobs remain unresolved. No physical FPGA operation, package pinout, physical I/O timing, physical latency, live market connectivity, or commercial CDC/RDC signoff is claimed. Phase 11 is optional.

Evidence: `tasks/WIRE-030.md`; C++ source/tests and replay under `tools/cpp/`; actual output and tool logs under `results/raw/cpp/`; prior FPGA, formal and CDC evidence indexed in `docs/EVIDENCE_INDEX.md`.
