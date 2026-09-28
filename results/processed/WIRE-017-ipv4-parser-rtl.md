# WIRE-017 — Architecture A IPv4 parser RTL

## A. Starting state

Starting HEAD was `1acca7d0493dcdd1e4a75b6645f6190406bf14c9`, on clean `main`, matching `origin/main`. Gate-0 remains peeled at `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. Authority

The implementation follows REQ-IP-001..007, REQ-IF-005, WIRE-D011/WIRE-D012, WIRE-002 protocol facts, WIRE-016 stage contracts, the Python framing/checksum model, and the frozen validation priority.

## C. PROJECT_STATE corrections

Stale Phase-2 wording was corrected to include the common ingress buffer, gearbox and Ethernet II stage, with IPv4 now recorded as implemented with simulation evidence and later stages still unimplemented. Evidence wording remains qualification-aware.

## D. IPv4 parser architecture

`rtl/arch_a/wire_ipv4_parser.sv` is a small synchronous FSM with fixed 20-byte header capture, a one-byte payload holding register, payload/padding/drop states, and a stable terminal rejection state. It does not parse UDP or buffer a complete packet.

## E. Header-field semantics

The stage consumes Version/IHL, Total Length, flags/offset, Protocol, checksum, and destination fields in network byte order. It requires Version 4, IHL 5, Protocol 17, MF=0 and offset=0, and exact configured destination equality. DF is ignored and both DF=0 and DF=1 pass the fragmentation rule.

## F. Validation priority

The complete-header priority is version, IHL, Total Length lower bound, checksum, fragmentation, destination, then protocol. Directed tests cover multi-fault headers and match the Python model for overlapping classifications.

## G. Checksum implementation

The RTL uses an original fixed ten-word one's-complement sum over the 160-bit header, with explicit end-around carry. Cocotb includes an independently constructed checksum vector and single-bit/header-checksum corruption cases.

## H. Total-Length/padding behavior

For accepted `Total Length > 20`, exactly `Total Length - 20` payload bytes are forwarded. `out_last` marks the declared datagram boundary, not necessarily physical Ethernet `in_last`; later physical bytes are consumed as padding without rejection. Physical end before the declared boundary produces fatal `IPV4_INVALID_LENGTH`. The late-truncation tests retain the already-forwarded prefix and expose the fatal status.

## I. Filtering/fatal behavior

Nonfatal filters are invalid Version, unsupported IHL, wrong destination and non-UDP Protocol. Fatal local errors are header truncation, Total-Length error, checksum, fragmentation and the WIRE-D013 empty project-payload case. Rejection fields are held until `reject_ready`; input and payload output are blocked while terminal status is pending.

## J. WIRE-D013

WIRE-D013 was added. A profile-valid `Total Length == 20` packet is rejected locally as fatal `IPV4_EMPTY_PROJECT_PAYLOAD`, because the downstream byte stream cannot represent an empty packet with a valid-byte `out_last`. The general IPv4 model remains unchanged and can report a later UDP-header truncation for the same bytes.

## K. Late-truncation/speculative-prefix limitation

The stage may emit payload prefix bytes before a late physical truncation is discovered. WIRE-017 explicitly does not claim end-to-end REQ-IP-007 mutation suppression; no downstream mutating RTL exists yet. Later parser/control integration must gate state mutation on complete accepted datagrams.

## L. Backpressure/reset

The one-byte output register is stable under `out_valid && !out_ready`. Rejection fields are stable under rejection backpressure, and `in_ready` is low during a pending rejection. Synchronous active-high reset clears header, payload, padding/drop and rejection state.

## M. Standalone cocotb

Standalone cocotb passed 5/5 tests. It covered fixed vectors, exhaustive header lengths 1..19, filters, priority, padding, stalls, reset, back-to-back packets and deterministic random seeds 1, 7 and 19.

## N. Composition verification

The `wire_buffer_gearbox_eth_ipv4_top` composition passed 3/3 tests. It verified accepted payload and padding suppression, filtered/fatal cases, declared-length late truncation and deterministic random backpressure through the complete four-stage byte path.

## O. Python cross-check

The focused cross-check passed for invalid version, IHL, Total Length, checksum, fragmentation, destination and protocol. Intentional layer-local differences are limited to WIRE-D013/late downstream truncation semantics; the Python production model was not changed.

## P. Formal reference model

`formal/ipv4_parser/wire_ipv4_parser_reference.sv` is a public-interface-only reference FSM. It does not inspect DUT-private state. `wire_ipv4_parser_safety.sv` passed at depth 20. The reference cover job passed at depth 32 and reached payload, drop, padding and reject paths. The full unconstrained correspondence BMC was configured at depth 32 but became solver-bound after step 22 on the qualified Yices flow; it is intentionally not claimed as closed.

## Q. Formal assumptions

The harness assumes synchronous reset initialization, stable input payload while upstream valid is stalled, and a fixed configured destination `0xC6336407` for the bounded correspondence instance. Downstream `out_ready` and `reject_ready` remain unconstrained. No DUT-private signal is used by the reference.

## R. Formal properties/results

- Output/rejection stall stability: local safety PASS at depth 20.
- Public-interface reference setup and state correspondence: harness elaborates; full BMC not closed after step 22.
- Payload/declared-length/padding behavior: exercised in cocotb; cover paths reached at depth 32.
- Classification/checksum correspondence: not claimed formally closed because the bounded solver run was stopped while solver-bound.

## S. Yosys synthesis sanity

Standalone parser and buffer→gearbox→Ethernet→IPv4 elaboration/synthesis sanity passed with Yosys 0.69+154. This is component sanity only; no P&R, PPA, timing or throughput result is claimed.

## T. Regression preservation

WIRE-014 gearbox simulation remained 6/6, WIRE-015 ingress-buffer simulation remained 5/5 standalone plus 1/1 composition, WIRE-016 remained 4/4 standalone plus 1/1 composition, and the Python regression remained 71/71.

## U. Requirement traceability

Simulation evidence exercises REQ-IP-001 through REQ-IP-006 and the IPv4 portion of REQ-IF-005. Formal safety/cover evidence is local and bounded as described above. REQ-IP-007 end-to-end mutation suppression remains unproven at RTL integration level; the late-truncation prefix limitation is explicit.

## V. Evidence classification

IPv4 parser and buffer→gearbox→Ethernet→IPv4 composition: `RTL-SIMULATED`. Local stall/rejection safety: `FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS` at depth 20. Reference reachability: `COVERED` at depth 32. Full classification/payload correspondence: pending formal closure. Yosys: `SYNTHESISED COMPONENT SANITY`.

## W. Problems/conflicts

No protocol-authority conflict was found. The full public-interface correspondence job is a tool-capacity limitation on the qualified local flow, not an RTL counterexample.

## X. What remains unproven

UDP, MoldUDP64, ITCH, normalized-event, order-state and decision RTL; end-to-end fatal-error mutation suppression; complete Architecture-A parser; application formal proof; application synthesis/P&R, timing, latency, throughput, CDC/RDC, C++ integration and physical FPGA operation.

## Y. WIRE-017 conclusion

The IPv4 stage is implemented and functionally RTL-simulated, with local safety formal checks and covers passing. WIRE-017A closes the named correspondence groups using decomposed bounded jobs documented below. `REQ-IP-007` end-to-end mutation suppression remains unproven because no downstream mutating RTL exists.

## WIRE-017A formal-closure addendum

The original monolithic public-interface BMC used SBY 0.69, `smtbmc yices`,
depth 32, reached step 22 and became solver-bound. It produced no RTL
counterexample and remains retained as historical evidence rather than being
relabelled as a failure or proof.

WIRE-017A left `rtl/arch_a/wire_ipv4_parser.sv` unchanged and split the
correspondence into public-interface-only jobs:

| Job | Scope | Result |
| --- | --- | --- |
| `wire_ipv4_header_reference.sby` | Eight fixed header vectors, priority, code/fatal result, no output | PASS, BMC depth 28 |
| `wire_ipv4_checksum_reference.sby` | Valid/corrupt checksum vectors | PASS, BMC depth 28 |
| `wire_ipv4_payload_reference.sby` | Four symbolic payload bytes, ordering and final marker | PASS, BMC depth 32 |
| `wire_ipv4_padding_reference.sby` | Declared boundary and physical padding suppression | PASS, BMC depth 40 |
| `wire_ipv4_truncation_reference.sby` | Physical end before declared length | PASS, BMC depth 32 |
| `wire_ipv4_next_packet_reference.sby` | Two rejected packets and new header-byte-zero alignment | PASS, BMC depth 44 |
| existing safety job | Output/rejection stall stability | PASS, BMC depth 20 |
| existing cover job | Payload/drop/padding/reject reachability | PASS, cover depth 32 |

The reference harnesses use no DUT-private state. Assumptions are
synchronous reset initialization, upstream valid/data/last stability while
stalled, and fixed `cfg_destination_ipv4 = 0xC6336407`. Targeted data-path
jobs hold downstream ready high to isolate the correspondence; the separate
safety job leaves downstream stalls unconstrained. Header and checksum jobs
use fixed vectors, while payload values are symbolic. These are bounded and
finite-vector checks, not exhaustive proofs over all 16-bit lengths or all
160-bit header combinations.

The existing cocotb suite remains 5/5 standalone and 3/3 composition, the
Python suite remains 71/71, and Verilator/Yosys checks remain passing. No
production RTL change was required. WIRE-017 is therefore closed for the
named local formal property set under documented assumptions, while
end-to-end mutation suppression and later protocol stages remain unproven.
