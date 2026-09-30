# WIRE-019 — MoldUDP64 header and sequence controller

## A. Starting state

Repository: `/Users/Dilan/Projects/wire-to-decision`; branch `main`; starting HEAD `0e85377352d4fd500f911c64c678a84b6bb512b9`; local `main` matched `origin/main`; starting tree clean. Gate-0 peeled commit: `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. Authority and WIRE-D015

The implementation follows the WIRE-002 Mold profile, WIRE-018 byte-stream boundary, the Python Mold model, and REQ-MOLD/REQ-ERR requirements. WIRE-D015 records the deferred sequence-commit contract: a normal packet commits `expected_sequence += message_count mod 2^64` only after downstream success.

## C. Architecture

`rtl/arch_a/wire_mold_header_seq.sv` captures the fixed header, compares all ten session bytes and the big-endian sequence, classifies count zero/FFFF/normal, exposes normal metadata, then forwards opaque body bytes after metadata handshake. `wire_buffer_gearbox_eth_ipv4_udp_mold_top.sv` provides the six-stage composition. Reset is synchronous active-high per WIRE-D011.

## D. Header, heartbeat, EOS, and normal behavior

Header truncation is fatal code 0; session mismatch code 1 has priority over sequence mismatch code 2; trailing bytes code 3 has priority over EOS code 4. Exact heartbeat emits no metadata/body/result and leaves sequence unchanged. Exact EOS emits code 4 and enters recovery. Normal counts produce stable metadata (`sequence`, `count`, `body_empty`) before body output. A failed result leaves sequence unchanged and blocks until re-arm; a successful result advances modulo 2^64. Zero-byte normal bodies are explicitly represented by `packet_body_empty` and wait for a downstream result.

## E. Backpressure and reset/re-arm

Metadata, raw-body output, and rejection tuples remain stable under their respective stalls. Input is blocked while metadata, result, rejection, or recovery state is pending. Reset and explicit re-arm discard partial/pending state, load the configured session/expected sequence, clear recovery, and restart at header byte 0.

## F. Cocotb simulation

Standalone: Verilator 5.053, cocotb 2.1.0.dev0+41564633; the initial committed suite contained 9 tests and passed 9/9 at WIRE-019. WIRE-019A added five tests; the current suite passes 14/14. It covers normal/deferred commit, body-empty failure/re-arm, heartbeat/wrap, trailing precedence, EOS recovery, session/sequence priority, truncation/reject stall, metadata/body stalls, deterministic random opaque bodies (seeds 1, 7, 19), immediate fail-closed on all four fatal drain paths, and re-arm during drain. The composition suite passes 2/2.

## G. Python cross-check and regressions

The independent Python cross-check passed 9 cases: header truncation, session mismatch, sequence mismatch, exact/trailing heartbeat, exact/trailing EOS, normal success/advance, and 64-bit wrap. WIRE-D015’s normal body is opaque in this stage; the Python side used valid message-block bytes where required. Python regression: 71/71.

Established primitive simulation regressions also passed: WIRE-014 gearbox 6/6, WIRE-015 ingress buffer 5/5, WIRE-016 Ethernet 4/4, WIRE-017 IPv4 5/5, and WIRE-018 UDP 5/5. Existing formal jobs were re-run where the established invocation was usable; their prior passing statuses remain unchanged. A pre-existing invocation-path issue in some older SBY files was not a WIRE-019 RTL issue and is not used as new WIRE-019 evidence.

## H. Formal assumptions and results

All WIRE-019 references use public DUT ports only; DUT-private state used: **NO**. Assumptions are synchronous reset initialization, upstream ready/valid stability while stalled, and configuration stability within a reset/re-arm epoch. General downstream readiness remains unconstrained in safety BMC; targeted fixed-vector jobs use ready high only where stated.

| Property group | Result / scope |
|---|---|
| output, rejection, metadata stall stability; recovery blocking; deferred commit safety | BOUNDED CHECKED depth 36, SBY BMC, `smtbmc yices` |
| normal header/body and no early sequence advance | FIXED-VECTOR BOUNDED CHECKED depth 40 |
| heartbeat exact semantics | FIXED-VECTOR BOUNDED CHECKED depth 28 |
| exact EOS semantics | FIXED-VECTOR BOUNDED CHECKED depth 28 |
| session mismatch priority | FIXED-VECTOR BOUNDED CHECKED depth 28 |
| sequence mismatch priority | FIXED-VECTOR BOUNDED CHECKED depth 28 |
| 64-bit sequence wrap | FIXED-VECTOR BOUNDED CHECKED depth 40 |
| body-empty normal, heartbeat/EOS trailing precedence, and header truncation | FIXED-VECTOR BOUNDED CHECKED at depths 28, 28, and 16 respectively |
| reachability covers | COVERED depth 40; covers are reachability only |

The formal jobs do not claim unbounded proof, exhaustive count/session space, or message-block correctness.

## I. Toolchain/synthesis

Verilator standalone and six-stage lint passed with no meaningful warnings. Yosys standalone and six-stage elaboration/synthesis sanity passed. Classification: SYNTHESISED COMPONENT SANITY. No P&R or performance measurement was run.

## J. Requirement traceability

REQ-MOLD-001/002 are exercised by the 20-byte big-endian header implementation and fixed-vector checks. REQ-MOLD-004/005/006/009 are exercised by sequence comparison, heartbeat/EOS handling, deferred commit, and wrap simulation/formal checks. REQ-MOLD-008 is only partial because message-block lengths are WIRE-020. REQ-MOLD-003 is not implemented. REQ-ERR-001/002/003 are supported at stage-local `controller_valid`/`recovery_required` level; global `book_valid` and decision suppression are not present. REQ-IF-005 is not established end-to-end.

## K. Evidence classification and limitations

Mold header/sequence controller: RTL-SIMULATED. Named local properties: FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS with bounded/fixed-vector scope recorded above. Six-stage composition: RTL-SIMULATED. Yosys: SYNTHESISED COMPONENT SANITY.

Still unproven: Mold message-block length/count parsing, late malformed suffix/no-rollback integration, ITCH parser, normalized events, cross-layer fatal-error-to-mutation gating, bounded order state, decisions, complete Architecture-A regression, application synthesis/P&R, timing/latency/throughput, Architecture-A bottleneck, Architecture B, CDC/RDC, independent C++ checker, and physical FPGA operation.

## L. WIRE-019 conclusion

PASS for the scoped MoldUDP64 header/session/sequence controller and its recorded bounded local properties. WIRE-020 remains the next task.

## WIRE-019A immediate fail-closed addendum

Independent review found that four fatal conditions entered `S_DROP` without immediately updating `controller_valid_q` and `recovery_required_q`: session mismatch with trailing data, sequence mismatch with trailing data, heartbeat trailing data, and EOS trailing data. Rejection and eventual recovery were already correct; the stage control outputs lagged detection until the physical packet ended. The production RTL now clears validity and asserts recovery in each detection branch while leaving `S_DROP` input-ready so the current malformed packet can drain. Metadata, body, and packet-result outputs remain inactive. Expected sequence is unchanged.

The formal safety harness previously asserted that `in_ready` must be low whenever recovery is set. That assertion contradicted the required current-packet drain behavior. It now checks that metadata, body, and result paths remain blocked in recovery; the four fixed-vector jobs assert `in_ready` during drain alongside immediate invalid/recovery outputs. This is a correction to the property scope. It does not change normal traffic assumptions.

WIRE-019A simulation: standalone 14/14 and six-stage composition 2/2 PASS. Formal: safety BMC depth 36 PASS; cover depth 40 PASS; session mismatch with trailing bytes and sequence mismatch with trailing bytes pass fixed-vector BMC at depth 28; heartbeat trailing and EOS trailing pass fixed-vector BMC at depth 28. All references use public interfaces only (DUT-private state: NO), synchronous reset, and the WIRE-019 upstream ready/valid stability assumption. `in_ready` is allowed high only to drain the detected malformed packet. The WIRE-019 session/sequence/heartbeat/EOS/wrap/deferred-commit jobs were rerun and pass.

WIRE-019A changed no sequence-commit behavior. Expected sequence still advances only on successful downstream packet-result handshake. Reset/re-arm still discards pending state and loads the configured session/sequence.
