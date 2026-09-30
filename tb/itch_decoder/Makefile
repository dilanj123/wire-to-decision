TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_itch_decoder
COCOTB_TEST_MODULES := test_itch_decoder
VERILOG_SOURCES := $(abspath ../../rtl/arch_a/wire_itch_decoder.sv)
COMPILE_ARGS += --language 1800-2012
include $(shell cocotb-config --makefiles)/Makefile.sim
