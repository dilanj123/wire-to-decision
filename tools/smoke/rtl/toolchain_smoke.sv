// WIRE-004 TOOLCHAIN SMOKE ONLY.
// This is not Wire-to-Decision application RTL.
module toolchain_smoke (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [8:0] sum_q
);

    always_ff @(posedge clk) begin
        if (!rst_n)
            sum_q <= '0;
        else
            sum_q <= {1'b0, a} + {1'b0, b};
    end

endmodule
