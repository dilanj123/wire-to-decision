module order_book_unknown_vector;
    (* gclk *) wire clk;
    reg [3:0] cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;
    wire rst = cycle == 0, rearm = 0, upstream_recovery_required = 0;
    wire event_valid = cycle == 2;
    wire [2:0] event_kind = 3'd1;
    wire [7:0] source_type = 8'h45;
    wire [63:0] mold_sequence = 64'h77, old_order_reference = 64'h55, new_order_reference = 0;
    wire [47:0] itch_timestamp = 48'h88;
    wire [15:0] stock_locate = 0;
    wire [31:0] quantity = 1, price = 0;
    wire side = 0, old_reference_valid = 1, new_reference_valid = 0;
    wire quantity_valid = 1, price_valid = 0, side_valid = 0;
    wire commit_ready = 1, error_ready = 0;
    wire event_ready, commit_valid, book_valid, recovery_required, error_valid;
    wire [63:0] commit_mold_sequence;
    wire [47:0] commit_itch_timestamp, commit_bid_total, commit_ask_total;
    wire [47:0] bid_total, ask_total;
    wire [3:0] error_code;
    wire [63:0] debug_reference = 64'h55;
    wire debug_found, debug_side, debug_way;
    wire [31:0] debug_price, debug_remaining_quantity;
    wire [15:0] last_accepted_stock_locate;
    wire [8:0] debug_set_index;
    wire_order_book #(.NUM_SETS(2)) dut (.*);
    always @(posedge clk) begin
        if (cycle == 4) begin
            assert(!commit_valid && error_valid && error_code == 4'd3);
            assert(!book_valid && recovery_required && !event_ready);
            assert(bid_total == 0 && ask_total == 0 && !debug_found);
        end
        if (cycle > 4) begin
            assert(!event_ready && !commit_valid);
            assert(bid_total == 0 && ask_total == 0 && !debug_found);
        end
        cover(cycle == 4 && error_valid && recovery_required);
    end
endmodule
