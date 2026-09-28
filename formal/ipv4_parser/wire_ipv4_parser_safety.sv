module wire_ipv4_parser_safety (
    input logic clk, input logic rst,
    input logic [31:0] cfg_destination_ipv4,
    input logic [7:0] in_data, input logic in_valid, input logic in_last,
    input logic out_ready, input logic reject_ready
);
    logic in_ready, out_valid, out_last, reject_valid, reject_fatal;
    logic [7:0] out_data;
    logic [3:0] reject_code;
    wire_ipv4_parser dut (
        .clk(clk), .rst(rst), .cfg_destination_ipv4(cfg_destination_ipv4),
        .in_data(in_data), .in_valid(in_valid), .in_ready(in_ready), .in_last(in_last),
        .out_data(out_data), .out_valid(out_valid), .out_ready(out_ready), .out_last(out_last),
        .reject_valid(reject_valid), .reject_ready(reject_ready),
        .reject_fatal(reject_fatal), .reject_code(reject_code)
    );

    always @(posedge clk) begin
        if ($initstate)
            assume(rst);
        if (!rst)
            assume(cfg_destination_ipv4 == 32'hC6336407);
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
