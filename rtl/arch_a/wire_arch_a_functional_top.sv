// Single-clock functional MVP: post-MAC ingress through parser, bounded book,
// aggregates and deterministic threshold/risk-budget decision output.
module wire_arch_a_functional_top #(
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
    input logic [47:0] cfg_decision_threshold,
    input logic [31:0] cfg_initial_budget,
    input logic decision_enable,

    input logic [63:0] rx_data,
    input logic [7:0] rx_keep,
    input logic rx_valid,
    output logic rx_ready,
    input logic rx_last,

    output logic decision_valid,
    input logic decision_ready,
    output logic decision_action,
    output logic [63:0] decision_mold_sequence,
    output logic [47:0] decision_itch_timestamp,
    output logic signed [48:0] decision_signed_imbalance,

    output logic parser_valid,
    output logic parser_recovery_required,
    output logic [3:0] parser_recovery_stage,
    output logic [63:0] current_expected_sequence,
    output logic book_valid,
    output logic book_recovery_required,
    output logic [47:0] bid_total,
    output logic [47:0] ask_total,
    output logic signed [48:0] previous_imbalance,
    output logic [31:0] remaining_budget,
    output logic [31:0] decision_count,
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
    output logic [63:0] event_mold_sequence_observed,
    output logic commit_valid_observed,
    output logic commit_ready_observed,
    output logic [63:0] commit_mold_sequence_observed,
    output logic [47:0] commit_bid_total_observed,
    output logic [47:0] commit_ask_total_observed
);
    logic commit_valid, commit_ready;
    logic [63:0] commit_mold_sequence;
    logic [47:0] commit_itch_timestamp, commit_bid_total, commit_ask_total;

    wire_arch_a_parser_book_top #(.BOOK_NUM_SETS(BOOK_NUM_SETS)) parser_book (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_destination_ipv4(cfg_destination_ipv4),
        .cfg_destination_udp_port(cfg_destination_udp_port),
        .cfg_active_session(cfg_active_session), .cfg_expected_sequence(cfg_expected_sequence),
        .cfg_tracked_stock_locate(cfg_tracked_stock_locate),
        .cfg_symbol_check_enable(cfg_symbol_check_enable),
        .cfg_expected_stock_symbol(cfg_expected_stock_symbol),
        .rx_data(rx_data), .rx_keep(rx_keep), .rx_valid(rx_valid),
        .rx_ready(rx_ready), .rx_last(rx_last),
        .parser_valid(parser_valid), .parser_recovery_required(parser_recovery_required),
        .parser_recovery_stage(parser_recovery_stage),
        .current_expected_sequence(current_expected_sequence),
        .book_valid(book_valid), .book_recovery_required(book_recovery_required),
        .bid_total(bid_total), .ask_total(ask_total),
        .commit_valid(commit_valid), .commit_ready(commit_ready),
        .commit_mold_sequence(commit_mold_sequence),
        .commit_itch_timestamp(commit_itch_timestamp),
        .commit_bid_total(commit_bid_total), .commit_ask_total(commit_ask_total),
        .error_valid(error_valid), .error_ready(error_ready), .error_code(error_code),
        .stage_reject_observed(stage_reject_observed),
        .stage_reject_fatal(stage_reject_fatal), .stage_reject_code(stage_reject_code),
        .debug_reference(debug_reference), .debug_found(debug_found),
        .debug_price(debug_price), .debug_remaining_quantity(debug_remaining_quantity),
        .debug_side(debug_side),
        .last_accepted_event_stock_locate(last_accepted_event_stock_locate),
        .debug_set_index(debug_set_index), .debug_way(debug_way),
        .event_valid_observed(event_valid_observed), .event_ready_observed(event_ready_observed),
        .event_kind_observed(event_kind_observed),
        .event_mold_sequence_observed(event_mold_sequence_observed));

    wire_decision_engine decision (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_decision_threshold(cfg_decision_threshold),
        .cfg_initial_budget(cfg_initial_budget), .decision_enable(decision_enable),
        .commit_valid(commit_valid), .commit_ready(commit_ready),
        .commit_mold_sequence(commit_mold_sequence),
        .commit_itch_timestamp(commit_itch_timestamp),
        .commit_bid_total(commit_bid_total), .commit_ask_total(commit_ask_total),
        .decision_valid(decision_valid), .decision_ready(decision_ready),
        .decision_action(decision_action),
        .decision_mold_sequence(decision_mold_sequence),
        .decision_itch_timestamp(decision_itch_timestamp),
        .decision_signed_imbalance(decision_signed_imbalance),
        .previous_imbalance(previous_imbalance),
        .remaining_budget(remaining_budget), .decision_count(decision_count));

    assign commit_valid_observed = commit_valid;
    assign commit_ready_observed = commit_ready;
    assign commit_mold_sequence_observed = commit_mold_sequence;
    assign commit_bid_total_observed = commit_bid_total;
    assign commit_ask_total_observed = commit_ask_total;
endmodule
