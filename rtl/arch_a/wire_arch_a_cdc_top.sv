// CDC learning wrapper: asynchronous RX framed beats -> the unchanged
// single-clock Architecture-A functional parser/book/decision top.
/* verilator lint_off DECLFILENAME */
module wire_cdc_epoch_domain (
    input  logic clk,
    input  logic arst,
    input  logic local_fault,
    input  logic peer_up_async,
    input  logic rearm_async,
    output logic epoch_up,
    output logic local_ready,
    output logic domain_reset
);
    (* async_reg = "true" *) logic [1:0] peer_up_sync_q;
    (* async_reg = "true" *) logic [1:0] rearm_sync_q;
    (* async_reg = "true" *) logic [1:0] rearm_valid_q;
    logic peer_seen_q;
    logic rearm_low_seen_q;
    logic rearm_pending_q;
    logic peer_down_seen_q;
    (* async_reg = "true" *) logic [1:0] reset_release_q;

    wire domain_arst = arst || !epoch_up || !peer_up_sync_q[1];

    always_ff @(posedge clk or posedge arst) begin
        if (arst) begin
            peer_up_sync_q <= '0;
            rearm_sync_q <= '0;
            rearm_valid_q <= '0;
        end else begin
            peer_up_sync_q <= {peer_up_sync_q[0], peer_up_async};
            rearm_sync_q <= {rearm_sync_q[0], rearm_async};
            rearm_valid_q <= {rearm_valid_q[0], 1'b1};
        end
    end

    // The peer-ready level remains low until that peer is explicitly rearmed.
    // A low observed after the peer was once up latches local epoch invalidity.
    always_ff @(posedge clk or posedge arst) begin
        if (arst) begin
            epoch_up <= 1'b0;
            peer_seen_q <= 1'b0;
            rearm_low_seen_q <= 1'b0;
            rearm_pending_q <= 1'b0;
            peer_down_seen_q <= 1'b0;
        end else if (peer_seen_q && !peer_up_sync_q[1] && !rearm_pending_q) begin
            // A one-sided reset is reported by the peer-up level. If rearm is
            // already low, remember that low and still require its later high.
            epoch_up <= 1'b0;
            peer_seen_q <= 1'b0;
            rearm_low_seen_q <= rearm_valid_q[1] && !rearm_sync_q[1];
            rearm_pending_q <= 1'b0;
            peer_down_seen_q <= 1'b1;
        end else if (local_fault) begin
            // Parser/book recovery invalidates this stream epoch. The peer
            // learns through the same synchronized epoch-up level.
            epoch_up <= 1'b0;
            peer_seen_q <= 1'b0;
            rearm_low_seen_q <= rearm_valid_q[1] && !rearm_sync_q[1];
            rearm_pending_q <= 1'b0;
            peer_down_seen_q <= 1'b0;
        end else begin
            if (peer_up_sync_q[1])
                peer_seen_q <= 1'b1;
            if (rearm_valid_q[1] && !rearm_sync_q[1] && !rearm_pending_q)
                rearm_low_seen_q <= 1'b1;
            if (rearm_valid_q[1] && rearm_sync_q[1] &&
                    rearm_low_seen_q && !rearm_pending_q) begin
                // Every explicit low/high rearm starts a fresh FIFO/parser
                // epoch, including when the wrapper was already active.
                epoch_up <= 1'b0;
                peer_seen_q <= 1'b0;
                rearm_low_seen_q <= 1'b0;
                rearm_pending_q <= 1'b1;
                peer_down_seen_q <= !peer_up_sync_q[1];
            end else if (rearm_pending_q) begin
                if (!peer_up_sync_q[1]) begin
                    peer_down_seen_q <= 1'b1;
                    peer_seen_q <= 1'b0;
                end
                if (peer_down_seen_q && rearm_valid_q[1] && rearm_sync_q[1]) begin
                    epoch_up <= 1'b1;
                    rearm_pending_q <= 1'b0;
                    peer_down_seen_q <= 1'b0;
                end
            end
        end
    end

    // Asynchronous assertion, two local-clock synchronous release stages.
    always_ff @(posedge clk or posedge domain_arst) begin
        if (domain_arst)
            reset_release_q <= '0;
        else
            reset_release_q <= {reset_release_q[0], 1'b1};
    end

    assign domain_reset = domain_arst || !reset_release_q[1];
    assign local_ready = epoch_up && peer_up_sync_q[1] && !domain_reset;
endmodule
/* verilator lint_on DECLFILENAME */

module wire_arch_a_cdc_top #(
    parameter integer BOOK_NUM_SETS = 512
) (
    input  logic        rx_clk,
    input  logic        proc_clk,
    input  logic        rx_rst,
    input  logic        proc_rst,
    input  logic        rearm,

    input  logic [31:0] cfg_destination_ipv4,
    input  logic [15:0] cfg_destination_udp_port,
    input  logic [79:0] cfg_active_session,
    input  logic [63:0] cfg_expected_sequence,
    input  logic [15:0] cfg_tracked_stock_locate,
    input  logic        cfg_symbol_check_enable,
    input  logic [63:0] cfg_expected_stock_symbol,
    input  logic [47:0] cfg_decision_threshold,
    input  logic [31:0] cfg_initial_budget,
    input  logic        decision_enable,

    input  logic [63:0] rx_data,
    input  logic [7:0]  rx_keep,
    input  logic        rx_valid,
    output logic        rx_ready,
    input  logic        rx_last,

    output logic        decision_valid,
    input  logic        decision_ready,
    output logic        decision_action,
    output logic [63:0] decision_mold_sequence,
    output logic [47:0] decision_itch_timestamp,
    output logic signed [48:0] decision_signed_imbalance,

    output logic        rx_epoch_ready,
    output logic        proc_epoch_ready,
    output logic        cdc_ready,
    output logic        parser_valid,
    output logic        parser_recovery_required,
    output logic        book_valid,
    output logic        book_recovery_required,
    output logic [47:0] bid_total,
    output logic [47:0] ask_total,
    output logic [63:0] current_expected_sequence,
    output logic [3:0]  parser_recovery_stage,
    output logic [5:0]  stage_reject_observed,
    output logic [5:0]  stage_reject_fatal,
    output logic [16:0] stage_reject_code,
    output logic        error_valid,
    output logic [3:0]  error_code,
    output logic        fifo_read_valid_observed,
    output logic        fifo_read_ready_observed,
    output logic [72:0] fifo_read_data_observed
);
    logic rx_epoch_up, proc_epoch_up;
    logic rx_domain_reset, proc_domain_reset;
    (* async_reg = "true" *) logic [1:0] proc_ready_sync_rx_q;
    (* async_reg = "true" *) logic [1:0] rx_ready_sync_proc_q;
    logic rx_active, proc_active;

    logic [72:0] fifo_wr_data, fifo_rd_data;
    logic fifo_wr_ready, fifo_rd_valid, core_rx_ready;
    logic core_decision_valid;
    logic [63:0] core_decision_sequence;
    logic [47:0] core_decision_timestamp;
    logic signed [48:0] core_decision_imbalance;

    wire_cdc_epoch_domain rx_epoch (
        .clk(rx_clk), .arst(rx_rst), .local_fault(1'b0), .peer_up_async(proc_epoch_up),
        .rearm_async(rearm), .epoch_up(rx_epoch_up),
        .local_ready(rx_epoch_ready), .domain_reset(rx_domain_reset)
    );
    wire_cdc_epoch_domain proc_epoch (
        .clk(proc_clk), .arst(proc_rst),
        .local_fault(parser_recovery_required || book_recovery_required),
        .peer_up_async(rx_epoch_up),
        .rearm_async(rearm), .epoch_up(proc_epoch_up),
        .local_ready(proc_epoch_ready), .domain_reset(proc_domain_reset)
    );

    // Exchange the fully released local-ready levels. Each side accepts work
    // only after its own reset release and the peer's ready level are observed.
    always_ff @(posedge rx_clk or posedge rx_rst) begin
        if (rx_rst)
            proc_ready_sync_rx_q <= '0;
        else
            proc_ready_sync_rx_q <= {proc_ready_sync_rx_q[0], proc_epoch_ready};
    end
    always_ff @(posedge proc_clk or posedge proc_rst) begin
        if (proc_rst)
            rx_ready_sync_proc_q <= '0;
        else
            rx_ready_sync_proc_q <= {rx_ready_sync_proc_q[0], rx_epoch_ready};
    end

    assign rx_active = rx_epoch_ready && proc_ready_sync_rx_q[1];
    assign proc_active = proc_epoch_ready && rx_ready_sync_proc_q[1];
    assign cdc_ready = rx_active && proc_active;

    assign fifo_wr_data = {rx_data, rx_keep, rx_last};
    assign fifo_read_valid_observed = fifo_rd_valid;
    assign fifo_read_ready_observed = proc_active && core_rx_ready;
    assign fifo_read_data_observed = fifo_rd_data;
    assign rx_ready = rx_active && fifo_wr_ready;

    wire_async_fifo #(.WIDTH(73), .DEPTH(8)) ingress_async_fifo (
        .wr_clk(rx_clk), .wr_rst(rx_domain_reset),
        .wr_data(fifo_wr_data), .wr_valid(rx_valid && rx_active),
        .wr_ready(fifo_wr_ready),
        .rd_clk(proc_clk), .rd_rst(proc_domain_reset),
        .rd_data(fifo_rd_data), .rd_valid(fifo_rd_valid),
        .rd_ready(proc_active && core_rx_ready)
    );

    // The omitted production diagnostics are intentionally not part of this
    // small CDC wrapper interface.
    /* verilator lint_off PINCONNECTEMPTY */
    /* verilator lint_off SYNCASYNCNET */
    wire_arch_a_functional_top #(.BOOK_NUM_SETS(BOOK_NUM_SETS)) functional_core (
        .clk(proc_clk), .rst(proc_domain_reset), .rearm(1'b0),
        .cfg_destination_ipv4(cfg_destination_ipv4),
        .cfg_destination_udp_port(cfg_destination_udp_port),
        .cfg_active_session(cfg_active_session),
        .cfg_expected_sequence(cfg_expected_sequence),
        .cfg_tracked_stock_locate(cfg_tracked_stock_locate),
        .cfg_symbol_check_enable(cfg_symbol_check_enable),
        .cfg_expected_stock_symbol(cfg_expected_stock_symbol),
        .cfg_decision_threshold(cfg_decision_threshold),
        .cfg_initial_budget(cfg_initial_budget), .decision_enable(decision_enable),
        .rx_data(fifo_rd_data[72:9]), .rx_keep(fifo_rd_data[8:1]),
        .rx_valid(fifo_rd_valid && proc_active), .rx_ready(core_rx_ready),
        .rx_last(fifo_rd_data[0]),
        .decision_valid(core_decision_valid),
        .decision_ready(decision_ready && proc_active),
        .decision_action(decision_action),
        .decision_mold_sequence(core_decision_sequence),
        .decision_itch_timestamp(core_decision_timestamp),
        .decision_signed_imbalance(core_decision_imbalance),
        .parser_valid(parser_valid),
        .parser_recovery_required(parser_recovery_required),
        .parser_recovery_stage(parser_recovery_stage), .current_expected_sequence(current_expected_sequence),
        .book_valid(book_valid), .book_recovery_required(book_recovery_required),
        .bid_total(bid_total), .ask_total(ask_total), .previous_imbalance(),
        .remaining_budget(), .decision_count(),
        .error_valid(error_valid), .error_ready(1'b1), .error_code(error_code),
        .stage_reject_observed(stage_reject_observed),
        .stage_reject_fatal(stage_reject_fatal), .stage_reject_code(stage_reject_code),
        .debug_reference(64'd0), .debug_found(), .debug_price(),
        .debug_remaining_quantity(), .debug_side(),
        .last_accepted_event_stock_locate(), .debug_set_index(), .debug_way(),
        .event_valid_observed(), .event_ready_observed(), .event_kind_observed(),
        .event_mold_sequence_observed(), .commit_valid_observed(),
        .commit_ready_observed(), .commit_mold_sequence_observed(),
        .commit_bid_total_observed(), .commit_ask_total_observed()
    );
    /* verilator lint_on SYNCASYNCNET */
    /* verilator lint_on PINCONNECTEMPTY */

    // Gate the old epoch's pending output as soon as local peer readiness falls.
    assign decision_valid = core_decision_valid && proc_active;
    assign decision_mold_sequence = core_decision_sequence;
    assign decision_itch_timestamp = core_decision_timestamp;
    assign decision_signed_imbalance = core_decision_imbalance;
endmodule
