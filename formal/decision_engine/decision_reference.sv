module decision_reference;
    (* gclk *) wire clk;
    (* anyseq *) logic rst, rearm;
    (* anyseq *) logic [47:0] cfg_decision_threshold;
    (* anyseq *) logic [31:0] cfg_initial_budget;
    (* anyseq *) logic decision_enable;
    (* anyseq *) logic commit_valid, decision_ready;
    (* anyseq *) logic [63:0] commit_mold_sequence;
    (* anyseq *) logic [47:0] commit_itch_timestamp;
    (* anyseq *) logic [47:0] commit_bid_total, commit_ask_total;
    wire commit_ready, decision_valid, decision_action;
    wire [63:0] decision_mold_sequence;
    wire [47:0] decision_itch_timestamp;
    wire signed [48:0] decision_signed_imbalance, previous_imbalance;
    wire [31:0] remaining_budget, decision_count;

    wire_decision_engine dut (.*);

    reg ref_valid = 0;
    reg ref_action = 0;
    reg [63:0] ref_sequence = 0;
    reg [47:0] ref_timestamp = 0;
    reg signed [48:0] ref_imbalance = 0;
    reg signed [48:0] ref_previous = 0;
    reg [47:0] ref_threshold = 0;
    reg [31:0] ref_budget = 0;
    reg [31:0] ref_initial_budget = 0;
    reg [31:0] ref_count = 0;
    reg past_valid = 0;

    wire signed [48:0] current_ref =
        $signed({1'b0, commit_bid_total}) - $signed({1'b0, commit_ask_total});
    wire signed [48:0] threshold_ref_signed = $signed({1'b0, ref_threshold});
    wire buy_ref = (ref_previous < threshold_ref_signed) &&
                   (current_ref >= threshold_ref_signed);
    wire sell_ref = (ref_previous > -threshold_ref_signed) &&
                    (current_ref <= -threshold_ref_signed);
    wire crossing_ref = decision_enable && (ref_budget != 0) && (buy_ref || sell_ref);

    always @(posedge clk) begin
        past_valid <= 1;
        if ($initstate) assume(rst);

        // Public-output independent reference state. No DUT-private state is read.
        if (past_valid) begin
            assert(decision_valid == ref_valid);
            assert(previous_imbalance == ref_previous);
            assert(remaining_budget == ref_budget);
            assert(decision_count == ref_count);
            assert(ref_count <= ref_initial_budget);
            assert(({1'b0, ref_budget} + {1'b0, ref_count}) ==
                   {1'b0, ref_initial_budget});
            if (ref_valid) begin
                assert(decision_action == ref_action);
                assert(decision_mold_sequence == ref_sequence);
                assert(decision_itch_timestamp == ref_timestamp);
                assert(decision_signed_imbalance == ref_imbalance);
            end
        end

        if (rst || rearm) begin
            ref_valid <= 0;
            ref_previous <= 0;
            ref_threshold <= cfg_decision_threshold;
            ref_initial_budget <= cfg_initial_budget;
            ref_budget <= cfg_initial_budget;
            ref_count <= 0;
            ref_action <= 0;
            ref_sequence <= 0;
            ref_timestamp <= 0;
            ref_imbalance <= 0;
        end else begin
            if (ref_valid && decision_ready)
                ref_valid <= 0;
            if (commit_valid && commit_ready) begin
                ref_previous <= current_ref;
                if (crossing_ref) begin
                    ref_valid <= 1;
                    ref_action <= sell_ref;
                    ref_sequence <= commit_mold_sequence;
                    ref_timestamp <= commit_itch_timestamp;
                    ref_imbalance <= current_ref;
                    ref_budget <= ref_budget - 1'b1;
                    ref_count <= ref_count + 1'b1;
                end
            end
        end

        // An upstream commit producer obeys transaction stability while stalled.
        if (past_valid && $past(!rst && !rearm && commit_valid && !commit_ready)) begin
            assume(commit_valid);
            assume(commit_mold_sequence == $past(commit_mold_sequence));
            assume(commit_itch_timestamp == $past(commit_itch_timestamp));
            assume(commit_bid_total == $past(commit_bid_total));
            assume(commit_ask_total == $past(commit_ask_total));
        end
        if (past_valid && !$past(rst || rearm)) begin
            if ($past(decision_valid && !decision_ready)) begin
                assert(decision_valid);
                assert(decision_action == $past(decision_action));
                assert(decision_mold_sequence == $past(decision_mold_sequence));
                assert(decision_itch_timestamp == $past(decision_itch_timestamp));
                assert(decision_signed_imbalance == $past(decision_signed_imbalance));
            end
            if ($past(commit_valid && commit_ready))
                assert(previous_imbalance == $past(current_ref));
            if ($past(!decision_valid && !(commit_valid && commit_ready)))
                assert(!decision_valid);
        end
    end
endmodule
