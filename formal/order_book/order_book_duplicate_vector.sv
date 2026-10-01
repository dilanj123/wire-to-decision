module order_book_duplicate_vector;
    (* gclk *) wire clk;
    reg [3:0] cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;
    wire rst = cycle == 0, rearm = 0, upstream_recovery_required = 0;
    wire event_valid = (cycle == 2) || (cycle == 6);
    wire [2:0] event_kind = 0;
    wire [7:0] source_type = 8'h41;
    wire [63:0] mold_sequence = cycle, old_order_reference = 0, new_order_reference = 64'h33;
    wire [47:0] itch_timestamp = cycle;
    wire [15:0] stock_locate = 0;
    wire [31:0] quantity = 5, price = 12;
    wire side = 1, old_reference_valid = 0, new_reference_valid = 1;
    wire quantity_valid = 1, price_valid = 1, side_valid = 1;
    wire commit_ready = 1, error_ready = 0;
    wire event_ready, commit_valid, book_valid, recovery_required, error_valid;
    wire [63:0] commit_mold_sequence;
    wire [47:0] commit_itch_timestamp, commit_bid_total, commit_ask_total;
    wire [47:0] bid_total, ask_total;
    wire [3:0] error_code;
    wire [63:0] debug_reference = 64'h33;
    wire debug_found, debug_side, debug_way;
    wire [31:0] debug_price, debug_remaining_quantity;
    wire [15:0] last_accepted_stock_locate;
    wire [8:0] debug_set_index;
    wire_order_book #(.NUM_SETS(2)) dut (.*);
    always @(posedge clk) begin
        if (cycle == 8) begin
            assert(!book_valid && recovery_required);
            assert(error_valid && error_code == 4'd1 && !commit_valid);
            assert(debug_found && debug_remaining_quantity == 5 && debug_price == 12);
            assert(bid_total == 0 && ask_total == 5);
        end
        if (cycle > 8) assert(!event_ready && !commit_valid && error_valid);
        cover(cycle == 8 && error_valid && debug_found);
    end
endmodule
