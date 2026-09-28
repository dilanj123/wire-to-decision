module wire_ipv4_parser_reference (
    input logic clk, input logic rst,
    input logic [31:0] cfg_destination_ipv4,
    input logic [7:0] in_data, input logic in_valid, input logic in_last,
    input logic out_ready, input logic reject_ready
);
    localparam logic [3:0] C_VERSION=0, C_IHL=1, C_LENGTH=2, C_CHECKSUM=3,
                           C_FRAGMENT=4, C_DEST=5, C_PROTOCOL=6,
                           C_TRUNC=7, C_EMPTY=8;
    typedef enum logic [2:0] {R_HEADER, R_PAYLOAD, R_PADDING, R_DROP, R_REJECT} state_t;
    state_t rs;
    logic [4:0] ri;
    logic [159:0] rh;
    logic [15:0] rem;
    logic [7:0] rd;
    logic rv, rl, rphys;
    logic rejv, rejf;
    logic [3:0] rejc;
    logic in_ready, out_valid, out_last, reject_valid, reject_fatal;
    logic [7:0] out_data;
    logic [3:0] reject_code;

    wire_ipv4_parser dut (
        .clk(clk), .rst(rst), .cfg_destination_ipv4(cfg_destination_ipv4),
        .in_data(in_data), .in_valid(in_valid), .in_ready(in_ready), .in_last(in_last),
        .out_data(out_data), .out_valid(out_valid), .out_ready(out_ready), .out_last(out_last),
        .reject_valid(reject_valid), .reject_ready(reject_ready),
        .reject_fatal(reject_fatal), .reject_code(reject_code)
    );
    wire input_fire = in_valid && in_ready;
    wire output_fire = out_valid && out_ready;
    wire reject_fire = reject_valid && reject_ready;
    wire ref_in_ready = (rs == R_HEADER) || (rs == R_DROP) || (rs == R_PADDING) ||
                        ((rs == R_PAYLOAD) && !rl && (!rv || out_ready));

    function automatic logic checksum_ok(input logic [159:0] h);
        logic [17:0] sum;
        begin
            sum = {2'b0,h[159:144]} + {2'b0,h[143:128]} +
                  {2'b0,h[127:112]} + {2'b0,h[111:96]} +
                  {2'b0,h[95:80]} + {2'b0,h[79:64]} +
                  {2'b0,h[63:48]} + {2'b0,h[47:32]} +
                  {2'b0,h[31:16]} + {2'b0,h[15:0]};
            sum = {2'b0,sum[15:0]} + {16'b0,sum[17:16]};
            sum = {2'b0,sum[15:0]} + {16'b0,sum[17:16]};
            checksum_ok = (sum[15:0] == 16'hffff);
        end
    endfunction
    function automatic logic [3:0] classify(input logic [159:0] h);
        logic [15:0] total; logic [13:0] frag;
        begin
            total = h[143:128]; frag = h[109:96];
            if (h[159:156] != 4) classify=C_VERSION;
            else if (h[155:152] != 5) classify=C_IHL;
            else if (total < 20) classify=C_LENGTH;
            else if (!checksum_ok(h)) classify=C_CHECKSUM;
            else if (frag[13] || frag[12:0] != 0) classify=C_FRAGMENT;
            else if (h[31:0] != cfg_destination_ipv4) classify=C_DEST;
            else if (h[87:80] != 17) classify=C_PROTOCOL;
            else classify=4'hf;
        end
    endfunction
    function automatic logic fatal_code(input logic [3:0] c);
        fatal_code=(c==C_LENGTH)||(c==C_CHECKSUM)||(c==C_FRAGMENT)||(c==C_TRUNC)||(c==C_EMPTY);
    endfunction

    logic [159:0] candidate;
    always @(*) begin
        candidate = {rh[159:8], in_data};
        if (!rst) begin
            assert(in_ready == ref_in_ready);
            assert(out_valid == rv);
            assert(out_last == (rv && rl));
            assert(reject_valid == rejv);
            if (rv) assert(out_data == rd);
            if (rejv) begin
                assert(reject_fatal == rejf);
                assert(reject_code == rejc);
                assert(!in_ready && !out_valid);
            end
        end
    end

    always @(posedge clk) begin
        if ($initstate) assume(rst);
        if (!rst) assume(cfg_destination_ipv4 == 32'hC6336407);
        if (!rst && $past(!rst && in_valid && !in_ready)) begin
            assume(in_valid); assume(in_data == $past(in_data)); assume(in_last == $past(in_last));
        end
        if (rst) begin
            rs<=R_HEADER; ri<=0; rh<=0; rem<=0; rd<=0; rv<=0; rl<=0; rphys<=0;
            rejv<=0; rejf<=0; rejc<=0;
        end else begin
            if (rs==R_PAYLOAD && output_fire) begin
                rv<=0;
                if (rl) begin
                    rl<=0; rphys<=0; rs<=rphys ? R_HEADER : R_PADDING; ri<=0;
                end
            end
            if (rs==R_REJECT && reject_fire) begin rs<=R_HEADER; ri<=0; rejv<=0; end
            if (input_fire) begin
                case (rs)
                    R_HEADER: begin
                        if (in_last && ri<19) begin rejf<=1; rejc<=C_TRUNC; rejv<=1; rs<=R_REJECT; end
                        else if (ri<19) begin rh[159-ri*8 -: 8]<=in_data; ri<=ri+1; end
                        else begin
                            rh<=candidate;
                            if (classify(candidate)==4'hf) begin
                                if (candidate[143:128]==20) begin rejf<=1; rejc<=C_EMPTY; rejv<=1; rs<=R_REJECT; end
                                else if (in_last) begin rejf<=1; rejc<=C_LENGTH; rejv<=1; rs<=R_REJECT; end
                                else begin rem<=candidate[143:128]-20; rs<=R_PAYLOAD; end
                            end else begin
                                rejf<=fatal_code(classify(candidate)); rejc<=classify(candidate);
                                if (in_last) begin rejv<=1; rs<=R_REJECT; end else rs<=R_DROP;
                            end
                        end
                    end
                    R_PAYLOAD: begin
                        if (in_last && rem>1) begin rejf<=1; rejc<=C_LENGTH; rejv<=1; rs<=R_REJECT; end
                        else begin rd<=in_data; rv<=1; rl<=rem==1; rphys<=in_last; rem<=rem-1; end
                    end
                    R_PADDING: if (in_last) rs<=R_HEADER;
                    R_DROP: if (in_last) begin rejv<=1; rs<=R_REJECT; end
                    default: begin end
                endcase
            end
        end
    end

    always @(posedge clk) begin
        if (!rst && $past(!rst && out_valid && !out_ready)) begin
            assert(out_valid); assert(out_data==$past(out_data)); assert(out_last==$past(out_last));
        end
        if (!rst && $past(!rst && reject_valid && !reject_ready)) begin
            assert(reject_valid); assert(reject_fatal==$past(reject_fatal));
            assert(reject_code==$past(reject_code)); assert(!in_ready); assert(!out_valid);
        end
        if (!rst) begin
            cover(rs==R_PAYLOAD && input_fire);
            cover(rs==R_PADDING && in_last && input_fire);
            cover(rs==R_DROP && in_last && input_fire);
            cover(rs==R_REJECT && !reject_ready);
        end
    end
endmodule
