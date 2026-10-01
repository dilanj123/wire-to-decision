module order_book_safety;
    (* gclk *) wire clk;
    (* anyseq *) logic rst, rearm, upstream_recovery_required;
    (* anyseq *) logic event_valid, commit_ready, error_ready;
    (* anyseq *) logic [2:0] event_kind;
    (* anyseq *) logic [7:0] source_type;
    (* anyseq *) logic [63:0] mold_sequence, old_order_reference, new_order_reference;
    (* anyseq *) logic [47:0] itch_timestamp;
    (* anyseq *) logic [15:0] stock_locate;
    (* anyseq *) logic [31:0] quantity, price;
    (* anyseq *) logic side, old_reference_valid, new_reference_valid;
    (* anyseq *) logic quantity_valid, price_valid, side_valid;
    (* anyseq *) logic [63:0] debug_reference;
    wire event_ready, commit_valid, book_valid, recovery_required, error_valid;
    wire [63:0] commit_mold_sequence;
    wire [47:0] commit_itch_timestamp, commit_bid_total, commit_ask_total;
    wire [47:0] bid_total, ask_total;
    wire [3:0] error_code;
    wire debug_found, debug_side, debug_way;
    wire [31:0] debug_price, debug_remaining_quantity;
    wire [15:0] last_accepted_stock_locate;
    wire [8:0] debug_set_index;

    wire_order_book #(.NUM_SETS(2)) dut (.*);

    reg past_valid = 0;
    always @(posedge clk) past_valid <= 1;
    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (past_valid && !$past(rst || rearm)) begin
            if ($past(commit_valid && !commit_ready)) begin
                assert(commit_valid);
                assert(commit_mold_sequence == $past(commit_mold_sequence));
                assert(commit_itch_timestamp == $past(commit_itch_timestamp));
                assert(commit_bid_total == $past(commit_bid_total));
                assert(commit_ask_total == $past(commit_ask_total));
            end
            if ($past(error_valid && !error_ready)) begin
                assert(error_valid);
                assert(error_code == $past(error_code));
            end
            if ($past(recovery_required)) begin
                assert(recovery_required);
                assert(!event_ready);
            end
            if ($past(upstream_recovery_required))
                assert(!event_ready);
        end
        if (past_valid && $past(rearm || rst)) begin
            assert(book_valid);
            assert(!recovery_required);
            assert(bid_total == 0 && ask_total == 0);
            assert(!commit_valid && !error_valid);
        end
    end

    // Legal upstream source stability. Consumer readiness remains arbitrary.
    always @(posedge clk) if (past_valid && $past(!rst && !rearm && event_valid && !event_ready)) begin
        assume(event_valid);
        assume(event_kind == $past(event_kind));
        assume(source_type == $past(source_type));
        assume(mold_sequence == $past(mold_sequence));
        assume(itch_timestamp == $past(itch_timestamp));
        assume(old_order_reference == $past(old_order_reference));
        assume(new_order_reference == $past(new_order_reference));
        assume(quantity == $past(quantity));
        assume(price == $past(price));
        assume(side == $past(side));
        assume(old_reference_valid == $past(old_reference_valid));
        assume(new_reference_valid == $past(new_reference_valid));
        assume(quantity_valid == $past(quantity_valid));
        assume(price_valid == $past(price_valid));
        assume(side_valid == $past(side_valid));
    end
endmodule
