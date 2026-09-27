Task ID: WIRE-005
Phase: Phase 0 — Bootstrap
Starting known-good commit: 590d550b34eb7131e0c243116eba179d60157834

Objective:
Freeze the canonical FPGA implementation target and primary timing objective using current Lattice documentation, the qualified local OSS CAD Suite, and an exact-target smoke P&R run.

Candidate target:
LFE5U-85F-8BG381C, mapped to nextpnr-ECP5 as --85k --package CABGA381 --speed 8.

Allowed modifications:
- tasks/WIRE-005.md
- docs/IMPLEMENTATION_TARGET.md
- docs/DECISIONS.md
- results/raw/implementation_target/*
- results/processed/WIRE-005-implementation-target.md
- docs/PROJECT_STATE.md
- docs/EVIDENCE_INDEX.md

Prohibited work:
- Wire-to-Decision application RTL or models
- application simulation, formal properties, synthesis or P&R
- Architecture B implementation
- board, pinout, or physical-hardware selection
- changing the canonical toolchain
- claiming application fit, timing closure, latency, throughput, or PPA

Source requirements:
- Current official Lattice ECP5/ECP5-5G family documentation.
- Existing WIRE-004 native Apple Silicon OSS CAD Suite and smoke RTL.
- Local nextpnr/Trellis support for the exact device/package/speed.

Validation commands:
- Yosys synth_ecp5 on tools/smoke/rtl/toolchain_smoke.sv.
- nextpnr-ecp5 --85k --package CABGA381 --speed 8 --freq 156.25 with unconstrained I/O.
- ecppack on the resulting Trellis text configuration.

Acceptance criteria:
- Exact part, package, speed grade, resources, and 156.25 MHz objective are source-backed.
- Local flow accepts and routes the exact target smoke design.
- A/B invariants, fixed seed policy, and non-production target status are recorded.
- No application RTL or application implementation claim is introduced.
- State and evidence index are updated and the final tree is clean.

Evidence requirements:
- results/raw/implementation_target/official_device_source.txt
- results/raw/implementation_target/local_nextpnr_target_check.txt
- results/raw/implementation_target/target_validation_yosys.log
- results/raw/implementation_target/target_validation_nextpnr.log
- results/raw/implementation_target/target_validation_ecppack.log
- results/processed/WIRE-005-implementation-target.md

Stop conditions:
- Repository identity, starting HEAD, or clean baseline differs unexpectedly.
- Official documentation or local database does not support the exact candidate.
- Target-validation synthesis, placement, routing, or packing fails.
- Any step would require application RTL or a production board decision.

Completion report:
Report repository state, frozen target, source-derived resources, selection rationale, smoke validation, invariants, evidence, limitations, conflicts, and next task.
