# WIRE-016 — Ethernet II parser RTL and verification

## A. Starting state

Started at `32d124c671e52fa36a366b1c0bdbffddcf2316ca` on `main`, with a clean tree and local `main == origin/main`. Gate-0 peeled commit remained `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. Authority

Used the frozen requirements, microarchitecture, verification/formal plans, WIRE-002 protocol lock, WIRE-014 gearbox evidence, and WIRE-015 ingress-buffer evidence. The Ethernet profile is Ethernet II, IPv4 EtherType `0x0800`, no VLAN support, post-MAC input, and synchronous active-high reset WIRE-D011.

## C. WIRE-015 bookkeeping corrections

`PROJECT_STATE.md` now distinguishes existing gearbox + common-buffer/composition RTL evidence from future protocol-parser evidence. `EVIDENCE_INDEX.md` now acknowledges EVID-014 and EVID-015 without promoting them to protocol-parser evidence.

## D. Ethernet parser architecture

`rtl/arch_a/wire_eth_parser.sv` uses a small `HEADER/PAYLOAD/DROP/REJECT` FSM. MAC bytes are consumed and not retained. EtherType is assembled big-endian from bytes 12 and 13. Payload uses one registered byte holding slot for ready/valid stability.

## E. Header/EtherType semantics

Exactly 14 header bytes are consumed. `0x0800` enters payload forwarding. `0x8100` and all other EtherTypes enter drop/filter handling. A frame-final byte before header byte 13 is `ETH_TRUNCATED_HEADER`; `0x0800` with byte 13 final is `ETH_EMPTY_IPV4_PAYLOAD`.

## F. Payload stripping/forwarding

Only bytes after the header are output. `out_last` is copied from the accepted final payload byte. Payload acceptance is coupled to output capacity; stalled output data/last remain stable. A final payload byte completes the frame and the next cycle starts a new header.

## G. Filter/fatal rejection semantics

The local rejection interface is ready/valid with `reject_fatal` and `reject_code`: filtered EtherType is nonfatal code 0; truncated header is fatal code 1; empty IPv4 payload is fatal code 2. A pending rejection blocks new input and output until handshaken.

## H. Backpressure and reset

The parser uses synchronous active-high `rst`. Reset clears header, payload, drop, and rejection state. No empty fall-through payload path was introduced. Input/output/rejection stalls were tested.

## I. Standalone cocotb

The four-test standalone suite passed. It covered valid IPv4, EtherType endianness, unsupported EtherType table including VLAN, exhaustive truncation lengths 1–13, empty/one-byte payload boundaries, output/rejection stalls, back-to-back operation, and deterministic random traffic with seeds 1, 7, and 19.

## J. Buffer→gearbox→Ethernet integration

The one-test composition suite passed. It independently packed post-MAC frames into legal 64-bit beats, checked payload-only output and `out_last`, checked filtered VLAN behavior, and exercised downstream stalls through the existing two-beat buffer and gearbox.

## K. Python cross-check

RTL-stage classification agreed with the existing Python overlap cases for IPv4 acceptance, unsupported EtherTypes including VLAN, truncated Ethernet headers, and empty IPv4 payload.

## L. Formal reference model

`formal/eth_parser/wire_eth_parser_reference.sv` is an independent public-interface reference FSM and one-byte holding model. It does not inspect DUT-private state. `wire_eth_parser_reference.sby` checked public correspondence through BMC depth 40.

## M. Formal assumptions

The harness assumes only normal upstream ready/valid stability while input is stalled and synchronous reset initialization. Downstream output and rejection readiness remain unconstrained. The safety job used BMC depth 20; the public-interface correspondence and cover jobs used depth 40.

## N. Formal properties/results

The safety BMC passed stall stability, rejection stability, and terminal status blocking. The independent correspondence BMC passed input/output/rejection behavior, payload holding, EtherType classification, truncation/empty-payload outcomes, and no-header-leak behavior represented by the reference. Covers passed for payload, drop/filter, rejection stall, and terminal payload transfer. These are bounded checks, not unbounded parser proofs.

## O. Yosys synthesis sanity

Standalone parser and buffer→gearbox→Ethernet composition elaboration/check passed with no reported problems. This is component synthesis sanity only.

## P. Regression preservation

WIRE-014 gearbox remained 6/6 cocotb PASS and its prove/reference/cover jobs passed. WIRE-015 standalone buffer remained 5/5, composition 1/1, and formal jobs passed. Python regression remained 71/71.

## Q. Requirement traceability

REQ-IF-002, REQ-IF-003, and the Ethernet-facing portion of REQ-IF-004/005 are RTL-simulated at the byte-stage boundary. REQ-ETH-001, REQ-ETH-002, and REQ-ETH-003 are RTL-simulated for EtherType acceptance, no-VLAN filtering, header stripping, and consume/drop behavior. Local parser safety/correspondence is formally checked only to the documented BMC depths. No IPv4 requirements are claimed RTL-verified.

## R. Evidence classification

Ethernet II parser and buffer→gearbox→Ethernet composition: `RTL-SIMULATED`. Named local parser properties: `FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS`, bounded through depth 20/40 as stated. Yosys result: `SYNTHESISED COMPONENT SANITY`.

## S. Problems/conflicts

No specification conflict found. No production RTL outside the Ethernet stage was changed.

## T. What remains unproven

IPv4, UDP, MoldUDP64, ITCH, normalized-event, bounded-state, and decision RTL remain unimplemented. Complete Architecture-A regression, application synthesis/P&R, timing, latency, throughput, CDC/RDC, C++ checking, and physical FPGA operation remain unproven.

## U. WIRE-016 conclusion

WIRE-016 passes its scoped Ethernet II implementation, simulation, bounded formal, synthesis-sanity, and regression-preservation checks. Next task: WIRE-017 — Architecture A IPv4 byte parser RTL and verification.
