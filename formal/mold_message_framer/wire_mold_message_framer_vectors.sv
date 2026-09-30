module mold_framer_vector #(parameter integer CASE = 0) ();
    (* gclk *) wire clk;
    reg [5:0] step = 0;
    reg [3:0] input_index = 0;
    reg [1:0] metadata_index = 0;
    reg [2:0] output_index = 0;
    wire rst = (step == 0);
    wire rearm = 1'b0;
    wire packet_valid = (step == 1);
    wire packet_ready;
    wire [63:0] packet_sequence = ((CASE == 0) || (CASE == 7)) ? 64'hfffffffffffffffe : 64'd100;
    wire [15:0] packet_message_count = (CASE == 4) ? 16'd2 :
                                       ((CASE == 7) ? 16'd3 :
                                       ((CASE == 8) ? 16'd3 : 16'd1));
    wire packet_body_empty = (CASE == 5);
    wire in_valid = (step >= 2) && (input_index < body_size(CASE));
    wire in_ready;
    wire [7:0] in_data = body_byte(CASE, input_index);
    wire in_last = (input_index == body_size(CASE)-1);
    wire message_valid, message_ready = 1'b1;
    wire [63:0] message_sequence;
    wire [15:0] message_length;
    wire message_empty;
    wire out_valid, out_ready = 1'b1, out_last;
    wire [7:0] out_data;
    wire packet_result_valid, packet_result_ready = 1'b1, packet_result_success;
    wire reject_valid, reject_ready = 1'b1, reject_fatal;
    wire [1:0] reject_code;

    function automatic [3:0] body_size(input integer c);
        case (c)
            0: body_size=4;                 // one two-byte message
            1: body_size=1;                 // incomplete length field
            2: body_size=4;                 // length 3, only 2 payload bytes
            3: body_size=4;                 // complete block then trailing byte
            4: body_size=3;                 // count two, only one complete block
            5: body_size=0;                  // body_empty positive-count packet
            6: body_size=2;                  // one zero-length message
            7: body_size=6;                  // three zero-length messages, sequence wrap
            8: body_size=10;                 // two complete prefix messages + truncated third
            default: body_size=0;
        endcase
    endfunction

    function automatic [7:0] body_byte(input integer c, input integer n);
        case (c)
            0: case (n) 0:body_byte=0; 1:body_byte=2; 2:body_byte=8'ha5; default:body_byte=8'h5a; endcase
            1: body_byte=0;
            2: case (n) 0:body_byte=0; 1:body_byte=3; 2:body_byte=8'ha5; default:body_byte=8'h5a; endcase
            3: case (n) 0:body_byte=0; 1:body_byte=1; 2:body_byte=8'ha5; default:body_byte=8'h99; endcase
            4: case (n) 0:body_byte=0; 1:body_byte=1; default:body_byte=8'ha5; endcase
            6,7: body_byte=0;
            8: case (n)
                0:body_byte=0; 1:body_byte=1; 2:body_byte=8'ha1;
                3:body_byte=0; 4:body_byte=1; 5:body_byte=8'hb2;
                6:body_byte=0; 7:body_byte=5; 8:body_byte=8'hc3;
                default:body_byte=8'hd4;
            endcase
            default: body_byte=0;
        endcase
    endfunction

    wire_mold_message_framer dut (.*);

    always @(posedge clk) begin
        if (step < 50) step <= step + 1'b1;
        if (rst) begin input_index <= 0; metadata_index <= 0; output_index <= 0; end
        else begin
            if (in_valid && in_ready) input_index <= input_index + 1'b1;
            if (message_valid && message_ready) metadata_index <= metadata_index + 1'b1;
            if (out_valid && out_ready) output_index <= output_index + 1'b1;
        end

        if (!rst) begin
            if (message_valid) begin
                assert(message_sequence == packet_sequence + metadata_index);
                if (CASE == 0) begin assert(message_length == 2); assert(!message_empty); end
                if (CASE == 2) begin assert(message_length == 3); assert(!message_empty); end
                if (CASE == 3 || CASE == 4) begin assert(message_length == 1); end
                if (CASE == 6) begin assert(message_length == 0); assert(message_empty); end
                if (CASE == 7) begin assert(message_length == 0); assert(message_empty); end
                if (CASE == 8) begin
                    if (metadata_index < 2) assert(message_length == 1);
                    else assert(message_length == 5);
                    assert(!message_empty);
                end
            end
            if (CASE == 0 && out_valid) begin
                assert(out_data == ((out_last) ? 8'h5a : 8'ha5));
                assert(out_last == (out_data == 8'h5a));
            end
            if (CASE == 2 && out_valid) begin
                assert(out_data == ((output_index == 0) ? 8'ha5 : 8'h5a));
                assert(!out_last);
            end
            if ((CASE == 3 || CASE == 4) && out_valid) begin
                assert(out_data == 8'ha5);
                assert(out_last);
            end
            if (CASE == 8 && out_valid) begin
                case (output_index)
                    0: begin assert(out_data == 8'ha1); assert(out_last); end
                    1: begin assert(out_data == 8'hb2); assert(out_last); end
                    2: begin assert(out_data == 8'hc3); assert(!out_last); end
                    default: begin assert(out_data == 8'hd4); assert(!out_last); end
                endcase
            end
            if (CASE == 1 && reject_valid) begin assert(reject_code == 0); assert(packet_result_valid && !packet_result_success); end
            if (CASE == 2 && reject_valid) begin assert(reject_code == 1); assert(packet_result_valid && !packet_result_success); end
            if (CASE == 3 && reject_valid) begin assert(reject_code == 2); assert(packet_result_valid && !packet_result_success); end
            if (CASE == 4 && reject_valid) begin assert(reject_code == 0); assert(packet_result_valid && !packet_result_success); end
            if (CASE == 5 && reject_valid) begin assert(reject_code == 0); assert(packet_result_valid && !packet_result_success); end
            if (CASE == 8 && reject_valid) begin assert(reject_code == 1); assert(packet_result_valid && !packet_result_success); end
            if ((CASE == 0 || CASE == 6 || CASE == 7) && packet_result_valid) assert(packet_result_success);
            if (CASE != 0 && CASE != 6 && CASE != 7 && packet_result_valid) assert(!packet_result_success);
        end
        if (CASE == 0) begin
            cover(packet_result_valid && packet_result_success);
            cover(out_valid && out_last);
        end
        if (CASE == 6 || CASE == 7) cover(message_valid && message_empty);
        if ((CASE >= 1 && CASE <= 5) || CASE == 8) cover(reject_valid);
        if (CASE == 8) cover(reject_valid && output_index >= 2);
    end
endmodule

module mold_framer_valid_case(input logic clk); mold_framer_vector #(.CASE(0)) x(); endmodule
module mold_framer_len_trunc_case(input logic clk); mold_framer_vector #(.CASE(1)) x(); endmodule
module mold_framer_payload_trunc_case(input logic clk); mold_framer_vector #(.CASE(2)) x(); endmodule
module mold_framer_trailing_case(input logic clk); mold_framer_vector #(.CASE(3)) x(); endmodule
module mold_framer_count_short_case(input logic clk); mold_framer_vector #(.CASE(4)) x(); endmodule
module mold_framer_empty_body_case(input logic clk); mold_framer_vector #(.CASE(5)) x(); endmodule
module mold_framer_zero_message_case(input logic clk); mold_framer_vector #(.CASE(6)) x(); endmodule
module mold_framer_wrap_case(input logic clk); mold_framer_vector #(.CASE(7)) x(); endmodule
module mold_framer_late_suffix_case(input logic clk); mold_framer_vector #(.CASE(8)) x(); endmodule
