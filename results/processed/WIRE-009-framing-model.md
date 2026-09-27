# WIRE-009 — Python Ethernet/IPv4/UDP/MoldUDP64 Framing Model

## A. Starting state

SOURCE-DERIVED: Started at `/Users/Dilan/Projects/wire-to-decision`, branch
`main`, commit `22b68f38fd907b8599ca9112cd29a9e30befa789`, with a clean tree.
The protected `kg-g0-env` tag remained unchanged and peeled to
`06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. Authority used

SOURCE-DERIVED: Used the relevant protocol/framing sections of
`docs/REQUIREMENTS.md`, `docs/MICROARCHITECTURE.md`, `docs/DECISIONS.md`,
`docs/SPEC_SOURCES.md`, `docs/VERIFICATION_PLAN.md`, the WIRE-002 protocol
lock, and the WIRE-008 canonical Python types. No authority conflict was found.

## C. Modules added

IMPLEMENTED: Added `checksum.py`, `mold.py`, and `framing.py`. Exported the
framing result/state/message types and pure `frame_packet` / `parse_mold_packet`
entry points. Raw ITCH payloads remain immutable opaque bytes.

## D. Ethernet profile implementation

SPECIFIED / IMPLEMENTED: Validates the 14-byte post-MAC Ethernet II header and
accepts IPv4 EtherType `0x0800` only. VLAN, IPv6, ARP, MAC filtering, and FCS
are outside scope. Ethernet padding after the IPv4 Total Length is permitted;
bytes inside the declared IPv4 datagram are parsed only through that boundary.

## E. IPv4 implementation

SPECIFIED / IMPLEMENTED: Requires Version 4, IHL 5, Protocol 17, valid
20-byte header checksum, non-fragmented flags (`MF=0` and Fragment Offset=0),
configured destination IPv4 address, and Total Length no smaller than the
header and no greater than available bytes. IPv4 options, reassembly, routing,
and IPv6 are not implemented.

## F. IPv4 checksum implementation

PYTHON-UNIT-TESTED: `checksum.py` implements the one's-complement checksum
directly. A fixed known-valid header vector, single-bit corruption, and
checksum-field corruption are tested independently of the parser's packet
construction path.

## G. UDP implementation

SPECIFIED / IMPLEMENTED: Parses the fixed 8-byte UDP header, requires
destination-port match, requires UDP Length >= 8 and exactly equal to the
declared IPv4 payload length, and accepts checksum zero only. Non-zero checksum
is rejected as an unsupported MVP capability; it is not labelled invalid UDP
generally.

## H. MoldUDP64 implementation

SPECIFIED / IMPLEMENTED: Parses the 20-byte big-endian downstream header
(10-byte Session, 8-byte sequence, 2-byte count), validates session and normal
expected sequence, parses exactly the declared number of two-byte-length
message blocks, and emits `FramedMessage(mold_sequence, payload)` values.

## I. Session/sequence state model

IMPLEMENTED: `FramingState` is immutable and explicit. Normal packets advance
expected sequence modulo 2^64 as required. Heartbeats require the expected
sequence, emit no messages, and do not advance state. Sequence/session errors
fail closed. No retransmission or automatic recovery exists.

## J. Heartbeat/end-of-session behaviour

PYTHON-UNIT-TESTED: Count zero is a successful no-message heartbeat. Count
`0xFFFF` is not treated as normal message count; it emits no messages, reports
`END_OF_SESSION`, and enters recovery-required invalid status without advancing
the expected sequence.

## K. Malformed/truncated behaviour

PYTHON-UNIT-TESTED: Header truncation, IPv4/UDP length errors, checksum errors,
Mold length-field truncation, message truncation, and forbidden Mold trailing
bytes are explicit failures. Malformed/truncated framing invalidates status;
ordinary profile filtering rejects without mutating framing state.

## L. Late-suffix prefix behaviour

PYTHON-UNIT-TESTED: A count-three Mold packet with two complete messages and a
third truncated block returns the two completed messages with implicit
sequences intact, reports `MESSAGE_TRUNCATED`, and returns fail-closed status.
No packet-level rollback is implied.

## M. Test coverage

PYTHON-UNIT-TESTED: The complete suite contains 29 tests: all 18 WIRE-008
primitive tests plus 11 WIRE-009 tests. Coverage includes positive one/multi-
message packets, padding, heartbeat, sequence progression, end-of-session,
checksum, Ethernet/IP/UDP/Mold negatives, and malformed suffix retention.

## N. Requirement traceability

PYTHON-UNIT-TESTED: WIRE-009 exercises REQ-IF-005, REQ-ETH-001 through
REQ-ETH-003, REQ-IP-001 through REQ-IP-007, REQ-UDP-001 through REQ-UDP-004,
REQ-MOLD-001 through REQ-MOLD-009, and the framing portions of REQ-ERR-002 and
REQ-ERR-004. No ITCH decoding, book, decision, RTL, or end-to-end requirement
is marked verified.

## O. Dependencies

IMPLEMENTED: No third-party Python dependency was added. The implementation
uses the standard library only and performs no network or file I/O.

## P. Problems/conflicts

INFERENCE: One initial test fixture exposed a padding-boundary bug: UDP was
initially sliced from available frame bytes rather than the declared IPv4
datagram. The implementation was corrected to respect Total Length, and the
padding regression now passes. No specification conflict remains.

## Q. What remains unproven

UNPROVEN: Full Python reference-model correctness, ITCH decoding, normalized
events, bounded order state, aggregates, decisions, RTL, formal application
properties, synthesis/P&R, timing, latency, throughput, CDC, C++ integration,
and physical FPGA operation.

## R. WIRE-009 conclusion

PASS: The project-owned Ethernet II / IPv4 / UDP / MoldUDP64 framing and
sequence model is implemented and exercised by 29 standard-library tests. The
model stops at raw ITCH message payloads and establishes no ITCH or downstream
functional correctness claim.
