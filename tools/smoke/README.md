# Toolchain Smoke Only

The files in this directory are WIRE-004 qualification infrastructure only.

They are **not Wire-to-Decision application RTL**, production verification, a reusable project primitive, or a production FPGA target. The design is a trivial registered 8-bit addition used only to exercise the native Apple Silicon OSS CAD Suite flow.

Run from the repository root:

```bash
tools/smoke/scripts/run_toolchain_smoke.sh
```

The driver activates the exact suite selected by `WIRE_TO_DECISION_OSS_CAD_SUITE` or the canonical local path `/Users/Dilan/eda/wire-to-decision/oss-cad-suite`. It writes retained logs under `results/raw/toolchain/` and uses a disposable build directory outside the repository.
