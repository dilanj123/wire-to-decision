# WIRE-020 — Architecture A MoldUDP64 message-block framing RTL

## Scope

Phase 2. Starting HEAD: `c75abb81bd67e7d28ecefaad8e390a70ba53fbce` on clean `main`, initially equal to `origin/main`. Gate-0 `kg-g0-env^{}`: `06f5643a940ac2c6fcfab0e377169b48ce700107`.

Implement the stage after WIRE-019 that consumes normal Mold packet metadata and the raw Mold body, emits per-message metadata and opaque message payload bytes, and returns structural packet success/failure to WIRE-019. No ITCH decoding is in scope.

## Authority and decision

Authority: `docs/REQUIREMENTS.md`, `docs/MICROARCHITECTURE.md`, `docs/VERIFICATION_PLAN.md`, `docs/FORMAL.md`, `docs/DECISIONS.md`, WIRE-019/WIRE-019A task and evidence, `model/python/wire_to_decision/mold.py`, `model/python/wire_to_decision/oracle.py`, and `rtl/arch_a/wire_mold_header_seq.sv`.

WIRE-D016 freezes the complete-message and structural-result boundary. Mold body blocks are a two-byte big-endian length followed by exactly that many opaque bytes. Message `i` receives sequence `(packet_sequence+i) mod 2^64`. Zero-length messages are legal structurally and complete on their metadata handshake. A nonempty message completes only when the final declared payload byte handshakes with `out_last=1`. Structural success requires exactly the declared message count and exact physical-body consumption, independent of future ITCH semantics.

Completed messages before a malformed suffix remain visible; there is no rollback transaction. An incomplete current message never gets an `out_last` boundary. Errors are fatal: missing/partial next length is `MESSAGE_LENGTH_TRUNCATED`, incomplete positive-length payload is `MESSAGE_TRUNCATED`, and bytes after the exact declared count are `TRAILING_BYTES`.

## Interfaces and reset

Production module: `rtl/arch_a/wire_mold_message_framer.sv`.

Inputs: WIRE-019 packet metadata (`packet_valid/ready`, sequence, count, body-empty), raw body byte ready/valid/data/last, synchronous active-high `rst`, and explicit `rearm`.

Outputs: ready/valid per-message sequence/length/empty metadata, raw message payload ready/valid/data/last, structural packet result ready/valid/success, and a stable local fatal rejection ready/valid/code interface. Reset/rearm discards partial lengths, messages, held payload, drops, results and rejections and returns to packet-metadata idle.

## Integration

Seven-stage test composition: ingress buffer → gearbox → Ethernet II → IPv4 → UDP → Mold header/sequence → Mold message framer. The framer result is connected directly to WIRE-019's deferred packet-result input. WIRE-019 advances expected sequence only after structural success; structural failure holds sequence and enters recovery. No global error arbiter or ITCH semantics are added.

## Verification plan

- Independent standalone cocotb scoreboard for lengths, payload bytes, message boundaries/sequences, results, rejection codes, stalls, deterministic seeds 1/7/19, reset/rearm, and Python `mold.py` comparisons.
- Seven-stage cocotb composition tests for successful structural commit and a late malformed suffix after two complete messages.
- Decomposed public-port-only SBY/Yices jobs: fixed vectors for valid, length-field truncation, payload truncation, trailing bytes, count-short, empty body, zero-length message, sequence wrap and two-message prefix before late truncation; bounded safety for metadata/payload/result/reject stalls; rearm-after-partial-state check; separate reachability covers.
- Verilator lint and cocotb builds; Yosys standalone and composition synthesis/elaboration sanity only.
- Preserve WIRE-019/019A 14-test standalone and composition baseline, applicable prior parser regressions, and Python 71-test regression.

## Exclusions

No 2-byte Mold message contents parsing, ITCH decoding, order state, decisions, Architecture B, CDC, P&R, or performance claims.

## Evidence and publication

Raw logs: `results/raw/rtl/mold_message_framer/`.
Processed report: `results/processed/WIRE-020-mold-message-framing-rtl.md`.
Evidence index: EVID-020.

Push `main` only if all required simulation, formal, composition, regression, Verilator and Yosys results pass; verify local/remote equality and Gate-0 tag afterward. Do not start WIRE-021 in this task.
