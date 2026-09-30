# WIRE-021 — Architecture A ITCH Decoder and Normalized-Event RTL

## Scope and baseline

Phase 2, starting commit `656f16a144b7f18a957686f8d1849b3ad0643e53`, on clean synchronized `main`; Gate-0 remained `06f5643a940ac2c6fcfab0e377169b48ce700107`. WIRE-020 is PASS/pushed and WIRE-D016 is recorded. WIRE-021 implements the frozen ITCH subset and WIRE-D008 normalized-event boundary only. No book, order state, decision logic, or full external-ingress production top is added.

## Authority and WIRE-D017

Authority: REQ-ITCH-001..004, REQ-ERR-005, WIRE-D007/WIRE-D008, WIRE-002’s official ITCH length/offset table, WIRE-010 Python decoder/types, and WIRE-020/WIRE-D016. No conflict was found. WIRE-D017 freezes event kind values `0 ADD`, `1 EXECUTE`, `2 EXECUTE_WITH_PRICE`, `3 CANCEL`, `4 DELETE`, `5 REPLACE`; side `0 BUY/B`, `1 SELL/S`; original ASCII source type; per-field validity; and the rule that no event is valid until the complete WIRE-D016 message boundary transfers.

## RTL and interfaces

Production module: `rtl/arch_a/wire_itch_decoder.sv`. It accepts WIRE-020 message metadata (`message_valid/ready`, sequence, length, empty) and message payload (`in_data/valid/ready/last`); captures up to the largest supported fixed message (44 bytes); validates the complete boundary before event publication; and holds event fields stable under event backpressure.

Configuration is tracked Stock Locate, symbol-check enable, and exact 8-byte expected symbol. Configuration is captured on synchronous active-high reset or `rearm`, and is held for the active configuration epoch. Re-arm discards partial input, pending event/rejection, and recovery state.

Event ports: `event_valid/event_ready`, `event_kind[2:0]`, `source_type[7:0]`, `mold_sequence[63:0]`, `itch_timestamp[47:0]`, `stock_locate[15:0]`, old/new references `[63:0]`, quantity/price `[31:0]`, side, and individual old-reference/new-reference/quantity/price/side validity outputs. Invalid payload fields are zeroed. Local fatal status is `reject_valid/reject_ready`, `reject_fatal`, `reject_code[2:0]`; stage state is `decoder_valid` and `recovery_required`.

Local codes: 0 empty message, 1 unsupported type, 2 wrong declared exact length, 3 invalid A/F side, 4 enabled A/F symbol mismatch, 5 inconsistent message boundary. The first fatal cause is retained. On semantic failure the decoder immediately suppresses future events, drains the remainder of the current message and subsequent WIRE-020 messages, and remains quarantined until reset/re-arm. It does not feed semantic failure into WIRE-020 structural packet result or WIRE-019 sequence commit.

## Message behavior

Official layouts/lengths and offsets are those frozen in WIRE-002 and mirrored by `model/python/wire_to_decision/itch.py`:

| Type | Bytes | Result |
|---|---:|---|
| A | 36 | ADD; new reference, quantity, price, side valid |
| F | 40 | ADD; same normalized fields as A; attribution ignored |
| E | 31 | EXECUTE; old reference and quantity valid |
| C | 36 | EXECUTE_WITH_PRICE; old reference and quantity valid; normalized resting price invalid |
| X | 23 | CANCEL; old reference and quantity valid |
| D | 19 | DELETE; old reference only |
| U | 35 | REPLACE; old/new references, quantity, price valid; side invalid/inherited |
| P | 44 | known non-mutating; no event |

All mutation types preserve supplied Mold sequence, 48-bit timestamp, Stock Locate, and source ASCII type. Every supported mutation type is filtered without recovery when its Stock Locate differs from configuration. A/F symbol bytes are compared exactly only when enabled; no padding normalization occurs. Unsupported types, empty messages, wrong lengths, invalid side, and enabled symbol mismatch latch fatal stage-local recovery.

## Verification and defect correction

Standalone Verilator/cocotb: **6/6 PASS**, seeds **1, 7, 19** (three seeded runs of all seven mutation types). Directed coverage includes each event mapping and field-valid tuple, P, endian-sensitive fields, Mold-sequence propagation, other-locate filtering, symbol enable/mismatch, invalid side, wrong length for A/F/E/C/X/D/U/P, empty, unsupported type, incomplete-message event suppression, event/rejection stalls, draining after error, and re-arm during a partial message. All seven mutation messages are cross-checked field-by-field against the WIRE-010 Python decoder; P is checked as non-mutating.

Mold header→framer→ITCH composition: **2/2 PASS**. A multi-message normal packet containing A, P, other-locate E, and U yields only the two expected mutation events and structural success; expected sequence advances by four. A structurally valid Mold packet containing A, unsupported ITCH, then U emits only the earlier A event, asserts ITCH recovery, drains the rest, and still reports WIRE-020 structural success; WIRE-019 expected sequence advances by the full structural message count. This is stage composition only, not the WIRE-022 64-bit ingress path.

One formal safety counterexample exposed a real RTL corner: a one-byte physical message with unsupported type `0x00` and declared length one entered the error-drain path, but the same cycle’s final-byte transition overwrote that state with validation; the default validation path returned to idle while recovery remained latched. The smallest correction gives first-byte type/declared-length failure priority over message-final validation for both unsupported types and known types with impossible lengths. The counterexample log, VCD, generated testbench, and SMT constraints are retained as `results/raw/rtl/itch_decoder/itch_safety_pre_fix_counterexample*`; the known-type one-byte wrong-length case also has its own passing fixed-vector formal job. No prior production stage was modified.

## Formal scope

SBY 0.69, `smtbmc yices`, Yices 2.7.0. No DUT-private state is used. Fourteen fixed-vector public-interface BMC jobs check A/F/E/C/X/D/U/P mappings, side and symbol failure, one-byte wrong-length handling, unsupported type, other-locate filtering, and empty-message failure. Depths are 48, 52, 44, 48, 35, 31, 47, 56, 48, 48, 16, 24, 48, and 12 respectively. A separate public-interface stall/recovery/re-arm safety BMC passes at depth 24; all ready inputs are unconstrained. Fixed-vector jobs drive the exact bounded packets and deterministic ready patterns; they do not exhaust all possible message bytes or configuration values. The generic safety job assumes reset at initialization and leaves upstream/downstream values unconstrained; it checks event/rejection stability, event suppression after recovery, drain availability, and reset/re-arm clearing. These are bounded checks, not induction/unbounded proofs. No cover job is claimed.

## Regression and implementation sanity

- WIRE-019/019A standalone: 14/14 PASS; six-stage composition: 2/2 PASS; established formal jobs rerun and PASS.
- WIRE-020 standalone: 10/10 PASS; seven-stage composition: 2/2 PASS; established formal jobs rerun and PASS.
- Python regression: 71/71 PASS.
- Verilator 5.053 `--lint-only --Wall`: standalone and Mold→framer→ITCH composition PASS with no warnings.
- Yosys 0.69+154 standalone and composition synthesis/check: PASS, zero final check problems. ABC combinational-network notices are recorded; this is component synthesis sanity only.
- No P&R or performance measurement was run.

## Traceability and limits

Supports REQ-ITCH-001..004, WIRE-D007/D008/D016/D017, and the stage-local semantic portion of REQ-ERR-005. No claim is made that an event has committed to order state: there is no downstream mutation/decision logic yet. The fail-closed drain is ITCH-stage-local, not parser-wide/global recovery. The complete external-ingress-to-event path and global recovery/event gating remain WIRE-022. ITCH types outside A/F/E/C/X/D/U/P remain unsupported and fail closed.

Evidence: `results/raw/rtl/itch_decoder/`, `results/processed/WIRE-021-itch-decoder-rtl.md`, and EVID-021. WIRE-021 may PASS after these results and the complete regression evidence are committed and pushed. Do not mark the Architecture-A parser checklist item complete; do not start WIRE-022 within this task.
