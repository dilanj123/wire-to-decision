#!/usr/bin/env bash
set -euo pipefail

# WIRE-007 PHASE-0 REPRODUCIBILITY CHECK ONLY.
# This checks repository/specification/toolchain reproducibility. It does not
# implement or verify Wire-to-Decision application logic.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
required_files=(
    00_MASTER_PROJECT_PLAN.md
    01_CHATGPT_PROJECT_OPERATING_INSTRUCTIONS.md
    04_MASTER_CHECKLIST.md
    README.md AGENTS.md THIRD_PARTY_NOTICES.md
    docs/REQUIREMENTS.md docs/MICROARCHITECTURE.md docs/VERIFICATION_PLAN.md
    docs/FORMAL.md docs/DECISIONS.md docs/PROJECT_STATE.md docs/EVIDENCE_INDEX.md
    docs/SPEC_SOURCES.md docs/THIRD_PARTY_MANIFEST.md docs/IMPLEMENTATION_TARGET.md
    tasks/WIRE-000.md tasks/WIRE-001.md tasks/WIRE-002.md tasks/WIRE-003.md
    tasks/WIRE-004.md tasks/WIRE-005.md tasks/WIRE-006.md
    tasks/WIRE-007.md
    tools/env/setup_oss_cad_suite.sh tools/smoke/README.md
    tools/smoke/scripts/run_toolchain_smoke.sh
    results/processed/reference_workflow_audit.md
    results/processed/WIRE-002-protocol-spec-lock.md
    results/processed/WIRE-003-third-party-audit.md
    results/processed/toolchain_smoke.md
    results/processed/WIRE-005-implementation-target.md
    results/processed/WIRE-006-specification-package.md
    results/processed/WIRE-007-clean-clone.md
)

echo "WIRE-007 Phase-0 reproducibility check"
echo "repository=$repo_root"
echo "=== required files ==="
for path in "${required_files[@]}"; do
    test -f "$repo_root/$path"
    echo "PRESENT $path"
done

echo "=== authority/evidence checks ==="
test "$(rg -o 'REQ-[A-Z]+-[0-9]{3}' "$repo_root/docs/REQUIREMENTS.md" | sort -u | wc -l | tr -d ' ')" = 71
test "$(rg -o 'EVID-00[0-7]' "$repo_root/docs/EVIDENCE_INDEX.md" | sort -u | wc -l | tr -d ' ')" = 8
for decision in WIRE-D001 WIRE-D002 WIRE-D003 WIRE-D004 WIRE-D005 WIRE-D006 WIRE-D007 WIRE-D008; do
    rg -q "^## $decision " "$repo_root/docs/DECISIONS.md"
done
echo "requirement_ids=71"
echo "evidence_ids=EVID-000..EVID-007 expected after WIRE-007 closure"
echo "decision_ids=D001..D008 present"

echo "=== toolchain activation ==="
source "$repo_root/tools/env/setup_oss_cad_suite.sh"
test "$WIRE_TO_DECISION_OSS_CAD_SUITE" = "${WIRE_OSS_CAD_SUITE_ROOT:-$WIRE_TO_DECISION_OSS_CAD_SUITE}"
test -x "$(command -v python3)"
test -x "$(command -v verilator)"
test -x "$(command -v yosys)"
test -x "$(command -v sby)"
test -x "$(command -v yices-smt2)"
test -x "$(command -v nextpnr-ecp5)"
test -x "$(command -v ecppack)"
python3 --version
verilator --version
python3 -c 'import cocotb; print("cocotb", cocotb.__version__)'
yosys -V
sby --version
yices-smt2 --version
nextpnr-ecp5 --version
ecppack --version

echo "=== toolchain smoke ==="
smoke_raw=""
target_build=""
cleanup() {
    if [[ -n "$smoke_raw" ]]; then
        rm -rf "$smoke_raw"
    fi
    if [[ -n "$target_build" ]]; then
        rm -rf "$target_build"
    fi
}
trap cleanup EXIT
smoke_raw="$(mktemp -d /tmp/wire007-smoke-raw.XXXXXX)"
WIRE_SMOKE_RAW_ROOT="$smoke_raw" \
    "$repo_root/tools/smoke/scripts/run_toolchain_smoke.sh"
test -s "$smoke_raw/verilator_smoke.log"
test -s "$smoke_raw/cocotb_verilator_smoke.log"
test -s "$smoke_raw/formal/prove.log"
test -s "$smoke_raw/formal/cover.log"
test -s "$smoke_raw/yosys_smoke.log"
test -s "$smoke_raw/nextpnr_ecp5_smoke.log"
test -s "$smoke_raw/ecppack_smoke.log"

echo "=== WIRE-005 target validation ==="
target_build="$(mktemp -d /tmp/wire007-target.XXXXXX)"
yosys -p "read_verilog -sv $repo_root/tools/smoke/rtl/toolchain_smoke.sv; synth_ecp5 -top toolchain_smoke -json $target_build/toolchain_smoke.json" \
    > "$target_build/yosys.log" 2>&1
nextpnr-ecp5 --85k --package CABGA381 --speed 8 --freq 156.25 \
    --json "$target_build/toolchain_smoke.json" \
    --textcfg "$target_build/toolchain_smoke.config" \
    --report "$target_build/report.json" \
    --lpf-allow-unconstrained \
    > "$target_build/nextpnr.log" 2>&1
ecppack --compress "$target_build/toolchain_smoke.config" "$target_build/toolchain_smoke.bit" \
    > "$target_build/ecppack.log" 2>&1
rg -q 'Program finished normally' "$target_build/nextpnr.log"
test -s "$target_build/toolchain_smoke.bit"
echo "target=LFE5U-85F-8BG381C"
echo "selectors=--85k --package CABGA381 --speed 8 --freq 156.25"

echo "=== post-run tracked tree ==="
test -z "$(git -C "$repo_root" status --short)"
git -C "$repo_root" status --short --branch
echo "WIRE-007 REPRODUCIBILITY PASS"
