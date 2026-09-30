// Fixed-subset TotalView-ITCH decoder. Events are published only after the
// complete WIRE-D016 message boundary has transferred.
module wire_itch_decoder (
    input  logic        clk,
    input  logic        rst,
    input  logic        rearm,
    input  logic [15:0] cfg_tracked_stock_locate,
    input  logic        cfg_symbol_check_enable,
    input  logic [63:0] cfg_expected_stock_symbol,

    input  logic        message_valid,
    output logic        message_ready,
    input  logic [63:0] message_sequence,
    input  logic [15:0] message_length,
    input  logic        message_empty,
    input  logic [7:0]  in_data,
    input  logic        in_valid,
    output logic        in_ready,
    input  logic        in_last,

    output logic        event_valid,
    input  logic        event_ready,
    output logic [2:0]  event_kind,
    output logic [7:0]  source_type,
    output logic [63:0] mold_sequence,
    output logic [47:0] itch_timestamp,
    output logic [15:0] stock_locate,
    output logic [63:0] old_order_reference,
    output logic [63:0] new_order_reference,
    output logic [31:0] quantity,
    output logic [31:0] price,
    output logic        side,
    output logic        old_reference_valid,
    output logic        new_reference_valid,
    output logic        quantity_valid,
    output logic        price_valid,
    output logic        side_valid,

    output logic        reject_valid,
    input  logic        reject_ready,
    output logic        reject_fatal,
    output logic [2:0]  reject_code,
    output logic        decoder_valid,
    output logic        recovery_required
);
    localparam logic [2:0] ERR_EMPTY = 3'd0;
    localparam logic [2:0] ERR_UNSUPPORTED = 3'd1;
    localparam logic [2:0] ERR_LENGTH = 3'd2;
    localparam logic [2:0] ERR_SIDE = 3'd3;
    localparam logic [2:0] ERR_SYMBOL = 3'd4;
    localparam logic [2:0] ERR_BOUNDARY = 3'd5;

    localparam logic [2:0] ADD = 3'd0, EXECUTE = 3'd1,
                           EXECUTE_WITH_PRICE = 3'd2, CANCEL = 3'd3,
                           DELETE = 3'd4, REPLACE = 3'd5;

    typedef enum logic [2:0] {S_IDLE, S_COLLECT, S_VALIDATE, S_EVENT,
                              S_DRAIN_CURRENT, S_DRAIN_MESSAGES} state_t;
    state_t state_q;
    logic [7:0] bytes_q [0:43];
    logic [5:0] byte_index_q;
    logic [15:0] declared_length_q;
    logic [63:0] message_sequence_q;
    logic [15:0] tracked_locate_q;
    logic symbol_enable_q;
    logic [63:0] expected_symbol_q;
    logic [2:0] reject_code_q;
    logic reject_pending_q;

    logic [2:0] event_kind_q;
    logic [7:0] source_type_q;
    logic [63:0] mold_sequence_q;
    logic [47:0] timestamp_q;
    logic [15:0] stock_locate_q;
    logic [63:0] old_ref_q, new_ref_q;
    logic [31:0] quantity_q, price_q;
    logic side_q;
    logic old_valid_q, new_valid_q, quantity_valid_q, price_valid_q, side_valid_q;

    function automatic logic [15:0] u16(input integer offset);
        u16 = {bytes_q[offset], bytes_q[offset+1]};
    endfunction
    function automatic logic [31:0] u32(input integer offset);
        u32 = {bytes_q[offset], bytes_q[offset+1], bytes_q[offset+2], bytes_q[offset+3]};
    endfunction
    function automatic logic [63:0] u64(input integer offset);
        u64 = {bytes_q[offset], bytes_q[offset+1], bytes_q[offset+2], bytes_q[offset+3],
               bytes_q[offset+4], bytes_q[offset+5], bytes_q[offset+6], bytes_q[offset+7]};
    endfunction
    function automatic logic [47:0] u48(input integer offset);
        u48 = {bytes_q[offset], bytes_q[offset+1], bytes_q[offset+2],
               bytes_q[offset+3], bytes_q[offset+4], bytes_q[offset+5]};
    endfunction
    function automatic logic [15:0] required_length(input logic [7:0] t);
        case (t)
            "A": required_length = 16'd36;
            "F": required_length = 16'd40;
            "E": required_length = 16'd31;
            "C": required_length = 16'd36;
            "X": required_length = 16'd23;
            "D": required_length = 16'd19;
            "U": required_length = 16'd35;
            "P": required_length = 16'd44;
            default: required_length = 16'd0;
        endcase
    endfunction

    wire message_fire = message_valid && message_ready;
    wire byte_fire = in_valid && in_ready;
    wire event_fire = event_valid && event_ready;
    wire first_byte_invalid = (byte_index_q == 0) &&
        ((required_length(in_data) == 0) || (declared_length_q != required_length(in_data)));
    assign message_ready = (state_q == S_IDLE) || (state_q == S_DRAIN_MESSAGES);
    assign in_ready = (state_q == S_COLLECT) || (state_q == S_DRAIN_CURRENT) ||
                      (state_q == S_DRAIN_MESSAGES);
    assign event_valid = (state_q == S_EVENT);
    assign event_kind = event_kind_q;
    assign source_type = source_type_q;
    assign mold_sequence = mold_sequence_q;
    assign itch_timestamp = timestamp_q;
    assign stock_locate = stock_locate_q;
    assign old_order_reference = old_ref_q;
    assign new_order_reference = new_ref_q;
    assign quantity = quantity_q;
    assign price = price_q;
    assign side = side_q;
    assign old_reference_valid = old_valid_q;
    assign new_reference_valid = new_valid_q;
    assign quantity_valid = quantity_valid_q;
    assign price_valid = price_valid_q;
    assign side_valid = side_valid_q;
    assign reject_valid = reject_pending_q;
    assign reject_fatal = 1'b1;
    assign reject_code = reject_code_q;
    assign decoder_valid = !recovery_required;

    always_ff @(posedge clk) begin
        if (rst || rearm) begin
            state_q <= S_IDLE;
            byte_index_q <= 0;
            declared_length_q <= 0;
            message_sequence_q <= 0;
            tracked_locate_q <= cfg_tracked_stock_locate;
            symbol_enable_q <= cfg_symbol_check_enable;
            expected_symbol_q <= cfg_expected_stock_symbol;
            reject_code_q <= ERR_EMPTY;
            reject_pending_q <= 1'b0;
            recovery_required <= 1'b0;
            event_kind_q <= 0; source_type_q <= 0; mold_sequence_q <= 0;
            timestamp_q <= 0; stock_locate_q <= 0; old_ref_q <= 0; new_ref_q <= 0;
            quantity_q <= 0; price_q <= 0; side_q <= 0;
            old_valid_q <= 0; new_valid_q <= 0; quantity_valid_q <= 0;
            price_valid_q <= 0; side_valid_q <= 0;
        end else begin
            if (reject_pending_q && reject_ready) reject_pending_q <= 1'b0;
            case (state_q)
                S_IDLE: if (message_fire) begin
                    message_sequence_q <= message_sequence;
                    declared_length_q <= message_length;
                    byte_index_q <= 0;
                    if (message_empty || message_length == 0) begin
                        if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_EMPTY; reject_pending_q <= 1'b1; end
                        state_q <= S_DRAIN_MESSAGES;
                    end else state_q <= S_COLLECT;
                end
                S_COLLECT: if (byte_fire) begin
                    if (byte_index_q < 44) bytes_q[byte_index_q] <= in_data;
                    if (byte_index_q == 0) begin
                        if (in_data != "A" && in_data != "F" && in_data != "E" &&
                            in_data != "C" && in_data != "X" && in_data != "D" &&
                            in_data != "U" && in_data != "P") begin
                            if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_UNSUPPORTED; reject_pending_q <= 1'b1; end
                            state_q <= in_last ? S_DRAIN_MESSAGES : S_DRAIN_CURRENT;
                        end else begin
                            case (in_data)
                                "A", "C": if (declared_length_q != 36) begin if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_LENGTH; reject_pending_q <= 1'b1; end state_q <= in_last ? S_DRAIN_MESSAGES : S_DRAIN_CURRENT; end
                                "F": if (declared_length_q != 40) begin if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_LENGTH; reject_pending_q <= 1'b1; end state_q <= in_last ? S_DRAIN_MESSAGES : S_DRAIN_CURRENT; end
                                "E": if (declared_length_q != 31) begin if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_LENGTH; reject_pending_q <= 1'b1; end state_q <= in_last ? S_DRAIN_MESSAGES : S_DRAIN_CURRENT; end
                                "X": if (declared_length_q != 23) begin if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_LENGTH; reject_pending_q <= 1'b1; end state_q <= in_last ? S_DRAIN_MESSAGES : S_DRAIN_CURRENT; end
                                "D": if (declared_length_q != 19) begin if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_LENGTH; reject_pending_q <= 1'b1; end state_q <= in_last ? S_DRAIN_MESSAGES : S_DRAIN_CURRENT; end
                                "U": if (declared_length_q != 35) begin if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_LENGTH; reject_pending_q <= 1'b1; end state_q <= in_last ? S_DRAIN_MESSAGES : S_DRAIN_CURRENT; end
                                "P": if (declared_length_q != 44) begin if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_LENGTH; reject_pending_q <= 1'b1; end state_q <= in_last ? S_DRAIN_MESSAGES : S_DRAIN_CURRENT; end
                                default: ;
                            endcase
                        end
                    end
                    if (in_last) begin
                        if (first_byte_invalid) begin
                            state_q <= S_DRAIN_MESSAGES;
                        end else if (({10'd0, byte_index_q} + 16'd1) != declared_length_q) begin
                            if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_BOUNDARY; reject_pending_q <= 1'b1; end
                            state_q <= S_DRAIN_MESSAGES;
                        end else state_q <= S_VALIDATE;
                    end else byte_index_q <= byte_index_q + 1'b1;
                end
                S_VALIDATE: begin
                    source_type_q <= bytes_q[0];
                    mold_sequence_q <= message_sequence_q;
                    timestamp_q <= u48(5);
                    stock_locate_q <= u16(1);
                    old_ref_q <= 0; new_ref_q <= 0; quantity_q <= 0; price_q <= 0; side_q <= 0;
                    old_valid_q <= 0; new_valid_q <= 0; quantity_valid_q <= 0;
                    price_valid_q <= 0; side_valid_q <= 0;
                    if (bytes_q[0] == "P") state_q <= S_IDLE;
                    else if (u16(1) != tracked_locate_q) state_q <= S_IDLE;
                    else if (bytes_q[0] == "A" || bytes_q[0] == "F") begin
                        if (symbol_enable_q && {bytes_q[24],bytes_q[25],bytes_q[26],bytes_q[27],bytes_q[28],bytes_q[29],bytes_q[30],bytes_q[31]} != expected_symbol_q) begin
                            if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_SYMBOL; reject_pending_q <= 1'b1; end state_q <= S_DRAIN_MESSAGES;
                        end else if (bytes_q[19] != "B" && bytes_q[19] != "S") begin
                            if (!recovery_required) begin recovery_required <= 1'b1; reject_code_q <= ERR_SIDE; reject_pending_q <= 1'b1; end state_q <= S_DRAIN_MESSAGES;
                        end else begin
                            event_kind_q <= ADD; new_ref_q <= u64(11); quantity_q <= u32(20); price_q <= u32(32);
                            side_q <= (bytes_q[19] == "S"); new_valid_q <= 1; quantity_valid_q <= 1; price_valid_q <= 1; side_valid_q <= 1;
                            state_q <= S_EVENT;
                        end
                    end else begin
                        case (bytes_q[0])
                            "E": begin event_kind_q <= EXECUTE; old_ref_q <= u64(11); quantity_q <= u32(19); old_valid_q <= 1; quantity_valid_q <= 1; state_q <= S_EVENT; end
                            "C": begin event_kind_q <= EXECUTE_WITH_PRICE; old_ref_q <= u64(11); quantity_q <= u32(19); old_valid_q <= 1; quantity_valid_q <= 1; state_q <= S_EVENT; end
                            "X": begin event_kind_q <= CANCEL; old_ref_q <= u64(11); quantity_q <= u32(19); old_valid_q <= 1; quantity_valid_q <= 1; state_q <= S_EVENT; end
                            "D": begin event_kind_q <= DELETE; old_ref_q <= u64(11); old_valid_q <= 1; state_q <= S_EVENT; end
                            "U": begin event_kind_q <= REPLACE; old_ref_q <= u64(11); new_ref_q <= u64(19); quantity_q <= u32(27); price_q <= u32(31); old_valid_q <= 1; new_valid_q <= 1; quantity_valid_q <= 1; price_valid_q <= 1; state_q <= S_EVENT; end
                            default: state_q <= S_IDLE;
                        endcase
                    end
                end
                S_EVENT: if (event_fire) state_q <= S_IDLE;
                S_DRAIN_CURRENT: if (byte_fire && in_last) state_q <= S_DRAIN_MESSAGES;
                S_DRAIN_MESSAGES: begin
                    if (message_fire) begin
                        if (!message_empty && message_length != 0) state_q <= S_DRAIN_CURRENT;
                    end
                    if (byte_fire && in_last) state_q <= S_DRAIN_MESSAGES;
                end
                default: state_q <= S_IDLE;
            endcase
        end
    end
endmodule
