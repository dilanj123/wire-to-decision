// Wire-to-Decision Architecture A fixed-profile UDP parser.
// Consumes an IPv4 payload stream and forwards only a valid UDP payload.
module wire_udp_parser (
    input  logic        clk,
    input  logic        rst,

    input  logic [15:0] cfg_destination_udp_port,

    input  logic [7:0]  in_data,
    input  logic        in_valid,
    output logic        in_ready,
    input  logic        in_last,

    output logic [7:0]  out_data,
    output logic        out_valid,
    input  logic        out_ready,
    output logic        out_last,

    output logic        reject_valid,
    input  logic        reject_ready,
    output logic        reject_fatal,
    output logic [2:0]  reject_code
);
    localparam logic [2:0] UDP_HEADER_TRUNCATED = 3'd0;
    localparam logic [2:0] UDP_LENGTH            = 3'd1;
    localparam logic [2:0] UDP_WRONG_PORT        = 3'd2;
    localparam logic [2:0] UDP_CHECKSUM_UNSUPPORTED = 3'd3;
    localparam logic [2:0] UDP_EMPTY_PAYLOAD     = 3'd4;

    typedef enum logic [1:0] {HEADER, PAYLOAD, DROP, REJECT} state_t;
    state_t state_q;
    logic [3:0]  header_index_q;
    logic [55:0] header_q;
    logic [15:0] declared_length_q;
    logic [15:0] actual_count_q;
    logic [15:0] remaining_q;
    logic [2:0]  pending_code_q;
    logic        pending_fatal_q;
    logic [7:0]  payload_data_q;
    logic        payload_valid_q;
    logic        payload_last_q;
    logic        reject_fatal_q;
    logic [2:0]  reject_code_q;

    wire output_fire = out_valid && out_ready;
    wire input_fire  = in_valid && in_ready;
    wire [63:0] candidate_header = {header_q, in_data};
    wire [15:0] candidate_port = candidate_header[47:32];
    wire [15:0] candidate_length = candidate_header[31:16];
    wire [15:0] candidate_checksum = candidate_header[15:0];
    wire candidate_wrong_port = (candidate_port != cfg_destination_udp_port);
    wire candidate_bad_checksum = (candidate_checksum != 16'h0000);

    assign out_valid = payload_valid_q;
    assign out_data  = payload_data_q;
    assign out_last  = payload_valid_q && payload_last_q;

    assign reject_valid = (state_q == REJECT);
    assign reject_fatal = reject_fatal_q;
    assign reject_code  = reject_code_q;

    assign in_ready = (state_q == HEADER) || (state_q == DROP) ||
                      ((state_q == PAYLOAD) &&
                       !payload_last_q && (!payload_valid_q || out_ready));

    always_ff @(posedge clk) begin
        if (rst) begin
            state_q           <= HEADER;
            header_index_q    <= 4'd0;
            header_q          <= '0;
            declared_length_q <= 16'd0;
            actual_count_q    <= 16'd0;
            remaining_q       <= 16'd0;
            pending_code_q    <= UDP_LENGTH;
            pending_fatal_q   <= 1'b1;
            payload_data_q    <= 8'h00;
            payload_valid_q   <= 1'b0;
            payload_last_q    <= 1'b0;
            reject_fatal_q    <= 1'b0;
            reject_code_q     <= UDP_LENGTH;
        end else begin
            if (state_q == PAYLOAD && output_fire) begin
                payload_valid_q <= 1'b0;
                if (payload_last_q) begin
                    payload_last_q <= 1'b0;
                    state_q <= HEADER;
                    header_index_q <= 4'd0;
                end
            end

            if (state_q == REJECT && reject_ready) begin
                state_q <= HEADER;
                header_index_q <= 4'd0;
            end

            if (input_fire) begin
                case (state_q)
                    HEADER: begin
                        if (in_last && header_index_q < 4'd7) begin
                            reject_fatal_q <= 1'b1;
                            reject_code_q <= UDP_HEADER_TRUNCATED;
                            state_q <= REJECT;
                        end else if (header_index_q < 4'd7) begin
                            header_q[55 - header_index_q*8 -: 8] <= in_data;
                            header_index_q <= header_index_q + 4'd1;
                        end else begin
                            header_q <= candidate_header[63:8];
                            declared_length_q <= candidate_length;
                            actual_count_q <= 16'd8;

                            if (candidate_length < 16'd8) begin
                                pending_code_q <= UDP_LENGTH;
                                pending_fatal_q <= 1'b1;
                                if (in_last) begin
                                    reject_code_q <= UDP_LENGTH;
                                    reject_fatal_q <= 1'b1;
                                    state_q <= REJECT;
                                end else begin
                                    state_q <= DROP;
                                end
                            end else if (candidate_length == 16'd8) begin
                                if (in_last) begin
                                    if (candidate_wrong_port) begin
                                        reject_code_q <= UDP_WRONG_PORT;
                                        reject_fatal_q <= 1'b0;
                                    end else if (candidate_bad_checksum) begin
                                        reject_code_q <= UDP_CHECKSUM_UNSUPPORTED;
                                        reject_fatal_q <= 1'b0;
                                    end else begin
                                        reject_code_q <= UDP_EMPTY_PAYLOAD;
                                        reject_fatal_q <= 1'b1;
                                    end
                                    state_q <= REJECT;
                                end else begin
                                    pending_code_q <= UDP_LENGTH;
                                    pending_fatal_q <= 1'b1;
                                    state_q <= DROP;
                                end
                            end else if (candidate_wrong_port || candidate_bad_checksum) begin
                                if (candidate_wrong_port) begin
                                    pending_code_q <= UDP_WRONG_PORT;
                                    pending_fatal_q <= 1'b0;
                                end else begin
                                    pending_code_q <= UDP_CHECKSUM_UNSUPPORTED;
                                    pending_fatal_q <= 1'b0;
                                end
                                if (in_last) begin
                                    reject_code_q <= UDP_LENGTH;
                                    reject_fatal_q <= 1'b1;
                                    state_q <= REJECT;
                                end else begin
                                    state_q <= DROP;
                                end
                            end else if (in_last) begin
                                reject_code_q <= UDP_LENGTH;
                                reject_fatal_q <= 1'b1;
                                state_q <= REJECT;
                            end else begin
                                remaining_q <= candidate_length - 16'd8;
                                state_q <= PAYLOAD;
                            end
                        end
                    end

                    PAYLOAD: begin
                        if (in_last && remaining_q > 16'd1) begin
                            reject_code_q <= UDP_LENGTH;
                            reject_fatal_q <= 1'b1;
                            state_q <= REJECT;
                        end else if (remaining_q == 16'd1) begin
                            if (in_last) begin
                                payload_data_q <= in_data;
                                payload_last_q <= 1'b1;
                                payload_valid_q <= 1'b1;
                            end else begin
                                pending_code_q <= UDP_LENGTH;
                                pending_fatal_q <= 1'b1;
                                actual_count_q <= declared_length_q;
                                state_q <= DROP;
                            end
                            remaining_q <= 16'd0;
                        end else begin
                            payload_data_q <= in_data;
                            payload_last_q <= 1'b0;
                            payload_valid_q <= 1'b1;
                            remaining_q <= remaining_q - 16'd1;
                        end
                    end

                    DROP: begin
                        actual_count_q <= actual_count_q + 16'd1;
                        if (in_last) begin
                            if ((actual_count_q + 16'd1) != declared_length_q) begin
                                reject_code_q <= UDP_LENGTH;
                                reject_fatal_q <= 1'b1;
                            end else begin
                                reject_code_q <= pending_code_q;
                                reject_fatal_q <= pending_fatal_q;
                            end
                            state_q <= REJECT;
                        end
                    end

                    default: begin
                        // REJECT has in_ready low, so no input_fire occurs.
                    end
                endcase
            end
        end
    end
endmodule
