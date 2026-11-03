// Bounded WIRE-D006/WIRE-D009 order store and side aggregates.
// Production default: exactly 512 sets x 2 ways. The packed set-row RAM has
// synchronous read access so ECP5 synthesis can map order data into EBRs.
module wire_order_book #(
    parameter integer NUM_SETS = 512
) (
    input  logic        clk,
    input  logic        rst,
    input  logic        rearm,
    input  logic        upstream_recovery_required,
    input  logic        event_valid,
    output logic        event_ready,
    input  logic [2:0]  event_kind,
    input  logic [7:0]  source_type,
    input  logic [63:0] mold_sequence,
    input  logic [47:0] itch_timestamp,
    input  logic [15:0] stock_locate,
    input  logic [63:0] old_order_reference,
    input  logic [63:0] new_order_reference,
    input  logic [31:0] quantity,
    input  logic [31:0] price,
    input  logic        side,
    input  logic        old_reference_valid,
    input  logic        new_reference_valid,
    input  logic        quantity_valid,
    input  logic        price_valid,
    input  logic        side_valid,
    output logic        commit_valid,
    input  logic        commit_ready,
    output logic [63:0] commit_mold_sequence,
    output logic [47:0] commit_itch_timestamp,
    output logic [47:0] commit_bid_total,
    output logic [47:0] commit_ask_total,
    output logic        book_valid,
    output logic        recovery_required,
    output logic [47:0] bid_total,
    output logic [47:0] ask_total,
    output logic        error_valid,
    input  logic        error_ready,
    output logic [3:0]  error_code,
    input  logic [63:0] debug_reference,
    output logic        debug_found,
    output logic [31:0] debug_price,
    output logic [31:0] debug_remaining_quantity,
    output logic        debug_side,
    output logic [15:0] last_accepted_stock_locate,
    output logic [8:0]  debug_set_index,
    output logic        debug_way
);
    localparam integer SET_BITS = $clog2(NUM_SETS);
    localparam integer ROW_BITS = 258; // two {ref64, price32, qty32, side1} entries
    localparam logic [3:0] ERR_EVENT_CONTRACT = 4'd0;
    localparam logic [3:0] ERR_DUPLICATE_REFERENCE = 4'd1;
    localparam logic [3:0] ERR_COLLISION_CAPACITY = 4'd2;
    localparam logic [3:0] ERR_UNKNOWN_REFERENCE = 4'd3;
    localparam logic [3:0] ERR_OVER_EXECUTE = 4'd4;
    localparam logic [3:0] ERR_OVER_CANCEL = 4'd5;
    localparam logic [3:0] ERR_NEW_REFERENCE_CONFLICT = 4'd6;
    localparam logic [3:0] ERR_AGGREGATE_RANGE = 4'd7;
    localparam logic [3:0] ERR_UPSTREAM_FATAL = 4'd8;

    typedef enum logic [2:0] {
        S_IDLE, S_READ_PRIMARY, S_READ_SECONDARY, S_EVAL,
        S_WRITE_SINGLE, S_WRITE_OLD, S_WRITE_NEW
    } state_t;
    state_t state_q;

    // Data is deliberately not reset. A set's resettable valid bits guard all
    // use of stale RAM contents after reset/rearm.
    logic [ROW_BITS-1:0] order_row_mem [0:NUM_SETS-1];
    logic [1:0] order_valid_mem [0:NUM_SETS-1];
    logic [ROW_BITS-1:0] primary_row_q, secondary_row_q;
    logic [1:0] primary_valid_q, secondary_valid_q;
    logic [ROW_BITS-1:0] write_row_q;
    logic [1:0] write_valid_q;
    logic [47:0] write_bid_total_q, write_ask_total_q;
    logic write_old_way_q;

    logic [47:0] bid_total_q, ask_total_q;
    logic book_valid_q, recovery_q;
    logic commit_valid_q, error_valid_q;
    logic [3:0] error_code_q;
    logic [63:0] commit_sequence_q;
    logic [47:0] commit_timestamp_q, commit_bid_q, commit_ask_q;
    logic [15:0] accepted_stock_locate_q;

    logic [2:0] event_kind_q;
    logic [63:0] event_sequence_q, old_reference_q, new_reference_q;
    logic [47:0] event_timestamp_q;
    logic [31:0] quantity_q, price_q;
    logic side_q, event_contract_q;
    logic [8:0] primary_hash_q, secondary_hash_q;
    logic [8:0] old_input_hash, new_input_hash;
    logic replace_cross_set_q;

    logic [ROW_BITS-1:0] debug_row_q;
    logic [1:0] debug_valid_q;
    logic [63:0] debug_reference_q;
    logic debug_match0, debug_match1;

    logic [ROW_BITS-1:0] candidate_row;
    logic [1:0] candidate_valid;
    logic [ROW_BITS-1:0] replacement_row;
    logic [1:0] replacement_valid;
    logic old_found, new_found;
    logic [31:0] old_remaining;
    logic old_side;
    integer old_way, free_way;
    logic eval_error;
    logic [3:0] eval_error_code;
    logic [47:0] next_bid_total, next_ask_total;
    logic signed [48:0] aggregate_candidate, aggregate_delta;
    logic aggregate_on_bid;
    logic [31:0] new_remaining;
    logic [8:0] debug_hash_comb;

    function automatic logic [8:0] order_hash(input logic [63:0] order_ref);
        order_hash = order_ref[8:0] ^ order_ref[17:9] ^ order_ref[26:18] ^
                     order_ref[35:27] ^ order_ref[44:36] ^ order_ref[53:45] ^
                     order_ref[62:54] ^ {8'b0, order_ref[63]};
    endfunction

    function automatic logic event_fields_valid(
        input logic [2:0] kind, input logic [7:0] source,
        input logic old_v, input logic new_v, input logic qty_v,
        input logic price_v, input logic side_v, input logic [31:0] qty
    );
        case (kind)
            3'd0: event_fields_valid = ((source == 8'h41) || (source == 8'h46)) &&
                !old_v && new_v && qty_v && price_v && side_v && (qty != 0);
            3'd1: event_fields_valid = source == 8'h45 && old_v && !new_v && qty_v && !price_v && !side_v && qty != 0;
            3'd2: event_fields_valid = source == 8'h43 && old_v && !new_v && qty_v && !price_v && !side_v && qty != 0;
            3'd3: event_fields_valid = source == 8'h58 && old_v && !new_v && qty_v && !price_v && !side_v && qty != 0;
            3'd4: event_fields_valid = source == 8'h44 && old_v && !new_v && !qty_v && !price_v && !side_v;
            3'd5: event_fields_valid = source == 8'h55 && old_v && new_v && qty_v && price_v && !side_v && qty != 0;
            default: event_fields_valid = 1'b0;
        endcase
    endfunction

    function automatic logic [63:0] row_reference(input logic [ROW_BITS-1:0] row, input integer way);
        row_reference = 64'(row >> (way * 129 + 65));
    endfunction
    function automatic logic [31:0] row_price(input logic [ROW_BITS-1:0] row, input integer way);
        row_price = 32'(row >> (way * 129 + 33));
    endfunction
    function automatic logic [31:0] row_quantity(input logic [ROW_BITS-1:0] row, input integer way);
        row_quantity = 32'(row >> (way * 129 + 1));
    endfunction
    function automatic logic row_side(input logic [ROW_BITS-1:0] row, input integer way);
        row_side = 1'(row >> (way * 129));
    endfunction
    function automatic logic [128:0] make_entry(
        input logic [63:0] ref_value, input logic [31:0] price_value,
        input logic [31:0] qty_value, input logic side_value
    );
        make_entry = {ref_value, price_value, qty_value, side_value};
    endfunction

    assign event_ready = state_q == S_IDLE && book_valid_q && !recovery_q &&
                         !upstream_recovery_required && !commit_valid_q && !error_valid_q;
    assign commit_valid = commit_valid_q;
    assign commit_mold_sequence = commit_sequence_q;
    assign commit_itch_timestamp = commit_timestamp_q;
    assign commit_bid_total = commit_bid_q;
    assign commit_ask_total = commit_ask_q;
    assign book_valid = book_valid_q;
    assign recovery_required = recovery_q;
    assign bid_total = bid_total_q;
    assign ask_total = ask_total_q;
    assign error_valid = error_valid_q;
    assign error_code = error_code_q;
    assign last_accepted_stock_locate = accepted_stock_locate_q;
    assign debug_hash_comb = order_hash(debug_reference);
    assign old_input_hash = order_hash(old_order_reference);
    assign new_input_hash = order_hash(new_order_reference);
    assign debug_set_index = debug_hash_comb;
    assign debug_match0 = debug_valid_q[0] && row_reference(debug_row_q, 0) == debug_reference_q;
    assign debug_match1 = debug_valid_q[1] && row_reference(debug_row_q, 1) == debug_reference_q;

    // Diagnostics are a one-cycle synchronous lookup and are available only
    // while idle. In particular, a multi-cycle REPLACE is never observable.
    always_comb begin
        debug_found = 1'b0;
        debug_price = 32'd0;
        debug_remaining_quantity = 32'd0;
        debug_side = 1'b0;
        debug_way = 1'b0;
        if (state_q == S_IDLE) begin
            if (debug_match0) begin
                debug_found = 1'b1;
                debug_price = row_price(debug_row_q, 0);
                debug_remaining_quantity = row_quantity(debug_row_q, 0);
            end else if (debug_match1) begin
                debug_found = 1'b1;
                debug_price = row_price(debug_row_q, 1);
                debug_remaining_quantity = row_quantity(debug_row_q, 1);
                debug_way = 1'b1;
            end
            if (debug_match0) debug_side = row_side(debug_row_q, 0);
            else if (debug_match1) debug_side = row_side(debug_row_q, 1);
        end
    end

    // Form the prospective mutation solely from registered RAM read results.
    always_comb begin
        candidate_row = primary_row_q;
        candidate_valid = primary_valid_q;
        if (replace_cross_set_q) begin
            // Primary is old set; secondary is destination set for U.
            candidate_row = secondary_row_q;
            candidate_valid = secondary_valid_q;
        end
        old_found = 1'b0;
        new_found = 1'b0;
        old_way = -1;
        free_way = -1;
        old_remaining = 32'd0;
        old_side = 1'b0;
        for (integer way = 0; way < 2; way = way + 1) begin
            if (primary_valid_q[way] && row_reference(primary_row_q, way) == old_reference_q) begin
                old_found = 1'b1;
                old_way = way;
                old_remaining = row_quantity(primary_row_q, way);
                old_side = row_side(primary_row_q, way);
            end
            if (candidate_valid[way] && row_reference(candidate_row, way) == new_reference_q) begin
                new_found = 1'b1;
            end
            if (!candidate_valid[way] && free_way == -1)
                free_way = way;
        end

        eval_error = 1'b0;
        eval_error_code = ERR_EVENT_CONTRACT;
        next_bid_total = bid_total_q;
        next_ask_total = ask_total_q;
        aggregate_candidate = 49'sd0;
        aggregate_delta = 49'sd0;
        aggregate_on_bid = 1'b0;
        new_remaining = 32'd0;
        replacement_row = candidate_row;
        replacement_valid = candidate_valid;

        if (!event_contract_q) begin
            eval_error = 1'b1;
            eval_error_code = ERR_EVENT_CONTRACT;
        end else begin
            case (event_kind_q)
                3'd0: begin
                    if (new_found) begin
                        eval_error = 1'b1;
                        eval_error_code = ERR_DUPLICATE_REFERENCE;
                    end else if (free_way == -1) begin
                        eval_error = 1'b1;
                        eval_error_code = ERR_COLLISION_CAPACITY;
                    end else begin
                        aggregate_delta = $signed({17'b0, quantity_q});
                        aggregate_on_bid = side_q == 1'b0;
                    end
                end
                3'd1, 3'd2, 3'd3, 3'd4: begin
                    if (!old_found) begin
                        eval_error = 1'b1;
                        eval_error_code = ERR_UNKNOWN_REFERENCE;
                    end else if (event_kind_q != 3'd4 && quantity_q > old_remaining) begin
                        eval_error = 1'b1;
                        eval_error_code = event_kind_q == 3'd3 ? ERR_OVER_CANCEL : ERR_OVER_EXECUTE;
                    end else begin
                        aggregate_delta = event_kind_q == 3'd4 ?
                            -$signed({17'b0, old_remaining}) : -$signed({17'b0, quantity_q});
                        aggregate_on_bid = old_side == 1'b0;
                        new_remaining = event_kind_q == 3'd4 ? 32'd0 : old_remaining - quantity_q;
                    end
                end
                3'd5: begin
                    if (!old_found) begin
                        eval_error = 1'b1;
                        eval_error_code = ERR_UNKNOWN_REFERENCE;
                    end else if (new_found && new_reference_q != old_reference_q) begin
                        eval_error = 1'b1;
                        eval_error_code = ERR_NEW_REFERENCE_CONFLICT;
                    end else if (free_way == -1 && !(primary_hash_q == secondary_hash_q && old_way >= 0)) begin
                        eval_error = 1'b1;
                        eval_error_code = ERR_COLLISION_CAPACITY;
                    end else begin
                        aggregate_delta = $signed({17'b0, quantity_q}) - $signed({17'b0, old_remaining});
                        aggregate_on_bid = old_side == 1'b0;
                    end
                end
                default: begin
                    eval_error = 1'b1;
                    eval_error_code = ERR_EVENT_CONTRACT;
                end
            endcase
        end

        if (!eval_error) begin
            aggregate_candidate = $signed({1'b0, aggregate_on_bid ? bid_total_q : ask_total_q}) + aggregate_delta;
            if (aggregate_candidate < 0 || aggregate_candidate > 49'sh0FFFFFFFFFFFF) begin
                eval_error = 1'b1;
                eval_error_code = ERR_AGGREGATE_RANGE;
            end else if (aggregate_on_bid) next_bid_total = aggregate_candidate[47:0];
            else next_ask_total = aggregate_candidate[47:0];
        end

        if (!eval_error) begin
            case (event_kind_q)
                3'd0: begin
                    if (free_way == 0) replacement_row[128:0] = make_entry(new_reference_q, price_q, quantity_q, side_q);
                    else replacement_row[257:129] = make_entry(new_reference_q, price_q, quantity_q, side_q);
                    replacement_valid[free_way] = 1'b1;
                end
                3'd1, 3'd2, 3'd3, 3'd4: begin
                    if (new_remaining == 0) replacement_valid[old_way] = 1'b0;
                    else if (old_way == 0) replacement_row[128:0] = make_entry(old_reference_q,
                        row_price(primary_row_q, 0), new_remaining, old_side);
                    else replacement_row[257:129] = make_entry(old_reference_q,
                        row_price(primary_row_q, 1), new_remaining, old_side);
                end
                3'd5: begin
                    if (!replace_cross_set_q && new_reference_q == old_reference_q)
                        free_way = old_way;
                    // Removal and insertion are prepared together in the row
                    // image; cross-set removal is committed in its own hidden
                    // write stage before the destination row is published.
                    if (!replace_cross_set_q) replacement_valid[old_way] = 1'b0;
                    if (free_way == 0) replacement_row[128:0] = make_entry(new_reference_q, price_q, quantity_q, old_side);
                    else replacement_row[257:129] = make_entry(new_reference_q, price_q, quantity_q, old_side);
                    replacement_valid[free_way] = 1'b1;
                end
                default: begin end
            endcase
        end
    end

    always_ff @(posedge clk) begin
        if (rst || rearm) begin
            state_q <= S_IDLE;
            bid_total_q <= 48'd0;
            ask_total_q <= 48'd0;
            book_valid_q <= 1'b1;
            recovery_q <= 1'b0;
            commit_valid_q <= 1'b0;
            error_valid_q <= 1'b0;
            error_code_q <= ERR_EVENT_CONTRACT;
            commit_sequence_q <= 64'd0;
            commit_timestamp_q <= 48'd0;
            commit_bid_q <= 48'd0;
            commit_ask_q <= 48'd0;
            accepted_stock_locate_q <= 16'd0;
            primary_row_q <= '0;
            secondary_row_q <= '0;
            primary_valid_q <= 2'b0;
            secondary_valid_q <= 2'b0;
            write_row_q <= '0;
            write_valid_q <= 2'b0;
            write_bid_total_q <= 48'd0;
            write_ask_total_q <= 48'd0;
            write_old_way_q <= 1'b0;
            debug_row_q <= '0;
            debug_valid_q <= 2'b0;
            debug_reference_q <= 64'd0;
            event_kind_q <= 3'd0;
            event_sequence_q <= 64'd0;
            event_timestamp_q <= 48'd0;
            old_reference_q <= 64'd0;
            new_reference_q <= 64'd0;
            quantity_q <= 32'd0;
            price_q <= 32'd0;
            side_q <= 1'b0;
            event_contract_q <= 1'b0;
            primary_hash_q <= 9'd0;
            secondary_hash_q <= 9'd0;
            replace_cross_set_q <= 1'b0;
            for (integer set_index = 0; set_index < NUM_SETS; set_index = set_index + 1)
                order_valid_mem[set_index] <= 2'b0;
        end else begin
            if (commit_valid_q && commit_ready) commit_valid_q <= 1'b0;
            if (error_valid_q && error_ready) error_valid_q <= 1'b0;

            // Single synchronous read port. Mutation reads take priority;
            // otherwise the diagnostic port samples one requested hash/set.
            if (state_q == S_READ_PRIMARY) begin
                primary_row_q <= order_row_mem[primary_hash_q[SET_BITS-1:0]];
                primary_valid_q <= order_valid_mem[primary_hash_q[SET_BITS-1:0]];
            end else if (state_q == S_READ_SECONDARY) begin
                secondary_row_q <= order_row_mem[secondary_hash_q[SET_BITS-1:0]];
                secondary_valid_q <= order_valid_mem[secondary_hash_q[SET_BITS-1:0]];
            end else if (state_q == S_IDLE && !(event_valid && event_ready)) begin
                debug_row_q <= order_row_mem[debug_hash_comb[SET_BITS-1:0]];
                debug_valid_q <= order_valid_mem[debug_hash_comb[SET_BITS-1:0]];
                debug_reference_q <= debug_reference;
            end

            if (upstream_recovery_required && !recovery_q) begin
                recovery_q <= 1'b1;
                book_valid_q <= 1'b0;
                if (state_q == S_IDLE) begin
                    error_code_q <= ERR_UPSTREAM_FATAL;
                    error_valid_q <= 1'b1;
                end
            end

            case (state_q)
                S_IDLE: begin
                    if (event_valid && event_ready) begin
                        event_kind_q <= event_kind;
                        event_sequence_q <= mold_sequence;
                        event_timestamp_q <= itch_timestamp;
                        accepted_stock_locate_q <= stock_locate;
                        old_reference_q <= old_order_reference;
                        new_reference_q <= new_order_reference;
                        quantity_q <= quantity;
                        price_q <= price;
                        side_q <= side;
                        event_contract_q <= event_fields_valid(event_kind, source_type,
                            old_reference_valid, new_reference_valid, quantity_valid,
                            price_valid, side_valid, quantity);
                        primary_hash_q <= event_kind == 3'd0 ? new_input_hash : old_input_hash;
                        secondary_hash_q <= new_input_hash;
                        replace_cross_set_q <= event_kind == 3'd5 &&
                            old_input_hash[SET_BITS-1:0] != new_input_hash[SET_BITS-1:0];
                        state_q <= S_READ_PRIMARY;
                    end
                end
                S_READ_PRIMARY: begin
                    if (replace_cross_set_q) state_q <= S_READ_SECONDARY;
                    else state_q <= S_EVAL;
                end
                S_READ_SECONDARY: state_q <= S_EVAL;
                S_EVAL: begin
                    if (eval_error) begin
                        state_q <= S_IDLE;
                        book_valid_q <= 1'b0;
                        recovery_q <= 1'b1;
                        error_code_q <= eval_error_code;
                        error_valid_q <= 1'b1;
                    end else begin
                        // Register the complete, validated write plan here.
                        // The following write state no longer has a combinational
                        // path from the EBR output through lookup/arithmetic.
                        write_row_q <= replacement_row;
                        write_valid_q <= replacement_valid;
                        write_bid_total_q <= next_bid_total;
                        write_ask_total_q <= next_ask_total;
                        write_old_way_q <= old_way[0];
                        if (event_kind_q == 3'd5 && replace_cross_set_q)
                            state_q <= S_WRITE_OLD;
                        else
                            state_q <= S_WRITE_SINGLE;
                    end
                end
                S_WRITE_SINGLE: begin
                    order_row_mem[primary_hash_q[SET_BITS-1:0]] <= write_row_q;
                    order_valid_mem[primary_hash_q[SET_BITS-1:0]] <= write_valid_q;
                    bid_total_q <= write_bid_total_q;
                    ask_total_q <= write_ask_total_q;
                    commit_sequence_q <= event_sequence_q;
                    commit_timestamp_q <= event_timestamp_q;
                    commit_bid_q <= write_bid_total_q;
                    commit_ask_q <= write_ask_total_q;
                    commit_valid_q <= 1'b1;
                    state_q <= S_IDLE;
                    if (upstream_recovery_required) begin
                        book_valid_q <= 1'b0;
                        recovery_q <= 1'b1;
                        error_code_q <= ERR_UPSTREAM_FATAL;
                        error_valid_q <= 1'b1;
                    end
                end
                S_WRITE_OLD: begin
                    // Hide diagnostics until both writes complete. No event,
                    // commit, or aggregate update is exposed at this stage.
                    order_valid_mem[primary_hash_q[SET_BITS-1:0]][write_old_way_q] <= 1'b0;
                    state_q <= S_WRITE_NEW;
                end
                S_WRITE_NEW: begin
                    order_row_mem[secondary_hash_q[SET_BITS-1:0]] <= write_row_q;
                    order_valid_mem[secondary_hash_q[SET_BITS-1:0]] <= write_valid_q;
                    bid_total_q <= write_bid_total_q;
                    ask_total_q <= write_ask_total_q;
                    commit_sequence_q <= event_sequence_q;
                    commit_timestamp_q <= event_timestamp_q;
                    commit_bid_q <= write_bid_total_q;
                    commit_ask_q <= write_ask_total_q;
                    commit_valid_q <= 1'b1;
                    state_q <= S_IDLE;
                    if (upstream_recovery_required) begin
                        book_valid_q <= 1'b0;
                        recovery_q <= 1'b1;
                        error_code_q <= ERR_UPSTREAM_FATAL;
                        error_valid_q <= 1'b1;
                    end
                end
                default: state_q <= S_IDLE;
            endcase
        end
    end
endmodule
