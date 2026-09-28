module wire_gearbox_reference (
    input logic clk,
    input logic rst,
    input logic [63:0] in_data,
    input logic [7:0] in_keep,
    input logic in_valid,
    input logic in_last,
    input logic out_ready
);
    logic in_ready, out_valid, out_last;
    logic [7:0] out_data;

    wire_gearbox_64to8 dut (
        .clk(clk), .rst(rst), .in_data(in_data), .in_keep(in_keep),
        .in_valid(in_valid), .in_ready(in_ready), .in_last(in_last),
        .out_data(out_data), .out_valid(out_valid),
        .out_ready(out_ready), .out_last(out_last)
    );

    function automatic logic [3:0] keep_count(input logic [7:0] keep);
        case (keep)
            8'h01: keep_count = 4'd1;
            8'h03: keep_count = 4'd2;
            8'h07: keep_count = 4'd3;
            8'h0f: keep_count = 4'd4;
            8'h1f: keep_count = 4'd5;
            8'h3f: keep_count = 4'd6;
            8'h7f: keep_count = 4'd7;
            8'hff: keep_count = 4'd8;
            default: keep_count = 4'd0;
        endcase
    endfunction

    function automatic logic legal_keep(input logic [7:0] keep);
        case (keep)
            8'h01, 8'h03, 8'h07, 8'h0f,
            8'h1f, 8'h3f, 8'h7f, 8'hff: legal_keep = 1'b1;
            default: legal_keep = 1'b0;
        endcase
    endfunction

    logic [63:0] ref_data;
    logic [3:0] ref_byte_count;
    logic [2:0] ref_index;
    logic ref_last, ref_valid;

    wire ref_done = ref_valid &&
                    ({1'b0, ref_index} == (ref_byte_count - 4'd1));
    wire ref_ready = !ref_valid || (ref_valid && out_ready && ref_done);
    wire ref_out_last = ref_valid && ref_last && ref_done;
    wire input_fire = in_valid && in_ready;
    wire output_fire = out_valid && out_ready;

    initial begin
        ref_data = '0;
        ref_byte_count = '0;
        ref_index = '0;
        ref_last = 1'b0;
        ref_valid = 1'b0;
    end

    // Legal stream contract and upstream stability assumption.
    always @(*) begin
        if (in_valid) begin
            if (in_last) assume(legal_keep(in_keep));
            else assume(in_keep == 8'hff);
        end
    end

    // Reference state is updated only from public transfers.
    always @(posedge clk) begin
        if ($initstate)
            assume(rst);
        if (!rst && $past(!rst && in_valid && !in_ready)) begin
            assume(in_valid);
            assume(in_data == $past(in_data));
            assume(in_keep == $past(in_keep));
            assume(in_last == $past(in_last));
        end
        if (rst) begin
            ref_data <= '0;
            ref_byte_count <= '0;
            ref_index <= '0;
            ref_last <= 1'b0;
            ref_valid <= 1'b0;
        end else begin
            if (input_fire) begin
                ref_data <= in_data;
                ref_byte_count <= keep_count(in_keep);
                ref_index <= 3'd0;
                ref_last <= in_last;
                ref_valid <= 1'b1;
            end else if (output_fire) begin
                if (ref_done) begin
                    ref_valid <= 1'b0;
                    ref_index <= '0;
                    ref_last <= 1'b0;
                end else begin
                    ref_index <= ref_index + 3'd1;
                end
            end

        end
    end

    // P2: input-ready correspondence; no overwrite and defined refill.
    always @(*) begin
        if (!rst)
            assert(in_ready == ref_ready);
    end

    // P3/P4/P6: exact public output correspondence, including lane order
    // and the frame-final marker.
    always @(posedge clk) begin
        if (!rst && $past(!rst)) begin
            assert(out_valid == ref_valid);
            assert(out_last == ref_out_last);
            if (ref_valid)
                assert(out_data == ref_data[ref_index * 8 +: 8]);
        end
    end

    // P1: stalled output payload stability.
    always @(posedge clk) begin
        if (!rst && $past(!rst && out_valid && !out_ready)) begin
            assert(out_valid);
            assert(out_data == $past(out_data));
            assert(out_last == $past(out_last));
        end
    end

    // P5: conservation is represented by the reference transition itself:
    // accepted beats are the only way ref_valid is set, each output transfer
    // advances exactly one reference byte, and a beat retires only at its
    // final valid lane.

    // P7: same-cycle retirement/refill is safe and exposes the new lane 0.
    always @(posedge clk) begin
        if (!rst && $past(!rst && ref_done && output_fire && input_fire)) begin
            assert(out_valid);
            assert(out_data == $past(in_data[7:0]));
        end
        if (!rst)
            cover(ref_done && output_fire && input_fire && !in_last);
        if (!rst)
            cover(ref_done && output_fire && input_fire && in_last);
    end
endmodule
