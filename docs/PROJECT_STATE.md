# Project State

## Phase

Phase 0 — Bootstrap

## Gate

Gate 0 — not passed; WIRE-001 workflow audit complete

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

WIRE-001 workflow/reference audit completed in `8d2a5cc41abb0913c6069d7333989a70a0133d87`. This is process evidence only.

No functional, protocol, formal, synthesis, timing, latency, throughput, CDC, or integration evidence exists.

## Open bugs

None recorded.

## Open decisions

- Exact Apple-Silicon tool versions.
- Exact primary formal solver.
- Exact ECP5 target device/package.
- RTL-to-Pixels workflow audit.
- Architecture B remains intentionally undefined pending Architecture A measurement.
- WIRE-001 process adoption details are recorded in `docs/DECISIONS.md`.

## Current bottleneck

Phase-0 environment/toolchain qualification and external protocol specification remain open.

## Next task

WIRE-002 — External protocol specification lock.
