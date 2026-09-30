// Wire-to-Decision Architecture A fixed-profile IPv4 parser.
// Consumes an IPv4 payload stream and forwards only the declared UDP payload.
module wire_ipv4_parser (
    input  logic        clk,
    input  logic        rst,

    input  logic [31:0] cfg_destination_ipv4,

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
    output logic [3:0]  reject_code
);
    localparam logic [3:0] IPV4_INVALID_VERSION  = 4'd0;
    localparam logic [3:0] IPV4_UNSUPPORTED_IHL  = 4'd1;
    localparam logic [3:0] IPV4_INVALID_LENGTH   = 4'd2;
    localparam logic [3:0] IPV4_CHECKSUM         = 4'd3;
    localparam logic [3:0] IPV4_FRAGMENTED       = 4'd4;
    localparam logic [3:0] IPV4_WRONG_DEST      = 4'd5;
    localparam logic [3:0] IPV4_NON_UDP         = 4'd6;
    localparam logic [3:0] IPV4_HEADER_TRUNCATED = 4'd7;
    localparam logic [3:0] IPV4_EMPTY_PAYLOAD   = 4'd8;
    localparam logic [3:0] IPV4_ACCEPT          = 4'hf;

    typedef enum logic [2:0] {HEADER, PAYLOAD, PADDING, DROP, REJECT} state_t;
    state_t state_q;
    logic [4:0]  header_index_q;
    logic [151:0] header_q;
    logic [15:0] remaining_q;
    logic [7:0] payload_data_q;
    logic       payload_valid_q;
    logic       payload_last_q;
    logic       payload_physical_last_q;
    logic       reject_fatal_q;
    logic [3:0] reject_code_q;

    function automatic logic checksum_valid(input logic [159:0] h);
        logic [17:0] sum;
        begin
            sum = {2'd0,h[159:144]} + {2'd0,h[143:128]} +
                  {2'd0,h[127:112]} + {2'd0,h[111:96]} +
                  {2'd0,h[95:80]} + {2'd0,h[79:64]} +
                  {2'd0,h[63:48]} + {2'd0,h[47:32]} +
                  {2'd0,h[31:16]} + {2'd0,h[15:0]};
            sum = {2'd0, sum[15:0]} + {16'd0, sum[17:16]};
            sum = {2'd0, sum[15:0]} + {16'd0, sum[17:16]};
            checksum_valid = (sum[15:0] == 16'hffff);
        end
    endfunction

    function automatic logic [3:0] classify_header(
        input logic [159:0] h,
        input logic [31:0] destination
    );
        logic [15:0] total_length;
        logic [13:0] flags_fragment;
        begin
            total_length = h[143:128];
            flags_fragment = h[109:96];
            if (h[159:156] != 4'd4)
                classify_header = IPV4_INVALID_VERSION;
            else if (h[155:152] != 4'd5)
                classify_header = IPV4_UNSUPPORTED_IHL;
            else if (total_length < 16'd20)
                classify_header = IPV4_INVALID_LENGTH;
            else if (!checksum_valid(h))
                classify_header = IPV4_CHECKSUM;
            else if (flags_fragment[13] || (flags_fragment[12:0] != 13'd0))
                classify_header = IPV4_FRAGMENTED;
            else if (h[31:0] != destination)
                classify_header = IPV4_WRONG_DEST;
            else if (h[87:80] != 8'd17)
                classify_header = IPV4_NON_UDP;
            else
                classify_header = IPV4_ACCEPT;
        end
    endfunction

    function automatic logic code_is_fatal(input logic [3:0] code);
        begin
            code_is_fatal = (code == IPV4_INVALID_LENGTH) ||
                            (code == IPV4_CHECKSUM) ||
                            (code == IPV4_FRAGMENTED) ||
                            (code == IPV4_HEADER_TRUNCATED) ||
                            (code == IPV4_EMPTY_PAYLOAD);
        end
    endfunction

    wire output_fire = out_valid && out_ready;
    wire input_fire  = in_valid && in_ready;
    wire [159:0] candidate_header = {header_q, in_data};
    wire [3:0] candidate_code = classify_header(candidate_header, cfg_destination_ipv4);

    assign out_valid = payload_valid_q;
    assign out_data  = payload_data_q;
    assign out_last  = payload_valid_q && payload_last_q;

    assign reject_valid = (state_q == REJECT);
    assign reject_fatal = reject_fatal_q;
    assign reject_code  = reject_code_q;

    assign in_ready = (state_q == HEADER) ||
                      (state_q == DROP) ||
                      (state_q == PADDING) ||
                      ((state_q == PAYLOAD) &&
                       !payload_last_q &&
                       (!payload_valid_q || out_ready));

    always_ff @(posedge clk) begin
        if (rst) begin
            state_q                    <= HEADER;
            header_index_q             <= 5'd0;
            header_q                   <= '0;
            remaining_q                <= 16'd0;
            payload_data_q             <= 8'h00;
            payload_valid_q            <= 1'b0;
            payload_last_q             <= 1'b0;
            payload_physical_last_q    <= 1'b0;
            reject_fatal_q             <= 1'b0;
            reject_code_q              <= IPV4_INVALID_VERSION;
        end else begin
            if (state_q == PAYLOAD && output_fire) begin
                payload_valid_q <= 1'b0;
                if (payload_last_q) begin
                    payload_last_q <= 1'b0;
                    payload_physical_last_q <= 1'b0;
                    state_q <= payload_physical_last_q ? HEADER : PADDING;
                    header_index_q <= 5'd0;
                end
            end

            if (state_q == REJECT && reject_ready) begin
                state_q <= HEADER;
                header_index_q <= 5'd0;
            end

            if (input_fire) begin
                case (state_q)
                    HEADER: begin
                        if (in_last && header_index_q < 5'd19) begin
                            reject_fatal_q <= 1'b1;
                            reject_code_q <= IPV4_HEADER_TRUNCATED;
                            state_q <= REJECT;
                        end else if (header_index_q < 5'd19) begin
                            header_q[151 - header_index_q*8 -: 8] <= in_data;
                            header_index_q <= header_index_q + 5'd1;
                        end else begin
                            header_q <= candidate_header[159:8];
                            if (candidate_code == IPV4_ACCEPT) begin
                                if (candidate_header[143:128] == 16'd20) begin
                                    reject_fatal_q <= 1'b1;
                                    reject_code_q <= IPV4_EMPTY_PAYLOAD;
                                    state_q <= REJECT;
                                end else if (in_last) begin
                                    reject_fatal_q <= 1'b1;
                                    reject_code_q <= IPV4_INVALID_LENGTH;
                                    state_q <= REJECT;
                                end else begin
                                    remaining_q <= candidate_header[143:128] - 16'd20;
                                    state_q <= PAYLOAD;
                                end
                            end else begin
                                reject_fatal_q <= code_is_fatal(candidate_code);
                                reject_code_q <= candidate_code;
                                if (in_last)
                                    state_q <= REJECT;
                                else
                                    state_q <= DROP;
                            end
                        end
                    end
                    PAYLOAD: begin
                        if (in_last && remaining_q > 16'd1) begin
                            reject_fatal_q <= 1'b1;
                            reject_code_q <= IPV4_INVALID_LENGTH;
                            state_q <= REJECT;
                        end else begin
                            payload_data_q <= in_data;
                            payload_last_q <= (remaining_q == 16'd1);
                            payload_physical_last_q <= in_last;
                            payload_valid_q <= 1'b1;
                            if (remaining_q != 16'd0)
                                remaining_q <= remaining_q - 16'd1;
                        end
                    end
                    PADDING: begin
                        if (in_last)
                            state_q <= HEADER;
                    end
                    DROP: begin
                        if (in_last)
                            state_q <= REJECT;
                    end
                    default: begin
                        // REJECT has in_ready low, so no input_fire occurs.
                    end
                endcase
            end
        end
    end
endmodule
