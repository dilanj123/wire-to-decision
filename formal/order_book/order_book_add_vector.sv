module order_book_add_vector;
    (* gclk *) wire clk;
    reg [4:0] cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;
    wire rst = cycle == 0;
    wire rearm = 1'b0, upstream_recovery_required = 1'b0;
    wire event_valid = (cycle == 2) || (cycle == 10);
    wire [2:0] event_kind = cycle == 2 ? 3'd0 : 3'd1;
    wire [7:0] source_type = cycle == 2 ? 8'h41 : 8'h45;
    wire [63:0] mold_sequence = 64'h0102030405060708;
    wire [47:0] itch_timestamp = 48'h112233445566;
    wire [15:0] stock_locate = 16'h1234;
    wire [63:0] old_order_reference = 64'h1, new_order_reference = 64'h1;
    wire [31:0] quantity = cycle == 2 ? 32'd13 : 32'd4;
    wire [31:0] price = cycle == 2 ? 32'h10203040 : 32'd0;
    wire side = 0;
    wire old_reference_valid = cycle != 2;
    wire new_reference_valid = cycle == 2;
    wire quantity_valid = 1'b1;
    wire price_valid = cycle == 2;
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
        if (cycle == 6 || cycle == 14) begin
            assert(book_valid && !recovery_required);
            assert(commit_valid);
            assert(commit_mold_sequence == 64'h0102030405060708);
            assert(commit_itch_timestamp == 48'h112233445566);
            assert(commit_ask_total == 0 && ask_total == 0);
            if (cycle == 6) assert(bid_total == 13 && commit_bid_total == 13);
            if (cycle == 14) assert(bid_total == 9 && commit_bid_total == 9);
        end
        if (cycle == 7) assert(debug_found && debug_price == 32'h10203040 && debug_remaining_quantity == 13);
        if (cycle == 15) assert(debug_found && debug_price == 32'h10203040 && debug_remaining_quantity == 9);
        cover(cycle == 15 && commit_valid && debug_found);
    end
endmodule
