# Implementation Target

## Status

Frozen by WIRE-005. This is an implementation-experiment target, not evidence that the application fits or meets timing.

## Canonical FPGA

Lattice ECP5U (LFE5U), selected for the post-MAC 64-bit packet-stream boundary without requiring embedded SERDES/PCS.

## Exact Part

LFE5U-85F-8BG381C

## Device Resources

Source-derived from Lattice FPGA-DS-02012-3.4:

- 84K LUTs
- 208 sysMEM blocks of 18 Kbits
- 3,744 Kbits embedded memory
- 669 Kbits distributed RAM
- 156 18×18 multipliers
- 4 PLLs / 4 DLLs
- 0 SERDES channels
- 205 user I/Os in 381-ball caBGA

## Package

381-ball caBGA, order-code selector `BG381`, nextpnr package `CABGA381`. No board or pinout is selected.

## Speed Grade

Speed grade `-8`, the fastest grade listed for this ECP5U ordering family. The exact commercial orderable part is documented by Lattice.

## Canonical Open-Source Tool Mapping

- Architecture: `ecp5`
- Device: `--85k`
- Package: `--package CABGA381`
- Speed: `--speed 8`
- Canonical flow: native Apple Silicon OSS CAD Suite from WIRE-004

## Primary Clock Target

156.25 MHz, nominal period 6.4 ns.

This is a timing objective for later routed application designs, not a measured Fmax or timing result.

## Timing Interpretation

Later reports must distinguish requested frequency, routed achieved timing, critical path, WNS/slack, and any legitimately derived maximum frequency. A target constraint is never itself an Fmax result. Latency in time requires both established cycle latency and valid routed timing evidence.

## Architecture-Experiment Invariants

Architecture A and any later authorized Architecture B comparison shall hold constant the exact FPGA target, package, speed grade, OSS CAD Suite/tool versions, Project Trellis database, clock target, top-level boundary, protocol subset, order-state implementation, decision logic, workload, P&R options, seed set, and report extraction. Architecture B remains undefined and unauthorized.

## Multi-Seed Policy

Use at least five fixed P&R seeds per architecture: `1`, `7`, `19`, `42`, and `97`. Freeze and reuse the same set before the first Architecture-A benchmark.

## Resource Reporting Policy

Later implementation reports shall include LUT, FF, EBR, DSP, meaningful I/O utilization, utilization percentages, critical path, and WNS or equivalent timing result. Resource pressure is evidence to interpret, not an arbitrary Phase-0 pass/fail threshold.

## Physical-Hardware Policy

Physical FPGA hardware is not required for the CV-ready gate. Synthesis, P&R, timing, resource utilization, and controlled architecture comparison are the mandatory implementation evidence chain.

## Optional Vendor-Flow Policy

Vivado, Radiant, and Diamond are not mandatory. Any vendor-flow cross-check is a later optional extension and does not replace the reproducible native Apple Silicon open-source flow.

## Evidence Supporting This Freeze

- Official Lattice ECP5 and ECP5-5G Family Data Sheet, FPGA-DS-02012-3.4, 2025-10-05.
- WIRE-004 canonical OSS CAD Suite build `2026-09-27`.
- Exact-target smoke evidence in `results/raw/implementation_target/`.
- Processed evidence in `results/processed/WIRE-005-implementation-target.md`.

## What This Freeze Does Not Prove

It does not prove application fit, resource utilization, timing closure, Architecture A/B performance, latency, throughput, CDC correctness, physical hardware compatibility, or any Wire-to-Decision RTL/model correctness.
