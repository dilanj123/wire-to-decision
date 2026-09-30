module itch_safety (
    input logic clk, rst, rearm,
    input logic [15:0] cfg_tracked_stock_locate,
    input logic cfg_symbol_check_enable,
    input logic [63:0] cfg_expected_stock_symbol,
    input logic message_valid,
    input logic [63:0] message_sequence,
    input logic [15:0] message_length,
    input logic message_empty,
    input logic [7:0] in_data,
    input logic in_valid, in_last,
    input logic event_ready, reject_ready
);
    logic message_ready, in_ready, event_valid;
    logic [2:0] event_kind;
    logic [7:0] source_type;
    logic [63:0] mold_sequence, old_order_reference, new_order_reference;
    logic [47:0] itch_timestamp;
    logic [15:0] stock_locate;
    logic [31:0] quantity, price;
    logic side, old_reference_valid, new_reference_valid, quantity_valid, price_valid, side_valid;
    logic reject_valid, reject_fatal, decoder_valid, recovery_required;
    logic [2:0] reject_code;
    wire out_fire = event_valid && event_ready;
    wire reject_fire = reject_valid && reject_ready;
    wire_itch_decoder dut (.*);

    always @(*) begin
        if (!rst && recovery_required) assert(!event_valid);
        if (!rst && reject_valid) assert(reject_fatal);
    end
    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!rst && !rearm && $past(!rst && !rearm && event_valid && !event_ready)) begin
            assert(event_valid);
            assert({event_kind,source_type,mold_sequence,itch_timestamp,stock_locate,
                    old_order_reference,new_order_reference,quantity,price,side,
                    old_reference_valid,new_reference_valid,quantity_valid,price_valid,side_valid} ==
                   $past({event_kind,source_type,mold_sequence,itch_timestamp,stock_locate,
                          old_order_reference,new_order_reference,quantity,price,side,
                          old_reference_valid,new_reference_valid,quantity_valid,price_valid,side_valid}));
        end
        if (!rst && !rearm && $past(!rst && !rearm && reject_valid && !reject_ready)) begin
            assert(reject_valid && reject_fatal);
            assert(reject_code == $past(reject_code));
        end
        if (!rst && recovery_required) assert(!out_fire);
        if (!rst && recovery_required) assert(message_ready || in_ready);
        if (!rst && $past(!rst && rearm)) begin
            assert(decoder_valid && !recovery_required);
            assert(!event_valid && !reject_valid);
        end
    end
endmodule
