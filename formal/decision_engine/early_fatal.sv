module early_fatal;
    (* gclk *) wire clk;
    reg [2:0] phase = 0;
    wire rst = (phase == 0);
    wire rearm = 1'b0;
    wire upstream_recovery_required = (phase >= 1);
    wire event_valid = (phase == 1);
    wire event_ready;
    wire commit_valid, commit_ready;
    wire [63:0] commit_mold_sequence;
    wire [47:0] commit_itch_timestamp, commit_bid_total, commit_ask_total;
    wire decision_valid, decision_action;
    wire [63:0] decision_mold_sequence;
    wire [47:0] decision_itch_timestamp;
    wire signed [48:0] decision_signed_imbalance, previous_imbalance;
    wire [31:0] remaining_budget, decision_count;
    wire book_valid, book_recovery_required;
    wire [47:0] bid_total, ask_total;
    wire error_valid;
    wire [3:0] error_code;
    wire debug_found, debug_side, debug_way;
    wire [31:0] debug_price, debug_remaining_quantity;
    wire [15:0] last_accepted_stock_locate;
    wire [8:0] debug_set_index;

    wire_order_book #(.NUM_SETS(2)) book (
        .clk(clk), .rst(rst), .rearm(rearm),
        .upstream_recovery_required(upstream_recovery_required),
        .event_valid(event_valid), .event_ready(event_ready), .event_kind(3'd0),
        .source_type(8'h41), .mold_sequence(64'h1), .itch_timestamp(48'h2),
        .stock_locate(16'h3), .old_order_reference(64'd0),
        .new_order_reference(64'h55), .quantity(32'd5), .price(32'd10), .side(1'b0),
        .old_reference_valid(1'b0), .new_reference_valid(1'b1),
        .quantity_valid(1'b1), .price_valid(1'b1), .side_valid(1'b1),
        .commit_valid(commit_valid), .commit_ready(commit_ready),
        .commit_mold_sequence(commit_mold_sequence),
        .commit_itch_timestamp(commit_itch_timestamp),
        .commit_bid_total(commit_bid_total), .commit_ask_total(commit_ask_total),
        .book_valid(book_valid), .recovery_required(book_recovery_required),
        .bid_total(bid_total), .ask_total(ask_total),
        .error_valid(error_valid), .error_ready(1'b1), .error_code(error_code),
        .debug_reference(64'h55), .debug_found(debug_found), .debug_price(debug_price),
        .debug_remaining_quantity(debug_remaining_quantity), .debug_side(debug_side),
        .last_accepted_stock_locate(last_accepted_stock_locate),
        .debug_set_index(debug_set_index), .debug_way(debug_way));

    wire_decision_engine decision (
        .clk(clk), .rst(rst), .rearm(rearm),
        .cfg_decision_threshold(48'd5), .cfg_initial_budget(32'd2),
        .decision_enable(1'b1), .commit_valid(commit_valid), .commit_ready(commit_ready),
        .commit_mold_sequence(commit_mold_sequence),
        .commit_itch_timestamp(commit_itch_timestamp),
        .commit_bid_total(commit_bid_total), .commit_ask_total(commit_ask_total),
        .decision_valid(decision_valid), .decision_ready(1'b1),
        .decision_action(decision_action),
        .decision_mold_sequence(decision_mold_sequence),
        .decision_itch_timestamp(decision_itch_timestamp),
        .decision_signed_imbalance(decision_signed_imbalance),
        .previous_imbalance(previous_imbalance), .remaining_budget(remaining_budget),
        .decision_count(decision_count));

    always @(posedge clk) begin
        if ($initstate) assume(phase == 0);
        if (phase == 0)
            phase <= 1;
        else
            phase <= 2;

        if (phase >= 2) begin
            assert(!book_valid);
            assert(book_recovery_required);
            assert(!event_ready);
            assert(!commit_valid);
            assert(!decision_valid);
            assert(bid_total == 0 && ask_total == 0);
            assert(remaining_budget == 32'd2 && decision_count == 0);
        end
    end
endmodule
