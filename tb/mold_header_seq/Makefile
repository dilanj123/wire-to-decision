TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_mold_header_seq
COCOTB_TEST_MODULES := test_mold_header_seq
VERILOG_SOURCES := $(abspath ../../rtl/arch_a/wire_mold_header_seq.sv)
COMPILE_ARGS += --language 1800-2012

include $(shell cocotb-config --makefiles)/Makefile.sim
