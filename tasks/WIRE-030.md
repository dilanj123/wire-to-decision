# WIRE-030 — Independent C++ Checker and Portfolio Closeout

## Result

**PASS.** The project-original C++20 checker independently parses the canonical replay bytes, tracks the bounded order store and decision model, and compares its expected sequence with decisions exported by a real Architecture-A functional-top Cocotb simulation.

## Starting state and implementation

- Starting `main`/`origin/main`: `8ecd5d2b8fff49f2e0d7a97f0448383e8da6df31`.
- Gate-0 peeled commit: `06f5643a940ac2c6fcfab0e377169b48ce700107`.
- Added a small standard-library C++20 CLI in `tools/cpp/`. It validates Ethernet II, IPv4, UDP, MoldUDP64 and the supported ITCH subset; maintains the 512×2 no-eviction book; applies A/F/E/C/X/D/U; and derives threshold/budget decisions.
- `WIRE_REPLAY_V1` stores configuration and ordered post-MAC frames as hex, with optional `REARM` and `ENABLE` actions. `WIRE_RTL_LOG_V1` stores actual RTL decisions, cycle-derived L1/L2/L3 samples and final book/sequence/recovery state.
- Prefix semantics are retained: complete Mold messages before a malformed suffix may mutate; incomplete messages do not. Structurally valid Mold sequence advancement is independent of later ITCH semantic failure.

## Verification

- C++20 compile: PASS with `-Wall -Wextra -Wpedantic`.
- C++ fixture suite: **15/15 PASS**, including hand-calculated ADD/BUY, SELL, budget/enable behavior, A/F/E/C/X/D/U mutations, P/filtering, duplicate/unknown, unsupported ITCH, session error/rearm, multi-message, malformed suffix, WIRE-D006 collision and 64-bit sequence-wrap vectors.
- Python oracle cross-check: canonical replay decisions agree; Python is not a C++ runtime dependency.
- Real RTL replay Cocotb: **1/1 PASS**. Four frames (ADD BUY, ADD SELL, P, heartbeat) produced two decisions and final bid/ask `10/20`, expected sequence `0x1020304050607083`, and no quarantine.
- C++ against actual RTL log: **4 frames, 3 Mold messages, 2 decisions, 0 mismatches**. An intentionally altered imbalance in a copy of the RTL log produced one reported mismatch and exit status 1.
- Simulation-cycle latency samples: L1 first ITCH byte to normalized-event valid `37/37/37/37`; L2 final ITCH byte to decision valid `7/7/7/7`; L3 first accepted external beat to decision valid `115/121/127/127` (min/median/p95/max; nearest-rank p95). These are testbench cycles, not physical latency.
- Regressions: Python **71/71**; functional-top Cocotb **15/15**; representative decision SBY/Yices BMC **depth 16 PASS**; functional-top Verilator lint PASS.

## Reproducibility and final gate

The README gives commands for Python, C++, actual RTL replay generation/comparison, a representative functional-top Cocotb run and a bounded formal job. A fresh local clone at commit `ad801db3d1d5d23ce3cae44ead06ee35afb3ee9e` reran those commands successfully; its complete output is `results/raw/cpp/clean_clone_validation.log`. The mandatory C++/portfolio checklist is closed by EVID-030. Phase 11 remains optional.

## Limitations

Architecture A still misses the 156.25 MHz objective (WIRE-027: 45.68–47.66 MHz). Architecture B remains rejected for the measured baseline. Historical solver-bound jobs are not passes. Formal evidence is bounded, no FPGA hardware or physical I/O/timing validation exists, and CDC/RDC physical signoff/Gray-bus skew remain open. No live market or trading functionality is implemented.
