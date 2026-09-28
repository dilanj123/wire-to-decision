// Targeted public-interface formal harnesses for WIRE-017A.
// These harnesses deliberately split classification and data-path obligations.

module ipv4_header_correspondence;
    logic clk, rst;
    logic [31:0] cfg = 32'hC6336407;
    logic [7:0] in_data;
    logic in_valid, in_ready, in_last;
    logic [7:0] out_data;
    logic out_valid, out_ready, out_last;
    logic reject_valid, reject_ready, reject_fatal;
    logic [3:0] reject_code;
    logic [2:0] scenario;
    logic [5:0] index;

    localparam logic [159:0] H0 = 160'h450000140000400040114E9DC0000201C6336407;
    localparam logic [159:0] H1 = 160'h650000180000400040112E99C0000201C6336407;
    localparam logic [159:0] H2 = 160'h440000180000400040114F99C0000201C6336407;
    localparam logic [159:0] H3 = 160'h450000130000400040114E9EC0000201C6336407;
    localparam logic [159:0] H4 = 160'h450000180000400040111234C0000201C6336407;
    localparam logic [159:0] H5 = 160'h450000180000200040116E99C0000201C6336407;
    localparam logic [159:0] H6 = 160'h4500001800004000401174CEC000020101020304;
    localparam logic [159:0] H7 = 160'h450000180000400040064EA4C0000201C6336407;

    function automatic logic [159:0] selected_header(input logic [2:0] s);
        case (s)
            3'd0: selected_header = H0;
            3'd1: selected_header = H1;
            3'd2: selected_header = H2;
            3'd3: selected_header = H3;
            3'd4: selected_header = H4;
            3'd5: selected_header = H5;
            3'd6: selected_header = H6;
            default: selected_header = H7;
        endcase
    endfunction
    function automatic logic [3:0] expected_code(input logic [2:0] s);
        case (s)
            3'd0: expected_code = 4'h8; // Total Length 24 is empty at this stage.
            3'd1: expected_code = 4'h0;
            3'd2: expected_code = 4'h1;
            3'd3: expected_code = 4'h2;
            3'd4: expected_code = 4'h3;
            3'd5: expected_code = 4'h4;
            3'd6: expected_code = 4'h5;
            default: expected_code = 4'h6;
        endcase
    endfunction

    wire [159:0] header = selected_header(scenario);
    always_comb begin
        in_valid = !rst && (index < 20);
        in_last = (index == 19);
        case (index)
            0: in_data = header[159:152]; 1: in_data = header[151:144];
            2: in_data = header[143:136]; 3: in_data = header[135:128];
            4: in_data = header[127:120]; 5: in_data = header[119:112];
            6: in_data = header[111:104]; 7: in_data = header[103:96];
            8: in_data = header[95:88]; 9: in_data = header[87:80];
            10: in_data = header[79:72]; 11: in_data = header[71:64];
            12: in_data = header[63:56]; 13: in_data = header[55:48];
            14: in_data = header[47:40]; 15: in_data = header[39:32];
            16: in_data = header[31:24]; 17: in_data = header[23:16];
            18: in_data = header[15:8]; 19: in_data = header[7:0];
            default: in_data = 8'h00;
        endcase
    end
    assign out_ready = 1'b1;
    assign reject_ready = 1'b1;

    wire input_fire = in_valid && in_ready;
    wire reject_fire = reject_valid && reject_ready;
    wire expected_fatal = (scenario == 3'd0) ||
                          (scenario >= 3'd3 && scenario <= 3'd5);

    wire_ipv4_parser dut (
        .clk(clk), .rst(rst), .cfg_destination_ipv4(cfg),
        .in_data(in_data), .in_valid(in_valid), .in_ready(in_ready), .in_last(in_last),
        .out_data(out_data), .out_valid(out_valid), .out_ready(out_ready), .out_last(out_last),
        .reject_valid(reject_valid), .reject_ready(reject_ready),
        .reject_fatal(reject_fatal), .reject_code(reject_code)
    );

    always @(posedge clk) begin
        if ($initstate) begin assume(rst); assume(scenario < 8); end
        if (!rst) assume(scenario < 8);
        if (!$initstate) assume(scenario == $past(scenario));
        if (!rst && $past(!rst && in_valid && !in_ready)) begin
            assume(in_valid); assume(in_data == $past(in_data)); assume(in_last == $past(in_last));
        end
        if (rst) index <= 0;
        else if (input_fire) index <= index + 1'b1;
        if (!rst) begin
            assert(!out_valid);
            if (reject_valid) begin
                assert(reject_code == expected_code(scenario));
                assert(reject_fatal == expected_fatal);
            end
            cover(reject_fire);
        end
    end
endmodule

module ipv4_payload_correspondence;
    logic clk, rst;
    logic [31:0] cfg = 32'hC6336407;
    logic [7:0] in_data, out_data;
    logic in_valid, in_ready, in_last, out_valid, out_ready, out_last;
    logic reject_valid, reject_ready, reject_fatal;
    logic [3:0] reject_code;
    logic [5:0] index;
    logic [2:0] out_index;
    logic [7:0] p0, p1, p2, p3;
    localparam logic [159:0] HEADER = 160'h450000180000400040114E99C0000201C6336407;

    always_comb begin
        in_valid = !rst && index < 24;
        in_last = index == 23;
        case (index)
            0: in_data=HEADER[159:152]; 1: in_data=HEADER[151:144];
            2: in_data=HEADER[143:136]; 3: in_data=HEADER[135:128];
            4: in_data=HEADER[127:120]; 5: in_data=HEADER[119:112];
            6: in_data=HEADER[111:104]; 7: in_data=HEADER[103:96];
            8: in_data=HEADER[95:88]; 9: in_data=HEADER[87:80];
            10: in_data=HEADER[79:72]; 11: in_data=HEADER[71:64];
            12: in_data=HEADER[63:56]; 13: in_data=HEADER[55:48];
            14: in_data=HEADER[47:40]; 15: in_data=HEADER[39:32];
            16: in_data=HEADER[31:24]; 17: in_data=HEADER[23:16];
            18: in_data=HEADER[15:8]; 19: in_data=HEADER[7:0];
            20: in_data=p0; 21: in_data=p1; 22: in_data=p2; 23: in_data=p3;
            default: in_data=0;
        endcase
    end
    assign out_ready=1'b1; assign reject_ready=1'b1;
    wire input_fire=in_valid&&in_ready;
    wire output_fire=out_valid&&out_ready;
    wire_ipv4_parser dut (
        .clk(clk), .rst(rst), .cfg_destination_ipv4(cfg), .in_data(in_data),
        .in_valid(in_valid), .in_ready(in_ready), .in_last(in_last),
        .out_data(out_data), .out_valid(out_valid), .out_ready(out_ready), .out_last(out_last),
        .reject_valid(reject_valid), .reject_ready(reject_ready),
        .reject_fatal(reject_fatal), .reject_code(reject_code)
    );
    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!$initstate) begin
            assume(p0 == $past(p0)); assume(p1 == $past(p1));
            assume(p2 == $past(p2)); assume(p3 == $past(p3));
        end
        if (!rst && $past(!rst && in_valid && !in_ready)) begin
            assume(in_valid); assume(in_data==$past(in_data)); assume(in_last==$past(in_last));
        end
        if (rst) begin index<=0; out_index<=0; end
        else begin
            if (input_fire) index<=index+1'b1;
            if (output_fire) out_index<=out_index+1'b1;
        end
        if (!rst) begin
            assert(!reject_valid);
            if (out_valid) begin
                case (out_index)
                    0: assert(out_data==p0);
                    1: assert(out_data==p1);
                    2: assert(out_data==p2);
                    3: assert(out_data==p3);
                    default: assert(1'b0);
                endcase
                assert(out_last == (out_index==3));
            end
            cover(out_index==4);
        end
    end
endmodule

module ipv4_padding_correspondence;
    logic clk,rst; logic [31:0] cfg=32'hC6336407;
    logic [7:0] in_data,out_data; logic in_valid,in_ready,in_last,out_valid,out_ready,out_last;
    logic reject_valid,reject_ready,reject_fatal; logic [3:0] reject_code;
    logic [5:0] index; logic [2:0] out_index;
    localparam logic [159:0] HEADER=160'h450000180000400040114E99C0000201C6336407;
    always_comb begin
        in_valid=!rst && index<28; in_last=index==27;
        case(index)
          0:in_data=HEADER[159:152];1:in_data=HEADER[151:144];2:in_data=HEADER[143:136];3:in_data=HEADER[135:128];
          4:in_data=HEADER[127:120];5:in_data=HEADER[119:112];6:in_data=HEADER[111:104];7:in_data=HEADER[103:96];
          8:in_data=HEADER[95:88];9:in_data=HEADER[87:80];10:in_data=HEADER[79:72];11:in_data=HEADER[71:64];
          12:in_data=HEADER[63:56];13:in_data=HEADER[55:48];14:in_data=HEADER[47:40];15:in_data=HEADER[39:32];
          16:in_data=HEADER[31:24];17:in_data=HEADER[23:16];18:in_data=HEADER[15:8];19:in_data=HEADER[7:0];
          20:in_data=8'ha0;21:in_data=8'ha1;22:in_data=8'ha2;23:in_data=8'ha3;
          default:in_data=8'h55;
        endcase
    end
    assign out_ready=1'b1; assign reject_ready=1'b1;
    wire input_fire=in_valid&&in_ready, output_fire=out_valid&&out_ready;
    wire_ipv4_parser dut(.clk(clk),.rst(rst),.cfg_destination_ipv4(cfg),.in_data(in_data),.in_valid(in_valid),.in_ready(in_ready),.in_last(in_last),.out_data(out_data),.out_valid(out_valid),.out_ready(out_ready),.out_last(out_last),.reject_valid(reject_valid),.reject_ready(reject_ready),.reject_fatal(reject_fatal),.reject_code(reject_code));
    always @(posedge clk) begin
      if($initstate) assume(rst);
      if(!rst && $past(!rst&&in_valid&&!in_ready)) begin assume(in_valid);assume(in_data==$past(in_data));assume(in_last==$past(in_last));end
      if(rst) begin index<=0;out_index<=0;end else begin if(input_fire)index<=index+1'b1; if(output_fire)out_index<=out_index+1'b1; end
      if(!rst) begin assert(!reject_valid); if(out_valid) begin assert(out_data==8'ha0+out_index); assert(out_last==(out_index==3)); end cover(out_index==4 && index==28); end
    end
endmodule

module ipv4_truncation_correspondence;
    logic clk,rst; logic [31:0] cfg=32'hC6336407;
    logic [7:0] in_data,out_data; logic in_valid,in_ready,in_last,out_valid,out_ready,out_last;
    logic reject_valid,reject_ready,reject_fatal; logic [3:0] reject_code; logic [5:0] index;
    localparam logic [159:0] HEADER=160'h4500001C0000400040114E95C0000201C6336407;
    always_comb begin
      in_valid=!rst && index<24; in_last=index==23;
      case(index)
       0:in_data=HEADER[159:152];1:in_data=HEADER[151:144];2:in_data=HEADER[143:136];3:in_data=HEADER[135:128];4:in_data=HEADER[127:120];5:in_data=HEADER[119:112];6:in_data=HEADER[111:104];7:in_data=HEADER[103:96];8:in_data=HEADER[95:88];9:in_data=HEADER[87:80];10:in_data=HEADER[79:72];11:in_data=HEADER[71:64];12:in_data=HEADER[63:56];13:in_data=HEADER[55:48];14:in_data=HEADER[47:40];15:in_data=HEADER[39:32];16:in_data=HEADER[31:24];17:in_data=HEADER[23:16];18:in_data=HEADER[15:8];19:in_data=HEADER[7:0];default:in_data=8'hb0;
      endcase
    end
    assign out_ready=1'b1; assign reject_ready=1'b1;
    wire input_fire=in_valid&&in_ready;
    wire_ipv4_parser dut(.clk(clk),.rst(rst),.cfg_destination_ipv4(cfg),.in_data(in_data),.in_valid(in_valid),.in_ready(in_ready),.in_last(in_last),.out_data(out_data),.out_valid(out_valid),.out_ready(out_ready),.out_last(out_last),.reject_valid(reject_valid),.reject_ready(reject_ready),.reject_fatal(reject_fatal),.reject_code(reject_code));
    always @(posedge clk) begin
      if($initstate) assume(rst);
      if(!rst && $past(!rst&&in_valid&&!in_ready)) begin assume(in_valid);assume(in_data==$past(in_data));assume(in_last==$past(in_last));end
      if(rst) index<=0; else if(input_fire) index<=index+1'b1;
      if(!rst) begin assert(!out_last); if(reject_valid) begin assert(reject_fatal);assert(reject_code==4'd2);end cover(reject_valid); end
    end
endmodule

module ipv4_checksum_correspondence;
    logic clk,rst; logic [31:0] cfg=32'hC6336407;
    logic [7:0] in_data; logic in_valid,in_ready,in_last;
    logic [7:0] out_data; logic out_valid,out_ready,out_last;
    logic reject_valid,reject_ready,reject_fatal; logic [3:0] reject_code;
    logic [5:0] index; logic bad_checksum;
    localparam logic [159:0] GOOD=160'h450000180000400040114E99C0000201C6336407;
    localparam logic [159:0] BAD =160'h450000180000400040111234C0000201C6336407;
    wire [159:0] header = bad_checksum ? BAD : GOOD;
    always_comb begin
      in_valid=!rst && index<20; in_last=index==19;
      case(index)
       0:in_data=header[159:152];1:in_data=header[151:144];2:in_data=header[143:136];3:in_data=header[135:128];4:in_data=header[127:120];5:in_data=header[119:112];6:in_data=header[111:104];7:in_data=header[103:96];8:in_data=header[95:88];9:in_data=header[87:80];10:in_data=header[79:72];11:in_data=header[71:64];12:in_data=header[63:56];13:in_data=header[55:48];14:in_data=header[47:40];15:in_data=header[39:32];16:in_data=header[31:24];17:in_data=header[23:16];18:in_data=header[15:8];19:in_data=header[7:0];default:in_data=0;
      endcase
    end
    assign out_ready=1'b1; assign reject_ready=1'b1;
    wire input_fire=in_valid&&in_ready;
    wire_ipv4_parser dut(.clk(clk),.rst(rst),.cfg_destination_ipv4(cfg),.in_data(in_data),.in_valid(in_valid),.in_ready(in_ready),.in_last(in_last),.out_data(out_data),.out_valid(out_valid),.out_ready(out_ready),.out_last(out_last),.reject_valid(reject_valid),.reject_ready(reject_ready),.reject_fatal(reject_fatal),.reject_code(reject_code));
    always @(posedge clk) begin
      if($initstate) begin assume(rst); end
      if(!$initstate) assume(bad_checksum==$past(bad_checksum));
      if(!rst && $past(!rst&&in_valid&&!in_ready)) begin assume(in_valid);assume(in_data==$past(in_data));assume(in_last==$past(in_last));end
      if(rst) index<=0; else if(input_fire) index<=index+1'b1;
      if(!rst) begin
        assert(!out_valid);
        if(reject_valid) begin
          if(bad_checksum) begin assert(reject_code==4'd3); assert(reject_fatal); end
          else assert(reject_code!=4'd3);
        end
        cover(reject_valid && bad_checksum);
      end
    end
endmodule

module ipv4_next_packet_reference;
    logic clk,rst; logic [31:0] cfg=32'hC6336407;
    logic [7:0] in_data; logic in_valid,in_ready,in_last;
    logic [7:0] out_data; logic out_valid,out_ready,out_last;
    logic reject_valid,reject_ready,reject_fatal; logic [3:0] reject_code;
    logic [5:0] index; localparam logic [159:0] HEADER=160'h450000140000400040114E9DC0000201C6336407;
    wire [5:0] pos=index%20;
    always_comb begin
      in_valid=!rst && index<40; in_last=pos==19;
      case(pos)
       0:in_data=HEADER[159:152];1:in_data=HEADER[151:144];2:in_data=HEADER[143:136];3:in_data=HEADER[135:128];4:in_data=HEADER[127:120];5:in_data=HEADER[119:112];6:in_data=HEADER[111:104];7:in_data=HEADER[103:96];8:in_data=HEADER[95:88];9:in_data=HEADER[87:80];10:in_data=HEADER[79:72];11:in_data=HEADER[71:64];12:in_data=HEADER[63:56];13:in_data=HEADER[55:48];14:in_data=HEADER[47:40];15:in_data=HEADER[39:32];16:in_data=HEADER[31:24];17:in_data=HEADER[23:16];18:in_data=HEADER[15:8];19:in_data=HEADER[7:0];default:in_data=0;
      endcase
    end
    assign out_ready=1'b1; assign reject_ready=1'b1;
    wire input_fire=in_valid&&in_ready;
    wire_ipv4_parser dut(.clk(clk),.rst(rst),.cfg_destination_ipv4(cfg),.in_data(in_data),.in_valid(in_valid),.in_ready(in_ready),.in_last(in_last),.out_data(out_data),.out_valid(out_valid),.out_ready(out_ready),.out_last(out_last),.reject_valid(reject_valid),.reject_ready(reject_ready),.reject_fatal(reject_fatal),.reject_code(reject_code));
    always @(posedge clk) begin
      if($initstate) assume(rst);
      if(!rst && $past(!rst&&in_valid&&!in_ready)) begin assume(in_valid);assume(in_data==$past(in_data));assume(in_last==$past(in_last));end
      if(rst) index<=0; else if(input_fire) index<=index+1'b1;
      if(!rst) begin assert(!out_valid); if(reject_valid) begin assert(reject_code==4'd8); assert(reject_fatal); end cover(index==40); end
    end
endmodule
