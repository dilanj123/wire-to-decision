# WIRE-014 — Architecture A 64-to-8 gearbox RTL and verification

## Phase

Phase 2 — Parser primitives and complete Architecture A parser.

## Starting state

- Starting HEAD: `7268fe898f27950aec2470523c698c8f464fd845`
- Gate-0 tag: `kg-g0-env`, peeled commit `06f5643a940ac2c6fcfab0e377169b48ce700107`

## Objective and authority

Implement and verify only the project-owned 64-bit legal framed beat to ordered 8-bit byte gearbox. Authority is `docs/REQUIREMENTS.md`, `docs/MICROARCHITECTURE.md`, `docs/VERIFICATION_PLAN.md`, `docs/FORMAL.md`, and WIRE-D011.

## Reset convention

Synchronous active-high `rst`, frozen by WIRE-D011 for Phase-2 single-clock primitives. This does not define later CDC reset behavior.

## Scope

Included: one-beat local storage, lane ordering, legal contiguous keep handling, frame-final `out_last`, ready/valid stability, same-cycle beat retire/refill, cocotb/Verilator verification, local SBY/Yices checks, and Yosys elaboration sanity.

Excluded: common ingress buffering, Ethernet/IP/UDP/Mold/ITCH parsing, order state, decision logic, CDC, Architecture B, P&R, timing, and throughput claims.

## Acceptance and evidence

All six cocotb tests pass with deterministic random seeds 1, 7, and 19. SBY prove and cover use Yices with depth 20; the safety harness assumes legal input keeps and upstream stability. The independent cocotb scoreboard establishes byte order/count/last behavior; formal checks cover stalled payload stability, legal `out_last`, first-byte loading, refill safety, and refill reachability.

## Allowed modifications

`rtl/arch_a/`, `tb/gearbox/`, `formal/gearbox/`, WIRE-014 raw/processed evidence, `docs/PROJECT_STATE.md`, `docs/DECISIONS.md`, `docs/EVIDENCE_INDEX.md`, `04_MASTER_CHECKLIST.md`, and this task record.

## Completion boundary

WIRE-014 does not establish complete Architecture-A parser correctness or application timing. Next task: WIRE-015 — Architecture A common ingress beat buffer RTL and verification.
