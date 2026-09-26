# Project State

## Phase

Phase 0 — Bootstrap

## Gate

Gate 0 — not passed

## Known-good commit

999e04fbbd36db9c7556187876551f4b40833dd3 (WIRE-000 scaffold commit)

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

WIRE-000 repository scaffold only.

No functional, formal, synthesis, timing or performance evidence exists.

## Open bugs

None recorded.

## Open decisions

- Exact Apple-Silicon tool versions.
- Exact primary formal solver.
- Exact ECP5 target device/package.
- RTL-to-Pixels workflow audit.
- Architecture B remains intentionally undefined pending Architecture A measurement.

## Current bottleneck

Phase-0 environment and project process have not yet been validated.

## Next task

WIRE-001 — RTL-to-Pixels reference workflow audit.
