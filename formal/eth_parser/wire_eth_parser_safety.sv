module wire_eth_parser_safety (
    input logic       clk,
    input logic       rst,
    input logic [7:0] in_data,
    input logic       in_valid,
    input logic       in_last,
    input logic       out_ready,
    input logic       reject_ready
);
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
    always @(posedge clk) begin
        if ($initstate)
            assume(rst);
        if (!rst && $past(!rst && in_valid && !in_ready)) begin
            assume(in_valid);
            assume(in_data == $past(in_data));
            assume(in_last == $past(in_last));
        end
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
    end
endmodule
