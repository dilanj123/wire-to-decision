module wire_arch_a_parser_late_suffix(input logic clk, rst);
    localparam logic [63:0] BASE_SEQUENCE = 64'h1020304050607080;
    logic [3:0] beat_index_q;
    logic [8:0] cycle_q;
    logic [1:0] event_count_q;

    logic rx_ready, event_valid;
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

    function automatic logic [63:0] beat_data(input logic [3:0] index);
        case (index)
            0: beat_data = 64'h0B0A050403020102;
            1: beat_data = 64'h104500080F0E0D0C;
            2: beat_data = 64'h1140004067455E00;
            3: beat_data = 64'h33C6210200C0BC08;
            4: beat_data = 64'h4A003412EFBE0764;
            5: beat_data = 64'h5345544432570000;
            6: beat_data = 64'h4030201031303054;
            7: beat_data = 64'h1300030080706050;
            8: beat_data = 64'h030201CDAB452344;
            9: beat_data = 64'h4455667788060504;
            10: beat_data = 64'h4523441300112233;
            11: beat_data = 64'h070504030201CEAB;
            12: beat_data = 64'h1222334455667788;
            default: beat_data = 64'h0000000062610500;
        endcase
    endfunction

    wire rx_valid = (beat_index_q < 4'd14) && !rst;
    wire rx_last = (beat_index_q == 4'd13);
    wire [7:0] rx_keep = rx_last ? 8'h0f : 8'hff;
    wire [63:0] rx_data = beat_data(beat_index_q);

    wire_arch_a_parser_top dut (
        .clk(clk), .rst(rst), .rearm(1'b0),
        .cfg_destination_ipv4(32'hC6336407), .cfg_destination_udp_port(16'h1234),
        .cfg_active_session(80'h57324454455354303031),
        .cfg_expected_sequence(BASE_SEQUENCE), .cfg_tracked_stock_locate(16'h2345),
        .cfg_symbol_check_enable(1'b0), .cfg_expected_stock_symbol(64'h414C504820202020),
        .rx_data(rx_data), .rx_keep(rx_keep), .rx_valid(rx_valid),
        .rx_ready(rx_ready), .rx_last(rx_last), .event_valid(event_valid),
        .event_ready(1'b1), .event_kind(event_kind), .source_type(source_type),
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
        if ($past(rst)) assume(!rst);
        if (rst) begin
            beat_index_q <= 0;
            cycle_q <= 0;
            event_count_q <= 0;
        end else begin
            cycle_q <= cycle_q + 1'b1;
            if (rx_valid && rx_ready)
                beat_index_q <= beat_index_q + 1'b1;
            if (event_valid) begin
                if (event_count_q == 0) begin
                    assert(event_kind == 3'd4 && source_type == "D");
                    assert(mold_sequence == BASE_SEQUENCE);
                end else if (event_count_q == 1) begin
                    assert(event_kind == 3'd4 && source_type == "D");
                    assert(mold_sequence == BASE_SEQUENCE + 1'b1);
                end else begin
                    assert(1'b0);
                end
                event_count_q <= event_count_q + 1'b1;
            end
            if (cycle_q == 9'd260) begin
                assert(beat_index_q == 4'd14);
                assert(recovery_required);
                assert(event_count_q == 2);
                assert(current_expected_sequence == BASE_SEQUENCE);
                assert(!event_valid);
            end
        end
    end
endmodule
