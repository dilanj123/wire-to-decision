module wire_async_fifo_formal (
    input logic wr_clk,
    input logic rd_clk,
    input logic wr_rst,
    input logic rd_rst,
    input logic [72:0] wr_data,
    input logic wr_valid,
    input logic rd_ready
);
    logic wr_ready;
    logic [72:0] rd_data;
    logic rd_valid;

    wire_async_fifo #(.WIDTH(73), .DEPTH(8)) dut (
        .wr_clk(wr_clk), .wr_rst(wr_rst), .wr_data(wr_data),
        .wr_valid(wr_valid), .wr_ready(wr_ready),
        .rd_clk(rd_clk), .rd_rst(rd_rst), .rd_data(rd_data),
        .rd_valid(rd_valid), .rd_ready(rd_ready)
    );

    // Reset initializes both local pointer domains. The clock inputs remain
    // independent; multiclock SBY models their edges separately.
    initial begin
        assume(wr_rst);
        assume(rd_rst);
    end
    always_comb assume(wr_rst == rd_rst);

    logic stalled_prev_q;
    logic [72:0] stalled_data_q;
    always_ff @(posedge rd_clk or posedge rd_rst) begin
        if (rd_rst) begin
            stalled_prev_q <= 1'b0;
            stalled_data_q <= '0;
        end else begin
            if (stalled_prev_q) begin
                assert(rd_valid);
                assert(rd_data == stalled_data_q);
            end
            stalled_prev_q <= rd_valid && !rd_ready;
            stalled_data_q <= rd_data;
        end
    end
endmodule
