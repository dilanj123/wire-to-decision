TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_udp_parser
COCOTB_TEST_MODULES := test_udp_parser
VERILOG_SOURCES := $(abspath ../../rtl/arch_a/wire_udp_parser.sv)
COMPILE_ARGS += --language 1800-2012

include $(shell cocotb-config --makefiles)/Makefile.sim
