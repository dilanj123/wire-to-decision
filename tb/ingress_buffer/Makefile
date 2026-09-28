# WIRE-015 standalone common ingress-buffer cocotb regression.
TOPLEVEL_LANG := verilog
SIM ?= verilator
TOPLEVEL := wire_ingress_buffer
COCOTB_TEST_MODULES := test_ingress_buffer
VERILOG_SOURCES := $(abspath ../../rtl/common/wire_ingress_buffer.sv)
COMPILE_ARGS += --language 1800-2012

include $(shell cocotb-config --makefiles)/Makefile.sim
