module wire_eth_parser_reference (
    input logic       clk,
    input logic       rst,
    input logic [7:0] in_data,
    input logic       in_valid,
    input logic       in_last,
    input logic       out_ready,
    input logic       reject_ready
);
    localparam logic [1:0] FILTERED = 2'd0;
    localparam logic [1:0] TRUNCATED = 2'd1;
    localparam logic [1:0] EMPTY = 2'd2;
    typedef enum logic [1:0] {R_HEADER, R_PAYLOAD, R_DROP, R_REJECT} ref_state_t;

    logic [7:0] out_data;
    logic out_valid, in_ready, out_last;
    logic reject_valid, reject_fatal;
    logic [1:0] reject_code;
    wire_eth_parser dut (
        .clk(clk), .rst(rst), .in_data(in_data), .in_valid(in_valid),
        .in_ready(in_ready), .in_last(in_last), .out_data(out_data),
        .out_valid(out_valid), .out_ready(out_ready), .out_last(out_last),
        .reject_valid(reject_valid), .reject_ready(reject_ready),
        .reject_fatal(reject_fatal), .reject_code(reject_code)
    );

    ref_state_t ref_state;
    logic [3:0] ref_index;
    logic [7:0] ref_eth_high;
    logic [7:0] ref_payload_data;
    logic ref_payload_valid, ref_payload_last;
    logic ref_reject_valid, ref_reject_fatal;
    logic [1:0] ref_reject_code;

    wire ref_in_ready = (ref_state == R_HEADER) || (ref_state == R_DROP) ||
                         ((ref_state == R_PAYLOAD) && !ref_payload_last &&
                          (!ref_payload_valid || out_ready));
    wire input_fire = in_valid && in_ready;
    wire output_fire = out_valid && out_ready;
    wire reject_fire = reject_valid && reject_ready;

    initial begin
        ref_state = R_HEADER;
        ref_index = 4'd0;
        ref_eth_high = 8'h00;
        ref_payload_data = 8'h00;
        ref_payload_valid = 1'b0;
        ref_payload_last = 1'b0;
        ref_reject_valid = 1'b0;
        ref_reject_fatal = 1'b0;
        ref_reject_code = FILTERED;
    end

    always @(posedge clk) begin
        if ($initstate)
            assume(rst);
        if (!rst && $past(!rst && in_valid && !in_ready)) begin
            assume(in_valid);
            assume(in_data == $past(in_data));
            assume(in_last == $past(in_last));
        end

        if (rst) begin
            ref_state <= R_HEADER;
            ref_index <= 4'd0;
            ref_eth_high <= 8'h00;
            ref_payload_valid <= 1'b0;
            ref_payload_last <= 1'b0;
            ref_reject_valid <= 1'b0;
            ref_reject_fatal <= 1'b0;
            ref_reject_code <= FILTERED;
        end else begin
            if (ref_state == R_PAYLOAD && output_fire) begin
                ref_payload_valid <= 1'b0;
                if (ref_payload_last) begin
                    ref_payload_last <= 1'b0;
                    ref_state <= R_HEADER;
                    ref_index <= 4'd0;
                end
            end
            if (ref_state == R_REJECT && reject_fire) begin
                ref_state <= R_HEADER;
                ref_index <= 4'd0;
                ref_reject_valid <= 1'b0;
            end
            if (input_fire) begin
                case (ref_state)
                    R_HEADER: begin
                        if (in_last && ref_index < 4'd13) begin
                            ref_reject_fatal <= 1'b1;
                            ref_reject_code <= TRUNCATED;
                            ref_reject_valid <= 1'b1;
                            ref_state <= R_REJECT;
                        end else begin
                            case (ref_index)
                                4'd12: begin
                                    ref_eth_high <= in_data;
                                    ref_index <= 4'd13;
                                end
                                4'd13: begin
                                    if ({ref_eth_high, in_data} == 16'h0800) begin
                                        if (in_last) begin
                                            ref_reject_fatal <= 1'b1;
                                            ref_reject_code <= EMPTY;
                                            ref_reject_valid <= 1'b1;
                                            ref_state <= R_REJECT;
                                        end else ref_state <= R_PAYLOAD;
                                    end else if (in_last) begin
                                        ref_reject_fatal <= 1'b0;
                                        ref_reject_code <= FILTERED;
                                        ref_reject_valid <= 1'b1;
                                        ref_state <= R_REJECT;
                                    end else ref_state <= R_DROP;
                                end
                                default: ref_index <= ref_index + 4'd1;
                            endcase
                        end
                    end
                    R_PAYLOAD: begin
                        ref_payload_data <= in_data;
                        ref_payload_last <= in_last;
                        ref_payload_valid <= 1'b1;
                    end
                    R_DROP: begin
                        if (in_last) begin
                            ref_reject_fatal <= 1'b0;
                            ref_reject_code <= FILTERED;
                            ref_reject_valid <= 1'b1;
                            ref_state <= R_REJECT;
                        end
                    end
                    default: begin end
                endcase
            end
        end
    end

    always @(*) begin
        if (!rst) begin
            assert(in_ready == ref_in_ready);
            assert(out_valid == ref_payload_valid);
            assert(reject_valid == ref_reject_valid);
            if (ref_payload_valid) begin
                assert(out_data == ref_payload_data);
                assert(out_last == ref_payload_last);
            end else assert(!out_last);
            if (ref_reject_valid) begin
                assert(reject_fatal == ref_reject_fatal);
                assert(reject_code == ref_reject_code);
                assert(!in_ready);
                assert(!out_valid);
            end
        end
    end

    always @(posedge clk) begin
        if (!rst && $past(!rst && out_valid && !out_ready)) begin
            assert(out_valid);
            assert(out_data == $past(out_data));
            assert(out_last == $past(out_last));
        end
        if (!rst && $past(!rst && reject_valid && !reject_ready)) begin
            assert(reject_valid);
            assert(reject_fatal == $past(reject_fatal));
            assert(reject_code == $past(reject_code));
            assert(!in_ready);
            assert(!out_valid);
        end
        if (!rst) begin
            cover(ref_state == R_PAYLOAD && input_fire);
            cover(ref_state == R_DROP && in_last && input_fire);
            cover(ref_state == R_REJECT && !reject_ready);
            cover(ref_state == R_PAYLOAD && output_fire && ref_payload_last);
        end
    end
endmodule
