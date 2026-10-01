# Project State

## Phase

Phase 3 — ACTIVE: bounded order state and deterministic decision

Phase 1: COMPLETE — 71-test Python end-to-end oracle baseline

Phase 2: COMPLETE — Architecture-A parser boundary through normalized events


## Gate

Gate 0 — CLOSED; WIRE-000 through WIRE-007 complete

## Known-good commit

9fbd24ec0b9fe6cd32f09312c1ee6905070755aa (WIRE-000 known-good baseline)

## Architecture

Architecture-A parser boundary is implemented and RTL-simulated from the common two-beat ingress buffer through Ethernet II, IPv4, UDP, MoldUDP64 header/sequence control, message-block framing, and ITCH normalized events. WIRE-022 composes these stages in a production-style top and adds parser-wide fatal recovery/rearm and external-frame drain gating. WIRE-023 adds the bounded order store, checked aggregates, successful-mutation commit boundary, and parser-fatal integration. Deterministic decision logic remains unimplemented.

Baseline candidate:

64-bit framed packet stream
→ Architecture A byte-serial parser
→ normalized event
→ bounded order state
→ deterministic decision

Architecture B is not authorized.

## Application status

Application RTL: Architecture-A parser boundary and WIRE-023 bounded order-state/aggregate block implemented and RTL-simulated. This excludes deterministic decisions, application P&R, and application timing evidence.

Bounded order-state / aggregate RTL: WIRE-023 implemented and RTL-simulated; local fixed-vector and reduced-store formal checks are bounded under documented assumptions. The production default is 512 sets × 2 ways; the 1,024-entry capacity test is RTL-simulated.

Parser→book integration: RTL-simulated for successful mutation sequences, complete-prefix retention after late Mold structural failure, ITCH semantic failure with independent Mold structural success, outer fatal before mutation, and explicit rearm.

Deterministic decision RTL: not started (WIRE-024).

MoldUDP64 header/sequence controller: RTL-simulated; fatal session/sequence and heartbeat/EOS trailing-byte conditions immediately clear stage validity and assert recovery while the current malformed packet drains; named header/control, deferred-commit, recovery, stall, and wrap properties checked under documented bounded/fixed-vector assumptions

MoldUDP64 message-block framer: RTL-simulated; preserves per-message boundaries and opaque payloads, supports zero-length structural messages, and reports exact-count/truncation/trailing errors. Named fixed-vector public-interface checks and bounded ready/valid safety checks pass; structural result drives WIRE-019 deferred sequence commit/recovery in seven-stage simulation.

ITCH decoder / normalized-event boundary: RTL-simulated; A/F/E/C/X/D/U mappings, P handling, tracked-locate filtering, exact symbol policy, and stage-local fail-closed drain are exercised. Events are gated on WIRE-D016 complete-message boundaries. Named fixed-vector/safety public-interface formal checks pass; Mold header→framer→ITCH composition confirms semantic ITCH failure does not alter Mold structural success.

ITCH decoder RTL: implemented for the frozen A/F/E/C/X/D/U/P subset; broader ITCH remains unsupported by design

Reference-model package: created

WIRE-008: complete. The initial task/specification conflict was resolved by
retaining higher-authority WIRE-D008 and correcting the Python implementation
and task interpretation.

Python canonical data model: implemented and unit-tested

WIRE-D006 hash: implemented and unit-tested in Python

WIRE-009: complete

Ethernet/IPv4/UDP/Mold framing model: unit-tested

Mold session/sequence handling: unit-tested

ITCH decoding beyond the supported subset: not started

WIRE-010: complete

ITCH A/F/E/C/X/D/U decoder: unit-tested

Normalized events from ITCH bytes: unit-tested

P known non-mutating handling: unit-tested

WIRE-011: complete functionally

Bounded order-state model: unit-tested

Bid/ask aggregates: unit-tested

Canonical GitHub repository: https://github.com/dilanj123/wire-to-decision

GitHub publication: complete; public repository, `main` and `kg-g0-env` pushed

Order-store mutation model: Python-unit-tested

WIRE-012: complete

Deterministic decision model: unit-tested

Risk-budget model: unit-tested

Full end-to-end Python oracle: unit-tested

WIRE-013: complete

End-to-end Python oracle: unit-tested

Packet-level fail-closed/recovery integration: unit-tested

Python component regression: 71 tests passing

64-to-8 gearbox: RTL-simulated

Common ingress buffer: RTL-simulated; two-beat registered FIFO frozen by WIRE-D012

Buffer→gearbox integration: RTL-simulated

Ethernet II parser: RTL-simulated

Buffer→gearbox→Ethernet integration: RTL-simulated

IPv4 parser: RTL-simulated; named public-interface formal correspondence closed with decomposed bounded checks under documented assumptions

Buffer→gearbox→Ethernet→IPv4 integration: RTL-simulated

UDP parser: RTL-simulated; named local properties checked with documented bounded/fixed-vector formal jobs

Buffer→gearbox→Ethernet→IPv4→UDP integration: RTL-simulated

Ingress-buffer local formal: reset-empty safety inductively checked; public-interface correspondence bounded-checked through depth 10

Gearbox local formal: closed under documented assumptions for ordering, accepted valid-byte conservation, exact last-marker behavior, stall stability, and refill safety; reference correspondence bounded-checked through depth 20

Application RTL functional evidence: WIRE-014..022 parser stages/composition plus WIRE-023 order-book/aggregate and parser→book boundary simulation; named local formal checks are bounded or fixed-vector as individually recorded. No complete parser/book/decision formal proof is claimed.

Formal parser evidence: named stage-local and top-level safety properties checked with documented bounded/fixed-vector scopes; no complete parser proof or application-level formal proof is claimed.

Application synthesis/P&R evidence: none

## Regression status

Python component regression: 71 tests passing

## Formal status

WIRE-014 gearbox local properties checked with SBY/Yices under documented legal-input assumptions. WIRE-015 ingress-buffer reset-empty safety is inductively checked and its independent public-interface queue correspondence is bounded-checked through depth 10. WIRE-016 Ethernet parser local safety is bounded-checked through depth 20 and public-interface correspondence through depth 40 under documented assumptions. WIRE-017 local safety is bounded-checked through depth 20; WIRE-017A decomposed public-interface checks cover classification, checksum, payload, Total-Length boundary, padding, truncation and restart at recorded depths. The original monolithic correspondence job remains solver-bound after step 22. WIRE-018 uses decomposed fixed-vector and bounded checks. WIRE-019/019A and WIRE-020/021 retain their named bounded/fixed-vector public-interface suites. WIRE-022 parser safety is BMC depth 20; its full-top late-suffix BMC remains solver-bound after step 69. WIRE-023 adds reduced two-set public-port BMCs (depths 12, 20 and 28) for commit/error/recovery/reset safety, hash vectors, duplicate/full-set behavior, successful mutation accounting, atomic full-destination replacement failure, unknown-reference failure, and upstream-fatal ordering. WIRE-023 formal results are bounded/fixed-vector checks, not proofs of all 512 sets or all event sequences.

## Synthesis / P&R status

Not run.

## Latest evidence

WIRE-004 native Apple Silicon open-source toolchain qualification completed in commit `89e2841` for the trivial smoke design. Canonical suite: OSS CAD Suite `2026-09-27`; details are in `results/processed/toolchain_smoke.md`. This is toolchain-smoke evidence only.

WIRE-005 froze LFE5U-85F-8BG381C / `--85k --package CABGA381 --speed 8` with a 156.25 MHz / 6.4 ns timing objective. Exact-target synthesis, placement, routing, and ecppack were validated using the trivial smoke design only in commit `c4ba1964049b6c104fbc80a1c8991a7476c51b16`. WIRE-006 created the authoritative specification package and consistency review in commit `a6ddb1f36ec945b8506e95a5c4935d1776806bbd`; WIRE-007 demonstrated clean-clone repository/toolchain reproducibility at candidate `e9123ea24a6a3314441bec3617cdb5da559cb775`. WIRE-008 through WIRE-013 provide Python-unit-tested component and end-to-end evidence. WIRE-014 through WIRE-021 provide limited primitive/stage RTL simulation and local formal evidence. WIRE-017A closed the named IPv4 correspondence set with decomposed bounded/fixed-vector checks; its original monolithic BMC remains solver-bound historical evidence. WIRE-022 composes the current Architecture-A parser through the normalized-event boundary and records parser-wide fatal recovery. Its full-top fixed-vector late-suffix BMC was solver-bound after step 69 (no counterexample); that end-to-end case passes cocotb and relevant lower-stage properties pass the established decomposed jobs. Application P&R/timing, latency, throughput, CDC, C++ integration, order state and decisions remain unimplemented/unproven.

## Open bugs

None recorded.

## Open decisions

- Architecture B remains unauthorized and undefined.
- WIRE-001 process adoption details are recorded in `docs/DECISIONS.md`.
- WIRE-002 external source authority and MVP protocol restrictions are recorded in `docs/DECISIONS.md`.
- WIRE-003 originality and third-party provenance policy are recorded in `docs/DECISIONS.md`.
- WIRE-004 canonical toolchain decision is recorded in `docs/DECISIONS.md`.
- WIRE-005 canonical implementation target and experiment invariants are recorded in `docs/DECISIONS.md` and `docs/IMPLEMENTATION_TARGET.md`.
- WIRE-006 authoritative requirements, microarchitecture, verification, and formal package is recorded in the master/specification documents. WIRE-014 added the single-clock reset convention and gearbox evidence.
- WIRE-D012 common ingress buffer depth decision is recorded in `docs/DECISIONS.md` and WIRE-015 evidence.
- WIRE-D015 deferred Mold normal-packet sequence commit is recorded in `docs/DECISIONS.md` and WIRE-019 evidence.
- WIRE-D016 Mold complete-message boundaries and structural packet-result semantics are recorded in `docs/DECISIONS.md` and WIRE-020 evidence.
- WIRE-D017 ITCH normalized-event RTL encoding and complete-message commit boundary are recorded in `docs/DECISIONS.md` and WIRE-021 evidence.
- WIRE-D018 parser-wide fatal recovery, current-frame drain, event-boundary no-rollback, and explicit rearm are recorded in `docs/DECISIONS.md` and WIRE-022 evidence.
- WIRE-D019 bounded-book atomic mutation commit and parser-fatal ordering are recorded in `docs/DECISIONS.md` and WIRE-023 evidence.

## Current bottleneck

Deterministic decision/risk-budget RTL and parser→book→decision integration remain; application-level timing/P&R and later verification gates are also open.

## Next task

WIRE-024 — deterministic decision/risk-budget RTL and complete single-clock functional MVP integration.
