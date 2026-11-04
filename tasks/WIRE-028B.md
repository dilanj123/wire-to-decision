# WIRE-028B — Final B parser synthesis simplification and A/B completion

## Result

**PASS as a completed controlled experiment. Architecture B is rejected for the current baseline; Architecture A remains production.** Work was performed at the authorized dirty WIRE-028 tree based on `c7ccd8a8b628db56074bbc50a934210c3ee1ca00`; local and remote base matched at start. Gate-0 remained `06f5643a940ac2c6fcfab0e377169b48ce700107`. No existing WIRE-028/028A work was discarded.

## Diagnosis and change

`PROC_MEMWR` was not the synthesis blocker. The original 8-lane source-ordered state walk produced a large mux/equality graph and Yosys spent 461 s in `FSM_EXTRACT`. Marking the state register `fsm_encoding="none"` completed a diagnostic map but was still slow and large, so it was not the final solution. The final RTL retains `fsm_encoding="none"` on the parser state and limits the ordered lane loop to two consecutive byte lanes per cycle, retaining unconsumed lanes in the registered beat/cursor. An eight-lane build with FSM extraction disabled was still slow and large; the two-lane build with the attribute completed synthesis. The experiment does not isolate the contribution of the attribute from the lane-width change. It reaches two bytes/cycle in simulation. Yosys documents the attribute as excluding a state signal from automatic FSM detection ([FSM handling](https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/index_passes_fsm.html)); it is not a resource-efficiency guarantee. The 352-bit message buffer, protocol semantics and shared order/decision logic are unchanged from the preceding experimental work; Architecture A is unchanged.

## Verification

- A/B parser comparison: 8/8 PASS on Verilator 5.053; includes fixed seeds 1, 7, 19, 42, 97 and lane progress/conservation.
- B parser→book→decision: 2/2 PASS; measured workloads match Python `ReferenceOracle` decisions and final state.
- Python: 71/71 PASS.
- Verilator benchmark-top lint: PASS.
- Public-interface SBY/Yices safety: PASS, BMC depth 12; reset initialization and stable source valid/data/keep/last while stalled. No DUT-private state in the harness. Bounded only.

## Implementation results

Yosys 0.69+154, OSS CAD Suite 2026-09-27: parser-only `synth_ecp5` 32.70 s, 9,431 LUT4, 1,539 FF, 16 distributed DPR16X4. Full 512×2 B benchmark synthesis 45.79 s, 14,559 LUT4, 3,700 FF, 16 DP16KD and 16 distributed DPR16X4. Five-seed nextpnr placement/routing passed 5/5; B Fmax was 19.997–21.047 MHz against 156.25 MHz. All timing objectives failed. The benchmark used 113 nextpnr I/O cells; no package pinout validation was performed.

The full-top matched workload cycle results and A/B resource comparison are in `results/processed/WIRE-028-architecture-ab-comparison.md`; machine-readable values are in `results/raw/implementation/arch_b/ab_comparison_028b.csv`. B uses roughly 1.97× A's LUT4. Although B halves simulated cycles and doubles average bytes/cycle, its lower routed frequency gives lower derived byte rate than A at each design's conservative minimum seed estimate. Architecture B is therefore **REJECTED for this project baseline**. This does not authorize future production B or alter A.

## Evidence index

- RTL: `rtl/arch_b/`
- Tests: `tb/arch_b_parser/`, `tb/arch_b_functional/`
- Formal: `formal/arch_b_parser/`
- Raw tool evidence, five seed reports, compressed lossless routed netlists, and the matched A/B CSV: `results/raw/implementation/arch_b/`
- Processed comparison: `results/processed/WIRE-028-architecture-ab-comparison.md`

No CDC, C++, Architecture-A modification, or unrelated feature work was performed. Next task: WIRE-029 minimal CDC/RDC extension.
