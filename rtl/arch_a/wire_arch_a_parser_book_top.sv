// Architecture-A parser plus bounded book/aggregate commit boundary.
// Decision generation remains outside this Phase-3 wrapper.
module wire_arch_a_parser_book_top #(
    parameter integer BOOK_NUM_SETS = 512
) (
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

    output logic parser_valid,
    output logic parser_recovery_required,
    output logic [3:0] parser_recovery_stage,
    output logic [63:0] current_expected_sequence,

    output logic book_valid,
    output logic book_recovery_required,
    output logic [47:0] bid_total,
    output logic [47:0] ask_total,
    output logic commit_valid,
    input logic commit_ready,
    output logic [63:0] commit_mold_sequence,
    output logic [47:0] commit_itch_timestamp,
    output logic [47:0] commit_bid_total,
    output logic [47:0] commit_ask_total,
    output logic error_valid,
    input logic error_ready,
    output logic [3:0] error_code,
    output logic [5:0] stage_reject_observed,
    output logic [5:0] stage_reject_fatal,
    output logic [16:0] stage_reject_code,

    input logic [63:0] debug_reference,
    output logic debug_found,
    output logic [31:0] debug_price,
    output logic [31:0] debug_remaining_quantity,
    output logic debug_side,
    output logic [15:0] last_accepted_event_stock_locate,
    output logic [8:0] debug_set_index,
    output logic debug_way,

    output logic event_valid_observed,
    output logic event_ready_observed,
    output logic [2:0] event_kind_observed,
    output logic [63:0] event_mold_sequence_observed
);
    logic event_valid, event_ready;
    logic [2:0] event_kind;
    logic [7:0] source_type;
    logic [63:0] mold_sequence, old_order_reference, new_order_reference;
    logic [47:0] itch_timestamp;
    logic [15:0] stock_locate;
    logic [31:0] quantity, price;
    logic side, old_reference_valid, new_reference_valid, quantity_valid;
    logic price_valid, side_valid;
    logic eth_reject_observed, eth_reject_fatal, ipv4_reject_observed, ipv4_reject_fatal;
    logic udp_reject_observed, udp_reject_fatal, mold_reject_observed;
    logic framer_reject_observed, itch_reject_observed;
    logic [1:0] eth_reject_code, framer_reject_code;
    logic [3:0] ipv4_reject_code;
    logic [2:0] udp_reject_code, mold_reject_code, itch_reject_code;

    wire_arch_a_parser_top parser (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_destination_ipv4(cfg_destination_ipv4),
        .cfg_destination_udp_port(cfg_destination_udp_port),
        .cfg_active_session(cfg_active_session), .cfg_expected_sequence(cfg_expected_sequence),
        .cfg_tracked_stock_locate(cfg_tracked_stock_locate),
        .cfg_symbol_check_enable(cfg_symbol_check_enable),
        .cfg_expected_stock_symbol(cfg_expected_stock_symbol),
        .rx_data(rx_data), .rx_keep(rx_keep), .rx_valid(rx_valid),
        .rx_ready(rx_ready), .rx_last(rx_last),
        .event_valid(event_valid), .event_ready(event_ready), .event_kind(event_kind),
        .source_type(source_type), .mold_sequence(mold_sequence),
        .itch_timestamp(itch_timestamp), .stock_locate(stock_locate),
        .old_order_reference(old_order_reference), .new_order_reference(new_order_reference),
        .quantity(quantity), .price(price), .side(side),
        .old_reference_valid(old_reference_valid), .new_reference_valid(new_reference_valid),
        .quantity_valid(quantity_valid), .price_valid(price_valid), .side_valid(side_valid),
        .parser_valid(parser_valid), .recovery_required(parser_recovery_required),
        .recovery_stage(parser_recovery_stage), .current_expected_sequence(current_expected_sequence),
        .eth_reject_observed(eth_reject_observed), .eth_reject_fatal(eth_reject_fatal),
        .eth_reject_code(eth_reject_code), .ipv4_reject_observed(ipv4_reject_observed),
        .ipv4_reject_fatal(ipv4_reject_fatal), .ipv4_reject_code(ipv4_reject_code),
        .udp_reject_observed(udp_reject_observed), .udp_reject_fatal(udp_reject_fatal),
        .udp_reject_code(udp_reject_code), .mold_reject_observed(mold_reject_observed),
        .mold_reject_code(mold_reject_code), .framer_reject_observed(framer_reject_observed),
        .framer_reject_code(framer_reject_code), .itch_reject_observed(itch_reject_observed),
        .itch_reject_code(itch_reject_code));

    wire_order_book #(.NUM_SETS(BOOK_NUM_SETS)) book (
        .clk(clk), .rst(rst), .rearm(rearm),
        .upstream_recovery_required(parser_recovery_required),
        .event_valid(event_valid), .event_ready(event_ready), .event_kind(event_kind),
        .source_type(source_type), .mold_sequence(mold_sequence), .itch_timestamp(itch_timestamp),
        .stock_locate(stock_locate), .old_order_reference(old_order_reference),
        .new_order_reference(new_order_reference), .quantity(quantity), .price(price), .side(side),
        .old_reference_valid(old_reference_valid), .new_reference_valid(new_reference_valid),
        .quantity_valid(quantity_valid), .price_valid(price_valid), .side_valid(side_valid),
        .commit_valid(commit_valid), .commit_ready(commit_ready),
        .commit_mold_sequence(commit_mold_sequence), .commit_itch_timestamp(commit_itch_timestamp),
        .commit_bid_total(commit_bid_total), .commit_ask_total(commit_ask_total),
        .book_valid(book_valid), .recovery_required(book_recovery_required),
        .bid_total(bid_total), .ask_total(ask_total), .error_valid(error_valid),
        .error_ready(error_ready), .error_code(error_code), .debug_reference(debug_reference),
        .debug_found(debug_found), .debug_price(debug_price),
        .debug_remaining_quantity(debug_remaining_quantity), .debug_side(debug_side),
        .last_accepted_stock_locate(last_accepted_event_stock_locate), .debug_set_index(debug_set_index),
        .debug_way(debug_way));

    assign event_valid_observed = event_valid;
    assign event_ready_observed = event_ready;
    assign event_kind_observed = event_kind;
    assign event_mold_sequence_observed = mold_sequence;
    assign stage_reject_observed = {itch_reject_observed, framer_reject_observed,
        mold_reject_observed, udp_reject_observed, ipv4_reject_observed, eth_reject_observed};
    assign stage_reject_fatal = {itch_reject_observed, framer_reject_observed,
        mold_reject_observed, udp_reject_fatal, ipv4_reject_fatal, eth_reject_fatal};
    assign stage_reject_code = {itch_reject_code, framer_reject_code,
        mold_reject_code, udp_reject_code, ipv4_reject_code, eth_reject_code};
endmodule
