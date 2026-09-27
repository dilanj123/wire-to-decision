# WIRE-004 TOOLCHAIN SMOKE ONLY. Not production project infrastructure.
TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := toolchain_smoke
COCOTB_TEST_MODULES := test_toolchain_smoke
VERILOG_SOURCES := $(abspath ../rtl/toolchain_smoke.sv)
COMPILE_ARGS += --language 1800-2012

include $(shell cocotb-config --makefiles)/Makefile.sim
