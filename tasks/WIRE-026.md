# WIRE-026 — Architecture-A FPGA Implementation and Measurement

## Status

**PARTIAL — implementation does not fit the frozen ECP5-85K target.** The full-capacity `synth_ecp5` mapping completed, but nextpnr failed before placement for all five seeds because mapped LUT demand is 182% of device capacity. Consequently there is no routed timing, Fmax, slack, or critical-path result and Phase 5 remains active. No push is authorized for this partial result.

## Starting state and authority

- Repository: `/Users/Dilan/Projects/wire-to-decision`
- Starting local/remote `main`: `e2527db38f126288c5c31b021dc607938e717bb8`
- Starting tree: clean
- Protected `kg-g0-env^{}`: `06f5643a940ac2c6fcfab0e377169b48ce700107`
- WIRE-025 and Phase 4 were recorded PASS.
- Ending source HEAD remains `e2527db38f126288c5c31b021dc607938e717bb8`; work is uncommitted because the task is partial and push criteria were not met.
- Frozen target: `LFE5U-85F-8BG381C`, nextpnr `--85k --package CABGA381 --speed 8`, 156.25 MHz / 6.4 ns, seeds 1, 7, 19, 42, 97.

## Benchmark wrapper

`rtl/arch_a/wire_arch_a_benchmark_top.sv` instantiates the real `wire_arch_a_functional_top` at its production default of 512 sets × 2 ways. It preserves the 64-bit post-MAC input and supplies a fixed legal configuration, including destination `198.51.100.7`, UDP port `0x1234`, session `W2DTEST001`, expected sequence `0x1020304050607080`, tracked locate `0x2345`, symbol `ALPH    `, threshold 10, budget 20, and enabled decisions.

The physical shell uses a lossless 32-bit/six-word ready/valid serializer for the complete decision tuple: action, 64-bit Mold sequence, 48-bit ITCH timestamp, and signed 49-bit imbalance. It exposes 113 I/O bits (including clock/reset/rearm), versus 365 package I/O cells. No board pinout or external I/O timing constraint is claimed. The serializer can backpressure the core while a tuple is being read; latency measurements use the unwrapped functional top with `decision_ready=1`, so the shell does not affect those canonical no-stall core measurements.

The wrapper equivalence test initially found a test-shell symbol constant mismatch (`ALPHAL  ` versus canonical `ALPH    `). The constant was corrected in both shell and equivalence fixture; final cocotb comparison passes for hand-calculated BUY and SELL tuples. No functional core RTL was changed.

## Synthesis and placement/routing

Tool versions and exact synthesis command are retained in `results/raw/implementation/arch_a/`. The corrected wrapper was synthesized with Yosys `synth_ecp5`, preserving the full-capacity book.

Mapped cells: 138,733 LUT4; 68,997 TRELLIS_FF; 2,128 TRELLIS_DPR16X4; 397 CCU2C; 6,774 L6MUX21; 19,203 PFUMX. No DP16KD EBR or MULT18X18D DSP cells were inferred. The 2,128 DPR16X4 cells are distributed LUT RAM; the order store did not map into EBRs. `check` found zero problems. The only Yosys feature warning was that `write_xaiger2` is experimental. ABC also printed its AIG/carry informational warnings.

For each required seed, nextpnr reported 152,295 total LUT4-equivalents against 83,640 available (182%), 68,997/83,640 FF (82%), and 113/365 I/O (31%). It placed zero cells and failed to place a combinational cell because no BELs remained. Routing and timing analysis were not reached. `--timing-allow-fail` was supplied; it cannot overcome resource overflow. No Fmax, slack, or critical path is available.

## Cycle measurements

Verilator/cocotb measurements use the original functional top, continuous valid input with legal held-beat behavior, and `decision_ready=1`. Cycle indices are sampled at the rising-edge handshake boundary. L1 is first accepted ITCH message payload byte to normalized event valid/handshake; L2 is final accepted ITCH payload byte (`in_last`) to decision valid; L3 is first accepted post-MAC frame beat to decision valid. External bytes are counted from accepted beat `keep` bits; throughput is accepted bytes divided by elapsed cycles through the final expected event/decision. The cycle-based stream had natural RX backpressure. At the frozen nominal 156.25 MHz only, one cycle corresponds to 6.4 ns; derived time values are not routed timing measurements.

| Workload | Bytes | Elapsed cycles | L1 cycles | L2 cycles | L3 cycles | Event II cycles | Decision II cycles | Bytes/cycle | RX stalled cycles |
|---|---:|---:|---:|---:|---|---|---|---:|---:|
| Single ADD → BUY | 100 | 114 | 37 | 5 | 113 | — | — | 0.877193 | 71 |
| Two messages in one Mold packet | 133 | 146 | 37 | 5 | 113 | 35 | — | 0.910959 | 101 |
| Stateful A/F/E/C/X/U/D frames | 668 | 697 | 37 | 5, 5, 5 | 113, 129, 127 | 107, 98, 103, 90, 102, 86 | 107, 393 | 0.958393 | 583 |

The measured decision tuples matched hand results: BUY `+10` at sequence base, SELL `-10` at base+1, and BUY `+15` at base+5. The serializer was absent from these measurements. The cycle results show approximately byte-serial ingress/event spacing for these workloads, but routed frequency and critical path are unknown.

## Bottleneck conclusion

**MODIFY HYPOTHESIS.** Cycle data gives a measurable serial-processing baseline, but the production-sized Architecture-A design cannot be placed on the frozen target, so clock frequency and critical path cannot be established. The immediate dominant blocker is mapped logic/storage cost, not a demonstrated timing path. Architecture B would not address the unresolved full-capacity book fit. The next focused investigation should examine an architecture-preserving order-store RAM mapping (synchronous/banked EBR-compatible access while retaining 512 × 2 semantics), prove its inference and functional equivalence, then rerun synthesis and the same five-seed campaign. Do not start an Architecture-B comparison until a placeable Architecture-A baseline exists.

## Verification and exclusions

- `scripts/run_wire026_checks.sh` reuses the established `scripts/run_wire025_regression.sh` for the Phase-4 Python/component/formal/lint campaign, then runs wrapper equivalence and strict wrapper lint. WIRE-026's constituent tests were run and logged individually; the full historical formal campaign was not needlessly rerun because no functional core RTL changed.
- Wrapper decision reconstruction: 1/1 cocotb PASS, BUY and SELL.
- Functional-top regression including the new three-workload measurement: 15/15 PASS (14 established WIRE-025 tests plus one WIRE-026 benchmark test).
- Python regression: 71/71 PASS.
- Strict Verilator lint for the physical wrapper hierarchy: PASS, no warnings.
- Full-capacity ECP5 synthesis: PASS as synthesis/elaboration only; device fit: FAIL.
- Five-seed placement: 0/5; routing: 0/5; timing: unavailable.
- No production functional RTL change; therefore no new formal rerun was needed. Existing WIRE-025 component/formal evidence remains the applicable baseline; the two historical solver-bound monolithic jobs remain excluded from PASS.
- No nextpnr timing closure, P&R success, board-level I/O timing, PPA, physical latency, or physical FPGA operation is claimed.

## WIRE-026A follow-up

The initial WIRE-026 result below is historical and was PARTIAL at that point. WIRE-026A subsequently inferred EBRs for the unchanged 512 × 2 store, routed all five frozen seeds, measured the timing miss and updated the combined conclusion. See `tasks/WIRE-026A.md` and `results/processed/WIRE-026-arch-a-implementation.md`.

## Phase status at the end of WIRE-026

At this task’s initial close, Phase 5 was **ACTIVE** and the implementation campaign was PARTIAL. WIRE-026A completed the follow-up campaign: Phase 5 implementation/measurement evidence is now COMPLETE, while timing closure remains unachieved. Architecture B remains unauthorized. See the WIRE-026A addendum and updated processed report.
