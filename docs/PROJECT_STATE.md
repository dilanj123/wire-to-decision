# Project State

## Phase

Phase 1 — Python reference model

## Gate

Gate 0 — CLOSED; WIRE-000 through WIRE-007 complete

## Known-good commit

9fbd24ec0b9fe6cd32f09312c1ee6905070755aa (WIRE-000 known-good baseline)

## Architecture

Specified only. No RTL implementation exists.

Baseline candidate:

64-bit framed packet stream
→ Architecture A byte-serial parser
→ normalized event
→ bounded order state
→ deterministic decision

Architecture B is not authorized.

## Application status

Application RTL: not started

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

Order-store mutation model: not started

Decision model: not started

Functional evidence: none

Formal application evidence: none

Application synthesis/P&R evidence: none

## Regression status

Not run.

## Formal status

Not run.

## Synthesis / P&R status

Not run.

## Latest evidence

WIRE-004 native Apple Silicon open-source toolchain qualification completed in commit `89e2841` for the trivial smoke design. Canonical suite: OSS CAD Suite `2026-09-27`; details are in `results/processed/toolchain_smoke.md`. This is toolchain-smoke evidence only.

WIRE-005 froze LFE5U-85F-8BG381C / `--85k --package CABGA381 --speed 8` with a 156.25 MHz / 6.4 ns timing objective. Exact-target synthesis, placement, routing, and ecppack were validated using the trivial smoke design only in commit `c4ba1964049b6c104fbc80a1c8991a7476c51b16`. WIRE-006 created the authoritative specification package and consistency review in commit `a6ddb1f36ec945b8506e95a5c4935d1776806bbd`; WIRE-007 demonstrated clean-clone repository/toolchain reproducibility at candidate `e9123ea24a6a3314441bec3617cdb5da559cb775`. These are specification/environment evidence only. No reference-model, application RTL, simulation, formal, application synthesis, timing, latency, throughput, CDC, or integration evidence exists.

## Open bugs

None recorded.

## Open decisions

- Architecture B remains intentionally undefined pending Architecture A measurement.
- WIRE-001 process adoption details are recorded in `docs/DECISIONS.md`.
- WIRE-002 external source authority and MVP protocol restrictions are recorded in `docs/DECISIONS.md`.
- WIRE-003 originality and third-party provenance policy are recorded in `docs/DECISIONS.md`.
- WIRE-004 canonical toolchain decision is recorded in `docs/DECISIONS.md`.
- WIRE-005 canonical implementation target and experiment invariants are recorded in `docs/DECISIONS.md` and `docs/IMPLEMENTATION_TARGET.md`.
- WIRE-006 authoritative requirements, microarchitecture, verification, and formal package is recorded in the master/specification documents.

## Current bottleneck

Decision-model behavior has not started.

## Next task

WIRE-012 — Python deterministic decision model.
