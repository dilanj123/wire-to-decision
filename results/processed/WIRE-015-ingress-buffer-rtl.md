# WIRE-015 — Common ingress beat buffer RTL and verification

## A. Starting state

The canonical repository was `/Users/Dilan/Projects/wire-to-decision`, branch `main`, at `185c487c5547014ec7bb90273e0a2ec33e37bc9c`, with `origin/main` equal and a clean tree after preflight reconciliation. The protected `kg-g0-env` tag remains peeled at `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. Authority

The implementation follows `docs/REQUIREMENTS.md`, `docs/MICROARCHITECTURE.md`, `docs/VERIFICATION_PLAN.md`, WIRE-D011, and WIRE-D012. The buffer is common infrastructure for Architecture A and any later authorized Architecture B.

## C. WIRE-D012 depth decision

WIRE-D012 freezes a synchronous two-entry FIFO of `{data[63:0], keep[7:0], last}`. The choice is a controlled baseline, not a performance-optimality claim. Output is registered storage with no combinational empty bypass.

## D. Buffer architecture

`rtl/common/wire_ingress_buffer.sv` uses two payload memories, one-bit read/write pointers, and a two-bit occupancy count. Input ready is asserted when occupancy is below two or when the current head transfers in the same cycle. Push and pop update pointers independently and preserve strict FIFO order.

## E. Interface semantics

The module exposes project-owned `in_*` and `out_*` ready/valid ports for data, keep, and last. It stores and forwards keep/last without interpreting protocol legality. Reset is synchronous active-high `rst` per WIRE-D011. Empty output is not a fall-through path.

## F. Full simultaneous push/pop

The FIFO accepts a replacement beat while full when the oldest output transfers. Directed simulation covers both occupancy-one and occupancy-two simultaneous operations; formal cover reaches both cases.

## G. Reset behavior

Reset clears occupancy and both pointers, discarding all pre-reset beats. Payload memories are not reset because occupancy makes their contents invalid until overwritten.

## H. Standalone cocotb verification

The independent queue scoreboard compares all `{data, keep, last}` fields. Five tests pass: empty/single/stall, fill/full backpressure, simultaneous operations, reset/frame-shaped traffic, and deterministic random traffic. Random seeds are 1, 7, and 19.

## I. Buffer-to-gearbox integration

`wire_buffer_gearbox_top.sv` composes the new common buffer with the existing gearbox. A one-test independent byte scoreboard passes under deterministic downstream stalls, preserving byte order, byte count, frame-final markers, and backpressure propagation.

## J. Formal reference model

`formal/ingress_buffer/wire_ingress_buffer_reference.sv` is an independent two-entry public-interface queue model. It does not inspect DUT-private state. It tracks payloads and occupancy from public transfers and checks ready, valid, oldest-payload correspondence, stall stability, and interface safety.

## K. Formal assumptions

The harness assumes synchronous active-high reset initialization and normal upstream ready/valid stability: an unaccepted valid beat holds `in_valid`, data, keep, and last stable. No downstream behavior is assumed; arbitrary `out_ready` stalls are allowed.

## L. Formal properties/results

The safety harness passes SBY/Yices k-induction at depth 20 for reset-empty behavior. The independent public-interface queue correspondence passes bounded SBY/Yices checking through depth 10, including ready/valid, payload/order, stall, and no-underflow/occupancy checks. Covers pass for occupancy-one and full simultaneous push/pop. The reference correspondence is reported as bounded, not unbounded induction.

## M. Yosys synthesis sanity

Standalone ingress-buffer elaboration/proc/opt/stat passes. The buffer-to-gearbox composition also elaborates and optimizes successfully. This is component synthesis sanity only; no P&R or application PPA claim is made.

## N. Regression preservation

WIRE-014 gearbox simulation remains 6/6 PASS with seeds 1, 7, and 19. WIRE-014 prove/reference/cover formal jobs remain PASS. The Python reference-model regression remains 71/71 PASS. Verilator lint/build reports no meaningful warnings.

## O. Requirement traceability

WIRE-015 provides Python-independent RTL simulation/formal evidence for the transfer semantics underlying REQ-IF-001 through REQ-IF-003: project-owned ready/valid transfer, lane/tuple preservation at the buffering boundary, and accepted-beat backpressure. REQ-IF-004 MAC-boundary behavior is not verified by this FIFO.

## P. Evidence classification

- Common ingress buffer: `RTL-SIMULATED`
- Buffer-to-gearbox composition: `RTL-SIMULATED`
- Named local FIFO properties: `FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS`; public-interface correspondence bounded through depth 10
- Yosys: `SYNTHESISED COMPONENT SANITY`

## Q. Problems/conflicts

No specification conflict or RTL defect was found. The external suite's macOS dynamic-library loader required temporary local symlinks during cocotb execution; these were removed and are not repository content.

## R. What remains unproven

Ethernet, IPv4, UDP, MoldUDP64, and ITCH parser RTL; normalized-event ready/valid integration; bounded order-state RTL; decision RTL; complete Architecture-A regression; application synthesis/P&R; timing, latency, throughput, CDC/RDC, C++ integration, and physical FPGA operation.

## S. WIRE-015 conclusion

WIRE-015 PASS. The common two-beat registered ingress FIFO and its buffer-to-gearbox composition are implemented and independently exercised. Formal evidence is explicitly separated into inductive local safety and depth-10 public-interface correspondence.
