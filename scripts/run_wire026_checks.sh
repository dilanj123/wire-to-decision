#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WIRE_OSS_CAD_SUITE="${WIRE_OSS_CAD_SUITE:-/Users/Dilan/eda/wire-to-decision/oss-cad-suite}"

# Reuse the established Phase-4 driver for Python, WIRE-014..024 cocotb,
# passing decomposed formal jobs, and functional-top Verilator lint.
"$ROOT/scripts/run_wire025_regression.sh"

source "$WIRE_OSS_CAD_SUITE/environment"
WRAPPER_DIR="$ROOT/tb/benchmark_wrapper"
CREATED_LIB_LINK=0
if [[ ! -e "$WRAPPER_DIR/lib" ]]; then
    ln -s "$WIRE_OSS_CAD_SUITE/lib" "$WRAPPER_DIR/lib"
    CREATED_LIB_LINK=1
fi
cleanup() {
    if [[ "$CREATED_LIB_LINK" == 1 && -L "$WRAPPER_DIR/lib" ]]; then
        unlink "$WRAPPER_DIR/lib"
    fi
}
trap cleanup EXIT

(cd "$WRAPPER_DIR" && make clean && make SIM=verilator)

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
    "$ROOT/rtl/arch_a/wire_arch_a_benchmark_top.sv"
)
verilator --lint-only --Wall --language 1800-2012 \
    --top-module wire_arch_a_benchmark_top "${RTL_SOURCES[@]}"

echo "WIRE-026 checks completed successfully"
