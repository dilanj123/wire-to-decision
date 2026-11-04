module wire_arch_b_safety (
    input logic clk, rst, rearm,
    input logic [63:0] rx_data,
    input logic [7:0] rx_keep,
    input logic rx_valid, rx_last,
    input logic event_ready
);
    logic rx_ready, event_valid, parser_valid, recovery_required;
    logic [2:0] event_kind;
    logic [7:0] source_type;
    logic [63:0] mold_sequence, old_ref, new_ref, expected_sequence;
    logic [47:0] timestamp;
    logic [15:0] locate;
    logic [31:0] quantity, price;
    logic side, old_valid, new_valid, quantity_valid, price_valid, side_valid;
    logic [3:0] recovery_stage;

    wire input_fire = rx_valid && rx_ready;
    wire_arch_b_parser_top dut (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_destination_ipv4(32'hC6336407), .cfg_destination_udp_port(16'h1234),
        .cfg_active_session(80'h57324454455354303031),
        .cfg_expected_sequence(64'h1020304050607080),
        .cfg_tracked_stock_locate(16'h2345), .cfg_symbol_check_enable(1'b0),
        .cfg_expected_stock_symbol(64'h414C504820202020),
        .rx_data(rx_data), .rx_keep(rx_keep), .rx_valid(rx_valid),
        .rx_ready(rx_ready), .rx_last(rx_last), .event_valid(event_valid),
        .event_ready(event_ready), .event_kind(event_kind), .source_type(source_type),
        .mold_sequence(mold_sequence), .itch_timestamp(timestamp), .stock_locate(locate),
        .old_order_reference(old_ref), .new_order_reference(new_ref),
        .quantity(quantity), .price(price), .side(side),
        .old_reference_valid(old_valid), .new_reference_valid(new_valid),
        .quantity_valid(quantity_valid), .price_valid(price_valid), .side_valid(side_valid),
        .parser_valid(parser_valid), .recovery_required(recovery_required),
        .recovery_stage(recovery_stage), .current_expected_sequence(expected_sequence)
    );

    always_ff @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!rst && !rearm && $past(!rst && !rearm && rx_valid && !rx_ready)) begin
            assume(rx_valid);
            assume($stable({rx_data,rx_keep,rx_last}));
        end
        if (!rst) begin
            if (recovery_required) begin
                assert(!event_valid);
                assert(!parser_valid);
            end
            if ($past(!rst && !rearm && event_valid && !event_ready)) begin
                assert(event_valid);
                assert($stable({event_kind,source_type,mold_sequence,timestamp,locate,
                    old_ref,new_ref,quantity,price,side,old_valid,new_valid,
                    quantity_valid,price_valid,side_valid}));
            end
            if ($past(!rst && rearm)) begin
                assert(parser_valid);
                assert(!recovery_required);
                assert(!event_valid);
                assert(expected_sequence == 64'h1020304050607080);
            end
        end
        cover(event_valid && event_ready);
        cover(recovery_required);
        cover(recovery_required && rearm);
    end
endmodule
