// Wire-to-Decision Architecture A MoldUDP64 header/sequence controller.
// The raw message-block body is intentionally opaque; WIRE-020 owns its parsing.
module wire_mold_header_seq (
    input  logic        clk,
    input  logic        rst,
    input  logic [79:0] cfg_active_session,
    input  logic [63:0] cfg_expected_sequence,
    input  logic        rearm,

    input  logic        in_valid,
    output logic        in_ready,
    input  logic [7:0]  in_data,
    input  logic        in_last,

    output logic        packet_valid,
    input  logic        packet_ready,
    output logic [63:0] packet_sequence,
    output logic [15:0] packet_message_count,
    output logic        packet_body_empty,

    output logic        out_valid,
    input  logic        out_ready,
    output logic [7:0]  out_data,
    output logic        out_last,

    input  logic        packet_result_valid,
    output logic        packet_result_ready,
    input  logic        packet_result_success,

    output logic        reject_valid,
    input  logic        reject_ready,
    output logic        reject_fatal,
    output logic [2:0]  reject_code,

    output logic        controller_valid,
    output logic        recovery_required,
    output logic [63:0] current_expected_sequence
);
    localparam logic [2:0] MOLD_HEADER_TRUNCATED = 3'd0;
    localparam logic [2:0] MOLD_SESSION_MISMATCH = 3'd1;
    localparam logic [2:0] MOLD_SEQUENCE_ERROR   = 3'd2;
    localparam logic [2:0] MOLD_TRAILING_BYTES   = 3'd3;
    localparam logic [2:0] MOLD_END_OF_SESSION   = 3'd4;

    typedef enum logic [2:0] {
        S_HEADER,
        S_META,
        S_BODY,
        S_WAIT_RESULT,
        S_DROP,
        S_REJECT,
        S_RECOVERY
    } state_t;

    state_t state_q;
    logic [4:0]  header_index_q;
    logic [151:0] header_q;
    logic [79:0] active_session_q;
    logic [63:0] expected_sequence_q;
    logic [63:0] packet_sequence_q;
    logic [15:0] packet_count_q;
    logic        packet_empty_q;
    logic        packet_valid_q;
    logic [7:0]  body_data_q;
    logic        body_valid_q;
    logic        body_last_q;
    logic [2:0]  reject_code_q;
    logic        reject_fatal_q;
    logic [2:0]  pending_code_q;
    logic        pending_fatal_q;

    wire input_fire = in_valid && in_ready;
    wire packet_fire = packet_valid && packet_ready;
    wire body_fire = out_valid && out_ready;
    wire result_fire = packet_result_valid && packet_result_ready;
    wire reject_fire = reject_valid && reject_ready;

    wire [159:0] candidate_header = {header_q, in_data};
    wire [79:0] candidate_session = candidate_header[159:80];
    wire [63:0] candidate_sequence = candidate_header[79:16];
    wire [15:0] candidate_count = candidate_header[15:0];

    assign packet_valid = packet_valid_q;
    assign packet_sequence = packet_sequence_q;
    assign packet_message_count = packet_count_q;
    assign packet_body_empty = packet_empty_q;

    assign out_valid = body_valid_q;
    assign out_data = body_data_q;
    assign out_last = body_valid_q && body_last_q;

    assign reject_valid = (state_q == S_REJECT);
    assign reject_fatal = reject_fatal_q;
    assign reject_code = reject_code_q;

    assign controller_valid = (state_q != S_RECOVERY) &&
                              (state_q != S_REJECT) && controller_valid_q;
    assign recovery_required = recovery_required_q;
    assign current_expected_sequence = expected_sequence_q;
    assign packet_result_ready = (state_q == S_WAIT_RESULT) && controller_valid_q;

    // Header/drop states consume one byte per transfer.  A held metadata,
    // body, result, or rejection transaction deliberately blocks input.
    assign in_ready = (state_q == S_HEADER) || (state_q == S_DROP) ||
                      ((state_q == S_BODY) &&
                       !body_last_q && (!body_valid_q || out_ready));

    logic controller_valid_q;
    logic recovery_required_q;

    always_ff @(posedge clk) begin
        if (rst || rearm) begin
            state_q <= S_HEADER;
            header_index_q <= 5'd0;
            header_q <= '0;
            active_session_q <= cfg_active_session;
            expected_sequence_q <= cfg_expected_sequence;
            packet_sequence_q <= '0;
            packet_count_q <= '0;
            packet_empty_q <= 1'b0;
            packet_valid_q <= 1'b0;
            body_data_q <= '0;
            body_valid_q <= 1'b0;
            body_last_q <= 1'b0;
            reject_code_q <= MOLD_HEADER_TRUNCATED;
            reject_fatal_q <= 1'b1;
            pending_code_q <= MOLD_TRAILING_BYTES;
            pending_fatal_q <= 1'b1;
            controller_valid_q <= 1'b1;
            recovery_required_q <= 1'b0;
        end else begin
            if (packet_fire) begin
                packet_valid_q <= 1'b0;
                if (packet_empty_q) begin
                    state_q <= S_WAIT_RESULT;
                end else begin
                    state_q <= S_BODY;
                end
            end

            if (body_fire) begin
                body_valid_q <= 1'b0;
                if (body_last_q) begin
                    body_last_q <= 1'b0;
                    state_q <= S_WAIT_RESULT;
                end
            end

            if (result_fire) begin
                if (packet_result_success) begin
                    expected_sequence_q <= expected_sequence_q + {48'd0, packet_count_q};
                    state_q <= S_HEADER;
                    header_index_q <= 5'd0;
                    controller_valid_q <= 1'b1;
                    recovery_required_q <= 1'b0;
                end else begin
                    state_q <= S_RECOVERY;
                    controller_valid_q <= 1'b0;
                    recovery_required_q <= 1'b1;
                end
            end

            if (reject_fire) begin
                state_q <= S_RECOVERY;
                controller_valid_q <= 1'b0;
                recovery_required_q <= 1'b1;
            end

            if (input_fire) begin
                case (state_q)
                    S_HEADER: begin
                        if (header_index_q < 5'd19) begin
                            if (in_last) begin
                                reject_code_q <= MOLD_HEADER_TRUNCATED;
                                reject_fatal_q <= 1'b1;
                                state_q <= S_REJECT;
                                controller_valid_q <= 1'b0;
                                recovery_required_q <= 1'b1;
                            end else begin
                                header_q[151 - header_index_q*8 -: 8] <= in_data;
                                header_index_q <= header_index_q + 5'd1;
                            end
                        end else begin
                            header_q <= candidate_header[159:8];
                            header_index_q <= 5'd0;
                            if (candidate_session != active_session_q) begin
                                pending_code_q <= MOLD_SESSION_MISMATCH;
                                pending_fatal_q <= 1'b1;
                                if (in_last) begin
                                    reject_code_q <= MOLD_SESSION_MISMATCH;
                                    reject_fatal_q <= 1'b1;
                                    state_q <= S_REJECT;
                                    controller_valid_q <= 1'b0;
                                    recovery_required_q <= 1'b1;
                                end else begin
                                    state_q <= S_DROP;
                                end
                            end else if (candidate_sequence != expected_sequence_q) begin
                                pending_code_q <= MOLD_SEQUENCE_ERROR;
                                pending_fatal_q <= 1'b1;
                                if (in_last) begin
                                    reject_code_q <= MOLD_SEQUENCE_ERROR;
                                    reject_fatal_q <= 1'b1;
                                    state_q <= S_REJECT;
                                    controller_valid_q <= 1'b0;
                                    recovery_required_q <= 1'b1;
                                end else begin
                                    state_q <= S_DROP;
                                end
                            end else if (candidate_count == 16'h0000) begin
                                if (in_last) begin
                                    state_q <= S_HEADER;
                                end else begin
                                    pending_code_q <= MOLD_TRAILING_BYTES;
                                    pending_fatal_q <= 1'b1;
                                    state_q <= S_DROP;
                                end
                            end else if (candidate_count == 16'hffff) begin
                                if (in_last) begin
                                    reject_code_q <= MOLD_END_OF_SESSION;
                                    reject_fatal_q <= 1'b1;
                                    state_q <= S_REJECT;
                                    controller_valid_q <= 1'b0;
                                    recovery_required_q <= 1'b1;
                                end else begin
                                    pending_code_q <= MOLD_TRAILING_BYTES;
                                    pending_fatal_q <= 1'b1;
                                    state_q <= S_DROP;
                                end
                            end else begin
                                packet_sequence_q <= candidate_sequence;
                                packet_count_q <= candidate_count;
                                packet_empty_q <= in_last;
                                packet_valid_q <= 1'b1;
                                state_q <= S_META;
                            end
                        end
                    end

                    S_DROP: begin
                        if (in_last) begin
                            reject_code_q <= pending_code_q;
                            reject_fatal_q <= pending_fatal_q;
                            state_q <= S_REJECT;
                            controller_valid_q <= 1'b0;
                            recovery_required_q <= 1'b1;
                        end
                    end

                    S_BODY: begin
                        body_data_q <= in_data;
                        body_valid_q <= 1'b1;
                        body_last_q <= in_last;
                    end

                    default: begin
                        // Other states intentionally deassert in_ready.
                    end
                endcase
            end
        end
    end
endmodule
