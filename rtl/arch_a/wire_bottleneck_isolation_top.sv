// Small measurement harness exposing the three existing service boundaries.
// It instantiates production-size blocks; no mutation or parser logic is copied.
module wire_bottleneck_isolation_top (
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
    input logic parser_event_ready,
    output logic parser_event_valid,
    output logic [2:0] parser_event_kind,
    output logic [63:0] parser_event_sequence,
    output logic parser_recovery_required,

    input logic book_event_valid,
    output logic book_event_ready,
    input logic [2:0] book_event_kind,
    input logic [7:0] book_source_type,
    input logic [63:0] book_mold_sequence,
    input logic [47:0] book_itch_timestamp,
    // {old_reference, new_reference, quantity, price, side} validity bits.
    input logic [4:0] book_fields_valid,
    input logic [63:0] book_old_reference,
    input logic [63:0] book_new_reference,
    input logic [31:0] book_quantity,
    input logic [31:0] book_price,
    input logic book_side,
    input logic book_upstream_recovery,
    output logic book_commit_valid,
    input logic book_commit_ready,
    output logic [63:0] book_commit_sequence,
    output logic [47:0] book_commit_timestamp,
    output logic [47:0] book_commit_bid,
    output logic [47:0] book_commit_ask,
    output logic book_recovery_required,
    output logic book_error_valid,
    input logic book_error_ready,
    output logic [3:0] book_error_code,

    input logic decision_commit_valid,
    output logic decision_commit_ready,
    input logic [63:0] decision_commit_sequence,
    input logic [47:0] decision_commit_timestamp,
    input logic [47:0] decision_commit_bid,
    input logic [47:0] decision_commit_ask,
    output logic decision_valid,
    input logic decision_ready,
    output logic decision_action,
    output logic [63:0] decision_sequence,
    output logic [47:0] decision_timestamp,
    output logic signed [48:0] decision_imbalance
);
    logic [31:0] unused_price;
    logic [31:0] unused_quantity;
    logic unused_side;
    logic [15:0] unused_locate;
    logic [8:0] unused_set;
    logic unused_way;
    logic unused_book_valid;
    logic [47:0] unused_bid, unused_ask;
    logic unused_parser_valid;
    logic [3:0] unused_recovery_stage;
    logic [63:0] unused_expected_sequence;
    logic [1:0] unused_eth_code;
    logic [3:0] unused_ip_code;
    logic [2:0] unused_udp_code, unused_mold_code, unused_itch_code;
    logic [1:0] unused_framer_code;
    logic unused_eth_reject, unused_eth_fatal, unused_ip_reject, unused_ip_fatal;
    logic unused_udp_reject, unused_udp_fatal, unused_mold_reject;
    logic unused_framer_reject, unused_itch_reject;
    logic signed [48:0] unused_previous;
    logic [31:0] unused_budget, unused_decision_count;

    wire_arch_a_parser_top parser (
        .clk, .rst, .rearm,
        .cfg_destination_ipv4, .cfg_destination_udp_port,
        .cfg_active_session, .cfg_expected_sequence,
        .cfg_tracked_stock_locate, .cfg_symbol_check_enable,
        .cfg_expected_stock_symbol,
        .rx_data, .rx_keep, .rx_valid, .rx_ready, .rx_last,
        .event_valid(parser_event_valid), .event_ready(parser_event_ready),
        .event_kind(parser_event_kind), .source_type(),
        .mold_sequence(parser_event_sequence), .itch_timestamp(), .stock_locate(),
        .old_order_reference(), .new_order_reference(), .quantity(), .price(), .side(),
        .old_reference_valid(), .new_reference_valid(), .quantity_valid(),
        .price_valid(), .side_valid(),
        .parser_valid(unused_parser_valid), .recovery_required(parser_recovery_required),
        .recovery_stage(unused_recovery_stage),
        .current_expected_sequence(unused_expected_sequence),
        .eth_reject_observed(unused_eth_reject), .eth_reject_fatal(unused_eth_fatal),
        .eth_reject_code(unused_eth_code), .ipv4_reject_observed(unused_ip_reject),
        .ipv4_reject_fatal(unused_ip_fatal), .ipv4_reject_code(unused_ip_code),
        .udp_reject_observed(unused_udp_reject), .udp_reject_fatal(unused_udp_fatal),
        .udp_reject_code(unused_udp_code), .mold_reject_observed(unused_mold_reject),
        .mold_reject_code(unused_mold_code), .framer_reject_observed(unused_framer_reject),
        .framer_reject_code(unused_framer_code), .itch_reject_observed(unused_itch_reject),
        .itch_reject_code(unused_itch_code));

    wire_order_book #(.NUM_SETS(512)) book (
        .clk, .rst, .rearm,
        .upstream_recovery_required(book_upstream_recovery),
        .event_valid(book_event_valid), .event_ready(book_event_ready),
        .event_kind(book_event_kind), .source_type(book_source_type),
        .mold_sequence(book_mold_sequence), .itch_timestamp(book_itch_timestamp),
        .stock_locate(16'd0), .old_order_reference(book_old_reference),
        .new_order_reference(book_new_reference), .quantity(book_quantity),
        .price(book_price), .side(book_side),
        .old_reference_valid(book_fields_valid[4]),
        .new_reference_valid(book_fields_valid[3]),
        .quantity_valid(book_fields_valid[2]), .price_valid(book_fields_valid[1]),
        .side_valid(book_fields_valid[0]),
        .commit_valid(book_commit_valid), .commit_ready(book_commit_ready),
        .commit_mold_sequence(book_commit_sequence),
        .commit_itch_timestamp(book_commit_timestamp),
        .commit_bid_total(book_commit_bid), .commit_ask_total(book_commit_ask),
        .book_valid(unused_book_valid), .recovery_required(book_recovery_required),
        .bid_total(unused_bid), .ask_total(unused_ask),
        .error_valid(book_error_valid), .error_ready(book_error_ready),
        .error_code(book_error_code), .debug_reference(64'd0),
        .debug_found(), .debug_price(unused_price),
        .debug_remaining_quantity(unused_quantity), .debug_side(unused_side),
        .last_accepted_stock_locate(unused_locate), .debug_set_index(unused_set),
        .debug_way(unused_way));

    wire_decision_engine decision (
        .clk, .rst, .rearm, .cfg_decision_threshold(48'd10),
        .cfg_initial_budget(32'd20), .decision_enable(1'b1),
        .commit_valid(decision_commit_valid), .commit_ready(decision_commit_ready),
        .commit_mold_sequence(decision_commit_sequence),
        .commit_itch_timestamp(decision_commit_timestamp),
        .commit_bid_total(decision_commit_bid), .commit_ask_total(decision_commit_ask),
        .decision_valid, .decision_ready, .decision_action,
        .decision_mold_sequence(decision_sequence),
        .decision_itch_timestamp(decision_timestamp),
        .decision_signed_imbalance(decision_imbalance),
        .previous_imbalance(unused_previous), .remaining_budget(unused_budget),
        .decision_count(unused_decision_count));
endmodule
