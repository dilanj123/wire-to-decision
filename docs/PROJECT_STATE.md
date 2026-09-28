# Project State

## Phase

Phase 2 — Parser primitives and complete Architecture A parser

Phase 1: COMPLETE — 71-test Python end-to-end oracle baseline

## Gate

Gate 0 — CLOSED; WIRE-000 through WIRE-007 complete

## Known-good commit

9fbd24ec0b9fe6cd32f09312c1ee6905070755aa (WIRE-000 known-good baseline)

## Architecture

Architecture A implementation has started with the common two-beat ingress buffer, 64-to-8 gearbox, and Ethernet II/IPv4 byte-parser stages. UDP and later protocol parser stages remain unimplemented.

Baseline candidate:

64-bit framed packet stream
→ Architecture A byte-serial parser
→ normalized event
→ bounded order state
→ deterministic decision

Architecture B is not authorized.

## Application status

Application RTL: started; Architecture-A ingress, gearbox, Ethernet II and IPv4 stages implemented with stage-level simulation evidence

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

Ingress-buffer local formal: reset-empty safety inductively checked; public-interface correspondence bounded-checked through depth 10

Gearbox local formal: closed under documented assumptions for ordering, accepted valid-byte conservation, exact last-marker behavior, stall stability, and refill safety; reference correspondence bounded-checked through depth 20

Application RTL functional evidence: gearbox + common ingress buffer + Ethernet II + IPv4 stage/composition simulation; IPv4 local formal property set closed with decomposed bounded checks

Formal application evidence: none

Application synthesis/P&R evidence: none

## Regression status

Python component regression: 71 tests passing

## Formal status

WIRE-014 gearbox local properties checked with SBY/Yices under documented legal-input assumptions. WIRE-015 ingress-buffer reset-empty safety is inductively checked and its independent public-interface queue correspondence is bounded-checked through depth 10. WIRE-016 Ethernet parser local safety is bounded-checked through depth 20 and public-interface correspondence through depth 40 under documented assumptions. WIRE-017 IPv4 local safety is bounded-checked through depth 20; WIRE-017A decomposed public-interface checks cover classification, checksum, payload, Total-Length boundary, padding, truncation and restart at recorded depths. The original monolithic correspondence job remains recorded as solver-bound after step 22.

## Synthesis / P&R status

Not run.

## Latest evidence

WIRE-004 native Apple Silicon open-source toolchain qualification completed in commit `89e2841` for the trivial smoke design. Canonical suite: OSS CAD Suite `2026-09-27`; details are in `results/processed/toolchain_smoke.md`. This is toolchain-smoke evidence only.

WIRE-005 froze LFE5U-85F-8BG381C / `--85k --package CABGA381 --speed 8` with a 156.25 MHz / 6.4 ns timing objective. Exact-target synthesis, placement, routing, and ecppack were validated using the trivial smoke design only in commit `c4ba1964049b6c104fbc80a1c8991a7476c51b16`. WIRE-006 created the authoritative specification package and consistency review in commit `a6ddb1f36ec945b8506e95a5c4935d1776806bbd`; WIRE-007 demonstrated clean-clone repository/toolchain reproducibility at candidate `e9123ea24a6a3314441bec3617cdb5da559cb775`. WIRE-008 through WIRE-013 provide Python-unit-tested component and end-to-end evidence. WIRE-014 through WIRE-017 provide limited primitive/stage RTL simulation and local formal evidence; WIRE-017 correspondence remains open. No UDP/Mold/ITCH parser RTL, application synthesis, timing, latency, throughput, CDC, or C++ integration evidence exists.

## Open bugs

None recorded.

## Open decisions

- Architecture B remains intentionally undefined pending Architecture A measurement.
- WIRE-001 process adoption details are recorded in `docs/DECISIONS.md`.
- WIRE-002 external source authority and MVP protocol restrictions are recorded in `docs/DECISIONS.md`.
- WIRE-003 originality and third-party provenance policy are recorded in `docs/DECISIONS.md`.
- WIRE-004 canonical toolchain decision is recorded in `docs/DECISIONS.md`.
- WIRE-005 canonical implementation target and experiment invariants are recorded in `docs/DECISIONS.md` and `docs/IMPLEMENTATION_TARGET.md`.
- WIRE-006 authoritative requirements, microarchitecture, verification, and formal package is recorded in the master/specification documents. WIRE-014 added the single-clock reset convention and gearbox evidence.
- WIRE-D012 common ingress buffer depth decision is recorded in `docs/DECISIONS.md` and WIRE-015 evidence.

## Current bottleneck

SystemVerilog implementation and cross-layer hardware verification remain.

## Next task

WIRE-018 — Architecture A UDP byte parser RTL and verification.
