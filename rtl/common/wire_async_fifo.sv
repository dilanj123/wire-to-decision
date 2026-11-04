// Small project-original asynchronous FIFO for framed post-MAC beats.
// wr_rst and rd_rst are active-high asynchronous-assert reset inputs. A
// containing design must coordinate independent resets before resuming traffic.
module wire_async_fifo #(
    parameter integer WIDTH = 73,
    parameter integer DEPTH = 8,
    parameter integer ADDR_BITS = $clog2(DEPTH),
    parameter integer PTR_BITS = ADDR_BITS + 1
) (
    input  logic                  wr_clk,
    input  logic                  wr_rst,
    input  logic [WIDTH-1:0]      wr_data,
    input  logic                  wr_valid,
    output logic                  wr_ready,

    input  logic                  rd_clk,
    input  logic                  rd_rst,
    output logic [WIDTH-1:0]      rd_data,
    output logic                  rd_valid,
    input  logic                  rd_ready
);
    logic [WIDTH-1:0] memory [0:DEPTH-1];
    logic [PTR_BITS-1:0] wr_bin_q, wr_gray_q;
    logic [PTR_BITS-1:0] rd_bin_q, rd_gray_q;
    logic wr_full_q, rd_empty_q;

    logic [PTR_BITS-1:0] wr_bin_next, wr_gray_next;
    logic [PTR_BITS-1:0] rd_bin_next, rd_gray_next;
    logic [PTR_BITS-1:0] rd_gray_full_compare;
    logic wr_fire, rd_fire;

    function automatic logic [PTR_BITS-1:0] to_gray(
        input logic [PTR_BITS-1:0] binary
    );
        to_gray = (binary >> 1) ^ binary;
    endfunction

    initial begin
        if (DEPTH < 2 || (DEPTH & (DEPTH-1)) != 0)
            $error("wire_async_fifo DEPTH must be a power of two >= 2");
        if (WIDTH < 1)
            $error("wire_async_fifo WIDTH must be positive");
    end

    assign wr_ready = !wr_full_q;
    assign rd_valid = !rd_empty_q;
    assign rd_data = memory[rd_bin_q[ADDR_BITS-1:0]];
    assign wr_fire = wr_valid && wr_ready;
    assign rd_fire = rd_valid && rd_ready;

    always_comb begin
        wr_bin_next = wr_bin_q + wr_fire;
        wr_gray_next = to_gray(wr_bin_next);
        rd_bin_next = rd_bin_q + rd_fire;
        rd_gray_next = to_gray(rd_bin_next);
        rd_gray_full_compare = rd_gray_wsync2_q_attr;
        rd_gray_full_compare[PTR_BITS-1 -: 2] =
            ~rd_gray_wsync2_q_attr[PTR_BITS-1 -: 2];
    end

    // The Gray pointer is the only multi-bit state crossing a clock boundary.
    // Keep each bus in its destination domain through two synchronizer flops.
    // A physical implementation must constrain Gray-bus skew/maximum delay
    // from each source pointer register to the first destination synchronizer
    // so routing cannot span multiple source-pointer transitions. RTL
    // simulation and these local checks do not establish that constraint.
    (* async_reg = "true" *) logic [PTR_BITS-1:0] rd_gray_wsync1_q_attr;
    (* async_reg = "true" *) logic [PTR_BITS-1:0] rd_gray_wsync2_q_attr;
    (* async_reg = "true" *) logic [PTR_BITS-1:0] wr_gray_rsync1_q_attr;
    (* async_reg = "true" *) logic [PTR_BITS-1:0] wr_gray_rsync2_q_attr;

    // These are the actual pointer synchronizer stages used by the logic.
    always_ff @(posedge wr_clk or posedge wr_rst) begin
        if (wr_rst) begin
            rd_gray_wsync1_q_attr <= '0;
            rd_gray_wsync2_q_attr <= '0;
            wr_bin_q <= '0;
            wr_gray_q <= '0;
            wr_full_q <= 1'b0;
        end else begin
            rd_gray_wsync1_q_attr <= rd_gray_q;
            rd_gray_wsync2_q_attr <= rd_gray_wsync1_q_attr;
            if (wr_fire)
                memory[wr_bin_q[ADDR_BITS-1:0]] <= wr_data;
            wr_bin_q <= wr_bin_next;
            wr_gray_q <= wr_gray_next;
            wr_full_q <= (wr_gray_next == rd_gray_full_compare);
        end
    end

    always_ff @(posedge rd_clk or posedge rd_rst) begin
        if (rd_rst) begin
            wr_gray_rsync1_q_attr <= '0;
            wr_gray_rsync2_q_attr <= '0;
            rd_bin_q <= '0;
            rd_gray_q <= '0;
            rd_empty_q <= 1'b1;
        end else begin
            wr_gray_rsync1_q_attr <= wr_gray_q;
            wr_gray_rsync2_q_attr <= wr_gray_rsync1_q_attr;
            rd_bin_q <= rd_bin_next;
            rd_gray_q <= rd_gray_next;
            rd_empty_q <= (rd_gray_next == wr_gray_rsync2_q_attr);
        end
    end

`ifdef FORMAL
    logic [PTR_BITS-1:0] wr_bin_prev_q, rd_bin_prev_q;
    logic [PTR_BITS-1:0] wr_gray_prev_q, rd_gray_prev_q;
    logic wr_fire_prev_q, rd_fire_prev_q;
    logic wr_seen_q, rd_seen_q;

    always_ff @(posedge wr_clk or posedge wr_rst) begin
        if (wr_rst) begin
            wr_bin_prev_q <= '0;
            wr_gray_prev_q <= '0;
            wr_fire_prev_q <= 1'b0;
            wr_seen_q <= 1'b0;
        end else begin
            if (wr_seen_q)
                assert(wr_bin_q == wr_bin_prev_q + wr_fire_prev_q);
            if (wr_seen_q && !wr_fire_prev_q)
                assert(wr_gray_q == wr_gray_prev_q);
            if (wr_seen_q && wr_fire_prev_q) begin
                assert(wr_gray_q != wr_gray_prev_q);
                assert(((wr_gray_q ^ wr_gray_prev_q) &
                        ((wr_gray_q ^ wr_gray_prev_q) - 1'b1)) == '0);
            end
            wr_bin_prev_q <= wr_bin_q;
            wr_gray_prev_q <= wr_gray_q;
            wr_fire_prev_q <= wr_fire;
            wr_seen_q <= 1'b1;
        end
    end

    always_ff @(posedge rd_clk or posedge rd_rst) begin
        if (rd_rst) begin
            rd_bin_prev_q <= '0;
            rd_gray_prev_q <= '0;
            rd_fire_prev_q <= 1'b0;
            rd_seen_q <= 1'b0;
        end else begin
            if (rd_seen_q)
                assert(rd_bin_q == rd_bin_prev_q + rd_fire_prev_q);
            if (rd_seen_q && !rd_fire_prev_q)
                assert(rd_gray_q == rd_gray_prev_q);
            if (rd_seen_q && rd_fire_prev_q) begin
                assert(rd_gray_q != rd_gray_prev_q);
                assert(((rd_gray_q ^ rd_gray_prev_q) &
                        ((rd_gray_q ^ rd_gray_prev_q) - 1'b1)) == '0);
            end
            rd_bin_prev_q <= rd_bin_q;
            rd_gray_prev_q <= rd_gray_q;
            rd_fire_prev_q <= rd_fire;
            rd_seen_q <= 1'b1;
        end
    end

    // Local-clock safety properties. Multi-clock SBY runs retain the two
    // independent clock inputs; these do not assume a phase relationship.
    always_ff @(posedge wr_clk) begin
        if (!wr_rst) begin
            assert(wr_gray_q == to_gray(wr_bin_q));
            assert(wr_ready == !wr_full_q);
            if (wr_full_q)
                assert(!wr_fire);
            if (wr_full_q)
                assert(!wr_ready);
        end
    end
    always_ff @(posedge rd_clk) begin
        if (!rd_rst) begin
            assert(rd_gray_q == to_gray(rd_bin_q));
            assert(rd_valid == !rd_empty_q);
            if (rd_empty_q)
                assert(!rd_fire);
            if (rd_empty_q)
                assert(!rd_valid);
        end
    end
`endif
endmodule
