# WIRE-007 — Clean-Clone Reproducibility Evidence

## A. Canonical starting state

The canonical repository began WIRE-007 at clean `main` HEAD `43189dd01442af9cfc12a6cd169b9fb0f4223712`, with no configured remote. WIRE-007 reproducibility infrastructure was added in narrow commits before the final closure clone.

## B. Clean-clone source and candidate commit

The clone source was local Git clone semantics from `/Users/Dilan/Projects/wire-to-decision`; no remote URL was invented. The final executable candidate tested by the closure checker is recorded in the final report section below. Temporary clone/build directories were outside the canonical repository under `/tmp`.

## C. Required-file audit

REPOSITORY-REPRODUCED: The repository-owned checker audits the authority hierarchy, README/agent/provenance files, WIRE-000 through WIRE-007 tasks, processed evidence, smoke infrastructure, and supporting specification records. The expected top-level directory structure is retained with `.gitkeep` markers where needed.

## D. Hidden-dependency audit

REPOSITORY-REPRODUCED: Historical references to other projects are documentation provenance only. The runtime smoke path uses only the clean clone and the explicit external OSS CAD Suite. No reference-project source tree is required.

## E. External toolchain contract

TOOLCHAIN-REPRODUCED: `tools/env/setup_oss_cad_suite.sh` accepts `WIRE_OSS_CAD_SUITE_ROOT`, retains the legacy `WIRE_TO_DECISION_OSS_CAD_SUITE` override, defaults to the qualified local suite, fails if `environment` is absent, and does not fall back to unrelated global tools.

## F. Tool-version validation

TOOLCHAIN-REPRODUCED: The final closure run compares the active tools with WIRE-004’s frozen OSS CAD Suite environment: Python 3.11.6, Verilator 5.053 devel, cocotb 2.1.0.dev0+41564633, Yosys 0.69+154, SBY v0.69, Yices 2.7.0, nextpnr-ecp5 0.11.1-34-gc4fbb55a, and ecppack/Project Trellis 1.4-83-g65fe191.

## G. Toolchain smoke result

TOOLCHAIN-REPRODUCED: The final clean-clone checker runs the repository smoke driver with disposable raw/build output. It requires PASS for Verilator lint, cocotb/Verilator, generic and ECP5 Yosys synthesis, SBY prove and cover with Yices, nextpnr placement/routing, and ecppack.

## H. Implementation-target recognition

TOOLCHAIN-REPRODUCED: The final checker independently runs the existing smoke RTL through `--85k --package CABGA381 --speed 8 --freq 156.25`, then requires normal nextpnr completion and a generated bitstream. This is target compatibility evidence only.

## I. Post-smoke Git hygiene

REPOSITORY-REPRODUCED: Smoke output is redirected to disposable directories. The final clean clone must remain clean after execution; retained canonical evidence is concise and does not include generated simulator/formal/P&R directories.

## J. Evidence-index consistency

The final checker requires EVID-000 through EVID-007 to be present in the index and checks the referenced task/processed evidence files. Historical supporting commits are retained in repository history; no technical claim is revalidated here.

## K. Decision/requirement consistency

The final checker requires WIRE-D001 through WIRE-D008 and exactly 71 stable requirement identifiers. Application requirements remain specified/not yet verified; reproducibility evidence is not functional application verification.

## L. Reproducibility fixes required

The audit found and fixed:

1. The smoke driver rewrote tracked historical raw logs. It now accepts `WIRE_SMOKE_RAW_ROOT` so clean-clone execution uses disposable raw output.
2. Informational macOS `sysctl` probes could stop the strict smoke script in a restricted environment. Those probes are now narrowly non-fatal; qualification stages remain strict.
3. SBY relative source paths depended on the caller’s current directory. The smoke driver now enters its repository root before running.
4. Cocotb result XML is directed into the disposable build directory.
5. The environment setup supports the explicit `WIRE_OSS_CAD_SUITE_ROOT` override without PATH fallback.

## M. Final clean-clone run

To be finalized after the evidence-preparation commit: create a new clone of the exact candidate, run `tools/repro/run_phase0_reproducibility.sh`, record its exit status, exact clone commit, tool results, target result, and post-run Git status here.

## N. Gate-0 decision

Pending the final closure run. Gate 0 must remain open until the final clean clone passes all mandatory checks.

## O. What remains unproven

This task does not establish Python reference-model correctness, Wire-to-Decision RTL correctness, RTL simulation, application formal properties, application synthesis, application P&R, timing closure, latency, throughput, CDC correctness, C++ integration, or physical FPGA operation.
