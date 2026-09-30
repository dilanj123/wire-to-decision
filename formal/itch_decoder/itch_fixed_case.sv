module itch_fixed_case #(
    parameter integer CASE = 0
);
    (* gclk *) wire clk;
    localparam integer LEN = CASE == 13 ? 0 : CASE == 10 ? 1 : CASE == 11 ? 7 : CASE == 12 ? 36 :
                             CASE == 8 || CASE == 9 ? 36 : CASE == 0 ? 36 : CASE == 1 ? 40 : CASE == 2 ? 31 :
                             CASE == 3 ? 36 : CASE == 4 ? 23 : CASE == 5 ? 19 :
                             CASE == 6 ? 35 : 44;
    localparam [7:0] TYPE = CASE == 11 ? "Z" : CASE == 8 || CASE == 9 || CASE == 10 || CASE == 12 ? "A" :
                            CASE == 0 ? "A" : CASE == 1 ? "F" : CASE == 2 ? "E" :
                            CASE == 3 ? "C" : CASE == 4 ? "X" : CASE == 5 ? "D" :
                            CASE == 6 ? "U" : "P";
    reg [6:0] cycle = 0;
    reg [5:0] index = 0;
    reg meta_sent = 0;
    wire rst = (cycle == 0);
    wire rearm = 0;
    wire [15:0] cfg_tracked_stock_locate = (CASE == 12) ? 16'h9999 : 16'h1234;
    wire cfg_symbol_check_enable = (CASE == 9);
    wire [63:0] cfg_expected_stock_symbol = 64'h4142434420202020;
    wire message_valid = (cycle == 1);
    wire message_ready;
    wire [63:0] message_sequence = 64'hfedcba9876543210;
    wire [15:0] message_length = LEN;
    wire message_empty = (CASE == 13);
    wire [7:0] in_data;
    wire in_valid = meta_sent && index < LEN;
    wire in_ready;
    wire in_last = (index == LEN-1);
    wire event_valid, event_ready = 1;
    wire [2:0] event_kind;
    wire [7:0] source_type;
    wire [63:0] mold_sequence;
    wire [47:0] itch_timestamp;
    wire [15:0] stock_locate;
    wire [63:0] old_order_reference, new_order_reference;
    wire [31:0] quantity, price;
    wire side, old_reference_valid, new_reference_valid;
    wire quantity_valid, price_valid, side_valid;
    wire reject_valid, reject_ready = 0;
    wire reject_fatal;
    wire [2:0] reject_code;
    wire decoder_valid, recovery_required;

    function automatic [7:0] byte_value(input integer n);
        begin
            byte_value = 0;
            if (n == 0) byte_value = TYPE;
            if (n == 1) byte_value = 8'h12;
            if (n == 2) byte_value = 8'h34;
            if (n >= 5 && n <= 10) byte_value = n - 4;
            if ((CASE == 0 || CASE == 1 || CASE == 8 || CASE == 9 || CASE == 12) && n >= 11 && n <= 18) byte_value = 8'h11 + n - 11;
            if ((CASE == 0 || CASE == 1 || CASE == 8 || CASE == 9 || CASE == 12) && n == 19) byte_value = (CASE == 8) ? "?" : "B";
            if ((CASE == 0 || CASE == 1 || CASE == 8 || CASE == 9 || CASE == 12) && n >= 20 && n <= 23) byte_value = 8'h21 + n - 20;
            if ((CASE == 0 || CASE == 1 || CASE == 8 || CASE == 9 || CASE == 12) && n >= 24 && n <= 31) byte_value = 8'h41 + n - 24;
            if ((CASE == 0 || CASE == 1 || CASE == 8 || CASE == 9 || CASE == 12) && n >= 32 && n <= 35) byte_value = 8'h31 + n - 32;
            if ((CASE == 2 || CASE == 3 || CASE == 4 || CASE == 5) && n >= 11 && n <= 18) byte_value = 8'h51 + n - 11;
            if ((CASE == 2 || CASE == 3 || CASE == 4) && n >= 19 && n <= 22) byte_value = 8'h61 + n - 19;
            if (CASE == 6 && n >= 11 && n <= 18) byte_value = 8'h71 + n - 11;
            if (CASE == 6 && n >= 19 && n <= 26) byte_value = 8'h81 + n - 19;
            if (CASE == 6 && n >= 27 && n <= 30) byte_value = 8'h91 + n - 27;
            if (CASE == 6 && n >= 31 && n <= 34) byte_value = 8'ha1 + n - 31;
        end
    endfunction
    assign in_data = byte_value(index);

    wire_itch_decoder dut (.*);
    always @(posedge clk) begin
        if (cycle < 80) cycle <= cycle + 1'b1;
        if (rst) begin index <= 0; meta_sent <= 0; end
        else begin
            if (message_valid && message_ready) meta_sent <= 1;
            if (in_valid && in_ready) index <= index + 1'b1;
        end
        if (cycle > 0 && event_valid) begin
            assert(index == LEN);
            assert(source_type == TYPE);
            assert(mold_sequence == 64'hfedcba9876543210);
            assert(itch_timestamp == 48'h010203040506);
            assert(stock_locate == 16'h1234);
            if (CASE >= 7) assert(1'b0);
            else begin
                assert(event_kind == (CASE <= 1 ? 0 : CASE == 2 ? 1 : CASE == 3 ? 2 : CASE == 4 ? 3 : CASE == 5 ? 4 : 5));
                if (CASE <= 1) begin
                    assert(!old_reference_valid && new_reference_valid && quantity_valid && price_valid && side_valid);
                    assert(new_order_reference == 64'h1112131415161718);
                    assert(quantity == 32'h21222324 && price == 32'h31323334 && side == 0);
                end
                if (CASE == 2 || CASE == 3 || CASE == 4) begin
                    assert(old_reference_valid && !new_reference_valid && quantity_valid && !price_valid && !side_valid);
                    assert(old_order_reference == 64'h5152535455565758);
                    assert(quantity == 32'h61626364);
                end
                if (CASE == 5) begin
                    assert(old_reference_valid && !new_reference_valid && !quantity_valid && !price_valid && !side_valid);
                    assert(old_order_reference == 64'h5152535455565758);
                end
                if (CASE == 6) begin
                    assert(old_reference_valid && new_reference_valid && quantity_valid && price_valid && !side_valid);
                    assert(old_order_reference == 64'h7172737475767778);
                    assert(new_order_reference == 64'h8182838485868788);
                    assert(quantity == 32'h91929394 && price == 32'ha1a2a3a4);
                end
            end
        end
        if (cycle > 0 && CASE == 7) begin
            assert(!event_valid);
            assert(!recovery_required);
        end
        if (cycle > LEN + 4) begin
            if (CASE == 7 || CASE == 12) assert(decoder_valid && !reject_valid);
            else if ((CASE >= 8 && CASE <= 11) || CASE == 13) begin
                assert(!decoder_valid && recovery_required && reject_valid && reject_fatal);
                assert(reject_code == (CASE == 8 ? 3 : CASE == 9 ? 4 : CASE == 10 ? 2 : CASE == 11 ? 1 : 0));
            end
            else assert(event_valid || !decoder_valid || index == LEN);
        end
    end
endmodule
