TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_arch_a_parser_top
SIM_BUILD := sim_build
COCOTB_TEST_MODULES := test_arch_a_parser
VERILOG_SOURCES := $(abspath ../../rtl/common/wire_ingress_buffer.sv) \
 $(abspath ../../rtl/arch_a/wire_gearbox_64to8.sv) \
 $(abspath ../../rtl/arch_a/wire_eth_parser.sv) \
 $(abspath ../../rtl/arch_a/wire_ipv4_parser.sv) \
 $(abspath ../../rtl/arch_a/wire_udp_parser.sv) \
 $(abspath ../../rtl/arch_a/wire_mold_header_seq.sv) \
 $(abspath ../../rtl/arch_a/wire_mold_message_framer.sv) \
 $(abspath ../../rtl/arch_a/wire_itch_decoder.sv) \
 $(abspath ../../rtl/arch_a/wire_arch_a_parser_top.sv)
COMPILE_ARGS += --language 1800-2012
include $(shell cocotb-config --makefiles)/Makefile.sim
