Task ID: WIRE-004
Phase: Phase 0 — Bootstrap
Known-good starting commit: e713a63202706e88fb79e2eb393972c2f69b9c6e

Objective: qualify a reproducible native Apple Silicon open-source RTL, simulation, formal, synthesis, ECP5 place-and-route, and packing flow using toolchain smoke infrastructure only.

Canonical tool distribution:
- Official YosysHQ OSS CAD Suite release source.
- Native `darwin-arm64` archive installed at `/Users/Dilan/eda/wire-to-decision/oss-cad-suite`.

Allowed files:
- tasks/WIRE-004.md
- tools/env/*
- tools/smoke/*
- results/raw/toolchain/*
- results/processed/toolchain_smoke.md
- docs/PROJECT_STATE.md
- docs/EVIDENCE_INDEX.md
- docs/DECISIONS.md only for the toolchain decision
- .gitignore only for narrow generated-artifact rules if required

Prohibited work:
- Wire-to-Decision application RTL, protocol logic, models, tests, formal properties, synthesis, P&R, or C++.
- Installing tools in the repository.
- Committing the OSS CAD Suite archive or installation.
- Freezing the production ECP5 device/package.
- Adding Vivado or vendor-tool requirements.

Qualification matrix:
- Verilator lint/build.
- cocotb plus Verilator simulation.
- generic Yosys synthesis/elaboration.
- Yosys `synth_ecp5`.
- SBY prove and cover with one executed solver.
- nextpnr-ECP5 placement and routing.
- ecppack, if available.

Acceptance criteria:
- Verify the repository identity, expected starting HEAD, branch, and clean starting tree.
- Record host architecture, macOS version, CPU count, memory, and tool paths.
- Freeze the exact native OSS CAD Suite archive, build/date, URL, size, and SHA-256.
- Execute every mandatory smoke stage and retain raw logs.
- Record warnings, failures, workarounds, exact commands, and limitations.
- Clearly label the smoke RTL and ECP5 part/package as non-production.
- Update project state and EVID-004 without claiming application correctness or performance.
- Leave the repository clean.

Evidence requirements:
- `results/raw/toolchain/host_inventory.txt`
- `results/raw/toolchain/suite_metadata.txt`
- tool-specific raw logs under `results/raw/toolchain/`
- `results/processed/toolchain_smoke.md`

Stop conditions:
- Repository identity, HEAD, or clean baseline differs unexpectedly.
- Native ARM64 execution cannot be established.
- A mandatory smoke stage fails and cannot be repaired without broadening scope.
- An existing unexplained installation would need to be overwritten.

Completion report:
- Report repository state, host, frozen suite, versions, each smoke result, formal scope, ECP5 smoke target, evidence, limitations, conflicts, and next task.
