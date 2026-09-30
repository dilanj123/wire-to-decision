module wire_arch_a_parser_safety (
    input logic clk, rst, rearm,
    input logic [63:0] rx_data,
    input logic [7:0] rx_keep,
    input logic rx_valid, rx_last,
    input logic event_ready
);
    logic rx_ready;
    logic event_valid;
    logic [2:0] event_kind;
    logic [7:0] source_type;
    logic [63:0] mold_sequence, old_order_reference, new_order_reference;
    logic [47:0] itch_timestamp;
    logic [15:0] stock_locate;
    logic [31:0] quantity, price;
    logic side, old_reference_valid, new_reference_valid, quantity_valid;
    logic price_valid, side_valid, parser_valid, recovery_required;
    logic [3:0] recovery_stage;
    logic [63:0] current_expected_sequence;
    logic eth_reject_observed, eth_reject_fatal, ipv4_reject_observed, ipv4_reject_fatal;
    logic udp_reject_observed, udp_reject_fatal, mold_reject_observed;
    logic framer_reject_observed, itch_reject_observed;
    logic [1:0] eth_reject_code, framer_reject_code;
    logic [3:0] ipv4_reject_code;
    logic [2:0] udp_reject_code, mold_reject_code, itch_reject_code;

    wire rx_fire = rx_valid && rx_ready;
    logic frame_open_ref;
    logic closed_after_recovery;

    wire_arch_a_parser_top dut (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_destination_ipv4(32'hC6336407), .cfg_destination_udp_port(16'h1234),
        .cfg_active_session(80'h57324454455354303031),
        .cfg_expected_sequence(64'h1020304050607080),
        .cfg_tracked_stock_locate(16'h2345), .cfg_symbol_check_enable(1'b0),
        .cfg_expected_stock_symbol(64'h414C504820202020),
        .rx_data(rx_data), .rx_keep(rx_keep), .rx_valid(rx_valid),
        .rx_ready(rx_ready), .rx_last(rx_last), .event_valid(event_valid),
        .event_ready(event_ready), .event_kind(event_kind), .source_type(source_type),
        .mold_sequence(mold_sequence), .itch_timestamp(itch_timestamp),
        .stock_locate(stock_locate), .old_order_reference(old_order_reference),
        .new_order_reference(new_order_reference), .quantity(quantity), .price(price),
        .side(side), .old_reference_valid(old_reference_valid),
        .new_reference_valid(new_reference_valid), .quantity_valid(quantity_valid),
        .price_valid(price_valid), .side_valid(side_valid), .parser_valid(parser_valid),
        .recovery_required(recovery_required), .recovery_stage(recovery_stage),
        .current_expected_sequence(current_expected_sequence),
        .eth_reject_observed(eth_reject_observed), .eth_reject_fatal(eth_reject_fatal),
        .eth_reject_code(eth_reject_code), .ipv4_reject_observed(ipv4_reject_observed),
        .ipv4_reject_fatal(ipv4_reject_fatal), .ipv4_reject_code(ipv4_reject_code),
        .udp_reject_observed(udp_reject_observed), .udp_reject_fatal(udp_reject_fatal),
        .udp_reject_code(udp_reject_code), .mold_reject_observed(mold_reject_observed),
        .mold_reject_code(mold_reject_code), .framer_reject_observed(framer_reject_observed),
        .framer_reject_code(framer_reject_code), .itch_reject_observed(itch_reject_observed),
        .itch_reject_code(itch_reject_code));

    always_ff @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!rst && !rearm && $past(!rst && !rearm && rx_valid && !rx_ready)) begin
            assume(rx_valid);
            assume($stable({rx_data, rx_keep, rx_last}));
        end
        if (rst || rearm) begin
            frame_open_ref <= 1'b0;
            closed_after_recovery <= 1'b0;
        end else begin
            if (rx_fire)
                frame_open_ref <= !rx_last;
            if (recovery_required && (!frame_open_ref || (rx_fire && rx_last)))
                closed_after_recovery <= 1'b1;
        end
        if (!rst) begin
            if (recovery_required) assert(!event_valid);
            if (recovery_required && closed_after_recovery) assert(!rx_ready);
            if ($past(!rst && !rearm && event_valid && !event_ready)) begin
                assert(event_valid);
                assert($stable({event_kind, source_type, mold_sequence, itch_timestamp,
                    stock_locate, old_order_reference, new_order_reference, quantity,
                    price, side, old_reference_valid, new_reference_valid,
                    quantity_valid, price_valid, side_valid}));
            end
            if ($past(!rst && rearm)) begin
                assert(parser_valid);
                assert(!recovery_required);
                assert(!event_valid);
            end
        end
    end
endmodule
