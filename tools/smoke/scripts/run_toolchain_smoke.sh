#!/usr/bin/env bash
set -euo pipefail

# WIRE-004 TOOLCHAIN SMOKE ONLY. No application RTL is exercised.
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
raw="$repo_root/results/raw/toolchain"
mkdir -p "$raw/formal"
source "$repo_root/tools/env/setup_oss_cad_suite.sh" >/tmp/wire004-env.$$
cat /tmp/wire004-env.$$ > "$raw/activation.log"
rm -f /tmp/wire004-env.$$

suite_root="$WIRE_TO_DECISION_OSS_CAD_SUITE"
build_dir="$(mktemp -d /tmp/wire004-smoke-build.XXXXXX)"
trap 'rm -rf "$build_dir"' EXIT

{
    echo "WIRE-004 TOOLCHAIN SMOKE ONLY"
    date -u '+UTC=%Y-%m-%dT%H:%M:%SZ'
    echo "repository=$repo_root"
    echo "suite_root=$suite_root"
    echo "build_dir=$build_dir"
    echo "=== host ==="
    uname -a
    uname -m
    sw_vers
    sysctl -n hw.ncpu
    sysctl -n hw.memsize
    xcode-select -p 2>&1 || true
    clang --version 2>&1 || true
    git --version
    echo "SHELL=$SHELL"
    echo "=== tool paths and versions ==="
    command -v python3; python3 --version
    command -v verilator; verilator --version
    command -v cocotb-config; cocotb-config --version 2>&1 || true
    python3 -c 'import cocotb; print("cocotb", cocotb.__version__)'
    command -v yosys; yosys -V
    command -v sby; sby --version 2>&1 || sby -h 2>&1 | head
    command -v nextpnr-ecp5; nextpnr-ecp5 --version 2>&1 || true
    command -v ecppack; ecppack --version 2>&1 || true
    for t in yices-smt2 boolector z3 bitwuzla btormc pono abc; do
        echo "=== $t ==="
        command -v "$t" || true
        "$t" --version 2>&1 | head -n 5 || true
    done
} > "$raw/host_inventory.txt" 2>&1

verilator --lint-only --Wall --language 1800-2012 \
    "$repo_root/tools/smoke/rtl/toolchain_smoke.sv" \
    2>&1 | tee "$raw/verilator_smoke.log"

# The packaged Python dylib refers to @executable_path/../lib.  The symlink is
# disposable and stays outside the repository with the disposable simulator.
ln -s "$suite_root/lib" "$build_dir/lib"
DYLD_LIBRARY_PATH="$suite_root/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}" \
DYLD_FALLBACK_LIBRARY_PATH="$suite_root/lib${DYLD_FALLBACK_LIBRARY_PATH:+:$DYLD_FALLBACK_LIBRARY_PATH}" \
make -C "$repo_root/tools/smoke/cocotb" SIM=verilator SIM_BUILD="$build_dir/cocotb_sim_build" \
    2>&1 | tee "$raw/cocotb_verilator_smoke.log"

yosys -p "read_verilog -sv $repo_root/tools/smoke/rtl/toolchain_smoke.sv; hierarchy -top toolchain_smoke; proc; opt; stat" \
    2>&1 | tee "$raw/yosys_generic_smoke.log"

yosys -p "read_verilog -sv $repo_root/tools/smoke/rtl/toolchain_smoke.sv; synth_ecp5 -top toolchain_smoke -json $build_dir/toolchain_smoke.json; stat" \
    2>&1 | tee "$raw/yosys_smoke.log"

sby -f -d "$build_dir/formal_prove" "$repo_root/tools/smoke/formal/toolchain_smoke_prove.sby" \
    2>&1 | tee "$raw/formal/prove.log"

sby -f -d "$build_dir/formal_cover" "$repo_root/tools/smoke/formal/toolchain_smoke_cover.sby" \
    2>&1 | tee "$raw/formal/cover.log"

nextpnr-ecp5 --25k --package CABGA381 \
    --json "$build_dir/toolchain_smoke.json" \
    --textcfg "$build_dir/toolchain_smoke.config" \
    --lpf-allow-unconstrained \
    --report "$build_dir/nextpnr_report.json" \
    2>&1 | tee "$raw/nextpnr_ecp5_smoke.log"

ecppack --compress "$build_dir/toolchain_smoke.config" "$build_dir/toolchain_smoke.bit" \
    2>&1 | tee "$raw/ecppack_smoke.log"

cp "$build_dir/nextpnr_report.json" "$raw/nextpnr_report.json"
echo "WIRE-004 TOOLCHAIN SMOKE PASS"
