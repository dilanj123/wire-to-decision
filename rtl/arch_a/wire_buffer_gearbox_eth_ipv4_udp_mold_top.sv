module wire_buffer_gearbox_eth_ipv4_udp_mold_top (
    input  logic        clk,
    input  logic        rst,
    input  logic [31:0] cfg_destination_ipv4,
    input  logic [15:0] cfg_destination_udp_port,
    input  logic [79:0] cfg_active_session,
    input  logic [63:0] cfg_expected_sequence,
    input  logic        rearm,
    input  logic [63:0] in_data,
    input  logic [7:0]  in_keep,
    input  logic        in_valid,
    output logic        in_ready,
    input  logic        in_last,
    output logic        packet_valid,
    input  logic        packet_ready,
    output logic [63:0] packet_sequence,
    output logic [15:0] packet_message_count,
    output logic        packet_body_empty,
    output logic        mold_out_valid,
    input  logic        mold_out_ready,
    output logic [7:0]  mold_out_data,
    output logic        mold_out_last,
    input  logic        packet_result_valid,
    output logic        packet_result_ready,
    input  logic        packet_result_success,
    output logic        mold_reject_valid,
    input  logic        mold_reject_ready,
    output logic        mold_reject_fatal,
    output logic [2:0]  mold_reject_code,
    output logic        controller_valid,
    output logic        recovery_required,
    output logic [63:0] current_expected_sequence,
    output logic        eth_reject_valid,
    input  logic        eth_reject_ready,
    output logic        eth_reject_fatal,
    output logic [1:0]  eth_reject_code,
    output logic        ipv4_reject_valid,
    input  logic        ipv4_reject_ready,
    output logic        ipv4_reject_fatal,
    output logic [3:0]  ipv4_reject_code,
    output logic        udp_reject_valid,
    input  logic        udp_reject_ready,
    output logic        udp_reject_fatal,
    output logic [2:0]  udp_reject_code
);
    logic [63:0] b_data;
    logic [7:0] b_keep;
    logic b_valid, b_ready, b_last;
    logic [7:0] g_data;
    logic g_valid, g_ready, g_last;
    logic [7:0] eth_data;
    logic eth_valid, eth_ready, eth_last;
    logic [7:0] ip_data;
    logic ip_valid, ip_ready, ip_last;
    logic [7:0] udp_data;
    logic udp_valid, udp_ready, udp_last;

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
        .in_last(eth_last), .out_data(ip_data), .out_valid(ip_valid),
        .out_ready(ip_ready), .out_last(ip_last),
        .reject_valid(ipv4_reject_valid), .reject_ready(ipv4_reject_ready),
        .reject_fatal(ipv4_reject_fatal), .reject_code(ipv4_reject_code)
    );
    wire_udp_parser udp (
        .clk(clk), .rst(rst), .cfg_destination_udp_port(cfg_destination_udp_port),
        .in_data(ip_data), .in_valid(ip_valid), .in_ready(ip_ready),
        .in_last(ip_last), .out_data(udp_data), .out_valid(udp_valid),
        .out_ready(udp_ready), .out_last(udp_last),
        .reject_valid(udp_reject_valid), .reject_ready(udp_reject_ready),
        .reject_fatal(udp_reject_fatal), .reject_code(udp_reject_code)
    );
    wire_mold_header_seq mold (
        .clk(clk), .rst(rst), .cfg_active_session(cfg_active_session),
        .cfg_expected_sequence(cfg_expected_sequence), .rearm(rearm),
        .in_valid(udp_valid), .in_ready(udp_ready), .in_data(udp_data),
        .in_last(udp_last), .packet_valid(packet_valid),
        .packet_ready(packet_ready), .packet_sequence(packet_sequence),
        .packet_message_count(packet_message_count),
        .packet_body_empty(packet_body_empty), .out_valid(mold_out_valid),
        .out_ready(mold_out_ready), .out_data(mold_out_data),
        .out_last(mold_out_last), .packet_result_valid(packet_result_valid),
        .packet_result_ready(packet_result_ready),
        .packet_result_success(packet_result_success),
        .reject_valid(mold_reject_valid), .reject_ready(mold_reject_ready),
        .reject_fatal(mold_reject_fatal), .reject_code(mold_reject_code),
        .controller_valid(controller_valid),
        .recovery_required(recovery_required),
        .current_expected_sequence(current_expected_sequence)
    );
endmodule
