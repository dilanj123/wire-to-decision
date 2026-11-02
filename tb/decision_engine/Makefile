TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_decision_engine
SIM_BUILD := sim_build
COCOTB_TEST_MODULES := test_decision_engine
VERILOG_SOURCES := $(abspath ../../rtl/common/wire_decision_engine.sv)
COMPILE_ARGS += --language 1800-2012
include $(shell cocotb-config --makefiles)/Makefile.sim
