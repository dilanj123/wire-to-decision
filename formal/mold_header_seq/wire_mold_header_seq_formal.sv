module mold_safety;
    (* gclk *) wire clk;
    logic rst, rearm;
    logic [79:0] cfg_active_session;
    logic [63:0] cfg_expected_sequence;
    logic in_valid, in_last;
    logic [7:0] in_data;
    logic packet_ready, out_ready, packet_result_valid, packet_result_success, reject_ready;
    wire in_ready, packet_valid, packet_body_empty, out_valid, out_last;
    wire [63:0] packet_sequence, current_expected_sequence;
    wire [15:0] packet_message_count;
    wire [7:0] out_data;
    wire packet_result_ready, reject_valid, reject_fatal, controller_valid, recovery_required;
    wire [2:0] reject_code;

    wire_mold_header_seq dut (.*);

    reg past_valid = 0;
    always @(posedge clk) past_valid <= 1;

    // Legal-source stability is an explicit assumption of this local proof.
    always @(posedge clk) if (past_valid && $past(!rst && !rearm && in_valid && !in_ready)) begin
        assume(in_valid);
        assume(in_data == $past(in_data));
        assume(in_last == $past(in_last));
    end

    always @(posedge clk) begin
        if (past_valid && !$past(rst) && !$past(rearm) && $past(out_valid && !out_ready)) begin
            assert(out_valid);
            assert(out_data == $past(out_data));
            assert(out_last == $past(out_last));
        end
        if (past_valid && !$past(rst) && !$past(rearm) && $past(reject_valid && !reject_ready)) begin
            assert(reject_valid);
            assert(reject_code == $past(reject_code));
            assert(reject_fatal == $past(reject_fatal));
            assert(!in_ready);
            assert(!out_valid);
        end
        if (past_valid && !$past(rst) && !$past(rearm) && $past(packet_valid && !packet_ready)) begin
            assert(packet_valid);
            assert(packet_sequence == $past(packet_sequence));
            assert(packet_message_count == $past(packet_message_count));
            assert(packet_body_empty == $past(packet_body_empty));
            assert(!in_ready);
            assert(!out_valid);
        end
        if (past_valid && !$past(rst) && !$past(rearm) && $past(recovery_required)) begin
            assert(recovery_required);
            assert(!in_ready);
            assert(!packet_valid);
            assert(!out_valid);
            assert(!packet_result_ready);
        end
        if (past_valid && !$past(rst) && !$past(rearm) && $past(packet_result_valid && packet_result_ready && packet_result_success))
            assert(current_expected_sequence == $past(current_expected_sequence) + {48'd0, $past(packet_message_count)});
        if (past_valid && !$past(rst) && !$past(rearm) && !$past(packet_result_valid && packet_result_ready && packet_result_success))
            assert(current_expected_sequence == $past(current_expected_sequence));
    end

    // Reset is synchronous and establishes a configuration epoch. The proof
    // intentionally leaves packet and result readiness unconstrained.
    always @(posedge clk) begin
        if ($initstate) begin
            assume(rst);
        end
    end
endmodule

module mold_cover;
    mold_safety base();
    always @(posedge base.clk) begin
        cover(base.packet_valid);
        cover(base.out_valid);
        cover(base.reject_valid);
        cover(base.packet_result_valid && base.packet_result_ready && base.packet_result_success);
        cover(base.recovery_required && base.rearm);
    end
endmodule
