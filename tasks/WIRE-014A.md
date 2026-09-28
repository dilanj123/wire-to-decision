# WIRE-014A — Gearbox formal closure

## Objective

Close the WIRE-014 formal-evidence gap without changing application scope or starting WIRE-015. The original WIRE-014 harness proved stall stability, first-byte loading, refill safety, and reachability, but did not independently check full lane ordering, valid-byte conservation, or exact frame-last correspondence.

## Starting state

- Starting HEAD: `66217013f37260db1b52b4203bea30549d1eaa83`
- `main` matched `origin/main`.
- `kg-g0-env` remained peeled at `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## Scope and method

The production RTL was preserved. `formal/gearbox/wire_gearbox_reference.sv` adds an independent public-interface serializer model tracking beat data, valid-lane count, byte index, and frame-final state. The existing inductive safety proof remains in `wire_gearbox_safety.sv`; the full reference correspondence is checked with SBY/Yices bounded model checking to depth 20, and reference covers exercise non-final and final refill.

The reference model does not inspect DUT-private state. Legal contiguous keep masks and upstream ready/valid stability are explicit assumptions.

## Acceptance evidence

- Existing safety prove: PASS by k-induction.
- Reference-contract BMC: PASS through depth 20.
- Reference covers: PASS.
- Cocotb: 6/6 PASS, seeds 1, 7, and 19.
- Verilator lint: PASS.
- Python regression: 71/71 PASS.
- Yosys component sanity: PASS.

## Exclusions

No production RTL change, protocol parser, ingress buffer, Architecture B, P&R, timing, or throughput work.

## Evidence

Raw logs are under `results/raw/rtl/gearbox/`; the processed WIRE-014 report contains the historical gap and closure addendum. No new evidence ID is created; EVID-014 is strengthened.
