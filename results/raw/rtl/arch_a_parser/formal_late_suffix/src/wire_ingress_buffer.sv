// Wire-to-Decision common synchronous two-beat ingress buffer.
// Stores complete framed beats without protocol interpretation or fall-through.
module wire_ingress_buffer (
    input  logic        clk,
    input  logic        rst,

    input  logic [63:0] in_data,
    input  logic [7:0]  in_keep,
    input  logic        in_valid,
    output logic        in_ready,
    input  logic        in_last,

    output logic [63:0] out_data,
    output logic [7:0]  out_keep,
    output logic        out_valid,
    input  logic        out_ready,
    output logic        out_last
);
    logic [63:0] data_q [0:1];
    logic [7:0]  keep_q [0:1];
    logic        last_q [0:1];
    logic        read_ptr_q;
    logic        write_ptr_q;
    logic [1:0]  count_q;

    wire pop = out_valid && out_ready;
    wire push = in_valid && in_ready;

    assign out_valid = (count_q != 2'd0);
    assign out_data  = data_q[read_ptr_q];
    assign out_keep  = keep_q[read_ptr_q];
    assign out_last  = last_q[read_ptr_q];

    // A full FIFO can accept a replacement beat when its head transfers.
    assign in_ready = (count_q != 2'd2) || pop;

    always_ff @(posedge clk) begin
        if (rst) begin
            read_ptr_q  <= 1'b0;
            write_ptr_q <= 1'b0;
            count_q     <= 2'd0;
        end else begin
            if (push) begin
                data_q[write_ptr_q] <= in_data;
                keep_q[write_ptr_q] <= in_keep;
                last_q[write_ptr_q] <= in_last;
                write_ptr_q <= write_ptr_q + 1'b1;
            end

            if (pop)
                read_ptr_q <= read_ptr_q + 1'b1;

            case ({push, pop})
                2'b10: count_q <= count_q + 2'd1;
                2'b01: count_q <= count_q - 2'd1;
                default: count_q <= count_q;
            endcase
        end
    end
endmodule
