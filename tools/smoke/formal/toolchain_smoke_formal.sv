// WIRE-004 TOOLCHAIN SMOKE ONLY.
// This is a local harness for one trivial registered-addition property.
module toolchain_smoke_formal (
    input logic clk,
    input logic rst_n,
    input logic [7:0] a,
    input logic [7:0] b
);
    logic [8:0] sum_q;

    toolchain_smoke dut (
        .clk   (clk),
        .rst_n (rst_n),
        .a     (a),
        .b     (b),
        .sum_q (sum_q)
    );

    always @(posedge clk) begin
        if ($initstate)
            assume(!rst_n);
        else
            assume(rst_n);
    end

    always @(posedge clk) begin
        if (rst_n && $past(rst_n))
            assert(sum_q == ({1'b0, $past(a)} + {1'b0, $past(b)}));
        if (rst_n && !$past(rst_n))
            cover(rst_n);
    end
endmodule
