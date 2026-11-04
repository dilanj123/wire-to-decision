# WIRE-029 — Minimal Asynchronous FIFO and CDC/RDC Extension

## Starting state and scope

- Starting main: 6fe5044c5493392d52c518cfa0bc9992d9345bc0, clean and equal to origin.
- Gate-0 peeled commit: 06f5643a940ac2c6fcfab0e377169b48ce700107.
- WIRE-028B had closed the controlled A/B experiment and rejected B. Architecture A remains unchanged.
- Add a separate two-clock learning wrapper and original 8-entry framed-beat FIFO.

## RTL

wire_async_fifo stores 73-bit {rx_data, rx_keep, rx_last} words. Each side has an extra-wrap-bit binary pointer, Gray pointer, two-flop synchronized remote Gray pointer, local full/empty state, and an independent asynchronous-assert reset. FIFO storage is not reset; epoch pointer resets ensure stale locations are unreachable.

wire_arch_a_cdc_top puts that FIFO before the unchanged single-clock Architecture-A functional top. RX and processing clocks are independent. A two-flop synchronized epoch-up level carries invalidation; parser/book fatal recovery also invalidates the processing epoch. A synchronized low/high rearm handshake resets both FIFO pointer domains and the parser/book/decision epoch before reopening traffic. The wrapper does not cross multi-bit configuration.

## Reset and physical CDC limits

Reset assertion is asynchronous in each local domain; release passes through two local-clock stages. A one-sided reset is observed remotely after the peer-up level traverses two destination synchronizer flops; the local reset gate then asserts asynchronously. Remote invalidation is therefore not instantaneous. Traffic or an old decision can still progress before the remote clock observes the synchronized level; the invalidated epoch is cleared before fresh traffic is reopened.

For physical implementation, constrain Gray-pointer bus skew/maximum delay from source pointer registers to first-stage synchronizers so the bus cannot span multiple source transitions. No board implementation, metastability resolution measurement, Gray-bus routing check, or commercial CDC/RDC signoff is included.

## Verification

- Standalone FIFO Cocotb: 2/2, Verilator; 5 ns write / 7 ns read and 11 ns write / 4 ns read. Covers order, full/empty, backpressure, simultaneous traffic, pointer wrap, randomized stalls, and stable stalled output.
- CDC full-top Cocotb: 3/3. A real valid Ethernet/IPv4/UDP/Mold/ITCH ADD frame matches the Python ReferenceOracle decision. Tests cover RX reset with FIFO full, processing reset during a buffered partial frame, a stalled decision across one-sided reset, parser-fatal epoch invalidation, active rearm, and fresh-frame processing.
- Existing functional MVP regression: 15/15; Python: 71/71.
- SBY/Yices BMC: FIFO local safety depth 16 with independent clock inputs and common-reset assumption; epoch readiness gate depth 12 with multiclock engine semantics. These are bounded local checks, not CDC signoff.
- Verilator strict lint passes with only the intentional mixed reset-use warning class suppressed (SYNCASYNCNET); the single-clock modules themselves are unchanged.
- Yosys hierarchy/process/check/synthesis sanity passes for FIFO and full CDC top.

## Classification and remaining limitations

FIFO and CDC-wrapper behavior: RTL-simulated. Named local properties: bounded formal checks under documented assumptions. Yosys: synthesised component sanity. No physical CDC/RDC signoff, post-route skew analysis, hardware operation, or whole-design formal proof is claimed.
