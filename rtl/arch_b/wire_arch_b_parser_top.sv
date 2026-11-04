// Experimental fixed-profile Architecture-B parser.
// It consumes valid lanes directly from 64-bit beats and has no byte gearbox.
// One bounded ITCH message (maximum supported length 44) is retained at a time.
module wire_arch_b_parser_top (
    input logic clk, rst, rearm,
    input logic [31:0] cfg_destination_ipv4,
    input logic [15:0] cfg_destination_udp_port,
    input logic [79:0] cfg_active_session,
    input logic [63:0] cfg_expected_sequence,
    input logic [15:0] cfg_tracked_stock_locate,
    input logic cfg_symbol_check_enable,
    input logic [63:0] cfg_expected_stock_symbol,
    input logic [63:0] rx_data,
    input logic [7:0] rx_keep,
    input logic rx_valid,
    output logic rx_ready,
    input logic rx_last,
    output logic event_valid,
    input logic event_ready,
    output logic [2:0] event_kind,
    output logic [7:0] source_type,
    output logic [63:0] mold_sequence,
    output logic [47:0] itch_timestamp,
    output logic [15:0] stock_locate,
    output logic [63:0] old_order_reference,
    output logic [63:0] new_order_reference,
    output logic [31:0] quantity,
    output logic [31:0] price,
    output logic side,
    output logic old_reference_valid,
    output logic new_reference_valid,
    output logic quantity_valid,
    output logic price_valid,
    output logic side_valid,
    output logic parser_valid,
    output logic recovery_required,
    output logic [3:0] recovery_stage,
    output logic [63:0] current_expected_sequence
);
    // The state names intentionally describe protocol boundaries, not a
    // programmable parser framework.
    typedef enum logic [3:0] {
        S_ETH, S_IP, S_UDP, S_MOLD, S_LEN_HI, S_LEN_LO, S_ITCH,
        S_DROP_FRAME, S_PAD
    } state_t;
    (* fsm_encoding = "none" *) state_t state_q;

    logic [63:0] beat_data_q;
    logic [7:0] beat_keep_q;
    logic beat_last_q, beat_active_q;
    logic [3:0] lane_q;
    logic frame_open_q;
    logic [3:0] eth_index_q;
    logic [4:0] ip_index_q, mold_index_q;
    logic [2:0] udp_index_q;
    logic [7:0] eth_q [0:13];
    logic [7:0] ip_q [0:19];
    logic [7:0] udp_q [0:7];
    logic [7:0] mold_q [0:19];
    // Some optional ITCH bytes (for example F's MPID and P contents) are
    // deliberately opaque in this frozen profile.
    /* verilator lint_off UNUSEDSIGNAL */
    logic [351:0] msg_buf_q;
    /* verilator lint_on UNUSEDSIGNAL */
    logic [5:0] msg_index_q;
    logic [15:0] msg_length_q, msg_remaining_q;
    logic [15:0] itch_remaining_q;
    logic [31:0] ip_total_q, ip_payload_remaining_q;
    logic [79:0] active_session_q;
    logic [63:0] expected_sequence_q, packet_sequence_q;
    logic [15:0] packet_count_q, messages_done_q;
    logic [15:0] active_locate_q;
    logic symbol_check_q;
    logic [63:0] expected_symbol_q;
    logic semantic_failed_q, structural_failed_q;

    logic event_valid_q;
    logic [2:0] event_kind_q;
    logic [7:0] source_type_q;
    logic [63:0] event_sequence_q, old_ref_q, new_ref_q;
    logic [47:0] timestamp_q;
    logic [15:0] locate_q;
    logic [31:0] quantity_q, price_q;
    logic side_q, old_valid_q, new_valid_q, quantity_valid_q,
          price_valid_q, side_valid_q;

    logic ingress_in_ready, ingress_valid, ingress_ready;
    logic [63:0] ingress_data;
    logic [7:0] ingress_keep;
    logic ingress_last;
    logic parser_recovery_q;
    logic [3:0] recovery_stage_q;

    wire rx_fire = rx_valid && rx_ready;
    wire event_fire = event_valid_q && event_ready;

    // Frame-tail drain follows WIRE-D018. The two-beat common FIFO is retained.
    assign rx_ready = ingress_in_ready && (!parser_recovery_q || frame_open_q);
    assign event_valid = event_valid_q;
    assign event_kind = event_kind_q;
    assign source_type = source_type_q;
    assign mold_sequence = event_sequence_q;
    assign itch_timestamp = timestamp_q;
    assign stock_locate = locate_q;
    assign old_order_reference = old_ref_q;
    assign new_order_reference = new_ref_q;
    assign quantity = quantity_q;
    assign price = price_q;
    assign side = side_q;
    assign old_reference_valid = old_valid_q;
    assign new_reference_valid = new_valid_q;
    assign quantity_valid = quantity_valid_q;
    assign price_valid = price_valid_q;
    assign side_valid = side_valid_q;
    assign recovery_required = parser_recovery_q;
    assign recovery_stage = recovery_stage_q;
    assign parser_valid = !parser_recovery_q;
    assign current_expected_sequence = expected_sequence_q;

    wire_ingress_buffer ingress (
        .clk(clk), .rst(rst | rearm),
        .in_data(rx_data), .in_keep(rx_keep),
        .in_valid(rx_valid && (!parser_recovery_q || frame_open_q)),
        .in_ready(ingress_in_ready), .in_last(rx_last),
        .out_data(ingress_data), .out_keep(ingress_keep),
        .out_valid(ingress_valid), .out_ready(ingress_ready),
        .out_last(ingress_last)
    );
    assign ingress_ready = !beat_active_q;

    // Helpers for the fixed profile and exact big-endian fields.
    function automatic logic [15:0] be16(input logic [7:0] a, b);
        be16 = {a,b};
    endfunction
    function automatic logic [31:0] be32(input logic [7:0] a,b,c,d);
        be32 = {a,b,c,d};
    endfunction
    function automatic logic [63:0] be64(input logic [7:0] a,b,c,d,e,f,g,h);
        be64 = {a,b,c,d,e,f,g,h};
    endfunction
    function automatic logic [47:0] be48(input logic [7:0] a,b,c,d,e,f);
        be48 = {a,b,c,d,e,f};
    endfunction
    // Fixed-width packed message storage avoids a dynamically indexed
    // 44-entry memory write for every lane of the unrolled beat walker.
    task automatic store_msg_byte(input logic [5:0] index, input logic [7:0] value);
        begin
            case (index)
                6'd0: msg_buf_q[7:0] = value;
                6'd1: msg_buf_q[15:8] = value;
                6'd2: msg_buf_q[23:16] = value;
                6'd3: msg_buf_q[31:24] = value;
                6'd4: msg_buf_q[39:32] = value;
                6'd5: msg_buf_q[47:40] = value;
                6'd6: msg_buf_q[55:48] = value;
                6'd7: msg_buf_q[63:56] = value;
                6'd8: msg_buf_q[71:64] = value;
                6'd9: msg_buf_q[79:72] = value;
                6'd10: msg_buf_q[87:80] = value;
                6'd11: msg_buf_q[95:88] = value;
                6'd12: msg_buf_q[103:96] = value;
                6'd13: msg_buf_q[111:104] = value;
                6'd14: msg_buf_q[119:112] = value;
                6'd15: msg_buf_q[127:120] = value;
                6'd16: msg_buf_q[135:128] = value;
                6'd17: msg_buf_q[143:136] = value;
                6'd18: msg_buf_q[151:144] = value;
                6'd19: msg_buf_q[159:152] = value;
                6'd20: msg_buf_q[167:160] = value;
                6'd21: msg_buf_q[175:168] = value;
                6'd22: msg_buf_q[183:176] = value;
                6'd23: msg_buf_q[191:184] = value;
                6'd24: msg_buf_q[199:192] = value;
                6'd25: msg_buf_q[207:200] = value;
                6'd26: msg_buf_q[215:208] = value;
                6'd27: msg_buf_q[223:216] = value;
                6'd28: msg_buf_q[231:224] = value;
                6'd29: msg_buf_q[239:232] = value;
                6'd30: msg_buf_q[247:240] = value;
                6'd31: msg_buf_q[255:248] = value;
                6'd32: msg_buf_q[263:256] = value;
                6'd33: msg_buf_q[271:264] = value;
                6'd34: msg_buf_q[279:272] = value;
                6'd35: msg_buf_q[287:280] = value;
                6'd36: msg_buf_q[295:288] = value;
                6'd37: msg_buf_q[303:296] = value;
                6'd38: msg_buf_q[311:304] = value;
                6'd39: msg_buf_q[319:312] = value;
                6'd40: msg_buf_q[327:320] = value;
                6'd41: msg_buf_q[335:328] = value;
                6'd42: msg_buf_q[343:336] = value;
                6'd43: msg_buf_q[351:344] = value;
                default: ;
            endcase
        end
    endtask

    function automatic logic [15:0] itch_length(input logic [7:0] t);
        case (t)
            "A": itch_length=36; "F": itch_length=40; "E": itch_length=31;
            "C": itch_length=36; "X": itch_length=23; "D": itch_length=19;
            "U": itch_length=35; "P": itch_length=44;
            default: itch_length=0;
        endcase
    endfunction

    // A valid keep is a contiguous low-lane prefix, as defined by REQ-IF-005.
    // This engine consumes consecutive lanes in byte order. Event creation
    // stops the walk, leaving the active beat and next lane untouched.
    // Each clock processes at most two consecutive valid lanes. The loop is
    // deliberately short so only two copies of the protocol transition logic
    // are built into the combinational path; the registered lane cursor
    // carries progress across cycles.
    /* verilator lint_off BLKSEQ */
    always_ff @(posedge clk) begin : lane_engine
        integer lane;
        integer j;
        logic stop_walk;
        logic lane_last;
        logic [7:0] b;
        logic [15:0] declared_len;
        logic [31:0] sum32;
        if (rst || rearm) begin
            state_q <= S_ETH;
            beat_data_q <= 0; beat_keep_q <= 0; beat_last_q <= 0;
            beat_active_q <= 0; lane_q <= 0; frame_open_q <= 0;
            eth_index_q <= 0; ip_index_q <= 0; udp_index_q <= 0; mold_index_q <= 0;
            msg_index_q <= 0; msg_length_q <= 0; msg_remaining_q <= 0; msg_buf_q <= '0;
            itch_remaining_q <= 0;
            ip_total_q <= 0; ip_payload_remaining_q <= 0;
            active_session_q <= cfg_active_session;
            expected_sequence_q <= cfg_expected_sequence; packet_sequence_q <= 0;
            packet_count_q <= 0; messages_done_q <= 0;
            active_locate_q <= cfg_tracked_stock_locate;
            symbol_check_q <= cfg_symbol_check_enable;
            expected_symbol_q <= cfg_expected_stock_symbol;
            semantic_failed_q <= 0; structural_failed_q <= 0;
            parser_recovery_q <= 0; recovery_stage_q <= 0;
            event_valid_q <= 0; event_kind_q <= 0; source_type_q <= 0;
            event_sequence_q <= 0; timestamp_q <= 0; locate_q <= 0;
            old_ref_q <= 0; new_ref_q <= 0; quantity_q <= 0; price_q <= 0;
            side_q <= 0; old_valid_q <= 0; new_valid_q <= 0;
            quantity_valid_q <= 0; price_valid_q <= 0; side_valid_q <= 0;
        end else begin
            // Track the physical frame boundary at the external accepted port.
            if (rx_fire) frame_open_q <= !rx_last;

            // Blocking assignments let the two fixed iterations consume the
            // next two lanes in order. Any remaining lanes stay in beat_data_q
            // and are consumed on a later clock.
            if (event_fire) event_valid_q = 1'b0;
            if (!beat_active_q && ingress_valid) begin
                beat_data_q = ingress_data;
                beat_keep_q = ingress_keep;
                beat_last_q = ingress_last;
                beat_active_q = 1'b1;
                lane_q = 0;
            end
            stop_walk = event_valid_q;
            if (beat_active_q && !event_valid_q) begin
                for (lane = 0; lane < 2; lane = lane + 1) begin
                    if (!stop_walk && (lane_q < 8) && beat_keep_q[lane_q[2:0]]) begin
                        b = beat_data_q[lane_q*8 +: 8];
                        lane_last = beat_last_q && ((lane_q == 7) ? 1'b1 : !beat_keep_q[lane_q+1]);
                        lane_q = lane_q + 1'b1;
                        case (state_q)
                            S_ETH: begin
                                if (eth_index_q == 0) begin ip_payload_remaining_q = 0; ip_total_q = 0; end
                                eth_q[eth_index_q] = b;
                                if (eth_index_q == 13) begin
                                    eth_index_q = 0;
                                    if ({eth_q[12],b} != 16'h0800) begin
                                        state_q = S_DROP_FRAME;
                                    end else state_q = S_IP;
                                end else eth_index_q = eth_index_q + 1'b1;
                                if (lane_last && state_q != S_DROP_FRAME) begin
                                    parser_recovery_q = 1; recovery_stage_q = 1;
                                    state_q = S_DROP_FRAME;
                                end
                            end
                            S_IP: begin
                                ip_q[ip_index_q] = b;
                                if (ip_index_q == 5'd19) begin
                                    ip_index_q = 0;
                                    ip_total_q = {16'd0,ip_q[2],ip_q[3]};
                                    sum32 = 0;
                                    for (j = 0; j < 10; j = j + 1)
                                        sum32 = sum32 + {16'd0, ip_q[2*j], ip_q[2*j+1]};
                                    // The final checksum word includes byte 19, not the old array value.
                                    sum32 = sum32 - {16'd0, ip_q[18], ip_q[19]} + {16'd0, ip_q[18], b};
                                    sum32 = {16'd0,sum32[15:0]} + {16'd0,sum32[31:16]};
                                    sum32 = {16'd0,sum32[15:0]} + {16'd0,sum32[31:16]};
                                    sum32 = {16'd0,sum32[15:0]} + {16'd0,sum32[31:16]};
                                    if (ip_q[0][7:4] != 4) begin
                                        parser_recovery_q = 1; recovery_stage_q = 2; state_q = S_DROP_FRAME;
                                    end else if (ip_q[0][3:0] != 5) begin
                                        parser_recovery_q = 1; recovery_stage_q = 2; state_q = S_DROP_FRAME;
                                    end else if (ip_total_q < 20) begin
                                        parser_recovery_q = 1; recovery_stage_q = 2; state_q = S_DROP_FRAME;
                                    end else if (sum32[15:0] != 16'hffff) begin
                                        parser_recovery_q = 1; recovery_stage_q = 2; state_q = S_DROP_FRAME;
                                    end else if (ip_q[6][5] || {ip_q[6][4:0],ip_q[7]} != 0) begin
                                        parser_recovery_q = 1; recovery_stage_q = 2; state_q = S_DROP_FRAME;
                                    end else if (be32(ip_q[16],ip_q[17],ip_q[18],ip_q[19]) != cfg_destination_ipv4) begin
                                        state_q = S_DROP_FRAME;
                                    end else if (ip_q[9] != 17) begin
                                        state_q = S_DROP_FRAME;
                                    end else if (ip_total_q == 20) begin
                                        parser_recovery_q = 1; recovery_stage_q = 2; state_q = S_DROP_FRAME;
                                    end else begin
                                        ip_payload_remaining_q = ip_total_q - 20;
                                        state_q = S_UDP;
                                    end
                                    if (ip_total_q > 20 && ip_q[0][7:4] == 4 && ip_q[0][3:0] == 5 &&
                                        sum32[15:0] == 16'hffff && !ip_q[6][5] &&
                                        {ip_q[6][4:0],ip_q[7]} == 0 &&
                                        be32(ip_q[16],ip_q[17],ip_q[18],ip_q[19]) == cfg_destination_ipv4 && ip_q[9] == 17)
                                        ip_payload_remaining_q = ip_total_q - 20;
                                end else ip_index_q = ip_index_q + 1'b1;
                                if (lane_last && state_q == S_IP) begin
                                    parser_recovery_q = 1; recovery_stage_q = 2; state_q = S_DROP_FRAME;
                                end
                            end
                            S_UDP: begin
                                udp_q[udp_index_q] = b;
                                ip_payload_remaining_q = ip_payload_remaining_q - 1;
                                if (udp_index_q == 7) begin
                                    udp_index_q = 0;
                                    if ({16'd0,udp_q[4],udp_q[5]} != ip_total_q - 20 ||
                                        {udp_q[4],udp_q[5]} < 8) begin
                                        parser_recovery_q = 1; recovery_stage_q = 3; state_q = S_DROP_FRAME;
                                    end else if ({udp_q[2],udp_q[3]} != cfg_destination_udp_port ||
                                                 {udp_q[6],b} != 0) begin
                                        state_q = S_DROP_FRAME;
                                    end else if ({udp_q[4],udp_q[5]} == 8) begin
                                        parser_recovery_q=1; recovery_stage_q=3; state_q=S_DROP_FRAME;
                                    end else begin
                                        mold_index_q = 0; messages_done_q = 0;
                                        structural_failed_q = 0; semantic_failed_q = 0;
                                        state_q = S_MOLD;
                                    end
                                end else udp_index_q = udp_index_q + 1'b1;
                                if (ip_payload_remaining_q == 0 && state_q == S_UDP) begin
                                    parser_recovery_q=1; recovery_stage_q=3; state_q=S_DROP_FRAME;
                                end
                                if (lane_last && state_q == S_UDP && ip_payload_remaining_q != 0) begin
                                    parser_recovery_q = 1; recovery_stage_q = 3; state_q = S_DROP_FRAME;
                                end
                            end
                            S_MOLD: begin
                                mold_q[mold_index_q] = b;
                                ip_payload_remaining_q = ip_payload_remaining_q - 1;
                                if (mold_index_q == 5'd19) begin
                                    mold_index_q = 0;
                                    packet_sequence_q = {mold_q[10],mold_q[11],mold_q[12],mold_q[13],mold_q[14],mold_q[15],mold_q[16],mold_q[17]};
                                    packet_count_q = {mold_q[18],b};
                                    if ({mold_q[0],mold_q[1],mold_q[2],mold_q[3],mold_q[4],mold_q[5],mold_q[6],mold_q[7],mold_q[8],mold_q[9]} != active_session_q) begin
                                        parser_recovery_q = 1; recovery_stage_q = 4; state_q = S_DROP_FRAME;
                                    end else if ({mold_q[10],mold_q[11],mold_q[12],mold_q[13],mold_q[14],mold_q[15],mold_q[16],mold_q[17]} != expected_sequence_q) begin
                                        parser_recovery_q = 1; recovery_stage_q = 4; state_q = S_DROP_FRAME;
                                    end else if ({mold_q[18],b} == 0 || {mold_q[18],b} == 16'hffff) begin
                                        if (ip_payload_remaining_q != 0) begin
                                            parser_recovery_q = 1; recovery_stage_q = 4; state_q = S_DROP_FRAME;
                                        end else if ({mold_q[18],b} == 16'hffff) begin
                                            parser_recovery_q = 1; recovery_stage_q = 4; state_q = S_DROP_FRAME;
                                        end else state_q = S_PAD;
                                    end else if (ip_payload_remaining_q == 0) begin
                                        parser_recovery_q = 1; recovery_stage_q = 5; state_q = S_DROP_FRAME;
                                    end else begin
                                        msg_remaining_q = ip_payload_remaining_q[15:0];
                                        state_q = S_LEN_HI;
                                    end
                                end else mold_index_q = mold_index_q + 1'b1;
                                if (ip_payload_remaining_q == 0 && state_q == S_MOLD) begin
                                    parser_recovery_q=1; recovery_stage_q=4; state_q=S_DROP_FRAME;
                                end
                                if (lane_last && state_q == S_MOLD && ip_payload_remaining_q != 0) begin
                                    parser_recovery_q = 1; recovery_stage_q = 4; state_q = S_DROP_FRAME;
                                end
                            end
                            S_LEN_HI: begin
                                msg_buf_q = '0;
                                ip_payload_remaining_q = ip_payload_remaining_q - 1;
                                msg_remaining_q = msg_remaining_q - 1;
                                if (msg_remaining_q == 0 || ip_payload_remaining_q == 0) begin
                                    parser_recovery_q = 1; recovery_stage_q = 5; state_q = S_DROP_FRAME;
                                end else begin
                                    msg_length_q[15:8] = b;
                                    state_q = S_LEN_LO;
                                end
                            end
                            S_LEN_LO: begin
                                ip_payload_remaining_q = ip_payload_remaining_q - 1;
                                msg_remaining_q = msg_remaining_q - 1;
                                msg_length_q[7:0] = b;
                                msg_index_q = 0;
                                if (msg_remaining_q == 0 || {msg_length_q[15:8],b} > msg_remaining_q) begin
                                    parser_recovery_q = 1; recovery_stage_q = 5; state_q = S_DROP_FRAME;
                                end else if ({msg_length_q[15:8],b} == 0) begin
                                    messages_done_q = messages_done_q + 1;
                                    if (!semantic_failed_q) begin
                                        parser_recovery_q=1; recovery_stage_q=6; semantic_failed_q=1;
                                    end
                                        if (messages_done_q == packet_count_q) begin
                                        if (msg_remaining_q != 0) begin parser_recovery_q=1; recovery_stage_q=5; structural_failed_q=1; state_q=S_DROP_FRAME; end
                                        else begin expected_sequence_q = expected_sequence_q + {48'd0,packet_count_q}; state_q = S_PAD; end
                                    end else if (ip_payload_remaining_q == 0) begin
                                        parser_recovery_q=1; recovery_stage_q=5; structural_failed_q=1; state_q=S_DROP_FRAME;
                                    end else state_q = S_LEN_HI;
                                end else begin
                                    msg_length_q = {msg_length_q[15:8],b};
                                    itch_remaining_q = {msg_length_q[15:8],b};
                                    state_q = S_ITCH;
                                end
                            end
                            S_ITCH: begin
                                ip_payload_remaining_q = ip_payload_remaining_q - 1;
                                msg_remaining_q = msg_remaining_q - 1;
                                itch_remaining_q = itch_remaining_q - 1;
                                if (msg_index_q < 44) begin store_msg_byte(msg_index_q,b); msg_index_q = msg_index_q + 1; end
                                if (itch_remaining_q == 0) begin
                                    messages_done_q = messages_done_q + 1;
                                    declared_len = itch_length(msg_buf_q[7:0]);
                                    if (!semantic_failed_q) begin
                                            if (declared_len == 0 || declared_len != msg_length_q) begin
                                            parser_recovery_q = 1; recovery_stage_q = 6; semantic_failed_q = 1;
                                        end else if (msg_buf_q[7:0] == "A" || msg_buf_q[7:0] == "F") begin
                                            if ({msg_buf_q[15:8],msg_buf_q[23:16]} == active_locate_q && symbol_check_q && {msg_buf_q[199:192],msg_buf_q[207:200],msg_buf_q[215:208],msg_buf_q[223:216],msg_buf_q[231:224],msg_buf_q[239:232],msg_buf_q[247:240],msg_buf_q[255:248]} != expected_symbol_q) begin
                                                parser_recovery_q=1; recovery_stage_q=6; semantic_failed_q=1;
                                            end else if ({msg_buf_q[15:8],msg_buf_q[23:16]} == active_locate_q && msg_buf_q[159:152] != "B" && msg_buf_q[159:152] != "S") begin
                                                parser_recovery_q=1; recovery_stage_q=6; semantic_failed_q=1;
                                            end else if ({msg_buf_q[15:8],msg_buf_q[23:16]} == active_locate_q) begin
                                                event_kind_q=0; source_type_q=msg_buf_q[7:0]; event_sequence_q=packet_sequence_q+{48'd0,messages_done_q}-64'd1;
                                                timestamp_q=be48(msg_buf_q[47:40],msg_buf_q[55:48],msg_buf_q[63:56],msg_buf_q[71:64],msg_buf_q[79:72],msg_buf_q[87:80]);
                                                locate_q=be16(msg_buf_q[15:8],msg_buf_q[23:16]); old_ref_q=0;
                                                new_ref_q=be64(msg_buf_q[95:88],msg_buf_q[103:96],msg_buf_q[111:104],msg_buf_q[119:112],msg_buf_q[127:120],msg_buf_q[135:128],msg_buf_q[143:136],msg_buf_q[151:144]);
                                                quantity_q=be32(msg_buf_q[167:160],msg_buf_q[175:168],msg_buf_q[183:176],msg_buf_q[191:184]); price_q=be32(msg_buf_q[263:256],msg_buf_q[271:264],msg_buf_q[279:272],msg_buf_q[287:280]);
                                                side_q=(msg_buf_q[159:152]=="S"); old_valid_q=0; new_valid_q=1; quantity_valid_q=1; price_valid_q=1; side_valid_q=1;
                                                event_valid_q=1; stop_walk=1;
                                            end
                                        end else if (msg_buf_q[7:0] != "P" && {msg_buf_q[15:8],msg_buf_q[23:16]} == active_locate_q) begin
                                            event_kind_q = 0; source_type_q = msg_buf_q[7:0];
                                            event_sequence_q = packet_sequence_q + {48'd0,messages_done_q} - 64'd1;
                                            timestamp_q = be48(msg_buf_q[47:40],msg_buf_q[55:48],msg_buf_q[63:56],msg_buf_q[71:64],msg_buf_q[79:72],msg_buf_q[87:80]);
                                            locate_q=be16(msg_buf_q[15:8],msg_buf_q[23:16]); new_ref_q=0; price_q=0; side_q=0;
                                            old_ref_q=be64(msg_buf_q[95:88],msg_buf_q[103:96],msg_buf_q[111:104],msg_buf_q[119:112],msg_buf_q[127:120],msg_buf_q[135:128],msg_buf_q[143:136],msg_buf_q[151:144]);
                                            quantity_q=0;
                                            old_valid_q=1; new_valid_q=0; quantity_valid_q=0; price_valid_q=0; side_valid_q=0;
                                            case (msg_buf_q[7:0])
                                                "E", "C", "X": begin
                                                    quantity_q=be32(msg_buf_q[159:152],msg_buf_q[167:160],msg_buf_q[175:168],msg_buf_q[183:176]); quantity_valid_q=1;
                                                    if(msg_buf_q[7:0]=="E") event_kind_q=1;
                                                    else if(msg_buf_q[7:0]=="C") event_kind_q=2;
                                                    else event_kind_q=3;
                                                end
                                                "D": event_kind_q=4;
                                                "U": begin
                                                    event_kind_q=5; new_ref_q=be64(msg_buf_q[159:152],msg_buf_q[167:160],msg_buf_q[175:168],msg_buf_q[183:176],msg_buf_q[191:184],msg_buf_q[199:192],msg_buf_q[207:200],msg_buf_q[215:208]);
                                                    quantity_q=be32(msg_buf_q[223:216],msg_buf_q[231:224],msg_buf_q[239:232],msg_buf_q[247:240]); price_q=be32(msg_buf_q[255:248],msg_buf_q[263:256],msg_buf_q[271:264],msg_buf_q[279:272]);
                                                    new_valid_q=1; quantity_valid_q=1; price_valid_q=1;
                                                end
                                                default: ;
                                            endcase
                                            event_valid_q=1; stop_walk=1;
                                        end
                                    end
                                    if (messages_done_q >= packet_count_q) begin
                                        if (ip_payload_remaining_q != 0) begin
                                            parser_recovery_q=1; recovery_stage_q=5; structural_failed_q=1; state_q=S_DROP_FRAME;
                                        end else begin
                                            if (!structural_failed_q) begin
                                                expected_sequence_q=expected_sequence_q+{48'd0,packet_count_q};
                                            end
                                            state_q=S_PAD;
                                        end
                                    end else if (ip_payload_remaining_q == 0) begin
                                        parser_recovery_q=1; recovery_stage_q=5; structural_failed_q=1; state_q=S_DROP_FRAME;
                                    end else state_q=S_LEN_HI;
                                end else if (ip_payload_remaining_q == 0) begin
                                    parser_recovery_q=1; recovery_stage_q=5; structural_failed_q=1; state_q=S_DROP_FRAME;
                                end
                            end
                            S_DROP_FRAME: begin
                                if (ip_payload_remaining_q != 0)
                                    ip_payload_remaining_q = ip_payload_remaining_q - 1;
                                if (lane_last) begin
                                    if (ip_payload_remaining_q != 0 && ip_total_q >= 20) begin
                                        parser_recovery_q=1; recovery_stage_q=2;
                                    end
                                    state_q=S_ETH; eth_index_q=0; ip_index_q=0; udp_index_q=0; mold_index_q=0;
                                end
                            end
                            S_PAD: begin
                                if (lane_last) begin
                                    state_q=S_ETH; eth_index_q=0; ip_index_q=0; udp_index_q=0; mold_index_q=0;
                                end
                            end
                            default: state_q=S_ETH;
                        endcase
                        if (lane_last && (state_q != S_DROP_FRAME) && (state_q != S_PAD)) begin
                            // Any still-open declared IPv4 packet ended early.
                            if (ip_payload_remaining_q != 0 && state_q != S_ETH && state_q != S_IP) begin
                                parser_recovery_q=1; recovery_stage_q=2; state_q=S_ETH;
                            end
                        end
                        if (lane_last && state_q == S_DROP_FRAME) begin
                            state_q = S_ETH; eth_index_q=0; ip_index_q=0; udp_index_q=0; mold_index_q=0;
                        end
                        if (lane_last && state_q == S_PAD) begin
                            state_q = S_ETH; eth_index_q=0; ip_index_q=0; udp_index_q=0; mold_index_q=0;
                        end
                    end
                end
                if (!stop_walk && ((lane_q >= 8) || ((lane_q < 8) && !beat_keep_q[lane_q[2:0]]))) begin
                    beat_active_q=0; lane_q=0;
                end
            end
            // A complete message can share the same lane-walk cycle with a
            // later structural error (for example trailing bytes). If its
            // event has not handshaken yet, fail-closed recovery suppresses it.
            if (parser_recovery_q) event_valid_q = 1'b0;
        end
    end
    /* verilator lint_on BLKSEQ */
endmodule
