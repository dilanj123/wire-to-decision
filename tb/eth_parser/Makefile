# WIRE-016 standalone Ethernet II parser cocotb regression.
TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_eth_parser
COCOTB_TEST_MODULES := test_eth_parser
VERILOG_SOURCES := $(abspath ../../rtl/arch_a/wire_eth_parser.sv)
COMPILE_ARGS += --language 1800-2012

include $(shell cocotb-config --makefiles)/Makefile.sim
