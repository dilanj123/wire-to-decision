# WIRE-019 — MoldUDP64 header and sequence controller

## Phase and starting state

Phase 2 — Parser primitives and complete Architecture A parser.
Starting HEAD: `0e85377352d4fd500f911c64c678a84b6bb512b9`; `main` initially matched `origin/main`; Gate-0 peeled commit remained `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## Objective and authority

Implement the project-owned 20-byte MoldUDP64 header/session/sequence controller after WIRE-018. Authority: `docs/REQUIREMENTS.md`, `docs/MICROARCHITECTURE.md`, `docs/VERIFICATION_PLAN.md`, `docs/FORMAL.md`, `docs/DECISIONS.md`, WIRE-002 protocol lock, WIRE-018 evidence, and `model/python/wire_to_decision/mold.py`.

WIRE-D015 freezes deferred normal-packet sequence commit: the controller captures configured session/expected sequence on synchronous reset or explicit `rearm`, exposes normal metadata before opaque body bytes, and advances expected sequence only after successful downstream packet-result handshake. Heartbeat does not advance; EOS and failed result enter recovery without advancing.

## Contract and exclusions

The 20-byte header is Session[10], Sequence[63:0] big-endian, and Message Count[15:0] big-endian. Count zero is an exact heartbeat; `FFFF` is exact EOS; `1..FFFE` is a normal packet. Normal body bytes are opaque and begin with the future message-block stream. The implementation does not parse message lengths, ITCH, normalized events, order state, decisions, Architecture B, CDC, or global error arbitration.

## Verification plan

Standalone cocotb uses an independent header/body scoreboard and deterministic seeds 1, 7, and 19. It covers normal metadata/body, body-empty failed result, heartbeat, EOS/trailing precedence, session/sequence priority, header truncation, metadata stall, body stall, reject stall, wrap, reset, and explicit re-arm. The six-stage wrapper connects ingress buffer, gearbox, Ethernet, IPv4, UDP, and this controller.

Formal uses only public DUT ports. SBY/Yices jobs cover output/rejection/metadata stall stability, recovery blocking, deferred commit, fixed-vector header classification, heartbeat, EOS, session/sequence mismatch, body correspondence, and modulo-2^64 wrap. The scope is bounded/fixed-vector; covers are reported separately. Upstream ready/valid stability and reset/configuration epoch assumptions are documented in the harness.

## Acceptance/evidence

Verilator and Yosys qualify the standalone and six-stage composition. The Python suite remains 71/71. Raw evidence is under `results/raw/rtl/mold_header_seq/`; processed evidence is `results/processed/WIRE-019-mold-header-sequence-rtl.md`. EVID-019 is narrow and does not claim Mold message-block completion or downstream mutation gating.

## GitHub

Push only after all required checks pass. Do not start WIRE-020 in this task.
