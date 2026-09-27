# WIRE-005 — Implementation Target Evidence

## A. Starting state

SOURCE-DERIVED: The task began in `/Users/Dilan/Projects/wire-to-decision`, branch `main`, at clean commit `590d550b34eb7131e0c243116eba179d60157834`.

The existing WIRE-004 smoke RTL was used. No application RTL was created or synthesized.

## B. Candidate targets considered

SOURCE-DERIVED: LFE5U-45 and LFE5U-85 are both available in the official ECP5 family selection table. The 45F provides 44K LUTs, 108 sysMEM blocks, 1,944 Kbits embedded memory, 351 Kbits distributed RAM, and 72 multipliers. The 85F provides 84K LUTs, 208 sysMEM blocks, 3,744 Kbits embedded memory, 669 Kbits distributed RAM, and 156 multipliers.

PROJECT DECISION: Select the 85F for experimental headroom so the Architecture-A experiment is not prematurely constrained by Phase-0 density selection. This does not claim the application needs 85F; actual application synthesis is required later.

PROJECT DECISION: Select LFE5U rather than LFE5UM/LFE5UM5G because the project boundary is a post-MAC 64-bit framed stream and the mandatory flow does not require FPGA SERDES/PCS/PHY resources. LFE5U has zero SERDES in the official selection table; the UM variants add SERDES capability that is outside the mandatory scope.

## C. Official device facts

SOURCE-DERIVED from Lattice `FPGA-DS-02012-3.4`, dated 2025-10-05:

| Fact | Selected target |
|---|---|
| Family | LFE5U / ECP5 FPGA |
| Exact orderable part | LFE5U-85F-8BG381C |
| Logic capacity | 84K LUTs; `85F` is the order-code capacity designation |
| sysMEM | 208 blocks, 18 Kbits each |
| Embedded memory | 3,744 Kbits |
| Distributed RAM | 669 Kbits |
| 18×18 multipliers | 156 |
| PLLs / DLLs | 4 / 4 |
| SERDES | 0 |
| Package | 381-ball caBGA, `BG381` order-code package |
| User I/O | 205 for LFE5U-85 in 381 caBGA |
| Speed | `-8`, listed as fastest ordering grade |
| Grade | `C`, commercial |

The official source URL and document identifier are retained in `results/raw/implementation_target/official_device_source.txt`.

## D. Density decision

PROJECT DECISION: Freeze 85F rather than 45F for controlled architecture experiments. Both A and any later authorized B implementation must use the same target. This is an experimental headroom decision, not a fit claim or resource estimate.

## E. Package decision

SOURCE-DERIVED: LFE5U-85 is listed with 205 user I/Os in the 381 caBGA package. The orderable package code is `BG381`.

PROJECT DECISION: Use nextpnr package `CABGA381`, consistent with the already qualified local database. No board, pinout, or physical hardware compatibility is claimed.

## F. Speed-grade decision

SOURCE-DERIVED: The ordering information lists speed grades `-6`, `-7`, and `-8`, with `-8` fastest. The exact `LFE5U-85F-8BG381C` orderable part is listed by Lattice.

PROJECT DECISION: Freeze speed grade `-8` so the architecture experiment is not dominated by an unnecessarily slow device grade. This is a common experimental condition, not a timing result.

## G. Clock-target decision

PROJECT DECISION: Freeze a primary processing-clock objective of 156.25 MHz, nominal period 6.4 ns. The arithmetic `64 × 156.25 MHz = 10.0 Gbit/s` describes raw 64-bit interface capacity only; it does not establish parser sustainable throughput, event throughput, or application timing.

Timing reports must separate requested frequency, achieved routed timing, critical path, WNS/slack, and any legitimately derived maximum frequency. The L1/L2/L3 latency metrics remain future measurements, not WIRE-005 results.

## H. Local open-source support validation

TARGET-VALIDATION EVIDENCE: WIRE-004's canonical OSS CAD Suite was activated from `/Users/Dilan/eda/wire-to-decision/oss-cad-suite/environment`.

Observed tools:

- Yosys `0.69+154`
- nextpnr-ecp5 `0.11.1-34-gc4fbb55a`
- Project Trellis ecppack `1.4-83-g65fe191`

Local nextpnr exposes `--85k`, `--package`, `--speed` with 6/7/8, and `--freq`.

## I. Target-validation P&R result

TARGET-VALIDATION EVIDENCE: The existing trivial `toolchain_smoke` design was synthesized with Yosys `synth_ecp5`, then run with:

```text
nextpnr-ecp5 --85k --package CABGA381 --speed 8 --freq 156.25 \
  --json <smoke-netlist.json> --textcfg <smoke.config> \
  --report <smoke.report.json> --lpf-allow-unconstrained
```

The run completed normally. The log reports 11/83,640 LUT4s and 9/83,640 DFFs before packing, routing completed, and the program finished normally. `ecppack --compress` also completed and produced a bitstream.

The smoke log reports no available Fmax because there were no interior timing paths. Therefore the run demonstrates exact target recognition, placement, routing, and constraint-option acceptance for the trivial design only. It does not demonstrate 156.25 MHz application timing.

Yosys emitted its existing experimental-feature warning; no fatal error occurred. This warning is retained in the raw log and does not change the narrow target-validation conclusion.

## J. A/B comparison invariants

PROJECT DECISION: Future A/B comparisons must hold constant exact device, package, speed grade, OSS CAD Suite/tool versions, Yosys, nextpnr, Project Trellis, clock target, top-level boundary, protocol subset, order-state implementation, decision logic, workload, P&R options, seed set, and report extraction. Architecture-specific RTL may differ only where explicitly authorized by the experiment. Architecture B remains undefined.

## K. Multi-seed policy

PROJECT DECISION: Use at least five fixed P&R seeds per architecture: `1`, `7`, `19`, `42`, and `97`. The same seed list must be applied to A and any later authorized B. No multi-seed experiment was run in WIRE-005.

## L. Physical-hardware policy

PROJECT DECISION: Physical FPGA hardware is not required for the CV-ready gate. The mandatory implementation evidence chain is synthesis, P&R, timing, resource utilization, and controlled architecture comparison. Vendor tools remain optional and non-mandatory.

## M. Risks / limitations

- The selected target has not been tested with application RTL; no application resource or timing result exists.
- The smoke design has no meaningful internal Fmax path, so the 156.25 MHz objective remains unproven.
- No board, pinout, PHY, PCS, SERDES, or physical hardware compatibility was selected.
- The exact Lattice family document is current official source material inspected for this task; future target refreshes must recheck the part and tool database.

## N. WIRE-005 conclusion

PASS: The canonical implementation target is frozen as LFE5U-85F-8BG381C, mapped as `--85k --package CABGA381 --speed 8`, with a primary timing objective of 156.25 MHz / 6.4 ns. The exact target was accepted and routed by the qualified local open-source flow using the trivial smoke design, and ecppack completed. This establishes target/source/tool compatibility only; it does not establish any Wire-to-Decision implementation result.
