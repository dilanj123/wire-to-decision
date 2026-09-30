module mold_framer_rearm_check ();
    (* gclk *) wire clk;
    reg [4:0] step = 0;
    reg [1:0] index = 0;
    wire rst = (step == 0);
    wire rearm = (step == 5);
    wire packet_valid = (step == 1);
    wire packet_ready;
    wire [63:0] packet_sequence = 64'd17;
    wire [15:0] packet_message_count = 16'd1;
    wire packet_body_empty = 1'b0;
    wire in_valid = (step == 2);
    wire in_ready;
    wire [7:0] in_data = 8'h00;
    wire in_last = 1'b0;
    wire message_valid, message_ready=1'b0;
    wire [63:0] message_sequence;
    wire [15:0] message_length;
    wire message_empty;
    wire out_valid, out_ready=1'b0, out_last;
    wire [7:0] out_data;
    wire packet_result_valid, packet_result_ready=1'b0, packet_result_success;
    wire reject_valid, reject_ready=1'b0, reject_fatal;
    wire [1:0] reject_code;

    wire_mold_message_framer dut (.*);
    always @(posedge clk) begin
        if (step < 20) step <= step + 1'b1;
        if (rst) index <= 0;
        else if (in_valid && in_ready) index <= index + 1'b1;
        if (!rst && rearm) begin
            assert(!message_valid);
            assert(!out_valid);
            assert(!packet_result_valid);
            assert(!reject_valid);
        end
        if (step == 6) begin
            assert(packet_ready);
            assert(!message_valid && !out_valid && !packet_result_valid && !reject_valid);
        end
    end
endmodule
