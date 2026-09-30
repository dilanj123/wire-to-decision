# WIRE-021 — Architecture A ITCH Decoder and Normalized-Event RTL

## A. Starting state and authority

Started on canonical repository `main` at `656f16a144b7f18a957686f8d1849b3ad0643e53`, clean and equal to `origin/main`. `kg-g0-env^{}` remained `06f5643a940ac2c6fcfab0e377169b48ce700107`. WIRE-020 was recorded PASS and pushed; WIRE-D016 and EVID-020 were present.

Authority inspected: ITCH/error requirements, normalized-event microarchitecture, WIRE-D007/D008, WIRE-002 official length/offset table, WIRE-010 task/evidence and Python decoder/types, and WIRE-020 task/interface/evidence. No authority conflict was found. No third-party protocol implementation was consulted.

## B. WIRE-D017 and architecture

Added WIRE-D017 to `docs/DECISIONS.md`. Event kind encoding is 0 ADD, 1 EXECUTE, 2 EXECUTE_WITH_PRICE, 3 CANCEL, 4 DELETE, 5 REPLACE; side encoding is 0 BUY/B and 1 SELL/S. Source type remains its original ASCII byte. Every optional event field has an independent valid output; invalid fields are driven to zero. Event valid cannot assert until the complete WIRE-D016 message boundary, represented by transfer of the final payload byte with `in_last`, has completed.

Production RTL: `rtl/arch_a/wire_itch_decoder.sv`. Companion stage composition: `rtl/arch_a/wire_mold_itch_top.sv`, wiring WIRE-019 header/sequence → WIRE-020 message framer → ITCH decoder. The semantic reject is not wired into the WIRE-020 structural result.

Configuration inputs are tracked Stock Locate, symbol-check enable, and expected 8-byte symbol. They are captured on reset/re-arm and must remain stable during an active configuration epoch. Reset/re-arm is synchronous active-high and clears partial-message state, pending event/rejection, and decoder recovery.

## C. Supported layouts and results

Lengths and offsets below are the exact frozen WIRE-002 layouts; multibyte numbers are big-endian.

| Type | Exact bytes | RTL normalized result |
|---|---:|---|
| A | 36 | ADD; new reference, quantity, price, side valid |
| F | 40 | ADD; same book-relevant fields as A; attribution ignored |
| E | 31 | EXECUTE; old reference and quantity valid |
| C | 36 | EXECUTE_WITH_PRICE; old reference/quantity valid; normalized resting price invalid |
| X | 23 | CANCEL; old reference and quantity valid |
| D | 19 | DELETE; old reference only |
| U | 35 | REPLACE; old/new references, quantity, price valid; side invalid/inherited |
| P | 44 | recognized known non-mutating; no event |

All mutation events preserve the per-message Mold sequence, 48-bit ITCH timestamp, Stock Locate, and original source-type byte. A/F/E/C/X/D/U for an untracked locate are consumed without event/recovery. A/F symbol check is exact eight-byte equality only when enabled. Invalid B/S is fatal only for A/F. Unsupported types, empty messages, wrong exact lengths, invalid side, and enabled symbol mismatch latch stage-local recovery and preserve the first rejection code.

## D. Fail-closed draining and structural independence

Upon a semantic error, `decoder_valid` deasserts and `recovery_required` asserts. The decoder emits no event for the failing message or later messages, while continuing to accept/drop the rest of the current message and subsequent framed messages so WIRE-020 can finish its structural packet parse. Re-arm/reset is required before semantic decoding resumes. This is not global parser recovery or book validity.

## E. Standalone simulation and Python comparison

Verilator 5.053, cocotb 2.1.0.dev0+41564633: **6/6 PASS**. Deterministic seeds: **1, 7, 19**, each exercising all seven mutation types with distinct Mold sequences. Directed tests check all seven exact field/validity mappings, P, multi-byte endian-sensitive fields, timestamp/sequence/locate, other-locate filtering, symbol check enabled/disabled, bad A/F side, one-short length for every supported type including P, empty/unsupported messages, no event before the final complete-message transfer, event stability under stall, rejection stability under stall, drain/quarantine, and re-arm during a partial message.

For A/F/E/C/X/D/U, the RTL event tuple is compared field-by-field to `decode_itch_message(FramedMessage(...), ModelConfig(...))`; P is compared as known non-mutating. This comparison supplements the test-owned explicit scoreboard and is not the scoreboard source.

## F. Mold header/framer/ITCH composition

**2/2 PASS**. Test 1 sends a structurally valid Mold packet with A, P, other-locate E, and U. Only A and U events appear, with their exact Mold sequences and payload metadata; WIRE-020 succeeds and WIRE-019 advances by the full count. Test 2 sends A, unsupported type, U in a structurally valid Mold packet. A transfers before the later semantic error; the failing and later message emit no events; ITCH recovery asserts; the remainder drains; WIRE-020 still reports structural success and WIRE-019 sequence advances according to WIRE-D015. This composition begins at Mold input and is not the full external 64-bit ingress composition reserved for WIRE-022.

## G. Formal model and properties

SBY 0.69, `smtbmc yices`, Yices 2.7.0. Formal harnesses use only the DUT public interface; no private register/state references occur.

Fourteen fixed-vector BMC jobs pass:

| Property group | Depth | Scope |
|---|---:|---|
| A mapping and complete-boundary gate | 48 | fixed 36-byte A vector |
| F mapping | 52 | fixed 40-byte F vector |
| E mapping | 44 | fixed 31-byte E vector |
| C mapping / resting price invalid | 48 | fixed 36-byte C vector |
| X mapping | 35 | fixed 23-byte X vector |
| D mapping | 31 | fixed 19-byte D vector |
| U mapping | 47 | fixed 35-byte U vector |
| P non-mutation | 56 | fixed 44-byte P vector |
| Invalid A/F side | 48 | fixed invalid-side A vector |
| Enabled symbol mismatch | 48 | fixed symbol mismatch A vector |
| Known type, impossible one-byte declared length | 16 | fixed corner case; rejection and no event |
| Unsupported type recovery | 24 | fixed unsupported message and drain |
| Other locate filtering | 48 | fixed otherwise-valid A; no event/recovery |
| Empty message | 12 | empty metadata transaction |

Separate safety BMC at depth 24 passes for event stability, rejection stability, recovery event suppression, drain availability, and re-arm clearing under arbitrary ready/valid/data values after the initial synchronous reset. Fixed-vector jobs use fixed packet/configuration contents; safety assumes reset at initialization. All are bounded checks, not inductive/unbounded proofs. There are no formal covers claimed.

### Formal-discovered correction

An initial generic safety BMC produced a real counterexample: a one-byte physical message with unsupported type `0x00` and declared length one entered the error-drain path, but the same cycle’s final-byte transition overwrote that state with validation; the default validation path returned to idle while recovery remained latched. The RTL now gives the detected first-byte type/declared-length failure priority over final-byte validation for unsupported and known types. The failure log and replayable VCD, generated testbench, and SMT constraints are retained in `results/raw/rtl/itch_decoder/itch_safety_pre_fix_counterexample*`. The known-type one-byte wrong-length vector passes `itch_length_edge` depth 16 and corrected safety passes depth 24. This was an RTL corner defect and was fixed narrowly. No earlier parser-stage RTL changed.

## H. Lint, synthesis sanity, and regressions

- Verilator 5.053 `--lint-only --Wall`: standalone and Mold→framer→ITCH composition PASS, no warnings.
- Yosys 0.69+154 standalone and composition `synth`/`check`: PASS, zero final check problems. ABC reported its combinational-network notices; result is component synthesis sanity only.
- WIRE-019/019A standalone: **14/14 PASS**; six-stage composition: **2/2 PASS**; all established SBY jobs rerun PASS.
- WIRE-020 standalone: **10/10 PASS**; seven-stage composition: **2/2 PASS**; all established SBY jobs rerun PASS.
- Python suite: **71/71 PASS**.

Raw logs, tool versions, formal property inventory, and the retained pre-fix counterexample are under `results/raw/rtl/itch_decoder/`.

## I. Requirement traceability and evidence class

Supports REQ-ITCH-001..004, the WIRE-D007/D008/D016/D017 contract, and stage-local REQ-ERR-005 behavior. It does not establish order-state commit, global `book_valid`, parser-wide event gating, or rollback. The complete external-ingress-to-normalized-event top and parser-wide recovery are WIRE-022.

- ITCH decoder and Mold→framer→ITCH composition: **RTL-SIMULATED**.
- Named local mappings/rejection/stability properties: **FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS**, with fixed-vector BMC depth and limitations above.
- Yosys: **SYNTHESISED COMPONENT SANITY**.
- No P&R, timing, throughput, latency, or application-performance claim.

## J. Conclusion and remaining work

WIRE-021 meets its scoped acceptance criteria after correction of the formal-discovered one-byte declared-length corner. WIRE-020 structural packet success remains independent of ITCH semantics. No book, decision, or complete external-ingress parser top exists yet. Phase 2 remains active; the master checklist Architecture-A parser item remains unchecked. Next task is WIRE-022; it was not started here.
