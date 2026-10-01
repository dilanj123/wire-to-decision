module order_book_add_vector;
    (* gclk *) wire clk;
    reg [4:0] cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;
    wire rst = cycle == 0;
    wire rearm = 1'b0, upstream_recovery_required = 1'b0;
    wire event_valid = (cycle == 2) || (cycle == 6) || (cycle == 10) ||
                       (cycle == 14) || (cycle == 18) || (cycle == 22);
    wire [2:0] event_kind = cycle == 2 ? 3'd0 : cycle == 6 ? 3'd1 :
                            cycle == 10 ? 3'd2 : cycle == 14 ? 3'd3 :
                            cycle == 18 ? 3'd5 : 3'd4;
    wire [7:0] source_type = cycle == 2 ? 8'h41 : cycle == 6 ? 8'h45 :
                             cycle == 10 ? 8'h43 : cycle == 14 ? 8'h58 :
                             cycle == 18 ? 8'h55 : 8'h44;
    wire [63:0] mold_sequence = 64'h0102030405060708;
    wire [47:0] itch_timestamp = 48'h112233445566;
    wire [15:0] stock_locate = 16'h1234;
    wire [63:0] old_order_reference = 64'h1, new_order_reference = 64'h1;
    wire [31:0] quantity = cycle == 2 ? 32'd13 : cycle == 6 ? 32'd4 :
        cycle == 10 ? 32'd2 : cycle == 14 ? 32'd3 : cycle == 18 ? 32'd20 : 32'd0;
    wire [31:0] price = cycle == 2 ? 32'h10203040 : cycle == 10 ? 32'hDEADBEEF :
                        cycle == 18 ? 32'h99887766 : 32'd0;
    wire side = 0;
    wire old_reference_valid = cycle != 2;
    wire new_reference_valid = (cycle == 2) || (cycle == 18);
    wire quantity_valid = cycle != 22;
    wire price_valid = (cycle == 2) || (cycle == 18);
    wire side_valid = cycle == 2;
    wire commit_ready = 1, error_ready = 1;
    wire event_ready, commit_valid, book_valid, recovery_required, error_valid;
    wire [63:0] commit_mold_sequence;
    wire [47:0] commit_itch_timestamp, commit_bid_total, commit_ask_total;
    wire [47:0] bid_total, ask_total;
    wire [3:0] error_code;
    wire [63:0] debug_reference = 64'h1;
    wire debug_found, debug_side, debug_way;
    wire [31:0] debug_price, debug_remaining_quantity;
    wire [15:0] last_accepted_stock_locate;
    wire [8:0] debug_set_index;
    wire_order_book #(.NUM_SETS(2)) dut (.*);
    always @(posedge clk) begin
        if (cycle == 4 || cycle == 8 || cycle == 12 || cycle == 16 || cycle == 20 || cycle == 24) begin
            assert(book_valid && !recovery_required);
            assert(commit_valid);
            assert(commit_mold_sequence == 64'h0102030405060708);
            assert(commit_itch_timestamp == 48'h112233445566);
            assert(commit_ask_total == 0 && ask_total == 0);
            if (cycle == 4) begin
                assert(bid_total == 13 && commit_bid_total == 13);
                assert(debug_found && debug_price == 32'h10203040 && debug_remaining_quantity == 13);
            end
            if (cycle == 8) begin
                assert(bid_total == 9 && commit_bid_total == 9);
                assert(debug_found && debug_price == 32'h10203040 && debug_remaining_quantity == 9);
            end
            if (cycle == 12) begin
                assert(bid_total == 7 && commit_bid_total == 7);
                assert(debug_found && debug_price == 32'h10203040 && debug_remaining_quantity == 7);
            end
            if (cycle == 16) begin
                assert(bid_total == 4 && commit_bid_total == 4);
                assert(debug_found && debug_price == 32'h10203040 && debug_remaining_quantity == 4);
            end
            if (cycle == 20) begin
                assert(bid_total == 20 && commit_bid_total == 20);
                assert(debug_found && debug_price == 32'h99887766 && debug_remaining_quantity == 20);
            end
            if (cycle == 24) begin
                assert(bid_total == 0 && commit_bid_total == 0);
                assert(!debug_found);
            end
        end
        cover(cycle == 24 && commit_valid && !debug_found);
    end
endmodule
