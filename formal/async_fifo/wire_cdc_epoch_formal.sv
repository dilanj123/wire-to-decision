module wire_cdc_epoch_formal (
    input logic clk,
    input logic arst,
    input logic local_fault,
    input logic peer_up_async,
    input logic rearm_async
);
    logic epoch_up;
    logic local_ready;
    logic domain_reset;

    wire_cdc_epoch_domain dut (
        .clk(clk), .arst(arst), .local_fault(local_fault),
        .peer_up_async(peer_up_async),
        .rearm_async(rearm_async), .epoch_up(epoch_up),
        .local_ready(local_ready), .domain_reset(domain_reset)
    );

    initial assume(arst);

    logic fault_prev_q;
    always_ff @(posedge clk or posedge arst) begin
        if (arst)
            fault_prev_q <= 1'b0;
        else begin
            if (fault_prev_q)
                assert(!local_ready);
            fault_prev_q <= local_fault;
        end
    end

    always_ff @(posedge clk) begin
        if (arst)
            assert(!local_ready);
        if (!arst && domain_reset)
            assert(!local_ready);
        if (!arst && !epoch_up)
            assert(!local_ready);
    end
endmodule
