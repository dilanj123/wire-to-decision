// Complete Architecture-A parser boundary from post-MAC framed beats to
// WIRE-D017 normalized mutation events. This is parser infrastructure only:
// no order state, decision logic, global error arbiter, CDC, or P&R contract.
module wire_arch_a_parser_top (
    input  logic        clk,
    input  logic        rst,
    input  logic        rearm,

    input  logic [31:0] cfg_destination_ipv4,
    input  logic [15:0] cfg_destination_udp_port,
    input  logic [79:0] cfg_active_session,
    input  logic [63:0] cfg_expected_sequence,
    input  logic [15:0] cfg_tracked_stock_locate,
    input  logic        cfg_symbol_check_enable,
    input  logic [63:0] cfg_expected_stock_symbol,

    input  logic [63:0] rx_data,
    input  logic [7:0]  rx_keep,
    input  logic        rx_valid,
    output logic        rx_ready,
    input  logic        rx_last,

    output logic        event_valid,
    input  logic        event_ready,
    output logic [2:0]  event_kind,
    output logic [7:0]  source_type,
    output logic [63:0] mold_sequence,
    output logic [47:0] itch_timestamp,
    output logic [15:0] stock_locate,
    output logic [63:0] old_order_reference,
    output logic [63:0] new_order_reference,
    output logic [31:0] quantity,
    output logic [31:0] price,
    output logic        side,
    output logic        old_reference_valid,
    output logic        new_reference_valid,
    output logic        quantity_valid,
    output logic        price_valid,
    output logic        side_valid,

    output logic        parser_valid,
    output logic        recovery_required,
    output logic [3:0]  recovery_stage,
    output logic [63:0] current_expected_sequence,

    // Stage-local diagnostic transactions are auto-accepted internally;
    // these valid/code outputs are observational pulses, not backpressured.
    output logic        eth_reject_observed,
    output logic        eth_reject_fatal,
    output logic [1:0]  eth_reject_code,
    output logic        ipv4_reject_observed,
    output logic        ipv4_reject_fatal,
    output logic [3:0]  ipv4_reject_code,
    output logic        udp_reject_observed,
    output logic        udp_reject_fatal,
    output logic [2:0]  udp_reject_code,
    output logic        mold_reject_observed,
    output logic [2:0]  mold_reject_code,
    output logic        framer_reject_observed,
    output logic [1:0]  framer_reject_code,
    output logic        itch_reject_observed,
    output logic [2:0]  itch_reject_code
);
    localparam logic [3:0] REC_NONE = 4'd0, REC_ETH = 4'd1,
        REC_IPV4 = 4'd2, REC_UDP = 4'd3, REC_MOLD = 4'd4,
        REC_FRAMER = 4'd5, REC_ITCH = 4'd6;

    logic parser_recovery_q;
    logic [3:0] recovery_stage_q;
    logic frame_open_q;
    logic stage_rst;

    logic [63:0] b_data;
    logic [7:0] b_keep;
    logic b_valid, b_ready, b_last;
    logic [7:0] g_data, eth_data, ip_data, udp_data, mold_data, msg_data;
    logic g_valid, g_ready, g_last;
    logic eth_valid, eth_ready, eth_last;
    logic ip_valid, ip_ready, ip_last;
    logic udp_valid, udp_ready, udp_last;
    logic mold_valid, mold_ready, mold_last;
    logic msg_valid, msg_ready, msg_last;

    logic eth_reject_valid;
    logic ip_reject_valid;
    logic udp_reject_valid;
    logic mold_reject_valid, mold_reject_fatal;
    logic framer_reject_valid, framer_reject_fatal;
    logic itch_reject_valid, itch_reject_fatal;

    logic mold_controller_valid, mold_recovery_required;
    logic [63:0] mold_expected_sequence;
    logic packet_valid, packet_ready, packet_body_empty;
    logic [63:0] packet_sequence;
    logic [15:0] packet_count;
    logic packet_result_valid, packet_result_ready, packet_result_success;
    logic message_valid, message_ready, message_empty;
    logic [63:0] message_sequence;
    logic [15:0] message_length;
    logic itch_decoder_valid, itch_recovery_required;
    logic fatal_detected;

    wire rx_fire = rx_valid && rx_ready;

    assign stage_rst = rst | rearm;
    assign recovery_required = parser_recovery_q;
    assign parser_valid = !parser_recovery_q && mold_controller_valid && itch_decoder_valid;
    assign recovery_stage = recovery_stage_q;
    assign current_expected_sequence = mold_expected_sequence;
    assign eth_reject_observed = eth_reject_valid;
    assign ipv4_reject_observed = ip_reject_valid;
    assign udp_reject_observed = udp_reject_valid;
    assign mold_reject_observed = mold_reject_valid;
    assign framer_reject_observed = framer_reject_valid;
    assign itch_reject_observed = itch_reject_valid;

    // The upstream-ready mask is the only parser-wide quarantine boundary.
    // If a fatal result arrives mid-frame, continue accepting that frame's
    // tail; once its accepted rx_last closes, no next frame can enter.
    assign rx_ready = b_ready &&
                      ((!parser_recovery_q && !fatal_detected) || frame_open_q);

    // Reject channels are consumed internally. Nonfatal classifications are
    // deliberately not promoted to parser recovery.
    assign fatal_detected =
        (eth_reject_valid && eth_reject_fatal) ||
        (ip_reject_valid && ipv4_reject_fatal) ||
        (udp_reject_valid && udp_reject_fatal) ||
        (mold_reject_valid && mold_reject_fatal) ||
        (framer_reject_valid && framer_reject_fatal) ||
        (itch_reject_valid && itch_reject_fatal) ||
        itch_recovery_required || mold_recovery_required;

    assign event_valid = itch_event_valid && !parser_recovery_q && !fatal_detected;

    always_ff @(posedge clk) begin
        if (stage_rst) begin
            parser_recovery_q <= 1'b0;
            recovery_stage_q <= REC_NONE;
            frame_open_q <= 1'b0;
        end else begin
            if (rx_fire)
                frame_open_q <= !rx_last;

            if (fatal_detected && !parser_recovery_q) begin
                parser_recovery_q <= 1'b1;
                if (eth_reject_valid && eth_reject_fatal) recovery_stage_q <= REC_ETH;
                else if (ip_reject_valid && ipv4_reject_fatal) recovery_stage_q <= REC_IPV4;
                else if (udp_reject_valid && udp_reject_fatal) recovery_stage_q <= REC_UDP;
                else if (mold_reject_valid && mold_reject_fatal) recovery_stage_q <= REC_MOLD;
                else if (framer_reject_valid && framer_reject_fatal) recovery_stage_q <= REC_FRAMER;
                else recovery_stage_q <= REC_ITCH;
            end
        end
    end

    wire_ingress_buffer ingress (
        .clk(clk), .rst(stage_rst), .in_data(rx_data), .in_keep(rx_keep),
        .in_valid(rx_valid && ((!parser_recovery_q && !fatal_detected) || frame_open_q)),
        .in_ready(b_ready), .in_last(rx_last), .out_data(b_data),
        .out_keep(b_keep), .out_valid(b_valid), .out_ready(b_ready_internal),
        .out_last(b_last));

    logic b_ready_internal;
    logic [2:0] itch_event_kind;
    logic itch_event_valid;

    wire_gearbox_64to8 gearbox (
        .clk(clk), .rst(stage_rst), .in_data(b_data), .in_valid(b_valid),
        .in_ready(b_ready_internal), .in_keep(b_keep), .in_last(b_last),
        .out_data(g_data), .out_valid(g_valid), .out_ready(g_ready), .out_last(g_last));

    wire_eth_parser eth (
        .clk(clk), .rst(stage_rst), .in_data(g_data), .in_valid(g_valid),
        .in_ready(g_ready), .in_last(g_last), .out_data(eth_data),
        .out_valid(eth_valid), .out_ready(eth_ready), .out_last(eth_last),
        .reject_valid(eth_reject_valid), .reject_ready(1'b1),
        .reject_fatal(eth_reject_fatal), .reject_code(eth_reject_code));

    wire_ipv4_parser ipv4 (
        .clk(clk), .rst(stage_rst), .cfg_destination_ipv4(cfg_destination_ipv4),
        .in_data(eth_data), .in_valid(eth_valid), .in_ready(eth_ready), .in_last(eth_last),
        .out_data(ip_data), .out_valid(ip_valid), .out_ready(ip_ready), .out_last(ip_last),
        .reject_valid(ip_reject_valid), .reject_ready(1'b1),
        .reject_fatal(ipv4_reject_fatal), .reject_code(ipv4_reject_code));

    wire_udp_parser udp (
        .clk(clk), .rst(stage_rst), .cfg_destination_udp_port(cfg_destination_udp_port),
        .in_data(ip_data), .in_valid(ip_valid), .in_ready(ip_ready), .in_last(ip_last),
        .out_data(udp_data), .out_valid(udp_valid), .out_ready(udp_ready), .out_last(udp_last),
        .reject_valid(udp_reject_valid), .reject_ready(1'b1),
        .reject_fatal(udp_reject_fatal), .reject_code(udp_reject_code));

    wire_mold_header_seq mold (
        .clk(clk), .rst(stage_rst), .cfg_active_session(cfg_active_session),
        .cfg_expected_sequence(cfg_expected_sequence), .rearm(rearm),
        .in_valid(udp_valid), .in_ready(udp_ready), .in_data(udp_data), .in_last(udp_last),
        .packet_valid(packet_valid), .packet_ready(packet_ready),
        .packet_sequence(packet_sequence), .packet_message_count(packet_count),
        .packet_body_empty(packet_body_empty), .out_valid(mold_valid), .out_ready(mold_ready),
        .out_data(mold_data), .out_last(mold_last),
        .packet_result_valid(packet_result_valid), .packet_result_ready(packet_result_ready),
        .packet_result_success(packet_result_success),
        .reject_valid(mold_reject_valid), .reject_ready(1'b1),
        .reject_fatal(mold_reject_fatal), .reject_code(mold_reject_code),
        .controller_valid(mold_controller_valid), .recovery_required(mold_recovery_required),
        .current_expected_sequence(mold_expected_sequence));

    wire_mold_message_framer framer (
        .clk(clk), .rst(stage_rst), .rearm(rearm),
        .packet_valid(packet_valid), .packet_ready(packet_ready),
        .packet_sequence(packet_sequence), .packet_message_count(packet_count),
        .packet_body_empty(packet_body_empty), .in_valid(mold_valid), .in_ready(mold_ready),
        .in_data(mold_data), .in_last(mold_last),
        .message_valid(message_valid), .message_ready(message_ready),
        .message_sequence(message_sequence), .message_length(message_length),
        .message_empty(message_empty), .out_valid(msg_valid), .out_ready(msg_ready),
        .out_data(msg_data), .out_last(msg_last),
        .packet_result_valid(packet_result_valid), .packet_result_ready(packet_result_ready),
        .packet_result_success(packet_result_success),
        .reject_valid(framer_reject_valid), .reject_ready(1'b1),
        .reject_fatal(framer_reject_fatal), .reject_code(framer_reject_code));

    wire_itch_decoder itch (
        .clk(clk), .rst(stage_rst), .rearm(rearm),
        .cfg_tracked_stock_locate(cfg_tracked_stock_locate),
        .cfg_symbol_check_enable(cfg_symbol_check_enable),
        .cfg_expected_stock_symbol(cfg_expected_stock_symbol),
        .message_valid(message_valid), .message_ready(message_ready),
        .message_sequence(message_sequence), .message_length(message_length),
        .message_empty(message_empty), .in_data(msg_data), .in_valid(msg_valid),
        .in_ready(msg_ready), .in_last(msg_last),
        .event_valid(itch_event_valid),
        .event_ready(event_ready && !parser_recovery_q && !fatal_detected),
        .event_kind(itch_event_kind), .source_type(source_type),
        .mold_sequence(mold_sequence), .itch_timestamp(itch_timestamp),
        .stock_locate(stock_locate), .old_order_reference(old_order_reference),
        .new_order_reference(new_order_reference), .quantity(quantity), .price(price),
        .side(side), .old_reference_valid(old_reference_valid),
        .new_reference_valid(new_reference_valid), .quantity_valid(quantity_valid),
        .price_valid(price_valid), .side_valid(side_valid),
        .reject_valid(itch_reject_valid), .reject_ready(1'b1),
        .reject_fatal(itch_reject_fatal), .reject_code(itch_reject_code),
        .decoder_valid(itch_decoder_valid), .recovery_required(itch_recovery_required));

    assign event_kind = itch_event_kind;
endmodule
