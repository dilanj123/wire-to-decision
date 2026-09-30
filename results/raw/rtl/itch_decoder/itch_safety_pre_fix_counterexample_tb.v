`ifndef VERILATOR
module testbench;
  reg [4095:0] vcdfile;
  reg clock;
`else
module testbench(input clock, output reg genclock);
  initial genclock = 1;
`endif
  reg genclock = 1;
  reg [31:0] cycle = 0;
  reg [7:0] PI_in_data;
  reg [15:0] PI_cfg_tracked_stock_locate;
  reg [63:0] PI_cfg_expected_stock_symbol;
  reg [0:0] PI_in_valid;
  reg [0:0] PI_event_ready;
  reg [15:0] PI_message_length;
  wire [0:0] PI_clk = clock;
  reg [0:0] PI_message_empty;
  reg [0:0] PI_message_valid;
  reg [0:0] PI_cfg_symbol_check_enable;
  reg [0:0] PI_in_last;
  reg [63:0] PI_message_sequence;
  reg [0:0] PI_reject_ready;
  reg [0:0] PI_rst;
  reg [0:0] PI_rearm;
  itch_safety UUT (
    .in_data(PI_in_data),
    .cfg_tracked_stock_locate(PI_cfg_tracked_stock_locate),
    .cfg_expected_stock_symbol(PI_cfg_expected_stock_symbol),
    .in_valid(PI_in_valid),
    .event_ready(PI_event_ready),
    .message_length(PI_message_length),
    .clk(PI_clk),
    .message_empty(PI_message_empty),
    .message_valid(PI_message_valid),
    .cfg_symbol_check_enable(PI_cfg_symbol_check_enable),
    .in_last(PI_in_last),
    .message_sequence(PI_message_sequence),
    .reject_ready(PI_reject_ready),
    .rst(PI_rst),
    .rearm(PI_rearm)
  );
`ifndef VERILATOR
  initial begin
    if ($value$plusargs("vcd=%s", vcdfile)) begin
      $dumpfile(vcdfile);
      $dumpvars(0, testbench);
    end
    #5 clock = 0;
    while (genclock) begin
      #5 clock = 0;
      #5 clock = 1;
    end
  end
`endif
  initial begin
`ifndef VERILATOR
    #1;
`endif
    // UUT.$auto$async2sync.\cc:107:execute$2638  = 1'b0;
    // UUT.$auto$async2sync.\cc:107:execute$2650  = 1'b0;
    // UUT.$auto$async2sync.\cc:107:execute$2662  = 1'b0;
    // UUT.$auto$async2sync.\cc:107:execute$2668  = 1'b0;
    // UUT.$auto$async2sync.\cc:116:execute$2636  = 1'b1;
    // UUT.$auto$async2sync.\cc:116:execute$2642  = 1'b1;
    // UUT.$auto$async2sync.\cc:116:execute$2648  = 1'b1;
    // UUT.$auto$async2sync.\cc:116:execute$2654  = 1'b1;
    // UUT.$auto$async2sync.\cc:116:execute$2660  = 1'b1;
    // UUT.$auto$async2sync.\cc:116:execute$2666  = 1'b1;
    // UUT.$auto$async2sync.\cc:116:execute$2672  = 1'b1;
    // UUT.$auto$async2sync.\cc:116:execute$2678  = 1'b1;
    UUT._witness_.anyinit_procdff_2569 = 1'b0;
    UUT._witness_.anyinit_procdff_2570 = 337'b0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000;
    UUT._witness_.anyinit_procdff_2571 = 1'b0;
    UUT._witness_.anyinit_procdff_2572 = 3'b000;
    UUT._witness_.anyinit_procdff_2573 = 1'b0;
    UUT.dut.byte_index_q = 6'b000000;
    UUT.dut.declared_length_q = 16'b0000000000000000;
    UUT.dut.event_kind_q = 3'b000;
    UUT.dut.expected_symbol_q = 64'b0000000000000000000000000000000000000000000000000000000000000000;
    UUT.dut.message_sequence_q = 64'b0000000000000000000000000000000000000000000000000000000000000000;
    UUT.dut.mold_sequence_q = 64'b0000000000000000000000000000000000000000000000000000000000000000;
    UUT.dut.new_ref_q = 64'b0000000000000000000000000000000000000000000000000000000000000000;
    UUT.dut.new_valid_q = 1'b0;
    UUT.dut.old_ref_q = 64'b0000000000000000000000000000000000000000000000000000000000000000;
    UUT.dut.old_valid_q = 1'b0;
    UUT.dut.price_q = 32'b00000000000000000000000000000000;
    UUT.dut.price_valid_q = 1'b0;
    UUT.dut.quantity_q = 32'b00000000000000000000000000000000;
    UUT.dut.quantity_valid_q = 1'b0;
    UUT.dut.recovery_required = 1'b0;
    UUT.dut.reject_code_q = 3'b000;
    UUT.dut.reject_pending_q = 1'b0;
    UUT.dut.side_q = 1'b0;
    UUT.dut.side_valid_q = 1'b0;
    UUT.dut.source_type_q = 8'b00000000;
    UUT.dut.state_q = 3'b000;
    UUT.dut.stock_locate_q = 16'b0000000000000000;
    UUT.dut.symbol_enable_q = 1'b0;
    UUT.dut.timestamp_q = 48'b000000000000000000000000000000000000000000000000;
    UUT.dut.tracked_locate_q = 16'b0000000000000000;
    UUT.dut.bytes_q[6'b001010] = 8'b00000000;
    UUT.dut.bytes_q[6'b001001] = 8'b00000000;
    UUT.dut.bytes_q[6'b001000] = 8'b00000000;
    UUT.dut.bytes_q[6'b000111] = 8'b00000000;
    UUT.dut.bytes_q[6'b000110] = 8'b00000000;
    UUT.dut.bytes_q[6'b000101] = 8'b00000000;
    UUT.dut.bytes_q[6'b000010] = 8'b00000000;
    UUT.dut.bytes_q[6'b000001] = 8'b00000000;
    UUT.dut.bytes_q[6'b100011] = 8'b00000000;
    UUT.dut.bytes_q[6'b000000] = 8'b00000000;
    UUT.dut.bytes_q[6'b010010] = 8'b00000000;
    UUT.dut.bytes_q[6'b010001] = 8'b00000000;
    UUT.dut.bytes_q[6'b010000] = 8'b00000000;
    UUT.dut.bytes_q[6'b001111] = 8'b00000000;
    UUT.dut.bytes_q[6'b001110] = 8'b00000000;
    UUT.dut.bytes_q[6'b001101] = 8'b00000000;
    UUT.dut.bytes_q[6'b001100] = 8'b00000000;
    UUT.dut.bytes_q[6'b001011] = 8'b00000000;
    UUT.dut.bytes_q[6'b011010] = 8'b00000000;
    UUT.dut.bytes_q[6'b011001] = 8'b00000000;
    UUT.dut.bytes_q[6'b011000] = 8'b00000000;
    UUT.dut.bytes_q[6'b010111] = 8'b00000000;
    UUT.dut.bytes_q[6'b010110] = 8'b00000000;
    UUT.dut.bytes_q[6'b010101] = 8'b00000000;
    UUT.dut.bytes_q[6'b010100] = 8'b00000000;
    UUT.dut.bytes_q[6'b010011] = 8'b00000000;
    UUT.dut.bytes_q[6'b011110] = 8'b00000000;
    UUT.dut.bytes_q[6'b011101] = 8'b00000000;
    UUT.dut.bytes_q[6'b011100] = 8'b00000000;
    UUT.dut.bytes_q[6'b011011] = 8'b00000000;
    UUT.dut.bytes_q[6'b100010] = 8'b00000000;
    UUT.dut.bytes_q[6'b100001] = 8'b00000000;
    UUT.dut.bytes_q[6'b100000] = 8'b00000000;
    UUT.dut.bytes_q[6'b011111] = 8'b00000000;

    // state 0
    PI_in_data = 8'b00000000;
    PI_cfg_tracked_stock_locate = 16'b1000000000000000;
    PI_cfg_expected_stock_symbol = 64'b1000000000000000000000000000000000000000000000000000000000000000;
    PI_in_valid = 1'b0;
    PI_event_ready = 1'b0;
    PI_message_length = 16'b0000000000000000;
    PI_message_empty = 1'b0;
    PI_message_valid = 1'b0;
    PI_cfg_symbol_check_enable = 1'b0;
    PI_in_last = 1'b0;
    PI_message_sequence = 64'b0000000000000000000000000000000000000000000000000000000000000000;
    PI_reject_ready = 1'b0;
    PI_rst = 1'b1;
    PI_rearm = 1'b0;
  end
  always @(posedge clock) begin
    // state 1
    if (cycle == 0) begin
      PI_in_data <= 8'b00000000;
      PI_cfg_tracked_stock_locate <= 16'b0000000000000000;
      PI_cfg_expected_stock_symbol <= 64'b0000000000000000000000000000000000000000000000000000000000000000;
      PI_in_valid <= 1'b0;
      PI_event_ready <= 1'b0;
      PI_message_length <= 16'b0000000000000001;
      PI_message_empty <= 1'b0;
      PI_message_valid <= 1'b1;
      PI_cfg_symbol_check_enable <= 1'b0;
      PI_in_last <= 1'b0;
      PI_message_sequence <= 64'b0000000000000000000000000000000000000000000000000000000000000000;
      PI_reject_ready <= 1'b0;
      PI_rst <= 1'b0;
      PI_rearm <= 1'b0;
    end

    // state 2
    if (cycle == 1) begin
      PI_in_data <= 8'b00000000;
      PI_cfg_tracked_stock_locate <= 16'b0000000000000000;
      PI_cfg_expected_stock_symbol <= 64'b0000000000000000000000000000000000000000000000000000000000000000;
      PI_in_valid <= 1'b1;
      PI_event_ready <= 1'b0;
      PI_message_length <= 16'b0000000000000000;
      PI_message_empty <= 1'b0;
      PI_message_valid <= 1'b0;
      PI_cfg_symbol_check_enable <= 1'b0;
      PI_in_last <= 1'b1;
      PI_message_sequence <= 64'b0000000000000000000000000000000000000000000000000000000000000000;
      PI_reject_ready <= 1'b0;
      PI_rst <= 1'b0;
      PI_rearm <= 1'b0;
    end

    // state 3
    if (cycle == 2) begin
      PI_in_data <= 8'b00000000;
      PI_cfg_tracked_stock_locate <= 16'b0000000000000000;
      PI_cfg_expected_stock_symbol <= 64'b0000000000000000000000000000000000000000000000000000000000000000;
      PI_in_valid <= 1'b0;
      PI_event_ready <= 1'b0;
      PI_message_length <= 16'b0000000000000000;
      PI_message_empty <= 1'b0;
      PI_message_valid <= 1'b0;
      PI_cfg_symbol_check_enable <= 1'b0;
      PI_in_last <= 1'b0;
      PI_message_sequence <= 64'b0000000000000000000000000000000000000000000000000000000000000000;
      PI_reject_ready <= 1'b0;
      PI_rst <= 1'b0;
      PI_rearm <= 1'b1;
    end

    // state 4
    if (cycle == 3) begin
      PI_in_data <= 8'b00000000;
      PI_cfg_tracked_stock_locate <= 16'b0000000000000000;
      PI_cfg_expected_stock_symbol <= 64'b0000000000000000000000000000000000000000000000000000000000000000;
      PI_in_valid <= 1'b0;
      PI_event_ready <= 1'b0;
      PI_message_length <= 16'b0000000000000000;
      PI_message_empty <= 1'b0;
      PI_message_valid <= 1'b0;
      PI_cfg_symbol_check_enable <= 1'b0;
      PI_in_last <= 1'b0;
      PI_message_sequence <= 64'b0000000000000000000000000000000000000000000000000000000000000000;
      PI_reject_ready <= 1'b0;
      PI_rst <= 1'b0;
      PI_rearm <= 1'b0;
    end

    genclock <= cycle < 4;
    cycle <= cycle + 1;
  end
endmodule
