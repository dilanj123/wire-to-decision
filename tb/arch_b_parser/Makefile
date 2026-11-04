TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(PWD)/../../rtl/common/wire_ingress_buffer.sv \
                  $(PWD)/../../rtl/arch_a/wire_gearbox_64to8.sv \
                  $(PWD)/../../rtl/arch_a/wire_eth_parser.sv \
                  $(PWD)/../../rtl/arch_a/wire_ipv4_parser.sv \
                  $(PWD)/../../rtl/arch_a/wire_udp_parser.sv \
                  $(PWD)/../../rtl/arch_a/wire_mold_header_seq.sv \
                  $(PWD)/../../rtl/arch_a/wire_mold_message_framer.sv \
                  $(PWD)/../../rtl/arch_a/wire_itch_decoder.sv \
                  $(PWD)/../../rtl/arch_a/wire_arch_a_parser_top.sv \
                  $(PWD)/../../rtl/arch_b/wire_arch_b_parser_top.sv \
                  $(PWD)/wire_arch_ab_parser_compare_top.sv
TOPLEVEL = wire_arch_ab_parser_compare_top
MODULE = test_arch_b_parser
SIM ?= verilator
COMPILE_ARGS += --timing -Wno-fatal
include $(shell cocotb-config --makefiles)/Makefile.sim
