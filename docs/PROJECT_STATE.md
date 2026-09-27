# Project State

## Phase

Phase 0 — Bootstrap

## Gate

Gate 0 — not passed; WIRE-001 workflow audit and WIRE-002 source lock complete

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

WIRE-002 external protocol specification lock completed in source-lock commit `8af65aa`. This is specification/source evidence only.

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

## Current bottleneck

Phase-0 environment/toolchain qualification and implementation-independent requirements remain open.

## Next task

WIRE-003 — Third-party reference/reuse audit and pinning.
