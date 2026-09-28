module wire_buffer_gearbox_top (
    input  logic        clk,
    input  logic        rst,

    input  logic [63:0] in_data,
    input  logic [7:0]  in_keep,
    input  logic        in_valid,
    output logic        in_ready,
    input  logic        in_last,

    output logic [7:0]  out_data,
    output logic        out_valid,
    input  logic        out_ready,
    output logic        out_last
);
    logic [63:0] buffer_data;
    logic [7:0]  buffer_keep;
    logic        buffer_valid;
    logic        buffer_ready;
    logic        buffer_last;

    wire_ingress_buffer buffer (
        .clk(clk), .rst(rst),
        .in_data(in_data), .in_keep(in_keep), .in_valid(in_valid),
        .in_ready(in_ready), .in_last(in_last),
        .out_data(buffer_data), .out_keep(buffer_keep),
        .out_valid(buffer_valid), .out_ready(buffer_ready),
        .out_last(buffer_last)
    );

    wire_gearbox_64to8 gearbox (
        .clk(clk), .rst(rst),
        .in_data(buffer_data), .in_keep(buffer_keep),
        .in_valid(buffer_valid), .in_ready(buffer_ready),
        .in_last(buffer_last),
        .out_data(out_data), .out_valid(out_valid),
        .out_ready(out_ready), .out_last(out_last)
    );
endmodule
