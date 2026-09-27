# Wire-to-Decision Requirements

## Status and language

This is the authoritative normative requirement set created by WIRE-006. Requirements are specified, not verified. `MUST` and `SHALL` are normative; `MAY` is optional. Labels identify the nature of a statement: `SPECIFIED`, `ASSUMED`, `PROJECT RESTRICTION`, `HYPOTHESIS`, or `UNPROVEN`.

External protocol facts are sourced through `docs/SPEC_SOURCES.md` and the WIRE-002 evidence. The implementation target and experiment controls are sourced through `docs/IMPLEMENTATION_TARGET.md` and WIRE-005. No third-party source is normative.

## Interface and framing

- REQ-IF-001 [SPECIFIED]: The application boundary SHALL be a project-owned ready/valid interface with `rx_data[63:0]`, `rx_keep[7:0]`, `rx_valid`, `rx_ready`, and `rx_last`.
- REQ-IF-002 [SPECIFIED]: `rx_data[7:0]` SHALL contain the earliest byte in each beat; byte time SHALL increase with lane number.
- REQ-IF-003 [SPECIFIED]: A beat SHALL transfer only on `rx_valid && rx_ready`; every non-final beat SHALL have `rx_keep == 8'hFF`; the final beat SHALL have contiguous valid lanes beginning at lane 0; `rx_last` SHALL identify the final beat.
- REQ-IF-004 [PROJECT RESTRICTION]: The first accepted frame byte SHALL be the first byte of the Ethernet destination MAC address. Preamble, SFD, FCS, PHY, and MAC implementation are outside this boundary.
- REQ-IF-005 [SPECIFIED]: A malformed or truncated frame SHALL produce no new state mutation from bytes that were not part of a complete accepted protocol message; any already committed earlier complete Mold messages are governed by REQ-ERR-004.

## Ethernet

- REQ-ETH-001 [SOURCE REQUIREMENT]: The IPv4 Ethernet II EtherType SHALL be `16'h0800`.
- REQ-ETH-002 [PROJECT RESTRICTION]: The MVP SHALL accept Ethernet II IPv4 only and SHALL not support VLAN-tagged frames.
- REQ-ETH-003 [PROJECT VALIDATION RULE]: A frame that is not an accepted IPv4 Ethernet II frame SHALL be consumed or dropped without ITCH/order-state mutation and without decision generation.

## IPv4

- REQ-IP-001 [SOURCE REQUIREMENT]: The IP version SHALL be 4, IHL SHALL be 5, and protocol SHALL be 17 for UDP.
- REQ-IP-002 [PROJECT RESTRICTION]: IPv4 options, IPv6, routing, ICMP, and fragmentation reassembly SHALL not be implemented.
- REQ-IP-003 [PROJECT VALIDATION RULE]: A datagram SHALL be accepted as non-fragmented only when `MF == 0` and `Fragment Offset == 0`; the DF bit is not required for this classification.
- REQ-IP-004 [PROJECT VALIDATION RULE]: The IPv4 header checksum SHALL validate before downstream state mutation.
- REQ-IP-005 [PROJECT VALIDATION RULE]: Total Length SHALL be at least the header length, no greater than the available datagram bytes, and internally consistent with the received frame boundary.
- REQ-IP-006 [PROJECT RESTRICTION]: Destination IPv4 address SHALL be configurable/filterable.
- REQ-IP-007 [PROJECT VALIDATION RULE]: Malformed, truncated, unsupported, or filtered IPv4 packets SHALL not create ITCH/book mutations.

## UDP

- REQ-UDP-001 [SOURCE REQUIREMENT]: UDP protocol number SHALL be 17, the UDP header length SHALL be at least 8 bytes, and UDP Length SHALL include header and payload.
- REQ-UDP-002 [PROJECT VALIDATION RULE]: UDP Length SHALL be consistent with IPv4 payload length and available received bytes.
- REQ-UDP-003 [PROJECT RESTRICTION]: Destination UDP port SHALL be configurable/filterable.
- REQ-UDP-004 [PROJECT RESTRICTION]: A zero UDP checksum SHALL be accepted for IPv4; a non-zero checksum SHALL be rejected before ITCH state mutation. This is a project restriction, not a claim that UDP requires zero checksums.

## MoldUDP64

- REQ-MOLD-001 [SOURCE REQUIREMENT]: The MVP SHALL use MoldUDP64 Version 1.00 framing with big-endian numeric fields.
- REQ-MOLD-002 [SOURCE REQUIREMENT]: The downstream header SHALL be 20 bytes: Session offset 0/length 10, Sequence Number offset 10/length 8, and Message Count offset 18/length 2.
- REQ-MOLD-003 [SOURCE REQUIREMENT]: Each message block SHALL begin with a two-byte Message Length whose value excludes the length field; block size is `2 + Message Length`.
- REQ-MOLD-004 [SPECIFIED]: For a normal packet with count `N`, header sequence SHALL equal `expected_sequence`; message `i` SHALL correspond to `header_sequence + i`; after complete successful processing, expected sequence SHALL advance by `N`.
- REQ-MOLD-005 [SOURCE REQUIREMENT]: Message Count zero SHALL be treated as heartbeat, shall carry the expected sequence, shall not advance expected sequence, and shall not mutate the book.
- REQ-MOLD-006 [SOURCE REQUIREMENT]: Message Count `16'hFFFF` SHALL be treated as end-of-session according to the source framing; it shall not mutate the book and shall enter recovery-required state.
- REQ-MOLD-007 [PROJECT RESTRICTION]: The MVP SHALL not generate MoldUDP Request Packets, interact with a retransmission server, or implement GLIMPSE/live exchange recovery.
- REQ-MOLD-008 [PROJECT VALIDATION RULE]: Session, sequence, message lengths, packet bounds, and message count SHALL be checked before the corresponding mutation event is committed.
- REQ-MOLD-009 [SPECIFIED]: Expected-sequence arithmetic SHALL be unsigned 64-bit modular arithmetic; after a normal packet, `expected_sequence = (expected_sequence + N) mod 2^64`.

## ITCH common representation and profile

- REQ-ITCH-001 [SOURCE REQUIREMENT]: Integer fields SHALL be decoded big-endian; Stock Locate is 16 bits; Timestamp is 48-bit nanoseconds since midnight; Order Reference Number is 64 bits; Shares is 32 bits; Price(4) is a 32-bit integer with four implied decimal places.
- REQ-ITCH-002 [PROJECT RESTRICTION]: The MVP SHALL track one configured 16-bit Stock Locate at a time; other locate values SHALL not mutate the tracked book. Stock Locate is dynamic/day-specific and shall not be assumed stable across trading days.
- REQ-ITCH-003 [PROJECT RESTRICTION]: The supported state-mutating subset SHALL be exactly `A`, `F`, `E`, `C`, `X`, `D`, and `U`, using the official message lengths/offsets recorded in WIRE-002 evidence.
- REQ-ITCH-004 [PROJECT VALIDATION RULE]: `P` Trade Message SHALL be recognized as legitimate non-displayable ITCH traffic that does not mutate displayed-order state. An unclassified or unsupported message type SHALL not silently mutate state; the profile-rejection policy is REQ-ERR-005.

## Bounded order state

- REQ-BOOK-001 [SPECIFIED]: The MVP SHALL support at most `MAX_ORDERS = 1024` valid tracked orders using 512 sets and 2 ways per set.
- REQ-BOOK-002 [SPECIFIED]: Each valid entry SHALL store at minimum a 64-bit order reference, 32-bit Price(4), 32-bit remaining quantity, side, and valid state.
- REQ-BOOK-003 [PROJECT RESTRICTION]: There SHALL be no eviction of a valid order. Duplicate reference, full/colliding set, unknown reference where a reference is required, and conflicting replacement reference SHALL be state-integrity failures.
- REQ-BOOK-004 [SPECIFIED]: Add `A`/`F` SHALL allocate a valid order for the tracked locate; F attribution need not be retained. Duplicate reference SHALL invalidate the book.
- REQ-BOOK-005 [SPECIFIED]: E/C execution and X cancellation SHALL subtract their quantities; zero remainder SHALL remove the order; over-subtraction SHALL invalidate the book. C execution price SHALL not replace the stored resting display price.
- REQ-BOOK-006 [SPECIFIED]: D SHALL remove the referenced order; U SHALL logically remove the old reference and create the new reference with new shares/price while inheriting side and tracked-stock identity. U may take multiple internal cycles.
- REQ-BOOK-007 [PROJECT VALIDATION RULE]: Every accepted mutation SHALL update order state and side aggregate consistently; aggregate overflow or underflow SHALL invalidate the book.
- REQ-BOOK-008 [PROJECT RESTRICTION]: Price-level/BBO logic, multi-symbol books, silent eviction, and a Stock Directory subsystem are outside the MVP.

## Aggregates and decision

- REQ-DEC-001 [SPECIFIED]: The state SHALL maintain unsigned 48-bit `bid_total` and `ask_total` representing remaining displayed shares of valid tracked orders by side.
- REQ-DEC-002 [SPECIFIED]: `imbalance` SHALL be a signed difference `signed(bid_total) - signed(ask_total)` with sufficient width for the full difference.
- REQ-DEC-003 [SPECIFIED]: A BUY event SHALL occur only when the valid armed state, decision enable, nonzero budget, `previous_imbalance < +THRESHOLD`, and `current_imbalance >= +THRESHOLD` all hold after a qualifying mutation.
- REQ-DEC-004 [SPECIFIED]: A SELL event SHALL occur only when the valid armed state, decision enable, nonzero budget, `previous_imbalance > -THRESHOLD`, and `current_imbalance <= -THRESHOLD` all hold after a qualifying mutation.
- REQ-DEC-005 [SPECIFIED]: A decision event SHALL consume one budget credit; `decision_count` SHALL never exceed `initial_budget`; no decision shall be emitted when book invalid, decision disabled, or budget is zero.
- REQ-DEC-006 [SPECIFIED]: Non-mutating messages SHALL not create a new crossing evaluation unless a later authoritative requirement explicitly changes this rule.
- REQ-DEC-007 [PROJECT RESTRICTION]: The decision is a deterministic synthetic engineering function, not a production trading strategy.

## Errors, recovery, and transaction limits

- REQ-ERR-001 [SPECIFIED]: The control state SHALL include `active_session`, `expected_sequence`, `book_valid`, and `recovery_required`.
- REQ-ERR-002 [SPECIFIED]: Unexpected session, sequence gap, duplicate, sequence regression/reorder, malformed/truncated framing, state-integrity failure, aggregate error, collision/full condition, or end-of-session SHALL set `book_valid = 0`, set `recovery_required = 1`, and suppress decisions.
- REQ-ERR-003 [SPECIFIED]: Recovery SHALL require explicit external re-arm/reset with known session, expected sequence, empty/known order state, budget, and configuration; no hidden automatic live recovery is permitted.
- REQ-ERR-004 [PROJECT RESTRICTION]: If complete earlier Mold messages have already committed before a malformed later suffix is detected, those updates are not rolled back; the book is then invalidated and future decisions are suppressed.
- REQ-ERR-005 [PROJECT DECISION]: `P` may be consumed without mutation. Any unclassified or unsupported message type SHALL cause profile rejection, invalidate the book, require re-arm, and produce no mutation from that message. This avoids silently skipping unknown semantics.

## Latency and throughput

- REQ-LAT-001 [SPECIFIED]: L1 SHALL measure first ITCH message byte accepted to corresponding normalized-event valid.
- REQ-LAT-002 [SPECIFIED]: L2 SHALL measure handshake of the final input byte required to determine the triggering mutation to `decision_valid`.
- REQ-LAT-003 [SPECIFIED]: L3 SHALL measure first Ethernet frame byte accepted to `decision_valid`; it SHALL not be called physical wire latency without a future MAC/PHY boundary.
- REQ-LAT-004 [SPECIFIED]: Canonical latency measurements SHALL use legal input, no output/backpressure stall, known armed state, and `book_valid = 1`; report cycles first and convert to time only with valid clock/timing evidence.

## CDC/RDC

- REQ-CDC-001 [PROJECT RESTRICTION]: Architecture A/B experiments SHALL be single-clock; CDC differences SHALL not contaminate the parser comparison.
- REQ-CDC-002 [SPECIFIED]: The later CDC extension SHALL use independent RX and processing domains and a project-original asynchronous FIFO.
- REQ-CDC-003 [SPECIFIED]: The FIFO SHALL use power-of-two depth, binary local pointers, Gray-coded crossing pointers, two-flop pointer synchronizers, safe full/empty generation, and explicit reset/epoch readiness.
- REQ-CDC-004 [SPECIFIED]: Independent asynchronous reset assertion and controlled local release, one-sided reset, stale token/data protection, and stream invalidation on ambiguous reset SHALL be tested. No commercial CDC/RDC signoff may be claimed.

## Implementation and evidence

- REQ-PPA-001 [PROJECT DECISION]: Application implementation evidence SHALL use LFE5U-85F-8BG381C, `--85k --package CABGA381 --speed 8`, 156.25 MHz objective, and the WIRE-005 five-seed set.
- REQ-PPA-002 [SPECIFIED]: Later reports SHALL include LUT/cells, FFs, EBRs, DSP/multipliers, meaningful I/O, utilization, critical path, WNS/slack, routed status, latency cycles, labelled latency time, initiation interval, and throughput.
- REQ-PPA-003 [PROJECT RESTRICTION]: The raw 64-bit interface arithmetic `64 × 156.25 MHz = 10 Gbit/s` SHALL not be reported as parser or decision throughput.
- REQ-PPA-004 [SPECIFIED]: Failure to meet the 156.25 MHz objective SHALL remain valid evidence and SHALL not be hidden by changing architecture or reporting conventions.

## Software and verification ownership

- REQ-SW-001 [SPECIFIED]: A Python reference model SHALL be implemented before application RTL and independently model protocol checks, Mold sequencing, supported ITCH decoding, filtering, order state, aggregates, fail-closed behavior, crossings, and budget.
- REQ-SW-002 [SPECIFIED]: A later independent C++20 checker SHALL parse canonical replay packets, maintain an independent order store, derive expected decisions, compare RTL logs, report mismatches, produce latency distributions, and write machine-readable summaries.
- REQ-SW-003 [PROJECT RESTRICTION]: The C++ checker SHALL not call the Python model for expected values.
- REQ-SW-004 [PROJECT RESTRICTION]: Synthetic canonical packets are acceptable and preferred for controlled tests; live exchange captures are not required for correctness.

## Provenance

- REQ-PROV-001 [PROJECT POLICY]: Mandatory parser, order state, decision, CDC/FIFO, formal, Python, C++, and project-specific verification work SHALL remain original Wire-to-Decision work.
- REQ-PROV-002 [PROJECT POLICY]: Third-party infrastructure MAY be used later only under the pinned, classified, independently checked policy in `docs/THIRD_PARTY_MANIFEST.md`; it shall not become normative expected-value logic.
- REQ-PROV-003 [PROJECT POLICY]: Every future claim SHALL use the evidence classification appropriate to actual recorded tool output.

## Open implementation parameters

The following are intentionally not frozen here: exact ingress buffer depth, RTL module/state names, pipeline register placement, external register mapping, exact sequence-wrap implementation details after a dedicated decision, and implementation-specific cycle schedules. They SHALL be specified before the implementation task that needs them and SHALL not contradict this document.
