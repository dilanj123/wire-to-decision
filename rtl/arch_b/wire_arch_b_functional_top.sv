// Architecture-B experimental parser with the unchanged WIRE-027 book and
// decision engine. Only the parser implementation differs from A.
module wire_arch_b_functional_top #(
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
    output logic [31:0] decision_count
);
    logic event_valid, event_ready;
    logic [2:0] event_kind;
    logic [7:0] source_type;
    logic [63:0] mold_sequence, old_ref, new_ref;
    logic [47:0] itch_timestamp;
    logic [15:0] stock_locate;
    logic [31:0] quantity, price;
    logic side, old_ref_valid, new_ref_valid, quantity_valid, price_valid, side_valid;
    logic commit_valid, commit_ready;
    logic [63:0] commit_sequence;
    logic [47:0] commit_timestamp, commit_bid, commit_ask;

    wire_arch_b_parser_top parser (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_destination_ipv4(cfg_destination_ipv4),
        .cfg_destination_udp_port(cfg_destination_udp_port),
        .cfg_active_session(cfg_active_session), .cfg_expected_sequence(cfg_expected_sequence),
        .cfg_tracked_stock_locate(cfg_tracked_stock_locate),
        .cfg_symbol_check_enable(cfg_symbol_check_enable),
        .cfg_expected_stock_symbol(cfg_expected_stock_symbol),
        .rx_data(rx_data), .rx_keep(rx_keep), .rx_valid(rx_valid), .rx_ready(rx_ready), .rx_last(rx_last),
        .event_valid(event_valid), .event_ready(event_ready), .event_kind(event_kind),
        .source_type(source_type), .mold_sequence(mold_sequence), .itch_timestamp(itch_timestamp),
        .stock_locate(stock_locate), .old_order_reference(old_ref), .new_order_reference(new_ref),
        .quantity(quantity), .price(price), .side(side),
        .old_reference_valid(old_ref_valid), .new_reference_valid(new_ref_valid),
        .quantity_valid(quantity_valid), .price_valid(price_valid), .side_valid(side_valid),
        .parser_valid(parser_valid), .recovery_required(parser_recovery_required),
        .recovery_stage(parser_recovery_stage), .current_expected_sequence(current_expected_sequence)
    );

    /* verilator lint_off PINCONNECTEMPTY */
    wire_order_book #(.NUM_SETS(BOOK_NUM_SETS)) book (
        .clk(clk), .rst(rst), .rearm(rearm), .upstream_recovery_required(parser_recovery_required),
        .event_valid(event_valid), .event_ready(event_ready), .event_kind(event_kind),
        .source_type(source_type), .mold_sequence(mold_sequence), .itch_timestamp(itch_timestamp),
        .stock_locate(stock_locate), .old_order_reference(old_ref), .new_order_reference(new_ref),
        .quantity(quantity), .price(price), .side(side),
        .old_reference_valid(old_ref_valid), .new_reference_valid(new_ref_valid),
        .quantity_valid(quantity_valid), .price_valid(price_valid), .side_valid(side_valid),
        .commit_valid(commit_valid), .commit_ready(commit_ready),
        .commit_mold_sequence(commit_sequence), .commit_itch_timestamp(commit_timestamp),
        .commit_bid_total(commit_bid), .commit_ask_total(commit_ask),
        .book_valid(book_valid), .recovery_required(book_recovery_required),
        .bid_total(bid_total), .ask_total(ask_total),
        .error_valid(), .error_ready(1'b1), .error_code(),
        .debug_reference(64'd0), .debug_found(), .debug_price(),
        .debug_remaining_quantity(), .debug_side(),
        .last_accepted_stock_locate(), .debug_set_index(), .debug_way()
    );
    /* verilator lint_on PINCONNECTEMPTY */

    wire_decision_engine decision (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_decision_threshold(cfg_decision_threshold), .cfg_initial_budget(cfg_initial_budget),
        .decision_enable(decision_enable), .commit_valid(commit_valid), .commit_ready(commit_ready),
        .commit_mold_sequence(commit_sequence), .commit_itch_timestamp(commit_timestamp),
        .commit_bid_total(commit_bid), .commit_ask_total(commit_ask),
        .decision_valid(decision_valid), .decision_ready(decision_ready),
        .decision_action(decision_action), .decision_mold_sequence(decision_mold_sequence),
        .decision_itch_timestamp(decision_itch_timestamp),
        .decision_signed_imbalance(decision_signed_imbalance),
        .previous_imbalance(previous_imbalance), .remaining_budget(remaining_budget),
        .decision_count(decision_count)
    );
endmodule
