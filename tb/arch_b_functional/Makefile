TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(PWD)/../../rtl/common/wire_ingress_buffer.sv \
                  $(PWD)/../../rtl/common/wire_order_book.sv \
                  $(PWD)/../../rtl/common/wire_decision_engine.sv \
                  $(PWD)/../../rtl/arch_b/wire_arch_b_parser_top.sv \
                  $(PWD)/../../rtl/arch_b/wire_arch_b_functional_top.sv
TOPLEVEL = wire_arch_b_functional_top
MODULE = test_arch_b_functional
SIM ?= verilator
COMPILE_ARGS += --timing -Wno-fatal
include $(shell cocotb-config --makefiles)/Makefile.sim
