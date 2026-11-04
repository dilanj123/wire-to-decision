# WIRE-029 — CDC FIFO extension

Added an original 8 × 73-bit asynchronous FIFO and a separate wrapper before the unchanged Architecture-A functional top. Local binary pointers generate Gray pointers; each remote Gray pointer crosses two synchronizer flops. Full/empty backpressure prevents overwrite and underflow.

The wrapper uses independent RX/proc clocks, asynchronous reset assertion and two-stage local release. A synchronized epoch-up level invalidates the peer after a one-sided reset or parser/book fatal. The remote domain learns after two destination synchronizer edges; this is not instantaneous. A low/high explicit rearm starts a fresh shared epoch, resets both FIFO pointer domains and clears parser/book/decision state before readiness returns. Stale FIFO data and pending decisions are cleared before reopening.

**Results:** FIFO Cocotb 2/2; full-top CDC integration 3/3; Architecture-A functional regression 15/15; Python 71/71; Verilator lint PASS; SBY/Yices local bounded jobs PASS (FIFO depth 16, epoch readiness depth 12); Yosys FIFO and CDC-top hierarchy/synthesis sanity PASS. The end-to-end ADD decision matches the Python ReferenceOracle. Reset tests cover both one-sided directions, a full FIFO, a partial frame, a stalled decision, parser-fatal recovery, and explicit rearm.

**Limitations:** Bounded local formal checks do not prove metastability behavior or the complete two-clock network processor. Gray-bus skew constraints remain necessary for physical implementation. No physical board, CDC/RDC signoff, P&R, timing, or throughput evidence was produced.

Raw logs: results/raw/rtl/cdc_fifo/.
