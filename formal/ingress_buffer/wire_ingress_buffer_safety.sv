module wire_ingress_buffer_safety (
    input logic        clk,
    input logic        rst,
    input logic [63:0] in_data,
    input logic [7:0]  in_keep,
    input logic        in_valid,
    input logic        in_last,
    input logic        out_ready
);
    logic [63:0] out_data;
    logic [7:0]  out_keep;
    logic        in_ready, out_valid, out_last;

    wire_ingress_buffer dut (
        .clk(clk), .rst(rst),
        .in_data(in_data), .in_keep(in_keep), .in_valid(in_valid),
        .in_ready(in_ready), .in_last(in_last),
        .out_data(out_data), .out_keep(out_keep),
        .out_valid(out_valid), .out_ready(out_ready), .out_last(out_last)
    );

    always @(posedge clk) begin
        if ($initstate)
            assume(rst);
        if (!rst && $past(!rst && in_valid && !in_ready)) begin
            assume(in_valid);
            assume(in_data == $past(in_data));
            assume(in_keep == $past(in_keep));
            assume(in_last == $past(in_last));
        end
    end

    always @(posedge clk) begin
        if (!rst && $past(rst))
            assert(!out_valid);
    end
endmodule
