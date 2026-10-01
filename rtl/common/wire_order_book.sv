// Bounded WIRE-D006/WIRE-D009 order store and side aggregates.
// Production default: exactly 512 sets x 2 ways. Smaller NUM_SETS values
// are reserved for documented formal abstractions; the hash fold itself is
// always the frozen 9-bit WIRE-D006 function.
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

    // Read-only diagnostic lookup; it does not participate in mutation flow.
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
    localparam integer ENTRY_COUNT = NUM_SETS * 2;
    localparam logic [3:0] ERR_EVENT_CONTRACT = 4'd0;
    localparam logic [3:0] ERR_DUPLICATE_REFERENCE = 4'd1;
    localparam logic [3:0] ERR_COLLISION_CAPACITY = 4'd2;
    localparam logic [3:0] ERR_UNKNOWN_REFERENCE = 4'd3;
    localparam logic [3:0] ERR_OVER_EXECUTE = 4'd4;
    localparam logic [3:0] ERR_OVER_CANCEL = 4'd5;
    localparam logic [3:0] ERR_NEW_REFERENCE_CONFLICT = 4'd6;
    localparam logic [3:0] ERR_AGGREGATE_RANGE = 4'd7;
    localparam logic [3:0] ERR_UPSTREAM_FATAL = 4'd8;

    typedef enum logic {S_IDLE, S_EVAL} state_t;
    state_t state_q;

    logic [63:0] order_reference_q [0:ENTRY_COUNT-1];
    logic [31:0] order_price_q [0:ENTRY_COUNT-1];
    logic [31:0] order_quantity_q [0:ENTRY_COUNT-1];
    logic        order_side_q [0:ENTRY_COUNT-1];
    logic        order_valid_q [0:ENTRY_COUNT-1];

    logic [47:0] bid_total_q, ask_total_q;
    logic book_valid_q, recovery_q;
    logic commit_valid_q, error_valid_q;
    logic [3:0] error_code_q;
    logic [63:0] commit_sequence_q;
    logic [47:0] commit_timestamp_q;
    logic [47:0] commit_bid_q, commit_ask_q;
    logic [15:0] accepted_stock_locate_q;

    logic [2:0] event_kind_q;
    logic [63:0] event_sequence_q;
    logic [47:0] event_timestamp_q;
    logic [63:0] old_reference_q, new_reference_q;
    logic [31:0] quantity_q, price_q;
    logic side_q;
    logic event_contract_q;

    logic event_contract_ok;
    logic [8:0] old_hash, new_hash, debug_hash;
    integer old_base, new_base, debug_base;
    integer old_slot, free_slot;
    logic old_found, new_found, debug_match;
    logic debug_way_index;
    logic [31:0] old_remaining;
    logic old_side;
    logic eval_error;
    logic [3:0] eval_error_code;
    logic [47:0] next_bid_total, next_ask_total;
    logic signed [48:0] aggregate_candidate, aggregate_delta;
    logic aggregate_on_bid;
    logic [31:0] new_remaining;

    function automatic logic [8:0] order_hash(input logic [63:0] order_ref);
        order_hash = order_ref[8:0] ^ order_ref[17:9] ^ order_ref[26:18] ^
                     order_ref[35:27] ^ order_ref[44:36] ^ order_ref[53:45] ^
                     order_ref[62:54] ^ {8'b0, order_ref[63]};
    endfunction

    function automatic logic event_fields_valid(
        input logic [2:0] kind,
        input logic [7:0] source,
        input logic old_v,
        input logic new_v,
        input logic qty_v,
        input logic price_v,
        input logic side_v,
        input logic [31:0] qty
    );
        case (kind)
            3'd0: event_fields_valid =
                ((source == 8'h41) || (source == 8'h46)) &&
                !old_v && new_v && qty_v && price_v && side_v && (qty != 0);
            3'd1: event_fields_valid = source == 8'h45 &&
                old_v && !new_v && qty_v && !price_v && !side_v && (qty != 0);
            3'd2: event_fields_valid = source == 8'h43 &&
                old_v && !new_v && qty_v && !price_v && !side_v && (qty != 0);
            3'd3: event_fields_valid = source == 8'h58 &&
                old_v && !new_v && qty_v && !price_v && !side_v && (qty != 0);
            3'd4: event_fields_valid = source == 8'h44 &&
                old_v && !new_v && !qty_v && !price_v && !side_v;
            3'd5: event_fields_valid = source == 8'h55 &&
                old_v && new_v && qty_v && price_v && !side_v && (qty != 0);
            default: event_fields_valid = 1'b0;
        endcase
    endfunction

    assign event_contract_ok = event_fields_valid(event_kind, source_type,
        old_reference_valid, new_reference_valid, quantity_valid,
        price_valid, side_valid, quantity);
    assign event_ready = (state_q == S_IDLE) && book_valid_q && !recovery_q &&
                         !upstream_recovery_required && !commit_valid_q &&
                         !error_valid_q;

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
    assign debug_set_index = debug_hash;

    always_comb begin
        old_hash = order_hash(old_reference_q);
        new_hash = order_hash(new_reference_q);
        debug_hash = order_hash(debug_reference);
        old_base = int'(old_hash[SET_BITS-1:0]) * 2;
        new_base = int'(new_hash[SET_BITS-1:0]) * 2;
        debug_base = int'(debug_hash[SET_BITS-1:0]) * 2;

        old_found = 1'b0;
        new_found = 1'b0;
        debug_match = 1'b0;
        debug_way_index = 1'b0;
        old_slot = -1;
        free_slot = -1;
        old_remaining = 32'd0;
        old_side = 1'b0;
        for (integer way = 0; way < 2; way = way + 1) begin
            if (order_valid_q[old_base + way] &&
                order_reference_q[old_base + way] == old_reference_q) begin
                old_found = 1'b1;
                old_slot = old_base + way;
                old_remaining = order_quantity_q[old_base + way];
                old_side = order_side_q[old_base + way];
            end
            if (order_valid_q[new_base + way] &&
                order_reference_q[new_base + way] == new_reference_q) begin
                new_found = 1'b1;
            end
            if (!order_valid_q[new_base + way] && free_slot == -1)
                free_slot = new_base + way;
            if (order_valid_q[debug_base + way] &&
                order_reference_q[debug_base + way] == debug_reference) begin
                debug_match = 1'b1;
                debug_way_index = way[0];
            end
        end

        debug_found = debug_match;
        debug_price = 32'd0;
        debug_remaining_quantity = 32'd0;
        debug_side = 1'b0;
        debug_way = debug_way_index;
        if (debug_match) begin
            for (integer way = 0; way < 2; way = way + 1) begin
                if (order_valid_q[debug_base + way] &&
                    order_reference_q[debug_base + way] == debug_reference) begin
                    debug_price = order_price_q[debug_base + way];
                    debug_remaining_quantity = order_quantity_q[debug_base + way];
                    debug_side = order_side_q[debug_base + way];
                end
            end
        end

        eval_error = 1'b0;
        eval_error_code = ERR_EVENT_CONTRACT;
        next_bid_total = bid_total_q;
        next_ask_total = ask_total_q;
        aggregate_candidate = 49'sd0;
        aggregate_delta = 49'sd0;
        aggregate_on_bid = 1'b0;
        new_remaining = 32'd0;
        if (!event_contract_q) begin
            eval_error = 1'b1;
            eval_error_code = ERR_EVENT_CONTRACT;
        end else begin
            case (event_kind_q)
                3'd0: begin
                    if (new_found) begin
                        eval_error = 1'b1;
                        eval_error_code = ERR_DUPLICATE_REFERENCE;
                    end else if (free_slot == -1) begin
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
                    end else begin
                        free_slot = -1;
                        for (integer way = 0; way < 2; way = way + 1) begin
                            if ((!order_valid_q[new_base + way] ||
                                 ((new_base == old_base) && (new_base + way == old_slot))) &&
                                free_slot == -1)
                                free_slot = new_base + way;
                        end
                        if (free_slot == -1) begin
                            eval_error = 1'b1;
                            eval_error_code = ERR_COLLISION_CAPACITY;
                        end else begin
                            aggregate_delta = $signed({17'b0, quantity_q}) -
                                              $signed({17'b0, old_remaining});
                            aggregate_on_bid = old_side == 1'b0;
                        end
                    end
                end
                default: begin
                    eval_error = 1'b1;
                    eval_error_code = ERR_EVENT_CONTRACT;
                end
            endcase
        end

        if (!eval_error) begin
            aggregate_candidate = $signed({1'b0,
                aggregate_on_bid ? bid_total_q : ask_total_q}) + aggregate_delta;
            if (aggregate_candidate < 0 || aggregate_candidate > 49'sh0FFFFFFFFFFFF) begin
                eval_error = 1'b1;
                eval_error_code = ERR_AGGREGATE_RANGE;
            end else if (aggregate_on_bid) begin
                next_bid_total = aggregate_candidate[47:0];
            end else begin
                next_ask_total = aggregate_candidate[47:0];
            end
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
            for (integer i = 0; i < ENTRY_COUNT; i = i + 1)
                order_valid_q[i] <= 1'b0;
        end else begin
            if (commit_valid_q && commit_ready)
                commit_valid_q <= 1'b0;
            if (error_valid_q && error_ready)
                error_valid_q <= 1'b0;

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
                        event_contract_q <= event_contract_ok;
                        state_q <= S_EVAL;
                    end
                end
                S_EVAL: begin
                    state_q <= S_IDLE;
                    if (eval_error) begin
                        book_valid_q <= 1'b0;
                        recovery_q <= 1'b1;
                        error_code_q <= eval_error_code;
                        error_valid_q <= 1'b1;
                    end else begin
                        case (event_kind_q)
                            3'd0: begin
                                order_reference_q[free_slot] <= new_reference_q;
                                order_price_q[free_slot] <= price_q;
                                order_quantity_q[free_slot] <= quantity_q;
                                order_side_q[free_slot] <= side_q;
                                order_valid_q[free_slot] <= 1'b1;
                            end
                            3'd1, 3'd2, 3'd3: begin
                                if (new_remaining == 0)
                                    order_valid_q[old_slot] <= 1'b0;
                                else
                                    order_quantity_q[old_slot] <= new_remaining;
                            end
                            3'd4: order_valid_q[old_slot] <= 1'b0;
                            3'd5: begin
                                if (free_slot != old_slot)
                                    order_valid_q[old_slot] <= 1'b0;
                                order_reference_q[free_slot] <= new_reference_q;
                                order_price_q[free_slot] <= price_q;
                                order_quantity_q[free_slot] <= quantity_q;
                                order_side_q[free_slot] <= old_side;
                                order_valid_q[free_slot] <= 1'b1;
                            end
                            default: begin end
                        endcase
                        bid_total_q <= next_bid_total;
                        ask_total_q <= next_ask_total;
                        commit_sequence_q <= event_sequence_q;
                        commit_timestamp_q <= event_timestamp_q;
                        commit_bid_q <= next_bid_total;
                        commit_ask_q <= next_ask_total;
                        commit_valid_q <= 1'b1;
                        if (upstream_recovery_required) begin
                            book_valid_q <= 1'b0;
                            recovery_q <= 1'b1;
                            error_code_q <= ERR_UPSTREAM_FATAL;
                            error_valid_q <= 1'b1;
                        end
                    end
                end
                default: state_q <= S_IDLE;
            endcase
        end
    end
endmodule
