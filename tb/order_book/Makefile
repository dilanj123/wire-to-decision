TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_order_book
SIM_BUILD := sim_build
COCOTB_TEST_MODULES := test_order_book
VERILOG_SOURCES := $(abspath ../../rtl/common/wire_order_book.sv)
COMPILE_ARGS += --language 1800-2012
include $(shell cocotb-config --makefiles)/Makefile.sim
