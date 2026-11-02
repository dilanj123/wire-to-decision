// WIRE-D020 deterministic threshold crossing and finite decision budget.
// A commit is evaluated once; a generated decision owns its budget credit
// immediately and remains stable until consumed or explicitly re-armed.
module wire_decision_engine (
    input  logic clk,
    input  logic rst,
    input  logic rearm,

    input  logic [47:0] cfg_decision_threshold,
    input  logic [31:0] cfg_initial_budget,
    input  logic decision_enable,

    input  logic commit_valid,
    output logic commit_ready,
    input  logic [63:0] commit_mold_sequence,
    input  logic [47:0] commit_itch_timestamp,
    input  logic [47:0] commit_bid_total,
    input  logic [47:0] commit_ask_total,

    output logic decision_valid,
    input  logic decision_ready,
    output logic decision_action,
    output logic [63:0] decision_mold_sequence,
    output logic [47:0] decision_itch_timestamp,
    output logic signed [48:0] decision_signed_imbalance,

    output logic signed [48:0] previous_imbalance,
    output logic [31:0] remaining_budget,
    output logic [31:0] decision_count
);
    logic [47:0] threshold_q;
    logic signed [48:0] previous_q;
    logic [31:0] budget_q, decision_count_q;
    logic decision_valid_q, action_q;
    logic [63:0] decision_sequence_q;
    logic [47:0] decision_timestamp_q;
    logic signed [48:0] decision_imbalance_q;

    logic signed [48:0] bid_extended, ask_extended;
    logic signed [48:0] current_imbalance;
    logic signed [48:0] positive_threshold, negative_threshold;
    logic buy_crossing, sell_crossing;
    logic commit_fire;

    always_comb begin
        bid_extended = $signed({1'b0, commit_bid_total});
        ask_extended = $signed({1'b0, commit_ask_total});
        current_imbalance = bid_extended - ask_extended;
        positive_threshold = $signed({1'b0, threshold_q});
        negative_threshold = -positive_threshold;
        buy_crossing = (previous_q < positive_threshold) &&
                       (current_imbalance >= positive_threshold);
        sell_crossing = (previous_q > negative_threshold) &&
                        (current_imbalance <= negative_threshold);
    end

    assign commit_ready = !decision_valid_q && !rst && !rearm;
    assign commit_fire = commit_valid && commit_ready;
    assign decision_valid = decision_valid_q;
    assign decision_action = action_q;
    assign decision_mold_sequence = decision_sequence_q;
    assign decision_itch_timestamp = decision_timestamp_q;
    assign decision_signed_imbalance = decision_imbalance_q;
    assign previous_imbalance = previous_q;
    assign remaining_budget = budget_q;
    assign decision_count = decision_count_q;

    always_ff @(posedge clk) begin
        if (rst || rearm) begin
            threshold_q <= cfg_decision_threshold;
            previous_q <= 49'sd0;
            budget_q <= cfg_initial_budget;
            decision_count_q <= 32'd0;
            decision_valid_q <= 1'b0;
            action_q <= 1'b0;
            decision_sequence_q <= 64'd0;
            decision_timestamp_q <= 48'd0;
            decision_imbalance_q <= 49'sd0;
        end else begin
            if (decision_valid_q && decision_ready)
                decision_valid_q <= 1'b0;

            if (commit_fire) begin
                // WIRE-D010: every successful mutation advances the trajectory,
                // including disabled and exhausted-budget crossings.
                previous_q <= current_imbalance;

                if (decision_enable && (budget_q != 0) &&
                    (buy_crossing || sell_crossing)) begin
                    decision_valid_q <= 1'b1;
                    action_q <= sell_crossing;
                    decision_sequence_q <= commit_mold_sequence;
                    decision_timestamp_q <= commit_itch_timestamp;
                    decision_imbalance_q <= current_imbalance;
                    budget_q <= budget_q - 32'd1;
                    decision_count_q <= decision_count_q + 32'd1;
                end
            end
        end
    end

endmodule
