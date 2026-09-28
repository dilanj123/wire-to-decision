# WIRE-017 — Architecture A IPv4 Byte Parser RTL and Verification

## Phase

Phase 2 — Parser primitives and complete Architecture A parser.

## Starting state

- Starting HEAD: `1acca7d0493dcdd1e4a75b6645f6190406bf14c9`.
- Branch: `main`; initial working tree clean; local `main == origin/main`.
- Gate-0 peeled commit: `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## Objective and authority

Implement the fixed Version-4/IHL-5, UDP-only IPv4 byte stage after WIRE-016. Authority: `docs/REQUIREMENTS.md`, `docs/MICROARCHITECTURE.md`, `docs/VERIFICATION_PLAN.md`, `docs/FORMAL.md`, `docs/DECISIONS.md`, WIRE-002 and WIRE-016 evidence, and the existing Python framing/checksum implementation.

## Scope

Allowed: fixed 20-byte header capture/validation, Internet checksum, fragmentation/destination/protocol filtering, Total-Length payload/padding handling, ready/valid output and local rejection status, composition with the existing ingress/gearbox/Ethernet stages, cocotb, Verilator, Yosys and local formal harnesses, evidence and state documentation.

Prohibited: IPv4 options, IPv6, reassembly, UDP/Mold/ITCH parsing, normalized events, order/decision RTL, Architecture B, CDC, P&R, and performance claims.

## Frozen behavior

- WIRE-D011 synchronous active-high `rst`.
- Validation priority: version, IHL, Total Length, checksum, fragmentation, destination, protocol.
- `Total Length` is big-endian and bounds forwarded payload; later physical bytes are padding.
- Fatal local conditions are held on `reject_valid` until `reject_ready`.
- WIRE-D013: a profile-valid `Total Length == 20` packet is fatal `IPV4_EMPTY_PROJECT_PAYLOAD` because the downstream byte stream cannot represent a zero-byte packet; the Python model remains unchanged and may fail later at UDP-header validation.
- A late physical truncation can follow already forwarded payload prefix bytes; end-to-end mutation suppression remains unproven until later parser/control integration.

## Verification plan

Standalone cocotb uses independent packet/checksum construction and tests valid, padding, filters, priority, truncation, checksum, fragmentation, stalls, reset and deterministic random seeds 1/7/19. Composition cocotb exercises buffer→gearbox→Ethernet→IPv4. Formal uses public ports only, explicit upstream stability and fixed stable configuration assumptions, a depth-20 local safety job, a depth-32 correspondence job, and a depth-32 cover job.

## Acceptance/evidence status

RTL simulation, Verilator and Yosys sanity pass. The local safety and cover jobs pass. The full unconstrained public-interface correspondence job is solver-bound after step 22 on the qualified local toolchain; it is not represented as passed evidence. WIRE-017 is therefore functionally implemented but formal correspondence closure remains open.

## GitHub push

Push is required only after the evidence state is accurately recorded and the formal closure status is resolved. No WIRE-018 work is included.
