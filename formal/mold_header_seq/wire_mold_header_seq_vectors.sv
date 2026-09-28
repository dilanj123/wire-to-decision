module mold_vector #(
    parameter integer CASE = 0
);
    (* gclk *) wire clk;
    reg [5:0] step = 0;
    wire rst = (step == 0);
    wire rearm = 0;
    wire [79:0] cfg_active_session = 80'h4142434445464748494a;
    wire [63:0] cfg_expected_sequence = (CASE == 5) ? 64'hfffffffffffffffe : 64'd100;
    wire in_valid = (step >= 1) && (step <= ((CASE == 0 || CASE == 5) ? 22 : ((CASE == 6 || CASE == 7) ? 21 : ((CASE == 8) ? 3 : 20))));
    wire [7:0] in_data = byte_at(step);
    wire in_last = (CASE == 0 || CASE == 5) ? (step == 22) : ((CASE == 6 || CASE == 7) ? (step == 21) : ((CASE == 8) ? (step == 3) : (step == 20)));
    wire packet_ready = 1;
    wire out_ready = 1;
    wire packet_result_valid = (CASE == 0 || CASE == 5) && (step >= 23);
    wire packet_result_success = 1;
    wire reject_ready = 1;
    wire in_ready, packet_valid, packet_body_empty, out_valid, out_last;
    wire [63:0] packet_sequence, current_expected_sequence;
    wire [15:0] packet_message_count;
    wire [7:0] out_data;
    wire packet_result_ready, reject_valid, reject_fatal, controller_valid, recovery_required;
    wire [2:0] reject_code;

    function automatic [7:0] byte_at(input [5:0] n);
        begin
            if (n <= 10) byte_at = 8'h40 + n;
            else if (n <= 18) begin
                if (CASE == 5 && n == 18) byte_at = 8'hfe;
                else if (CASE == 5) byte_at = 8'hff;
                else byte_at = (100 >> (8*(18-n))) & 8'hff;
            end else if (n == 19) begin
                if (CASE == 0) byte_at = 8'h00;
                else if (CASE == 1) byte_at = 8'h00;
                else if (CASE == 2 || CASE == 7) byte_at = 8'hff;
                else byte_at = 8'h00;
            end else if (n == 20) begin
                if (CASE == 0) byte_at = 8'h02;
                else if (CASE == 1) byte_at = 8'h00;
                else if (CASE == 2) byte_at = 8'hff;
                else if (CASE == 5) byte_at = 8'h02;
                else if (CASE == 9) byte_at = 8'h01;
                else if (CASE == 6) byte_at = 8'h00;
                else if (CASE == 7) byte_at = 8'hff;
                else byte_at = 8'h01;
            end else if (n == 21) byte_at = 8'hA5;
            else if (n == 22) byte_at = 8'h5A;
            else byte_at = 8'h00;
        end
    endfunction

    wire [79:0] session_for_case = (CASE == 3) ? 80'h5152535455565758595a : cfg_active_session;
    wire [63:0] expected_for_case = (CASE == 4) ? 64'd999 : cfg_expected_sequence;
    // The configuration substitutions above are intentionally public inputs
    // to the DUT, not references to implementation state.
    wire [79:0] cfg_session = session_for_case;
    wire [63:0] cfg_sequence = expected_for_case;

    wire_mold_header_seq dut (
        .clk(clk), .rst(rst), .cfg_active_session(cfg_session),
        .cfg_expected_sequence(cfg_sequence), .rearm(rearm),
        .in_valid(in_valid), .in_ready(in_ready), .in_data(in_data), .in_last(in_last),
        .packet_valid(packet_valid), .packet_ready(packet_ready),
        .packet_sequence(packet_sequence), .packet_message_count(packet_message_count),
        .packet_body_empty(packet_body_empty), .out_valid(out_valid),
        .out_ready(out_ready), .out_data(out_data), .out_last(out_last),
        .packet_result_valid(packet_result_valid), .packet_result_ready(packet_result_ready),
        .packet_result_success(packet_result_success), .reject_valid(reject_valid),
        .reject_ready(reject_ready), .reject_fatal(reject_fatal), .reject_code(reject_code),
        .controller_valid(controller_valid), .recovery_required(recovery_required),
        .current_expected_sequence(current_expected_sequence)
    );

    always @(posedge clk) if (step < 40) step <= step + 1;

    always @(posedge clk) begin
        if (!rst && packet_valid) begin
            assert(packet_sequence == ((CASE == 5) ? 64'hfffffffffffffffe : 64'd100));
            assert(packet_message_count == ((CASE == 0 || CASE == 5) ? 16'd2 : 16'd1));
        end
        if (CASE == 0 || CASE == 5) begin
            if (step < 24 && !rst) assert(current_expected_sequence == ((CASE == 5) ? 64'hfffffffffffffffe : 64'd100));
            if (step >= 25) assert(current_expected_sequence == ((CASE == 5) ? 64'd0 : 64'd102));
        end
        if (CASE == 1 && step >= 21) begin
            assert(!packet_valid);
            assert(!out_valid);
            assert(!reject_valid);
            assert(current_expected_sequence == 64'd100);
        end
        if (CASE == 2 && step >= 21) begin
            if (reject_valid) assert(reject_code == 3'd4);
            assert(recovery_required || reject_valid);
        end
        if ((CASE == 3 || CASE == 4) && step >= 21) begin
            if (reject_valid) assert(reject_code == ((CASE == 3) ? 3'd1 : 3'd2));
            assert(recovery_required || reject_valid);
        end
        if ((CASE == 6 || CASE == 7) && step >= 22) begin
            if (reject_valid) assert(reject_code == 3'd3);
            assert(recovery_required || reject_valid);
        end
        if (CASE == 8 && step >= 4) begin
            if (reject_valid) assert(reject_code == 3'd0);
            assert(recovery_required || reject_valid);
        end
        if (CASE == 9 && !rst && packet_valid) begin
            assert(packet_message_count == 16'd1);
            assert(packet_body_empty);
        end
    end

    always @(posedge clk) begin
        cover(packet_valid);
        cover(out_valid && out_last);
        cover(reject_valid);
        cover(recovery_required);
    end
endmodule
