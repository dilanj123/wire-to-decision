// Structural MoldUDP64 message-block parser. Message payloads remain opaque.
module wire_mold_message_framer (
    input  logic        clk,
    input  logic        rst,
    input  logic        rearm,

    input  logic        packet_valid,
    output logic        packet_ready,
    input  logic [63:0] packet_sequence,
    input  logic [15:0] packet_message_count,
    input  logic        packet_body_empty,

    input  logic        in_valid,
    output logic        in_ready,
    input  logic [7:0]  in_data,
    input  logic        in_last,

    output logic        message_valid,
    input  logic        message_ready,
    output logic [63:0] message_sequence,
    output logic [15:0] message_length,
    output logic        message_empty,

    output logic        out_valid,
    input  logic        out_ready,
    output logic [7:0]  out_data,
    output logic        out_last,

    output logic        packet_result_valid,
    input  logic        packet_result_ready,
    output logic        packet_result_success,

    output logic        reject_valid,
    input  logic        reject_ready,
    output logic        reject_fatal,
    output logic [1:0]  reject_code
);
    localparam logic [1:0] MESSAGE_LENGTH_TRUNCATED = 2'd0;
    localparam logic [1:0] MESSAGE_TRUNCATED        = 2'd1;
    localparam logic [1:0] TRAILING_BYTES           = 2'd2;

    typedef enum logic [3:0] {
        S_IDLE,
        S_LENGTH_HI,
        S_LENGTH_LO,
        S_MESSAGE_META,
        S_PAYLOAD,
        S_PAYLOAD_END,
        S_DROP_TRAILING,
        S_SUCCESS,
        S_FAILURE,
        S_RECOVERY
    } state_t;

    typedef enum logic [2:0] {
        A_NEXT_LENGTH,
        A_PACKET_SUCCESS,
        A_PACKET_LENGTH_ERROR,
        A_DROP_TRAILING,
        A_PACKET_MESSAGE_ERROR
    } action_t;

    state_t state_q;
    action_t payload_action_q;
    logic [63:0] packet_sequence_q;
    logic [15:0] packet_count_q;
    logic [15:0] messages_done_q;
    logic [7:0] length_hi_q;
    logic [15:0] message_length_q;
    logic [15:0] payload_remaining_q;
    logic message_empty_q;
    logic header_ended_q;
    logic [7:0] payload_data_q;
    logic payload_valid_q;
    logic payload_last_q;
    logic [1:0] reject_code_q;
    logic reject_pending_q;
    logic result_pending_q;

    wire packet_fire = packet_valid && packet_ready;
    wire input_fire = in_valid && in_ready;
    wire message_fire = message_valid && message_ready;
    wire output_fire = out_valid && out_ready;
    wire result_fire = packet_result_valid && packet_result_ready;
    wire reject_fire = reject_valid && reject_ready;
    wire [15:0] completed_next = messages_done_q + 16'd1;

    assign packet_ready = (state_q == S_IDLE);

    assign in_ready = (state_q == S_LENGTH_HI) ||
                      (state_q == S_LENGTH_LO) ||
                      (state_q == S_DROP_TRAILING) ||
                      ((state_q == S_PAYLOAD) &&
                       (!payload_valid_q || out_ready));

    assign message_valid = (state_q == S_MESSAGE_META);
    assign message_sequence = packet_sequence_q + {48'd0, messages_done_q};
    assign message_length = message_length_q;
    assign message_empty = message_empty_q;

    assign out_valid = payload_valid_q;
    assign out_data = payload_data_q;
    assign out_last = payload_valid_q && payload_last_q;

    assign packet_result_valid = ((state_q == S_SUCCESS) && result_pending_q) ||
                                 ((state_q == S_FAILURE) && result_pending_q);
    assign packet_result_success = (state_q == S_SUCCESS);
    assign reject_valid = (state_q == S_FAILURE) && reject_pending_q;
    assign reject_fatal = 1'b1;
    assign reject_code = reject_code_q;

    always_ff @(posedge clk) begin
        if (rst || rearm) begin
            state_q <= S_IDLE;
            payload_action_q <= A_NEXT_LENGTH;
            packet_sequence_q <= '0;
            packet_count_q <= '0;
            messages_done_q <= '0;
            length_hi_q <= '0;
            message_length_q <= '0;
            payload_remaining_q <= '0;
            message_empty_q <= 1'b0;
            header_ended_q <= 1'b0;
            payload_data_q <= '0;
            payload_valid_q <= 1'b0;
            payload_last_q <= 1'b0;
            reject_code_q <= MESSAGE_LENGTH_TRUNCATED;
            reject_pending_q <= 1'b0;
            result_pending_q <= 1'b0;
        end else begin
            if (output_fire) begin
                payload_valid_q <= 1'b0;
                payload_last_q <= 1'b0;
                if (state_q == S_PAYLOAD_END) begin
                    case (payload_action_q)
                        A_NEXT_LENGTH: state_q <= S_LENGTH_HI;
                        A_PACKET_SUCCESS: begin
                            state_q <= S_SUCCESS;
                            result_pending_q <= 1'b1;
                        end
                        A_PACKET_LENGTH_ERROR: begin
                            state_q <= S_FAILURE;
                            reject_code_q <= MESSAGE_LENGTH_TRUNCATED;
                            reject_pending_q <= 1'b1;
                            result_pending_q <= 1'b1;
                        end
                        A_PACKET_MESSAGE_ERROR: begin
                            state_q <= S_FAILURE;
                            reject_code_q <= MESSAGE_TRUNCATED;
                            reject_pending_q <= 1'b1;
                            result_pending_q <= 1'b1;
                        end
                        default: state_q <= S_DROP_TRAILING;
                    endcase
                end
            end

            if (message_fire) begin
                if (message_empty_q) begin
                    messages_done_q <= completed_next;
                    if (header_ended_q) begin
                        if (completed_next == packet_count_q) begin
                            state_q <= S_SUCCESS;
                            result_pending_q <= 1'b1;
                        end else begin
                            state_q <= S_FAILURE;
                            reject_code_q <= MESSAGE_LENGTH_TRUNCATED;
                            reject_pending_q <= 1'b1;
                            result_pending_q <= 1'b1;
                        end
                    end else if (completed_next == packet_count_q) begin
                        state_q <= S_DROP_TRAILING;
                    end else begin
                        state_q <= S_LENGTH_HI;
                    end
                end else if (header_ended_q) begin
                    state_q <= S_FAILURE;
                    reject_code_q <= MESSAGE_TRUNCATED;
                    reject_pending_q <= 1'b1;
                    result_pending_q <= 1'b1;
                end else begin
                    state_q <= S_PAYLOAD;
                end
            end

            if (packet_fire) begin
                packet_sequence_q <= packet_sequence;
                packet_count_q <= packet_message_count;
                messages_done_q <= 16'd0;
                if (packet_body_empty) begin
                    state_q <= S_FAILURE;
                    reject_code_q <= MESSAGE_LENGTH_TRUNCATED;
                    reject_pending_q <= 1'b1;
                    result_pending_q <= 1'b1;
                end else begin
                    state_q <= S_LENGTH_HI;
                end
            end

            if (input_fire) begin
                case (state_q)
                    S_LENGTH_HI: begin
                        if (in_last) begin
                            state_q <= S_FAILURE;
                            reject_code_q <= MESSAGE_LENGTH_TRUNCATED;
                            reject_pending_q <= 1'b1;
                            result_pending_q <= 1'b1;
                        end else begin
                            length_hi_q <= in_data;
                            state_q <= S_LENGTH_LO;
                        end
                    end
                    S_LENGTH_LO: begin
                        message_length_q <= {length_hi_q, in_data};
                        payload_remaining_q <= {length_hi_q, in_data};
                        message_empty_q <= ({length_hi_q, in_data} == 16'd0);
                        header_ended_q <= in_last;
                        state_q <= S_MESSAGE_META;
                    end
                    S_PAYLOAD: begin
                        payload_data_q <= in_data;
                        payload_valid_q <= 1'b1;
                        if (payload_remaining_q == 16'd1) begin
                            payload_last_q <= 1'b1;
                            messages_done_q <= completed_next;
                            if (in_last) begin
                                if (completed_next == packet_count_q)
                                    payload_action_q <= A_PACKET_SUCCESS;
                                else
                                    payload_action_q <= A_PACKET_LENGTH_ERROR;
                            end else if (completed_next == packet_count_q) begin
                                payload_action_q <= A_DROP_TRAILING;
                            end else begin
                                payload_action_q <= A_NEXT_LENGTH;
                            end
                            state_q <= S_PAYLOAD_END;
                        end else begin
                            payload_last_q <= 1'b0;
                            payload_remaining_q <= payload_remaining_q - 16'd1;
                            if (in_last) begin
                                payload_action_q <= A_PACKET_MESSAGE_ERROR;
                                state_q <= S_PAYLOAD_END;
                            end
                        end
                    end
                    S_DROP_TRAILING: begin
                        if (in_last) begin
                            state_q <= S_FAILURE;
                            reject_code_q <= TRAILING_BYTES;
                            reject_pending_q <= 1'b1;
                            result_pending_q <= 1'b1;
                        end
                    end
                    default: begin
                        // Metadata, terminal, and recovery states block input.
                    end
                endcase
            end

            if (state_q == S_SUCCESS && result_fire) begin
                result_pending_q <= 1'b0;
                state_q <= S_IDLE;
            end

            if (state_q == S_FAILURE) begin
                if (result_fire) result_pending_q <= 1'b0;
                if (reject_fire) reject_pending_q <= 1'b0;
                if ((!result_pending_q || result_fire) &&
                    (!reject_pending_q || reject_fire))
                    state_q <= S_RECOVERY;
            end
        end
    end
endmodule
