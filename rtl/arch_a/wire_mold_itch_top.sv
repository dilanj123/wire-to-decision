// Mold header/sequence -> structural message framer -> semantic ITCH decoder.
// ITCH failure is observable here but is deliberately not wired into the
// WIRE-020 structural packet result.
module wire_mold_itch_top (
    input logic clk, input logic rst, input logic rearm,
    input logic [79:0] cfg_active_session,
    input logic [63:0] cfg_expected_sequence,
    input logic [15:0] cfg_tracked_stock_locate,
    input logic cfg_symbol_check_enable,
    input logic [63:0] cfg_expected_stock_symbol,
    input logic [7:0] in_data, input logic in_valid, output logic in_ready,
    input logic in_last,
    output logic event_valid, input logic event_ready,
    output logic [2:0] event_kind, output logic [7:0] source_type,
    output logic [63:0] mold_sequence, output logic [47:0] itch_timestamp,
    output logic [15:0] stock_locate,
    output logic [63:0] old_order_reference, new_order_reference,
    output logic [31:0] quantity, price, output logic side,
    output logic old_reference_valid, new_reference_valid,
    output logic quantity_valid, price_valid, side_valid,
    output logic decoder_reject_valid, input logic decoder_reject_ready,
    output logic decoder_reject_fatal, output logic [2:0] decoder_reject_code,
    output logic decoder_valid, output logic recovery_required,
    output logic [63:0] current_expected_sequence,
    output logic mold_reject_valid, input logic mold_reject_ready,
    output logic mold_reject_fatal, output logic [2:0] mold_reject_code,
    output logic mold_controller_valid, output logic mold_recovery_required,
    output logic framer_reject_valid, input logic framer_reject_ready,
    output logic framer_reject_fatal, output logic [1:0] framer_reject_code,
    output logic structural_result_valid,
    output logic structural_result_success
);
    logic packet_valid, packet_ready, body_empty;
    logic [63:0] packet_sequence;
    logic [15:0] packet_count;
    logic body_valid, body_ready, body_last;
    logic [7:0] body_data;
    logic result_valid, result_ready, result_success;
    logic message_valid, message_ready, message_empty;
    logic [63:0] message_sequence;
    logic [15:0] message_length;
    logic itch_in_valid, itch_in_ready, itch_in_last;
    logic [7:0] itch_in_data;

    assign structural_result_valid = result_valid && result_ready;
    assign structural_result_success = result_success;

    wire_mold_header_seq mold (
        .clk(clk), .rst(rst), .cfg_active_session(cfg_active_session),
        .cfg_expected_sequence(cfg_expected_sequence), .rearm(rearm),
        .in_valid(in_valid), .in_ready(in_ready), .in_data(in_data), .in_last(in_last),
        .packet_valid(packet_valid), .packet_ready(packet_ready),
        .packet_sequence(packet_sequence), .packet_message_count(packet_count),
        .packet_body_empty(body_empty), .out_valid(body_valid), .out_ready(body_ready),
        .out_data(body_data), .out_last(body_last),
        .packet_result_valid(result_valid), .packet_result_ready(result_ready),
        .packet_result_success(result_success),
        .reject_valid(mold_reject_valid), .reject_ready(mold_reject_ready),
        .reject_fatal(mold_reject_fatal), .reject_code(mold_reject_code),
        .controller_valid(mold_controller_valid), .recovery_required(mold_recovery_required),
        .current_expected_sequence(current_expected_sequence));

    wire_mold_message_framer framer (
        .clk(clk), .rst(rst), .rearm(rearm),
        .packet_valid(packet_valid), .packet_ready(packet_ready),
        .packet_sequence(packet_sequence), .packet_message_count(packet_count),
        .packet_body_empty(body_empty), .in_valid(body_valid), .in_ready(body_ready),
        .in_data(body_data), .in_last(body_last),
        .message_valid(message_valid), .message_ready(message_ready),
        .message_sequence(message_sequence), .message_length(message_length),
        .message_empty(message_empty), .out_valid(itch_in_valid), .out_ready(itch_in_ready),
        .out_data(itch_in_data), .out_last(itch_in_last),
        .packet_result_valid(result_valid), .packet_result_ready(result_ready),
        .packet_result_success(result_success), .reject_valid(framer_reject_valid),
        .reject_ready(framer_reject_ready), .reject_fatal(framer_reject_fatal),
        .reject_code(framer_reject_code));

    wire_itch_decoder itch (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_tracked_stock_locate(cfg_tracked_stock_locate),
        .cfg_symbol_check_enable(cfg_symbol_check_enable),
        .cfg_expected_stock_symbol(cfg_expected_stock_symbol),
        .message_valid(message_valid), .message_ready(message_ready),
        .message_sequence(message_sequence), .message_length(message_length),
        .message_empty(message_empty), .in_data(itch_in_data), .in_valid(itch_in_valid),
        .in_ready(itch_in_ready), .in_last(itch_in_last),
        .event_valid(event_valid), .event_ready(event_ready), .event_kind(event_kind),
        .source_type(source_type), .mold_sequence(mold_sequence), .itch_timestamp(itch_timestamp),
        .stock_locate(stock_locate), .old_order_reference(old_order_reference),
        .new_order_reference(new_order_reference), .quantity(quantity), .price(price), .side(side),
        .old_reference_valid(old_reference_valid), .new_reference_valid(new_reference_valid),
        .quantity_valid(quantity_valid), .price_valid(price_valid), .side_valid(side_valid),
        .reject_valid(decoder_reject_valid), .reject_ready(decoder_reject_ready),
        .reject_fatal(decoder_reject_fatal), .reject_code(decoder_reject_code),
        .decoder_valid(decoder_valid), .recovery_required(recovery_required));
endmodule
