module mold_framer_safety (
    input logic clk, input logic rst, input logic rearm,
    input logic packet_valid, input logic [63:0] packet_sequence,
    input logic [15:0] packet_message_count, input logic packet_body_empty,
    input logic in_valid, input logic [7:0] in_data, input logic in_last,
    input logic message_ready, input logic out_ready,
    input logic packet_result_ready, input logic reject_ready
);
    logic packet_ready, in_ready, message_valid, message_empty;
    logic [63:0] message_sequence;
    logic [15:0] message_length;
    logic out_valid, out_last;
    logic [7:0] out_data;
    logic packet_result_valid, packet_result_success;
    logic reject_valid, reject_fatal;
    logic [1:0] reject_code;

    wire_mold_message_framer dut (.*);

    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!rst && !rearm && $past(!rst && !rearm && in_valid && !in_ready)) begin
            assume(in_valid);
            assume(in_data == $past(in_data));
            assume(in_last == $past(in_last));
        end
        if (!rst && !rearm && $past(!rst && !rearm && packet_valid && !packet_ready)) begin
            assume(packet_valid);
            assume(packet_sequence == $past(packet_sequence));
            assume(packet_message_count == $past(packet_message_count));
            assume(packet_body_empty == $past(packet_body_empty));
        end
        if (!rst && !rearm && $past(!rst && !rearm && message_valid && !message_ready)) begin
            assert(message_valid);
            assert(message_sequence == $past(message_sequence));
            assert(message_length == $past(message_length));
            assert(message_empty == $past(message_empty));
            assert(!in_ready && !out_valid);
        end
        if (!rst && !rearm && $past(!rst && !rearm && out_valid && !out_ready)) begin
            assert(out_valid);
            assert(out_data == $past(out_data));
            assert(out_last == $past(out_last));
        end
        if (!rst && !rearm && $past(!rst && !rearm && packet_result_valid && !packet_result_ready)) begin
            assert(packet_result_valid);
            assert(packet_result_success == $past(packet_result_success));
        end
        if (!rst && !rearm && $past(!rst && !rearm && reject_valid && !reject_ready)) begin
            assert(reject_valid);
            assert(reject_fatal == $past(reject_fatal));
            assert(reject_code == $past(reject_code));
        end
    end
endmodule
