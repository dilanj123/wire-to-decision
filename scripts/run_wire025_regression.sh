#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WIRE_OSS_CAD_SUITE="${WIRE_OSS_CAD_SUITE:-/Users/Dilan/eda/wire-to-decision/oss-cad-suite}"
ENV_FILE="$WIRE_OSS_CAD_SUITE/environment"
RAW="$ROOT/results/raw/wire025"
mkdir -p "$RAW/cocotb" "$RAW/formal"
source "$ENV_FILE"

# Cocotb's Verilator loader expects the qualified suite library beside each test.
TEST_DIRS=(gearbox ingress_buffer eth_parser ipv4_parser udp_parser mold_header_seq mold_message_framer itch_decoder arch_a_parser order_book parser_book decision_engine functional_mvp)
for test_name in "${TEST_DIRS[@]}"; do
    test_dir="$ROOT/tb/$test_name"
    if [[ ! -e "$test_dir/lib" ]]; then
        ln -s "$WIRE_OSS_CAD_SUITE/lib" "$test_dir/lib"
    fi
done
cleanup() {
    for test_name in "${TEST_DIRS[@]}"; do
        test_dir="$ROOT/tb/$test_name"
        if [[ -L "$test_dir/lib" ]]; then unlink "$test_dir/lib"; fi
    done
}
trap cleanup EXIT

run_cocotb() {
    local test_name="$1" makefile="$2" label="$3"
    local test_dir="$ROOT/tb/$test_name"
    local log="$RAW/cocotb/${label}.log"
    echo "RUN cocotb $label"
    (cd "$test_dir" && make -f "$makefile" clean && make -f "$makefile" SIM=verilator) 2>&1 | tee "$log"
}

run_cocotb gearbox Makefile wire014_gearbox
run_cocotb ingress_buffer Makefile wire015_ingress
run_cocotb ingress_buffer Makefile.integration wire015_buffer_gearbox
run_cocotb eth_parser Makefile wire016_ethernet
run_cocotb eth_parser Makefile.composition wire016_composition
run_cocotb ipv4_parser Makefile wire017_ipv4
run_cocotb ipv4_parser Makefile.composition wire017_composition
run_cocotb udp_parser Makefile wire018_udp
run_cocotb udp_parser Makefile.composition wire018_composition
run_cocotb mold_header_seq Makefile wire019_mold_header
run_cocotb mold_header_seq Makefile.composition wire019_composition
run_cocotb mold_message_framer Makefile wire020_mold_framer
run_cocotb mold_message_framer Makefile.composition wire020_composition
run_cocotb itch_decoder Makefile wire021_itch
run_cocotb itch_decoder Makefile.composition wire021_composition
run_cocotb arch_a_parser Makefile wire022_full_parser
run_cocotb order_book Makefile wire023_order_book
run_cocotb parser_book Makefile wire023_parser_book
run_cocotb decision_engine Makefile wire024_decision
run_cocotb functional_mvp Makefile wire024_functional_mvp

PYTHONPATH="$ROOT/model/python" python3 -m unittest discover -s "$ROOT/model/python/tests" -v 2>&1 | tee "$RAW/python_71.log"

# Keep the two documented solver-bound monolithic jobs as historical evidence.
SKIP_JOBS=(formal/ipv4_parser/wire_ipv4_parser_reference.sby formal/arch_a_parser/wire_arch_a_parser_late_suffix.sby)
while IFS= read -r job; do
    skip=0
    for excluded in "${SKIP_JOBS[@]}"; do
        [[ "$job" == "$ROOT/$excluded" ]] && skip=1
    done
    (( skip )) && continue
    job_dir="$(dirname "$job")"
    job_file="$(basename "$job")"
    label="$(basename "$job_dir")_${job_file%.sby}"
    log="$RAW/formal/${label}.log"
    echo "RUN formal $job"
    if grep -Eq '^(rtl|formal)/' "$job_dir/$job_file"; then
        (cd "$ROOT" && sby -f "$job") 2>&1 | tee "$log"
    else
        (cd "$job_dir" && sby -f "$job_file") 2>&1 | tee "$log"
    fi
done < <(find "$ROOT/formal" -mindepth 2 -maxdepth 2 -type f -name '*.sby' | sort)

RTL_SOURCES=(
    "$ROOT/rtl/common/wire_ingress_buffer.sv"
    "$ROOT/rtl/common/wire_order_book.sv"
    "$ROOT/rtl/common/wire_decision_engine.sv"
    "$ROOT/rtl/arch_a/wire_gearbox_64to8.sv"
    "$ROOT/rtl/arch_a/wire_eth_parser.sv"
    "$ROOT/rtl/arch_a/wire_ipv4_parser.sv"
    "$ROOT/rtl/arch_a/wire_udp_parser.sv"
    "$ROOT/rtl/arch_a/wire_mold_header_seq.sv"
    "$ROOT/rtl/arch_a/wire_mold_message_framer.sv"
    "$ROOT/rtl/arch_a/wire_itch_decoder.sv"
    "$ROOT/rtl/arch_a/wire_arch_a_parser_top.sv"
    "$ROOT/rtl/arch_a/wire_arch_a_parser_book_top.sv"
    "$ROOT/rtl/arch_a/wire_arch_a_functional_top.sv"
)
verilator --lint-only --Wall --language 1800-2012 --top-module wire_arch_a_functional_top "${RTL_SOURCES[@]}" 2>&1 | tee "$RAW/verilator_functional_top.log"
echo "WIRE-025 regression campaign completed successfully"
