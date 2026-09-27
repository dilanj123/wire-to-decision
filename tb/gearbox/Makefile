# WIRE-014 Architecture A gearbox cocotb regression.
TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_gearbox_64to8
COCOTB_TEST_MODULES := test_gearbox
VERILOG_SOURCES := $(abspath ../../rtl/arch_a/wire_gearbox_64to8.sv)
COMPILE_ARGS += --language 1800-2012

include $(shell cocotb-config --makefiles)/Makefile.sim
