# Wire-to-Decision — Deterministic Low-Latency FPGA Network Processor

Wire-to-Decision is an evidence-driven public SystemVerilog/FPGA portfolio project focused on:

- deterministic low-latency networking;
- streaming RTL;
- Ethernet/IP/UDP processing;
- MoldUDP64/ITCH processing;
- bounded stateful hardware;
- formal verification;
- CDC/RDC;
- FPGA implementation and timing;
- Python/C++ integration;
- controlled microarchitecture experiments.

Repository source code alone is not evidence that the design works. Simulation, formal, synthesis, place-and-route, timing, performance and hardware claims must be backed by recorded tool output.

## Current status

```text
Phase: Phase 0 — Bootstrap
Application RTL: not started
Verified RTL: none
Formal evidence: none
Synthesis evidence: none
P&R evidence: none
Timing evidence: none
```

## Early non-goals

- production trading strategy;
- PCIe before the CV-ready gate;
- Linux drivers;
- live exchange connectivity;
- mandatory physical FPGA;
- unnecessary PHY/MAC implementation.

## Phase-0 navigation

The authority order and phase plan are in [00_MASTER_PROJECT_PLAN.md](00_MASTER_PROJECT_PLAN.md). Current state is summarized in [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md), with claims indexed by [docs/EVIDENCE_INDEX.md](docs/EVIDENCE_INDEX.md).

The qualified external OSS CAD Suite is activated with:

```bash
source tools/env/setup_oss_cad_suite.sh
```

The WIRE-004 toolchain smoke is run with:

```bash
tools/smoke/scripts/run_toolchain_smoke.sh
```

The final Phase-0 repository/environment reproducibility check is:

```bash
tools/repro/run_phase0_reproducibility.sh
```

The canonical implementation target is documented in [docs/IMPLEMENTATION_TARGET.md](docs/IMPLEMENTATION_TARGET.md). Raw logs are retained under `results/raw/`; processed evidence is under `results/processed/`.
