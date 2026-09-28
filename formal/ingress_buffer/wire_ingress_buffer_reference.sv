module wire_ingress_buffer_reference (
    input logic        clk,
    input logic        rst,
    input logic [63:0] in_data,
    input logic [7:0]  in_keep,
    input logic        in_valid,
    input logic        in_last,
    input logic        out_ready
);
    logic [63:0] out_data;
    logic [7:0]  out_keep;
    logic        in_ready, out_valid, out_last;

    wire_ingress_buffer dut (
        .clk(clk), .rst(rst),
        .in_data(in_data), .in_keep(in_keep), .in_valid(in_valid),
        .in_ready(in_ready), .in_last(in_last),
        .out_data(out_data), .out_keep(out_keep),
        .out_valid(out_valid), .out_ready(out_ready), .out_last(out_last)
    );

    logic [63:0] ref_data0, ref_data1;
    logic [7:0]  ref_keep0, ref_keep1;
    logic        ref_last0, ref_last1;
    logic [1:0]  ref_count;

    wire ref_nonempty = (ref_count != 2'd0);
    wire ref_full = (ref_count == 2'd2);
    wire ref_pop = ref_nonempty && out_ready;
    wire ref_ready = !ref_full || ref_pop;
    wire input_fire = in_valid && in_ready;
    wire output_fire = out_valid && out_ready;

    initial begin
        ref_data0 = '0;
        ref_data1 = '0;
        ref_keep0 = '0;
        ref_keep1 = '0;
        ref_last0 = 1'b0;
        ref_last1 = 1'b0;
        ref_count = 2'd0;
    end

    // Upstream ready/valid contract: a rejected valid beat is held stable.
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
            ref_count <= 2'd0;
            ref_data0 <= '0;
            ref_data1 <= '0;
            ref_keep0 <= '0;
            ref_keep1 <= '0;
            ref_last0 <= 1'b0;
            ref_last1 <= 1'b0;
        end else begin
            case ({input_fire, output_fire})
                2'b10: begin
                    if (ref_count == 2'd0) begin
                        ref_data0 <= in_data;
                        ref_keep0 <= in_keep;
                        ref_last0 <= in_last;
                    end else begin
                        ref_data1 <= in_data;
                        ref_keep1 <= in_keep;
                        ref_last1 <= in_last;
                    end
                    ref_count <= ref_count + 2'd1;
                end
                2'b01: begin
                    if (ref_count == 2'd2) begin
                        ref_data0 <= ref_data1;
                        ref_keep0 <= ref_keep1;
                        ref_last0 <= ref_last1;
                    end
                    ref_count <= ref_count - 2'd1;
                end
                2'b11: begin
                    if (ref_count == 2'd1) begin
                        ref_data0 <= in_data;
                        ref_keep0 <= in_keep;
                        ref_last0 <= in_last;
                    end else if (ref_count == 2'd2) begin
                        ref_data0 <= ref_data1;
                        ref_keep0 <= ref_keep1;
                        ref_last0 <= ref_last1;
                        ref_data1 <= in_data;
                        ref_keep1 <= in_keep;
                        ref_last1 <= in_last;
                    end
                end
                default: begin end
            endcase
        end
    end

    // P1: the public ready signal exactly reflects independent capacity.
    always @(*) begin
        if (!rst)
            assert(in_ready == ref_ready);
    end

    // P2/P4: valid and payload correspond to the oldest reference entry.
    always @(*) begin
        if (!rst) begin
            assert(out_valid == ref_nonempty);
            if (ref_nonempty) begin
                assert(out_data == ref_data0);
                assert(out_keep == ref_keep0);
                assert(out_last == ref_last0);
            end
        end
    end

    // P5/P6: no interface operation can pop an empty queue or exceed depth 2.
    always @(*) begin
        if (!rst) begin
            assert(ref_count <= 2'd2);
            assert(!(output_fire && !ref_nonempty));
        end
    end

    // P3: stalled output tuple remains stable.
    always @(posedge clk) begin
        if (!rst && $past(!rst && out_valid && !out_ready)) begin
            assert(out_valid);
            assert(out_data == $past(out_data));
            assert(out_keep == $past(out_keep));
            assert(out_last == $past(out_last));
        end
    end

    // P7/P8/P9: simultaneous operations are reachable, with both occupancy
    // one and full occupancy represented by the reference transition.
    always @(posedge clk) begin
        if (!rst)
            cover(ref_count == 2'd1 && input_fire && output_fire);
        if (!rst)
            cover(ref_count == 2'd2 && input_fire && output_fire);
    end
endmodule
