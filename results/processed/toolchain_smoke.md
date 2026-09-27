# WIRE-004 — Apple Silicon Toolchain Smoke

Status: PASS — native Apple Silicon open-source toolchain qualification for the trivial WIRE-004 smoke design only. This is not Wire-to-Decision design evidence.

## A. Host

- Host: Darwin `Mac.ultrahub`, kernel `25.4.0`, `arm64`.
- macOS: `26.4.1`, build `25E253`.
- CPU count: 12.
- Memory: 17179869184 bytes.
- Xcode developer path: `/Applications/Xcode.app/Contents/Developer`.
- Apple Clang: 21.0.0.
- Shell: `/bin/zsh`.
- Raw inventory: `results/raw/toolchain/host_inventory.txt`.

## B. Frozen OSS CAD Suite artifact

- Release/build: `2026-09-27`.
- Archive: `oss-cad-suite-darwin-arm64-20260927.tgz`.
- Source: `https://github.com/YosysHQ/oss-cad-suite-build/releases`.
- Archive size: 523987393 bytes.
- SHA-256: `0df7ff004bb038f5aaef70959da0ba9c23c19472f5887698673d36f4b9528455`.
- Installed at: `/Users/Dilan/eda/wire-to-decision/oss-cad-suite`.
- Raw metadata: `results/raw/toolchain/suite_metadata.txt`.

## C. Activation

Canonical activation:

```bash
source /Users/Dilan/eda/wire-to-decision/oss-cad-suite/environment
```

Repository helper:

```bash
source tools/env/setup_oss_cad_suite.sh
```

The helper fails if the exact suite path is missing and does not fall back to Homebrew or global EDA binaries. The smoke driver uses a disposable `/tmp` simulator build and a disposable library symlink required by the suite’s macOS packaged Python dylib; no symlink remains in the repository.

## D. Tool versions

| Tool | Actual path/version |
|---|---|
| Python | suite `py3bin/python3`, 3.11.6 |
| Verilator | suite `bin/verilator`, 5.053 devel rev `v5.052-119-g014c9820d` |
| cocotb | 2.1.0.dev0+41564633 |
| Yosys | 0.69+154, git `30d62572e` |
| SBY | v0.69 |
| Primary solver | Yices 2.7.0, `yices-smt2` |
| nextpnr-ecp5 | nextpnr 0.11.1-34-gc4fbb55a |
| ecppack | Project Trellis 1.4-83-g65fe191 |

Other packaged solver executables observed were Boolector 3.2.4, Z3 4.15.5, Bitwuzla 0.9.1, BTORMC 3.2.4, and Pono. They were inventoried but not selected as the primary solver. `abc` was not a standalone PATH executable; Yosys used its bundled ABC flow internally during ECP5 synthesis.

## E. Verilator result

PASS. Command executed by the smoke driver:

```bash
verilator --lint-only --Wall --language 1800-2012 tools/smoke/rtl/toolchain_smoke.sv
```

The SystemVerilog smoke module linted without fatal/error diagnostics. Evidence: `results/raw/toolchain/verilator_smoke.log`.

## F. cocotb/Verilator result

PASS. The supplied suite cocotb imported successfully and ran one test with deterministic vectors `0+0`, `1+2`, `0xff+1`, and `0xff+0xff`. The test drove clock/reset/inputs and checked independently computed expected sums.

Command:

```bash
make -C tools/smoke/cocotb SIM=verilator SIM_BUILD=<temporary-build>/cocotb_sim_build
```

Result: `TESTS=1 PASS=1 FAIL=0`, 80 ns simulated. Evidence: `results/raw/toolchain/cocotb_verilator_smoke.log`.

## G. Yosys result

PASS. Generic SystemVerilog read/elaboration/process/optimization/stat completed with the smoke top. Evidence: `results/raw/toolchain/yosys_generic_smoke.log`.

## H. SBY/solver result

PASS for the exact smoke harness and property only.

- Engine: `smtbmc`.
- Solver: Yices 2.7.0 (`yices-smt2`).
- Prove mode: depth 8; basecase and k-induction passed.
- Property: after the explicit formal reset contract, the registered sum equals the previous cycle’s unconstrained inputs added together.
- Cover mode: depth 8; cover reached at step 2.
- Evidence: `results/raw/toolchain/formal/prove.log` and `results/raw/toolchain/formal/cover.log`.
- Earlier failed harness attempts are retained as `prove_initial_failure.log` and `prove_second_failure.log`; they document repair of the smoke harness, not a project functional result.

This does not prove any Wire-to-Decision formal property.

## I. ECP5 synthesis result

PASS. Yosys `synth_ecp5` generated a JSON netlist. Final smoke statistics were 5 `CCU2C`, 1 `LUT4`, and 9 `TRELLIS_FF`; these are smoke-design tool output only and are not Wire-to-Decision resource estimates.

Command form:

```bash
yosys -p "read_verilog -sv tools/smoke/rtl/toolchain_smoke.sv; synth_ecp5 -top toolchain_smoke -json <temporary-build>/toolchain_smoke.json; stat"
```

Evidence: `results/raw/toolchain/yosys_smoke.log`.

## J. nextpnr-ECP5 result

PASS. Placement and routing completed normally with no LPF pin file, using the documented unconstrained-I/O option.

- Device: `LFE5U-25F` selected by `--25k`.
- Package: `CABGA381`.
- Command form:

```bash
nextpnr-ecp5 --25k --package CABGA381 --json <temporary-build>/toolchain_smoke.json --textcfg <temporary-build>/toolchain_smoke.config --lpf-allow-unconstrained --report <temporary-build>/nextpnr_report.json
```

Routing completed and the report was retained as `results/raw/toolchain/nextpnr_report.json`. nextpnr emitted “No Fmax available; no interior timing paths found in design”; this is a limitation of the trivial unconstrained smoke design, not a timing result.

This device/package is a WIRE-004 toolchain smoke target only and is not the frozen Wire-to-Decision implementation target.

## K. ecppack result

PASS. `ecppack --compress` converted the nextpnr text configuration to a temporary bitstream and exited successfully. The bitstream was intentionally not retained or committed. Evidence: `results/raw/toolchain/ecppack_smoke.log`.

## L. Qualified canonical commands

Run from the repository root:

```bash
tools/smoke/scripts/run_toolchain_smoke.sh
```

The driver uses `set -euo pipefail`, stops on unexpected failures, activates the exact suite, runs lint, cocotb/Verilator, generic Yosys, ECP5 Yosys, SBY prove/cover, nextpnr-ECP5, and ecppack in order, and stores raw logs under `results/raw/toolchain/`.

## M. Known limitations

- The smoke RTL is intentionally trivial and is not application RTL.
- No production ECP5 device/package was frozen.
- No LPF board constraints were used; I/O placement is intentionally unconstrained.
- No meaningful Fmax, timing closure, latency, throughput, or resource claim is established.
- No Vivado or vendor tool was installed or qualified.
- The suite archive and installation remain outside the repository.

## N. Failures/workarounds

- Initial cocotb execution failed because the packaged macOS Python dylib could not resolve its `@executable_path/../lib` dependency. The final driver uses a disposable `/tmp` build and symlink to the suite library directory; this workaround is recorded in the activation and final cocotb logs.
- Initial SBY runs failed due to relative source paths and then an under-constrained formal reset history. Both failures are retained; the final task uses repository-root source paths and an explicit formal reset assumption. The final prove and cover runs passed.

## O. WIRE-004 conclusion

The native Apple Silicon OSS CAD Suite flow was actually executed successfully through Verilator, cocotb/Verilator, Yosys, SBY with Yices, Yosys ECP5 synthesis, nextpnr-ECP5 placement/routing, and ecppack for the WIRE-004 smoke design. This establishes toolchain qualification evidence only. It does not establish any Wire-to-Decision functional or implementation result.
