TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_async_fifo
COCOTB_TEST_MODULES := test_async_fifo
VERILOG_SOURCES := $(abspath ../../rtl/common/wire_async_fifo.sv)
COMPILE_ARGS += --language 1800-2012
include $(shell cocotb-config --makefiles)/Makefile.sim
