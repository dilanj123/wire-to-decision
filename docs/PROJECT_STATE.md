# Project State

## Phase

Phase 0 — Bootstrap

## Gate

Gate 0 — not passed; WIRE-001 workflow audit, WIRE-002 source lock, WIRE-003 provenance audit, and WIRE-004 toolchain qualification complete

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

## Regression status

Not run.

## Formal status

Not run.

## Synthesis / P&R status

Not run.

## Latest evidence

WIRE-004 native Apple Silicon open-source toolchain qualification completed in commit `89e2841` for the trivial smoke design. Canonical suite: OSS CAD Suite `2026-09-27`; details are in `results/processed/toolchain_smoke.md`. This is toolchain-smoke evidence only.

No reference-model, RTL, simulation, formal, synthesis, timing, latency, throughput, CDC, or integration evidence exists.

## Open bugs

None recorded.

## Open decisions

- Exact Apple-Silicon tool versions.
- Exact primary formal solver.
- Exact ECP5 target device/package.
- Architecture B remains intentionally undefined pending Architecture A measurement.
- WIRE-001 process adoption details are recorded in `docs/DECISIONS.md`.
- WIRE-002 external source authority and MVP protocol restrictions are recorded in `docs/DECISIONS.md`.
- WIRE-003 originality and third-party provenance policy are recorded in `docs/DECISIONS.md`.
- WIRE-004 canonical toolchain decision is recorded in `docs/DECISIONS.md`.

## Current bottleneck

Implementation-independent requirements and production ECP5 target selection remain open.

## Next task

WIRE-005 — Implementation target freeze.
