module wire_buffer_gearbox_eth_top (
    input  logic       clk,
    input  logic       rst,
    input  logic [63:0] in_data,
    input  logic [7:0] in_keep,
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
    logic [63:0] b_data;
    logic [7:0]  b_keep;
    logic        b_valid, b_ready, b_last;
    logic [7:0]  g_data;
    logic        g_valid, g_ready, g_last;

    wire_ingress_buffer buffer (
        .clk(clk), .rst(rst), .in_data(in_data), .in_keep(in_keep),
        .in_valid(in_valid), .in_ready(in_ready), .in_last(in_last),
        .out_data(b_data), .out_keep(b_keep), .out_valid(b_valid),
        .out_ready(b_ready), .out_last(b_last)
    );
    wire_gearbox_64to8 gearbox (
        .clk(clk), .rst(rst), .in_data(b_data), .in_keep(b_keep),
        .in_valid(b_valid), .in_ready(b_ready), .in_last(b_last),
        .out_data(g_data), .out_valid(g_valid), .out_ready(g_ready),
        .out_last(g_last)
    );
    wire_eth_parser parser (
        .clk(clk), .rst(rst), .in_data(g_data), .in_valid(g_valid),
        .in_ready(g_ready), .in_last(g_last), .out_data(out_data),
        .out_valid(out_valid), .out_ready(out_ready), .out_last(out_last),
        .reject_valid(reject_valid), .reject_ready(reject_ready),
        .reject_fatal(reject_fatal), .reject_code(reject_code)
    );
endmodule
