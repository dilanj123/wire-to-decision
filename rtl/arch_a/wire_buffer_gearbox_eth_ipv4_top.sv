module wire_buffer_gearbox_eth_ipv4_top (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] cfg_destination_ipv4,
    input  logic [63:0] in_data,
    input  logic [7:0]  in_keep,
    input  logic        in_valid,
    output logic        in_ready,
    input  logic        in_last,
    output logic [7:0]  out_data,
    output logic        out_valid,
    input  logic        out_ready,
    output logic        out_last,
    output logic        eth_reject_valid,
    input  logic        eth_reject_ready,
    output logic        eth_reject_fatal,
    output logic [1:0]  eth_reject_code,
    output logic        ipv4_reject_valid,
    input  logic        ipv4_reject_ready,
    output logic        ipv4_reject_fatal,
    output logic [3:0]  ipv4_reject_code
);
    logic [63:0] b_data;
    logic [7:0]  b_keep;
    logic        b_valid, b_ready, b_last;
    logic [7:0]  g_data;
    logic        g_valid, g_ready, g_last;
    logic [7:0]  eth_data;
    logic        eth_valid, eth_ready, eth_last;

    wire_ingress_buffer buffer (
        .clk(clk), .rst(rst), .in_data(in_data), .in_keep(in_keep),
        .in_valid(in_valid), .in_ready(in_ready), .in_last(in_last),
        .out_data(b_data), .out_keep(b_keep), .out_valid(b_valid),
        .out_ready(b_ready), .out_last(b_last)
    );
    wire_gearbox_64to8 gearbox (
        .clk(clk), .rst(rst), .in_data(b_data), .in_valid(b_valid),
        .in_ready(b_ready), .in_keep(b_keep), .in_last(b_last),
        .out_data(g_data), .out_valid(g_valid), .out_ready(g_ready),
        .out_last(g_last)
    );
    wire_eth_parser eth (
        .clk(clk), .rst(rst), .in_data(g_data), .in_valid(g_valid),
        .in_ready(g_ready), .in_last(g_last), .out_data(eth_data),
        .out_valid(eth_valid), .out_ready(eth_ready), .out_last(eth_last),
        .reject_valid(eth_reject_valid), .reject_ready(eth_reject_ready),
        .reject_fatal(eth_reject_fatal), .reject_code(eth_reject_code)
    );
    wire_ipv4_parser ipv4 (
        .clk(clk), .rst(rst), .cfg_destination_ipv4(cfg_destination_ipv4),
        .in_data(eth_data), .in_valid(eth_valid), .in_ready(eth_ready),
        .in_last(eth_last), .out_data(out_data), .out_valid(out_valid),
        .out_ready(out_ready), .out_last(out_last),
        .reject_valid(ipv4_reject_valid), .reject_ready(ipv4_reject_ready),
        .reject_fatal(ipv4_reject_fatal), .reject_code(ipv4_reject_code)
    );
endmodule
