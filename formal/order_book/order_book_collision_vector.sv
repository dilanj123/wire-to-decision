module order_book_collision_vector;
    (* gclk *) wire clk;
    reg [5:0] cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;
    wire rst = cycle == 0;
    wire rearm = 0, upstream_recovery_required = 0;
    wire event_valid = (cycle == 2) || (cycle == 6) || (cycle == 10) || (cycle == 14);
    wire [2:0] event_kind = cycle == 14 ? 3'd5 : 3'd0;
    wire [7:0] source_type = cycle == 14 ? 8'h55 : 8'h41;
    wire [63:0] mold_sequence = 64'h55;
    wire [47:0] itch_timestamp = 48'h66;
    wire [15:0] stock_locate = 16'h77;
    wire [63:0] old_order_reference = 64'h10;
    wire [63:0] new_order_reference = cycle < 6 ? 64'h10 :
                                         cycle < 10 ? 64'h11 :
                                         cycle < 14 ? 64'h40211 : 64'h80411;
    wire [31:0] quantity = 32'd5, price = 32'd99;
    wire side = cycle == 2;
    wire old_reference_valid = cycle == 14;
    wire new_reference_valid = 1;
    wire quantity_valid = 1, price_valid = 1, side_valid = cycle != 14;
    wire commit_ready = 1, error_ready = 0;
    wire event_ready, commit_valid, book_valid, recovery_required, error_valid;
    wire [63:0] commit_mold_sequence;
    wire [47:0] commit_itch_timestamp, commit_bid_total, commit_ask_total;
    wire [47:0] bid_total, ask_total;
    wire [3:0] error_code;
    wire [63:0] debug_reference = cycle == 16 ? 64'h10 :
        cycle == 17 ? 64'h11 : cycle == 18 ? 64'h40211 :
        cycle == 19 ? 64'h80411 : 64'h10;
    wire debug_found, debug_side, debug_way;
    wire [31:0] debug_price, debug_remaining_quantity;
    wire [15:0] last_accepted_stock_locate;
    wire [8:0] debug_set_index;
    wire_order_book #(.NUM_SETS(2)) dut (.*);
    always @(posedge clk) begin
        if (cycle == 16) begin
            assert(!book_valid && recovery_required);
            assert(error_valid && error_code == 4'd2);
            assert(bid_total == 10 && ask_total == 5);
            assert(debug_found && debug_remaining_quantity == 5);
        end
        if (cycle == 17 || cycle == 18) begin
            assert(!event_ready && error_valid && error_code == 4'd2);
            assert(debug_found && debug_remaining_quantity == 5);
        end
        if (cycle == 19) begin
            assert(!event_ready && error_valid && error_code == 4'd2);
            assert(!debug_found);
            assert(bid_total == 10 && ask_total == 5);
        end
        cover(cycle == 16 && error_valid && debug_found);
    end
endmodule
