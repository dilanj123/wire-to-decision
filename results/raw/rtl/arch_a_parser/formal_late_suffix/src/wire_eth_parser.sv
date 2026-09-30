// Wire-to-Decision Architecture A Ethernet II header stripper.
// Accepts only Ethernet II frames carrying IPv4 (EtherType 0x0800).
module wire_eth_parser (
    input  logic       clk,
    input  logic       rst,

    input  logic [7:0] in_data,
    input  logic       in_valid,
    output logic       in_ready,
    input  logic       in_last,

    output logic [7:0] out_data,
    output logic       out_valid,
    input  logic       out_ready,
    output logic       out_last,

    output logic       reject_valid,
    input  logic       reject_ready,
    output logic       reject_fatal,
    output logic [1:0] reject_code
);
    localparam logic [1:0] ETH_FILTERED_ETHERTYPE = 2'd0;
    localparam logic [1:0] ETH_TRUNCATED_HEADER   = 2'd1;
    localparam logic [1:0] ETH_EMPTY_IPV4_PAYLOAD = 2'd2;

    typedef enum logic [1:0] {HEADER, PAYLOAD, DROP, REJECT} state_t;
    state_t state_q;
    logic [3:0] header_index_q;
    logic [7:0] ethertype_high_q;
    logic [7:0] payload_data_q;
    logic       payload_last_q;
    logic       payload_valid_q;
    logic       reject_fatal_q;
    logic [1:0] reject_code_q;

    wire output_fire = out_valid && out_ready;
    wire input_fire  = in_valid && in_ready;

    assign out_valid = payload_valid_q;
    assign out_data  = payload_data_q;
    assign out_last  = payload_valid_q && payload_last_q;

    // A final payload byte is not replaced by a new frame-header byte on the
    // same cycle; the following cycle begins the next frame in HEADER.
    assign in_ready = (state_q == HEADER) ||
                      (state_q == DROP) ||
                      ((state_q == PAYLOAD) &&
                       !payload_last_q &&
                       (!payload_valid_q || out_ready));

    assign reject_valid = (state_q == REJECT);
    assign reject_fatal = reject_fatal_q;
    assign reject_code  = reject_code_q;

    always_ff @(posedge clk) begin
        if (rst) begin
            state_q          <= HEADER;
            header_index_q   <= 4'd0;
            ethertype_high_q <= 8'h00;
            payload_data_q   <= 8'h00;
            payload_last_q   <= 1'b0;
            payload_valid_q  <= 1'b0;
            reject_fatal_q   <= 1'b0;
            reject_code_q    <= ETH_FILTERED_ETHERTYPE;
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
                        if (in_last && header_index_q < 4'd13) begin
                            reject_fatal_q <= 1'b1;
                            reject_code_q  <= ETH_TRUNCATED_HEADER;
                            state_q        <= REJECT;
                        end else begin
                            case (header_index_q)
                                4'd12: begin
                                    ethertype_high_q <= in_data;
                                    header_index_q <= 4'd13;
                                end
                                4'd13: begin
                                    if ({ethertype_high_q, in_data} == 16'h0800) begin
                                        if (in_last) begin
                                            reject_fatal_q <= 1'b1;
                                            reject_code_q  <= ETH_EMPTY_IPV4_PAYLOAD;
                                            state_q        <= REJECT;
                                        end else begin
                                            state_q <= PAYLOAD;
                                        end
                                    end else if (in_last) begin
                                        reject_fatal_q <= 1'b0;
                                        reject_code_q  <= ETH_FILTERED_ETHERTYPE;
                                        state_q        <= REJECT;
                                    end else begin
                                        state_q <= DROP;
                                    end
                                end
                                default: header_index_q <= header_index_q + 4'd1;
                            endcase
                        end
                    end
                    PAYLOAD: begin
                        payload_data_q  <= in_data;
                        payload_last_q  <= in_last;
                        payload_valid_q <= 1'b1;
                    end
                    DROP: begin
                        if (in_last) begin
                            reject_fatal_q <= 1'b0;
                            reject_code_q  <= ETH_FILTERED_ETHERTYPE;
                            state_q        <= REJECT;
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
