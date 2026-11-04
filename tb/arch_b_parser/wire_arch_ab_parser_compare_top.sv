module wire_arch_ab_parser_compare_top (
    input logic clk, rst, rearm,
    input logic [31:0] cfg_destination_ipv4,
    input logic [15:0] cfg_destination_udp_port,
    input logic [79:0] cfg_active_session,
    input logic [63:0] cfg_expected_sequence,
    input logic [15:0] cfg_tracked_stock_locate,
    input logic cfg_symbol_check_enable,
    input logic [63:0] cfg_expected_stock_symbol,
    input logic [63:0] rx_data,
    input logic [7:0] rx_keep,
    input logic rx_valid,
    output logic rx_ready,
    input logic rx_last,
    input logic a_event_ready,
    output logic a_event_valid,
    output logic [336:0] a_event,
    output logic a_recovery,
    output logic [63:0] a_expected_sequence,
    input logic b_event_ready,
    output logic b_event_valid,
    output logic [336:0] b_event,
    output logic b_recovery,
    output logic [63:0] b_expected_sequence
);
    logic a_ready, b_ready;
    logic shared_valid;
    logic [2:0] ak, bk;
    logic [7:0] atype, btype;
    logic [63:0] amold, bmold, aold, bold, anew, bnew;
    logic [47:0] ats, bts;
    logic [15:0] aloc, bloc;
    logic [31:0] aq, bq, ap, bp;
    logic aside, bside, aov, bov, anv, bnv, aqv, bqv, apv, bpv, asv, bsv;
    logic av, bv;
    logic [3:0] astage;

    assign rx_ready = a_ready && b_ready;
    assign shared_valid = rx_valid && rx_ready;
    assign a_event = {ak,atype,amold,ats,aloc,aold,anew,aq,ap,aside,aov,anv,aqv,apv,asv};
    assign b_event = {bk,btype,bmold,bts,bloc,bold,bnew,bq,bp,bside,bov,bnv,bqv,bpv,bsv};
    assign a_event_valid = av;
    assign b_event_valid = bv;

    wire_arch_a_parser_top a (
        .clk(clk),.rst(rst),.rearm(rearm),.cfg_destination_ipv4(cfg_destination_ipv4),
        .cfg_destination_udp_port(cfg_destination_udp_port),.cfg_active_session(cfg_active_session),
        .cfg_expected_sequence(cfg_expected_sequence),.cfg_tracked_stock_locate(cfg_tracked_stock_locate),
        .cfg_symbol_check_enable(cfg_symbol_check_enable),.cfg_expected_stock_symbol(cfg_expected_stock_symbol),
        .rx_data(rx_data),.rx_keep(rx_keep),.rx_valid(shared_valid),.rx_ready(a_ready),.rx_last(rx_last),
        .event_valid(av),.event_ready(a_event_ready),.event_kind(ak),.source_type(atype),
        .mold_sequence(amold),.itch_timestamp(ats),.stock_locate(aloc),.old_order_reference(aold),
        .new_order_reference(anew),.quantity(aq),.price(ap),.side(aside),
        .old_reference_valid(aov),.new_reference_valid(anv),.quantity_valid(aqv),
        .price_valid(apv),.side_valid(asv),.parser_valid(),.recovery_required(a_recovery),
        .recovery_stage(astage),.current_expected_sequence(a_expected_sequence),
        .eth_reject_observed(),.eth_reject_fatal(),.eth_reject_code(),
        .ipv4_reject_observed(),.ipv4_reject_fatal(),.ipv4_reject_code(),
        .udp_reject_observed(),.udp_reject_fatal(),.udp_reject_code(),
        .mold_reject_observed(),.mold_reject_code(),.framer_reject_observed(),
        .framer_reject_code(),.itch_reject_observed(),.itch_reject_code()
    );
    wire_arch_b_parser_top b (
        .clk(clk),.rst(rst),.rearm(rearm),.cfg_destination_ipv4(cfg_destination_ipv4),
        .cfg_destination_udp_port(cfg_destination_udp_port),.cfg_active_session(cfg_active_session),
        .cfg_expected_sequence(cfg_expected_sequence),.cfg_tracked_stock_locate(cfg_tracked_stock_locate),
        .cfg_symbol_check_enable(cfg_symbol_check_enable),.cfg_expected_stock_symbol(cfg_expected_stock_symbol),
        .rx_data(rx_data),.rx_keep(rx_keep),.rx_valid(shared_valid),.rx_ready(b_ready),.rx_last(rx_last),
        .event_valid(bv),.event_ready(b_event_ready),.event_kind(bk),.source_type(btype),
        .mold_sequence(bmold),.itch_timestamp(bts),.stock_locate(bloc),.old_order_reference(bold),
        .new_order_reference(bnew),.quantity(bq),.price(bp),.side(bside),
        .old_reference_valid(bov),.new_reference_valid(bnv),.quantity_valid(bqv),
        .price_valid(bpv),.side_valid(bsv),.parser_valid(),.recovery_required(b_recovery),
        .recovery_stage(),.current_expected_sequence(b_expected_sequence)
    );
endmodule
