module order_book_hash_vectors;
    (* gclk *) wire clk;
    reg [2:0] cycle = 0;
    always @(posedge clk) cycle <= cycle + 1'b1;
    wire rst = 1'b1, rearm = 1'b0, upstream_recovery_required = 1'b0;
    wire event_valid = 1'b0, commit_ready = 1'b1, error_ready = 1'b1;
    wire [2:0] event_kind = 0;
    wire [7:0] source_type = 0;
    wire [63:0] mold_sequence = 0, old_order_reference = 0, new_order_reference = 0;
    wire [47:0] itch_timestamp = 0;
    wire [15:0] stock_locate = 0;
    wire [31:0] quantity = 0, price = 0;
    wire side = 0, old_reference_valid = 0, new_reference_valid = 0;
    wire quantity_valid = 0, price_valid = 0, side_valid = 0;
    wire [63:0] debug_reference = cycle == 0 ? 64'h1 :
        cycle == 1 ? 64'h200 : cycle == 2 ? 64'h40000 :
        cycle == 3 ? 64'h8000000000000000 : 64'hFFFFFFFFFFFFFFFF;
    wire event_ready, commit_valid, book_valid, recovery_required, error_valid;
    wire [63:0] commit_mold_sequence;
    wire [47:0] commit_itch_timestamp, commit_bid_total, commit_ask_total;
    wire [47:0] bid_total, ask_total;
    wire [3:0] error_code;
    wire debug_found, debug_side, debug_way;
    wire [31:0] debug_price, debug_remaining_quantity;
    wire [15:0] last_accepted_stock_locate;
    wire [8:0] debug_set_index;
    wire_order_book dut (.*);
    always @(posedge clk) begin
        if (cycle < 3) assert(debug_set_index == 9'd1);
        if (cycle == 3) assert(debug_set_index == 9'd1);
        if (cycle == 4) assert(debug_set_index == 9'h1FE);
        cover(cycle == 4 && debug_set_index == 9'h1FE);
    end
endmodule
