module wire_gearbox_safety (
    input logic clk, rst,
    input logic [63:0] in_data,
    input logic [7:0] in_keep,
    input logic in_valid,
    input logic in_last,
    input logic out_ready
);
    logic in_ready, out_valid, out_last;
    logic [7:0] out_data;
    wire_gearbox_64to8 dut (
        .clk(clk), .rst(rst), .in_data(in_data), .in_keep(in_keep),
        .in_valid(in_valid), .in_ready(in_ready), .in_last(in_last),
        .out_data(out_data), .out_valid(out_valid),
        .out_ready(out_ready), .out_last(out_last)
    );

    function automatic logic legal_keep(input logic [7:0] keep);
        case (keep)
            8'h01, 8'h03, 8'h07, 8'h0f, 8'h1f, 8'h3f, 8'h7f, 8'hff: legal_keep = 1'b1;
            default: legal_keep = 1'b0;
        endcase
    endfunction

    always @(*) begin
        if (in_valid) begin
            if (in_last) assume(legal_keep(in_keep));
            else assume(in_keep == 8'hff);
        end
        if (!rst) assert(!out_last || out_valid);
    end

    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!rst && $past(!rst && out_valid && !out_ready)) begin
            assert(out_valid);
            assert(out_data == $past(out_data));
            assert(out_last == $past(out_last));
        end
        if (!rst && $past(!rst && out_valid && out_ready && out_last &&
                          in_valid && in_ready)) begin
            assert(out_valid);
            assert(out_data == $past(in_data[7:0]));
        end
        if (!rst && $past(!rst && !out_valid && in_valid && in_ready)) begin
            assert(out_valid);
            assert(out_data == $past(in_data[7:0]));
        end
        if (!rst)
            cover(out_valid && out_ready && in_valid && in_ready && out_last);
    end
endmodule
