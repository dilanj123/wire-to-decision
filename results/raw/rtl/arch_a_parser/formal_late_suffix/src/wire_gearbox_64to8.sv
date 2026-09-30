// Wire-to-Decision Architecture A primitive.
// 64-bit legal framed beat stream to one ordered byte per transfer.
module wire_gearbox_64to8 (
    input  logic       clk,
    input  logic       rst,

    input  logic [63:0] in_data,
    input  logic [7:0]  in_keep,
    input  logic        in_valid,
    output logic        in_ready,
    input  logic        in_last,

    output logic [7:0]  out_data,
    output logic        out_valid,
    input  logic        out_ready,
    output logic        out_last
);
    logic [63:0] data_q;
    logic [3:0]  count_q;
    logic [2:0]  index_q;
    logic        last_q;
    logic        valid_q;

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

    wire beat_done  = valid_q && ({1'b0, index_q} == (count_q - 4'd1));
    wire final_byte = beat_done && last_q;

    assign out_valid = valid_q;
    assign out_data  = valid_q ? data_q[index_q * 8 +: 8] : 8'h00;
    assign out_last  = final_byte;

    // A new beat may replace the current beat on the cycle its final byte
    // transfers. This permits continuous serialization across full beats.
    assign in_ready = !valid_q || (out_valid && out_ready && beat_done);

    always_ff @(posedge clk) begin
        if (rst) begin
            data_q  <= '0;
            count_q <= '0;
            index_q <= '0;
            last_q  <= 1'b0;
            valid_q <= 1'b0;
        end else if (in_valid && in_ready) begin
            data_q  <= in_data;
            count_q <= keep_count(in_keep);
            index_q <= 3'd0;
            last_q  <= in_last;
            valid_q <= 1'b1;
        end else if (out_valid && out_ready) begin
            if (beat_done) begin
                valid_q <= 1'b0;
                index_q <= 3'd0;
                last_q  <= 1'b0;
            end else begin
                index_q <= index_q + 3'd1;
            end
        end
    end
endmodule
