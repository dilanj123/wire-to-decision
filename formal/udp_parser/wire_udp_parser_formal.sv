module udp_safety (
    input logic clk, input logic rst,
    input logic [15:0] cfg_destination_udp_port,
    input logic [7:0] in_data, input logic in_valid, input logic in_last,
    input logic out_ready, input logic reject_ready
);
    logic in_ready, out_valid, out_last, reject_valid, reject_fatal;
    logic [7:0] out_data;
    logic [2:0] reject_code;
    wire_udp_parser dut (.*);

    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!rst) assume(cfg_destination_udp_port == 16'h1234);
        if (!rst && $past(!rst && in_valid && !in_ready)) begin
            assume(in_valid);
            assume(in_data == $past(in_data));
            assume(in_last == $past(in_last));
        end
        if (!rst && $past(!rst && out_valid && !out_ready)) begin
            assert(out_valid);
            assert(out_data == $past(out_data));
            assert(out_last == $past(out_last));
        end
        if (!rst && $past(!rst && reject_valid && !reject_ready)) begin
            assert(reject_valid);
            assert(reject_fatal == $past(reject_fatal));
            assert(reject_code == $past(reject_code));
            assert(!in_ready && !out_valid);
        end
    end
endmodule

module udp_header_case #(parameter integer CASE = 0) (
    input logic clk, input logic rst
);
    logic [15:0] cfg_destination_udp_port = 16'h1234;
    logic [7:0] in_data, out_data;
    logic in_valid, in_ready, in_last, out_valid, out_ready, out_last;
    logic reject_valid, reject_ready, reject_fatal;
    logic [2:0] reject_code;
    logic [3:0] index;

    function automatic [7:0] packet_byte(input integer n);
        begin
            case (CASE)
                0: case (n)
                    0: packet_byte=8'hca; 1: packet_byte=8'hfe;
                    2: packet_byte=8'h99; 3: packet_byte=8'h99;
                    4: packet_byte=8'h00; 5: packet_byte=8'h14;
                    6: packet_byte=8'h00; 7: packet_byte=8'h00;
                    default: packet_byte=0;
                endcase
                1: case (n)
                    0: packet_byte=8'hca; 1: packet_byte=8'hfe;
                    2: packet_byte=8'h12; 3: packet_byte=8'h34;
                    4: packet_byte=8'h00; 5: packet_byte=8'h14;
                    6: packet_byte=8'h00; 7: packet_byte=8'h01;
                    default: packet_byte=0;
                endcase
                2: case (n)
                    0: packet_byte=8'hca; 1: packet_byte=8'hfe;
                    2: packet_byte=8'h99; 3: packet_byte=8'h99;
                    4: packet_byte=8'h00; 5: packet_byte=8'h08;
                    6: packet_byte=8'h00; 7: packet_byte=8'h01;
                    default: packet_byte=0;
                endcase
                default: case (n)
                    0: packet_byte=8'hca; 1: packet_byte=8'hfe;
                    2: packet_byte=8'h12; 3: packet_byte=8'h34;
                    4: packet_byte=8'h00; 5: packet_byte=8'h08;
                    6: packet_byte=8'h00; 7: packet_byte=8'h00;
                    default: packet_byte=0;
                endcase
            endcase
        end
    endfunction

    assign in_valid = !rst && !reject_valid;
    assign in_data = packet_byte(index);
    assign in_last = (index == 7);
    assign out_ready = 1'b1;
    assign reject_ready = 1'b1;

    wire_udp_parser dut (.*);

    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!rst && in_valid && in_ready) index <= index + 1'b1;
        if (rst) index <= 0;
        if (!rst && reject_valid) begin
            if (CASE == 0 || CASE == 1) begin
                assert(reject_fatal); assert(reject_code == 3'd1);
            end else if (CASE == 2) begin
                assert(!reject_fatal); assert(reject_code == 3'd2);
            end else begin
                assert(reject_fatal); assert(reject_code == 3'd4);
            end
            assert(!out_valid);
        end
    end
endmodule

module udp_payload_correspondence (
    input logic clk, input logic rst
);
    logic [15:0] cfg_destination_udp_port = 16'h1234;
    logic [7:0] in_data, out_data;
    logic in_valid, in_ready, in_last, out_valid, out_ready, out_last;
    logic reject_valid, reject_ready, reject_fatal;
    logic [2:0] reject_code;
    logic [3:0] index;
    logic [1:0] outputs;
    function automatic [7:0] packet_byte(input integer n);
        case (n)
            0: packet_byte=8'hca; 1: packet_byte=8'hfe;
            2: packet_byte=8'h12; 3: packet_byte=8'h34;
            4: packet_byte=8'h00; 5: packet_byte=8'h0a;
            6: packet_byte=8'h00; 7: packet_byte=8'h00;
            8: packet_byte=8'haa; 9: packet_byte=8'h55;
            default: packet_byte=0;
        endcase
    endfunction
    assign in_valid = !rst && !reject_valid;
    assign in_data = packet_byte(index);
    assign in_last = (index == 9);
    assign out_ready = 1'b1;
    assign reject_ready = 1'b1;
    wire_udp_parser dut (.*);
    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (rst) begin index<=0; outputs<=0; end
        else begin
            if (in_valid && in_ready) index <= index + 1'b1;
            if (out_valid) begin
                assert(out_data == ((outputs == 0) ? 8'haa : 8'h55));
                assert(out_last == (outputs == 1));
            end
            if (out_valid && out_ready) outputs <= outputs + 1'b1;
            assert(!reject_valid);
        end
    end
endmodule

module udp_header_case1(input logic clk, input logic rst);
    udp_header_case #(.CASE(1)) impl(.clk(clk), .rst(rst));
endmodule
module udp_header_case2(input logic clk, input logic rst);
    udp_header_case #(.CASE(2)) impl(.clk(clk), .rst(rst));
endmodule
module udp_header_case3(input logic clk, input logic rst);
    udp_header_case #(.CASE(3)) impl(.clk(clk), .rst(rst));
endmodule

module udp_short_length (
    input logic clk, input logic rst
);
    logic [15:0] cfg_destination_udp_port = 16'h1234;
    logic [7:0] in_data, out_data;
    logic in_valid, in_ready, in_last, out_valid, out_ready, out_last;
    logic reject_valid, reject_ready, reject_fatal;
    logic [2:0] reject_code;
    logic [3:0] index;
    function automatic [7:0] packet_byte(input integer n);
        case (n)
            0: packet_byte=8'hca; 1: packet_byte=8'hfe;
            2: packet_byte=8'h12; 3: packet_byte=8'h34;
            4: packet_byte=8'h00; 5: packet_byte=8'h0a;
            6: packet_byte=8'h00; 7: packet_byte=8'h00;
            8: packet_byte=8'haa;
            default: packet_byte=0;
        endcase
    endfunction
    assign in_valid = !rst && !reject_valid;
    assign in_data = packet_byte(index);
    assign in_last = (index == 8);
    assign out_ready = 1'b1; assign reject_ready = 1'b1;
    wire_udp_parser dut (.*);
    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (rst) index<=0;
        else begin
            if (in_valid && in_ready) index<=index+1'b1;
            if (out_valid) assert(!out_last);
            if (reject_valid) begin assert(reject_fatal); assert(reject_code==3'd1); end
        end
    end
endmodule

module udp_long_length (
    input logic clk, input logic rst
);
    logic [15:0] cfg_destination_udp_port = 16'h1234;
    logic [7:0] in_data, out_data;
    logic in_valid, in_ready, in_last, out_valid, out_ready, out_last;
    logic reject_valid, reject_ready, reject_fatal;
    logic [2:0] reject_code;
    logic [3:0] index;
    function automatic [7:0] packet_byte(input integer n);
        case (n)
            0: packet_byte=8'hca; 1: packet_byte=8'hfe;
            2: packet_byte=8'h12; 3: packet_byte=8'h34;
            4: packet_byte=8'h00; 5: packet_byte=8'h09;
            6: packet_byte=8'h00; 7: packet_byte=8'h00;
            8: packet_byte=8'haa; 9: packet_byte=8'h55;
            default: packet_byte=0;
        endcase
    endfunction
    assign in_valid = !rst && !reject_valid;
    assign in_data = packet_byte(index);
    assign in_last = (index == 9);
    assign out_ready = 1'b1; assign reject_ready = 1'b1;
    wire_udp_parser dut (.*);
    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (rst) index<=0;
        else begin
            if (in_valid && in_ready) index<=index+1'b1;
            if (out_valid) assert(!out_last);
            if (reject_valid) begin assert(reject_fatal); assert(reject_code==3'd1); end
        end
    end
endmodule

module udp_cover (
    input logic clk, input logic rst,
    input logic [15:0] cfg_destination_udp_port,
    input logic [7:0] in_data, input logic in_valid, input logic in_last,
    input logic out_ready, input logic reject_ready
);
    logic in_ready, out_valid, out_last, reject_valid, reject_fatal;
    logic [7:0] out_data;
    logic [2:0] reject_code;
    wire_udp_parser dut (.*);
    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!rst && $past(!rst && in_valid && !in_ready)) begin
            assume(in_valid); assume(in_data == $past(in_data));
            assume(in_last == $past(in_last));
        end
        if (!rst) begin
            cover(out_valid && out_ready && out_last);
            cover(reject_valid && reject_ready && reject_code == 3'd1);
            cover(reject_valid && reject_ready && reject_code == 3'd2);
            cover(reject_valid && reject_ready && reject_code == 3'd3);
            cover(reject_valid && reject_ready && reject_code == 3'd4);
            cover(out_valid && !out_ready);
            cover(reject_valid && !reject_ready);
        end
    end
endmodule

module udp_next_packet(input logic clk, input logic rst);
    logic [15:0] cfg_destination_udp_port = 16'h1234;
    logic [7:0] in_data, out_data;
    logic in_valid, in_ready, in_last, out_valid, out_ready, out_last;
    logic reject_valid, reject_ready, reject_fatal;
    logic [2:0] reject_code;
    logic [4:0] index;
    logic [1:0] outputs;
    function automatic [7:0] packet_byte(input integer n);
        case (n % 9)
            0: packet_byte=8'hca; 1: packet_byte=8'hfe;
            2: packet_byte=8'h12; 3: packet_byte=8'h34;
            4: packet_byte=8'h00; 5: packet_byte=8'h09;
            6: packet_byte=8'h00; 7: packet_byte=8'h00;
            default: packet_byte=(n < 9) ? 8'haa : 8'hbb;
        endcase
    endfunction
    assign in_valid = !rst && !reject_valid;
    assign in_data = packet_byte(index);
    assign in_last = (index == 8) || (index == 17);
    assign out_ready = 1'b1; assign reject_ready = 1'b1;
    wire_udp_parser dut (.*);
    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (rst) begin index<=0; outputs<=0; end
        else begin
            if (in_valid && in_ready) index<=index+1'b1;
            if (out_valid) begin
                assert(out_data == ((outputs == 0) ? 8'haa : 8'hbb));
                assert(out_last);
            end
            if (out_valid && out_ready) outputs<=outputs+1'b1;
            assert(!reject_valid);
        end
    end
endmodule
