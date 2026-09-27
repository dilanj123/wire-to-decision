# Wire-to-Decision Verification Plan

## Status

This plan defines future verification. No application tests, reference model, RTL simulation, formal application run, synthesis, or P&R has been executed. Every application requirement is `SPECIFIED / NOT YET VERIFIED`.

## Verification ownership

The Python model is the primary functional oracle and must be implemented before application RTL. Parser/event, order-state, aggregate, and decision scoreboards remain separate. End-to-end tests are required in addition to component scoreboards. A later independent C++20 checker provides implementation diversity and must not call Python for expected values.

## Layered plan

### Protocol and framing

Directed and constrained-random tests cover lane ordering, keep/last legality, truncation, Ethernet EtherType, IPv4 version/IHL/options/checksum/length/fragmentation, UDP protocol/port/length/checksum policy, Mold header/message lengths, session/sequence, heartbeat, and end-of-session.

### ITCH and normalized events

Test exact field extraction and normalized-event semantics for A, F, E, C, X, D, and U, including source lengths, timestamps, Stock Locate filtering, side, shares, prices, references, and invalid-field behavior. P is tested as legitimate non-mutating traffic. Unsupported/unclassified types are tested as profile rejection.

### Book and aggregates

Separate order-state scoreboard tests cover insert, duplicate, partial/full execute, partial/full cancel, delete, replace, unknown reference, over-subtract, new-reference conflict, hash collisions, full sets, aggregate overflow/underflow, side totals, and no eviction.

### Decision

Separate decision scoreboard tests cover positive and negative crossings, no repeated decision while beyond threshold, cross-back and recross, enable suppression, budget exhaustion/decrement, invalid-book suppression, mutation-only evaluation, payload stability, and budget safety.

### Error/recovery

Test session mismatch, sequence gap, duplicate, reorder/regression, malformed message, truncation, late malformed suffix with no rollback, profile rejection, end-of-session, explicit re-arm, known empty state, and suppression until recovery.

### Backpressure

Test ingress backpressure, normalized-event consumer stalls, decision-output stalls, ready/valid payload stability, no duplication, no loss, and deterministic recovery around packet boundaries.

### Randomness and reproducibility

Use directed corner cases, constrained-random valid traffic, constrained-random malformed traffic, longer stateful sequences, and reproducible seeds. Each failure retains seed and input data sufficient for replay. Synthetic canonical packets are preferred; live exchange captures are unnecessary.

## Traceability matrix

The ranges below enumerate every stable requirement identifier in `docs/REQUIREMENTS.md`; each identifier in a range has the same planned verification level and status. No application requirement is currently verified.

| Requirement | Verification level | Planned method | Evidence target | Status |
|---|---|---|---|---|
| REQ-IF-001..005 | protocol/framing, RTL-simulated | Python model, directed/random ingress, ready/valid tests | processed simulation report and raw logs | SPECIFIED / NOT YET VERIFIED |
| REQ-ETH-001..003 | protocol/framing | canonical frame vectors and parser scoreboard | model/RTL protocol evidence | SPECIFIED / NOT YET VERIFIED |
| REQ-IP-001..007 | protocol/framing | valid/invalid header vectors, checksum and fragmentation cases | model/RTL protocol evidence | SPECIFIED / NOT YET VERIFIED |
| REQ-UDP-001..004 | protocol/framing | length/port/checksum vectors, rejection-before-mutation checks | model/RTL protocol evidence | SPECIFIED / NOT YET VERIFIED |
| REQ-MOLD-001..009 | protocol/framing, state/error | packet framing, sequence, heartbeat, EOS, malformed suffix tests | model/RTL Mold evidence | SPECIFIED / NOT YET VERIFIED |
| REQ-ITCH-001..004 | ITCH/event | official-format directed vectors and event scoreboard | normalized-event evidence | SPECIFIED / NOT YET VERIFIED |
| REQ-BOOK-001..008 | order-state | independent order scoreboard, directed and random state sequences | book/aggregate evidence | SPECIFIED / NOT YET VERIFIED |
| REQ-DEC-001..007 | decision | independent decision scoreboard and crossing sequences | decision evidence | SPECIFIED / NOT YET VERIFIED |
| REQ-ERR-001..005 | error/recovery | malformed, discontinuity, profile-rejection, suffix, and re-arm tests | recovery evidence | SPECIFIED / NOT YET VERIFIED |
| REQ-LAT-001..004 | simulation/implementation | cycle counters under canonical no-stall conditions; routed timing later | latency reports | SPECIFIED / NOT YET VERIFIED |
| REQ-CDC-001..004 | CDC extension | async-clock simulation, formal/local checks, reset-domain tests | CDC evidence with limitations | SPECIFIED / NOT YET VERIFIED |
| REQ-PPA-001..004 | synthesis/P&R/derived | Yosys, five fixed seeds, nextpnr, timing/resource extraction | raw reports and processed comparison | SPECIFIED / NOT YET VERIFIED |
| REQ-SW-001..004 | reference/C++ verification | independent model tests, replay, checker comparison | model/checker evidence | SPECIFIED / NOT YET VERIFIED |
| REQ-PROV-001..003 | review/process | provenance review, manifests, evidence-index review | process evidence | SPECIFIED / NOT YET VERIFIED |

## Implementation evidence plan

Architecture A must undergo Yosys ECP5 synthesis, nextpnr-ECP5 P&R, timing analysis, resource extraction, five fixed seeds, latency-cycle measurement, and throughput measurement on the WIRE-005 target. Reports must distinguish target frequency, achieved timing, critical path, WNS/slack, utilization, latency cycles, labelled time, initiation interval, and throughput. Failure to meet 156.25 MHz is retained as evidence.

The later A/B comparison must use the same target, toolchain, top-level boundary, protocol subset, normalized-event contract, order state, decision logic, workload, P&R options, report extraction, and seeds.

## No overclaiming

Simulation PASS applies only to the tested design/input/scope. Formal results must name assumptions and bounds. A synthesis or P&R result for application RTL is not timing closure unless timing evidence supports it. Raw 10 Gbit/s interface arithmetic is not parser throughput.
