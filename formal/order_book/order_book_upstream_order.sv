module order_book_upstream_order;
    (* gclk *) wire clk;
    reg [3:0] cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;
    wire rst = cycle == 0, rearm = 0;
    wire upstream_recovery_required = cycle >= 3;
    wire event_valid = cycle == 2;
    wire [2:0] event_kind = 0;
    wire [7:0] source_type = 8'h41;
    wire [63:0] mold_sequence = 64'h12345678, old_order_reference = 0, new_order_reference = 64'h1;
    wire [47:0] itch_timestamp = 48'h102030405060;
    wire [15:0] stock_locate = 16'h1234;
    wire [31:0] quantity = 9, price = 77;
    wire side = 0, old_reference_valid = 0, new_reference_valid = 1;
    wire quantity_valid = 1, price_valid = 1, side_valid = 1;
    wire commit_ready = 0, error_ready = 0;
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
        if (cycle == 4) begin
            assert(!event_ready && !book_valid && recovery_required);
            assert(commit_valid && commit_bid_total == 9 && bid_total == 9);
            assert(commit_mold_sequence == mold_sequence);
            assert(commit_itch_timestamp == itch_timestamp);
            assert(debug_found && debug_remaining_quantity == 9);
        end
        if (cycle > 4) begin
            assert(!event_ready && recovery_required);
            assert(commit_valid && commit_bid_total == 9 && bid_total == 9);
        end
        cover(cycle == 4 && commit_valid && recovery_required);
    end
endmodule
