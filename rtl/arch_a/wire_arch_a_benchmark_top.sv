// Board-independent benchmark shell for the complete Architecture-A MVP.
// Fixed legal test configuration is documented in WIRE-026. The 32-bit
// readout emits each 162-bit decision tuple over six ready/valid words.
module wire_arch_a_benchmark_top (
    input  logic        clk,
    input  logic        rst,
    input  logic        rearm,

    input  logic [63:0] rx_data,
    input  logic [7:0]  rx_keep,
    input  logic        rx_valid,
    output logic        rx_ready,
    input  logic        rx_last,

    output logic [31:0] readout_data,
    output logic        readout_valid,
    input  logic        readout_ready,
    output logic        readout_last
);
    localparam logic [31:0] DEST_IPV4 = 32'hC6336407;
    localparam logic [15:0] DEST_UDP_PORT = 16'h1234;
    localparam logic [79:0] ACTIVE_SESSION = 80'h57324454455354303031;
    localparam logic [63:0] EXPECTED_SEQUENCE = 64'h1020304050607080;
    localparam logic [15:0] TRACKED_LOCATE = 16'h2345;
    localparam logic [63:0] EXPECTED_SYMBOL = 64'h414C504820202020;
    localparam logic [47:0] DECISION_THRESHOLD = 48'd10;
    localparam logic [31:0] INITIAL_BUDGET = 32'd20;

    logic decision_valid, decision_ready, decision_action;
    logic [63:0] decision_sequence;
    logic [47:0] decision_timestamp;
    logic signed [48:0] decision_imbalance;
    logic [63:0] readout_sequence_q;
    logic [47:0] readout_timestamp_q;
    logic signed [48:0] readout_imbalance_q;
    logic readout_action_q;
    logic [2:0] readout_word_q;
    logic readout_busy_q;

    assign decision_ready = !readout_busy_q;
    assign readout_valid = readout_busy_q;
    assign readout_last = readout_busy_q && (readout_word_q == 3'd5);

    always_comb begin
        readout_data = 32'd0;
        case (readout_word_q)
            3'd0: readout_data = readout_sequence_q[63:32];
            3'd1: readout_data = readout_sequence_q[31:0];
            3'd2: readout_data = {15'd0, readout_action_q, readout_timestamp_q[47:32]};
            3'd3: readout_data = readout_timestamp_q[31:0];
            3'd4: readout_data = readout_imbalance_q[48:17];
            3'd5: readout_data = {15'd0, readout_imbalance_q[16:0]};
            default: readout_data = 32'd0;
        endcase
    end

    /* verilator lint_off PINCONNECTEMPTY */
    wire_arch_a_functional_top #(.BOOK_NUM_SETS(512)) core (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_destination_ipv4(DEST_IPV4),
        .cfg_destination_udp_port(DEST_UDP_PORT),
        .cfg_active_session(ACTIVE_SESSION),
        .cfg_expected_sequence(EXPECTED_SEQUENCE),
        .cfg_tracked_stock_locate(TRACKED_LOCATE),
        .cfg_symbol_check_enable(1'b1),
        .cfg_expected_stock_symbol(EXPECTED_SYMBOL),
        .cfg_decision_threshold(DECISION_THRESHOLD),
        .cfg_initial_budget(INITIAL_BUDGET), .decision_enable(1'b1),
        .rx_data(rx_data), .rx_keep(rx_keep), .rx_valid(rx_valid),
        .rx_ready(rx_ready), .rx_last(rx_last),
        .decision_valid(decision_valid), .decision_ready(decision_ready),
        .decision_action(decision_action),
        .decision_mold_sequence(decision_sequence),
        .decision_itch_timestamp(decision_timestamp),
        .decision_signed_imbalance(decision_imbalance),
        .parser_valid(), .parser_recovery_required(), .parser_recovery_stage(),
        .current_expected_sequence(), .book_valid(), .book_recovery_required(),
        .bid_total(), .ask_total(), .previous_imbalance(),
        .remaining_budget(), .decision_count(),
        .error_valid(), .error_ready(1'b1), .error_code(),
        .stage_reject_observed(), .stage_reject_fatal(), .stage_reject_code(),
        .debug_reference(64'd0), .debug_found(), .debug_price(),
        .debug_remaining_quantity(), .debug_side(),
        .last_accepted_event_stock_locate(),
        .debug_set_index(), .debug_way(),
        .event_valid_observed(), .event_ready_observed(), .event_kind_observed(),
        .event_mold_sequence_observed(), .commit_valid_observed(),
        .commit_ready_observed(), .commit_mold_sequence_observed(),
        .commit_bid_total_observed(), .commit_ask_total_observed()
    );
    /* verilator lint_on PINCONNECTEMPTY */

    always_ff @(posedge clk) begin
        if (rst || rearm) begin
            readout_sequence_q <= 64'd0;
            readout_timestamp_q <= 48'd0;
            readout_imbalance_q <= 49'sd0;
            readout_action_q <= 1'b0;
            readout_word_q <= 3'd0;
            readout_busy_q <= 1'b0;
        end else begin
            if (decision_valid && decision_ready) begin
                readout_sequence_q <= decision_sequence;
                readout_timestamp_q <= decision_timestamp;
                readout_imbalance_q <= decision_imbalance;
                readout_action_q <= decision_action;
                readout_word_q <= 3'd0;
                readout_busy_q <= 1'b1;
            end else if (readout_busy_q && readout_ready) begin
                if (readout_word_q == 3'd5) begin
                    readout_busy_q <= 1'b0;
                    readout_word_q <= 3'd0;
                end else begin
                    readout_word_q <= readout_word_q + 3'd1;
                end
            end
        end
    end
endmodule
