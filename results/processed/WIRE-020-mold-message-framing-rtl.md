# WIRE-020 — MoldUDP64 message-block framing RTL

## A. Starting state

Started on `main` at `c75abb81bd67e7d28ecefaad8e390a70ba53fbce`, clean and equal to `origin/main`. Protected Gate-0 tag peeled to `06f5643a940ac2c6fcfab0e377169b48ce700107`. Canonical remote: `https://github.com/dilanj123/wire-to-decision`.

## B. Authority and scope

Relevant requirements/microarchitecture/formal authorities, WIRE-019/019A records, Python `mold.py`/`oracle.py`, and WIRE-019 RTL were inspected. No unresolved authority conflict was found. Python structurally parses Mold message blocks before ITCH semantics; its successful sequence transition occurs only after exact structural success.

WIRE-020 adds the Mold message-block framer only. It does not decode ITCH or add order/decision logic.

## C. WIRE-D016

`docs/DECISIONS.md` now records WIRE-D016. Per-message metadata precedes payload. A nonempty message boundary is valid only on transfer of the final declared payload byte with `out_last=1`; zero-length structural messages complete on the metadata handshake with `message_empty=1`. The packet succeeds structurally only when exactly Message Count blocks consume the entire physical body. This result has no dependency on future ITCH classification. Complete earlier messages are retained if a later suffix fails; no rollback exists.

## D. Framer architecture and interface

Production module: `rtl/arch_a/wire_mold_message_framer.sv`.

- Packet metadata input: `packet_valid/packet_ready`, `packet_sequence[63:0]`, `packet_message_count[15:0]`, `packet_body_empty`.
- Raw Mold body input: `in_valid/in_ready`, `in_data[7:0]`, `in_last`.
- Message metadata output: `message_valid/message_ready`, `message_sequence[63:0]`, `message_length[15:0]`, `message_empty`.
- Raw message payload output: `out_valid/out_ready`, `out_data[7:0]`, `out_last`.
- Structural result: `packet_result_valid/packet_result_ready`, `packet_result_success`.
- Fatal local rejection: `reject_valid/reject_ready`, `reject_fatal`, `reject_code[1:0]`.
- Control: synchronous active-high `rst` and `rearm`.

Message sequence is `packet_sequence + completed-message index` modulo 2^64. Message lengths are two-byte big-endian values excluding their own field. Payload remains opaque.

Rejection codes: `0 MESSAGE_LENGTH_TRUNCATED`; `1 MESSAGE_TRUNCATED`; `2 TRAILING_BYTES`; `3 reserved`. Packet result and rejection are independently held until their respective handshakes. A failed packet requires explicit rearm/reset before accepting another metadata transaction.

## E. Structural behavior and defect corrected

The FSM captures WIRE-019 metadata only on its packet metadata handshake, then reads each length field, holds per-message metadata until accepted, streams payload through a one-byte holding register, and withholds packet success until all message boundaries and physical termination are complete.

Directed simulation initially found that early physical termination inside a positive declared message incorrectly reused the `MESSAGE_LENGTH_TRUNCATED` action used for a missing next block length. The implementation was corrected with a distinct `A_PACKET_MESSAGE_ERROR` transition yielding `MESSAGE_TRUNCATED`. The failing first-run log is retained separately; the final rerun passes. No pre-existing production RTL was changed.

Other cases:

- Missing both bytes (WIRE-019 `packet_body_empty`) and a first length byte without its second byte produce `MESSAGE_LENGTH_TRUNCATED`.
- A positive length with no payload or insufficient payload produces `MESSAGE_TRUNCATED`; no `out_last` is asserted for the incomplete message.
- Fewer complete blocks than Message Count produces `MESSAGE_LENGTH_TRUNCATED`.
- After all N complete blocks, extra bytes are drained and produce `TRAILING_BYTES`; all N complete message outputs remain valid.
- A zero-length message emits metadata with empty asserted and no payload; it contributes one structural message boundary.

## F. Standalone cocotb

Verilator 5.053 and cocotb 2.1.0.dev0+41564633; **10/10 PASS**. Tests cover one/multiple messages, lengths 1/2/>2, zero length between nonempty messages, wrap annotation, empty positive-count body, both length truncation forms, positive-message truncation, count shortfall, trailing data, metadata/payload/result/reject stalls, rearm during partial state and pending rejection, synchronous reset during a held payload, and Python comparisons. Deterministic randomized seeds: **1, 7, 19**. Python comparison vectors include valid bodies, missing length byte, insufficient message bytes, too few blocks, trailing bytes, and empty physical body.

For a truncated current message, the RTL may have already emitted an incomplete payload prefix without `out_last`; Python's `MoldResult.messages` includes only complete messages. The cross-check compares complete prefixes and verifies that the incomplete suffix has no completion marker. This is consistent with WIRE-D016's no-rollback model.

Raw: `results/raw/rtl/mold_message_framer/cocotb_standalone.log`.

## G. Seven-stage composition

Wrapper: `rtl/arch_a/wire_buffer_gearbox_eth_ipv4_udp_mold_framer_top.sv`.

Composition tests: **2/2 PASS**. The valid frame contains two messages with opaque payloads of 2 and 3 bytes. Metadata sequence values are `FFFFFFFFFFFFFFFE` and `FFFFFFFFFFFFFFFF`; five body bytes are output with the two exact message-final markers. Structural success handshakes into WIRE-019, which advances expected sequence by two and wraps to zero.

The late-suffix frame contains three blocks: complete `A`, complete `BC`, then declared length five with only `xy` physically present. The two complete prefix messages receive boundaries; the third message metadata is visible but its two emitted prefix bytes have no final marker. Framer reports fatal `MESSAGE_TRUNCATED`, packet result is failure, WIRE-019 expected sequence remains `FFFFFFFFFFFFFFFE`, and WIRE-019 enters recovery. No rollback of the completed prefix is claimed.

Raw: `results/raw/rtl/mold_message_framer/cocotb_seven_stage.log`.

## H. Formal evidence

SBY 0.69, `smtbmc yices`, Yices 2.7.0. **No DUT-private state is used.** Formal checks are decomposed; there is no monolithic unrestricted parser proof.

- Fixed normal sequence/length/payload/final-boundary and structural-success vector: BMC depth 24, PASS.
- First-byte-only length field, positive payload truncation, full-count trailing, count-short, and body-empty cases: each fixed-vector BMC depth 24, PASS.
- Zero-length structural message and three-message sequence annotation wrap (`FFFFFFFFFFFFFFFE`, `FFFFFFFFFFFFFFFF`, `0`): fixed-vector BMC depth 24, PASS.
- Late malformed suffix after two complete prefix messages: fixed-vector BMC depth 32, PASS. It asserts the complete prefix boundaries, lack of final marker on the incomplete current message, and fatal result.
- Metadata, payload, packet-result, and rejection stability: public-port safety BMC depth 20, PASS. Upstream input and packet metadata are assumed stable while valid/not-ready; all downstream ready inputs remain unconstrained. Stability assertions are masked across reset/rearm, which are allowed to cancel pending transactions.
- Partial length followed by rearm: fixed-vector BMC depth 12, PASS.
- Valid-success/final-boundary, zero-length metadata, and late-suffix rejection-after-prefix covers: cover depths 24/24/32, PASS. Covers are reachability only.

All claims are bounded/fixed-vector checks, not inductive or unbounded proofs. They do not exhaust the full 16-bit count/length space.

An initial safety harness run failed because its stall-stability assertion incorrectly spanned a legal `rearm`. The failed raw log is retained. The harness was corrected to mask reset/rearm, then rerun to depth 20 PASS; no RTL counterexample was involved.

Raw formal logs and inventory: `results/raw/rtl/mold_message_framer/`.

## I. Regression preservation

- WIRE-019/019A standalone: **14/14 PASS**.
- WIRE-019 six-stage composition: **2/2 PASS**.
- WIRE-019 existing SBY jobs: **12/12 PASS**.
- WIRE-014 gearbox: **6/6 PASS**.
- WIRE-015 ingress buffer: **5/5 standalone**, **1/1 composition PASS**.
- WIRE-016 Ethernet: **4/4 standalone**, **1/1 composition PASS**.
- WIRE-017 IPv4: **5/5 standalone**, **3/3 composition PASS**.
- WIRE-018 UDP: **5/5 standalone**, **3/3 composition PASS**.
- Python suite: **71/71 PASS**.

## J. Lint and synthesis sanity

Verilator standalone framer and seven-stage composition lint/build: PASS, no meaningful warnings. Yosys standalone framer and seven-stage composition `synth`/`check`: PASS; both final checks report zero problems. Seven-stage ABC mapping emitted combinational-network notices, not structural-check errors. This is component synthesis sanity only; no nextpnr/P&R or PPA claim.

## K. Requirement traceability and classification

Supports structural Mold message framing and exact message count/body consumption (REQ-MOLD-003/008), Mold error handling prerequisite (REQ-ERR-004), WIRE-D015 deferred sequence commit, and WIRE-D016 complete-message boundaries. Evidence classification:

- Mold message-block framer: **RTL-SIMULATED**.
- Named local framing/stability properties: **FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS**, with bounded/fixed-vector scopes above.
- Buffer→gearbox→Ethernet→IPv4→UDP→Mold header/sequence→framer: **RTL-SIMULATED**.
- Yosys: **SYNTHESISED COMPONENT SANITY**.

No ITCH semantic, mutation/decision, rollback, or global recovery arbitration behavior is established here.

## L. Problems, limitations, and conclusion

No unresolved functional counterexample remains. The standalone test found and corrected the incomplete-message rejection-code defect described above. Formal scope is bounded and fixed-vector. ITCH decoder, order state, decisions, and end-to-end semantic commit gating remain unimplemented. No P&R or application performance evidence was generated.

WIRE-020 meets its scoped acceptance criteria after the final 10/10 standalone, 2/2 composition, formal, regression, lint, and Yosys reruns. Do not start WIRE-021 within this task.
