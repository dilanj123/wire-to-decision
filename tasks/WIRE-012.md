# WIRE-012 — Python Deterministic Decision Model

## Task

- Phase: Phase 1 — Python reference model
- Starting HEAD: `0c95d8e9571551c6ea315fdd9b7936a608c1e34e`
- Protected tag: `kg-g0-env` peeled to `06f5643a940ac2c6fcfab0e377169b48ce700107`
- Objective: implement and unit-test deterministic imbalance threshold crossings and risk-budget behavior above the completed bounded order/aggregate model.

## Authority

Use `docs/REQUIREMENTS.md`, `docs/MICROARCHITECTURE.md`, `docs/DECISIONS.md`, WIRE-011 book evidence, and the canonical Python types. WIRE-D010 freezes previous-imbalance updates after successful tracked mutations.

## Scope

Allowed: Python decision state, decision-event emission, book/decoder integration tests, raw and processed evidence, task/state/evidence-index updates.

Prohibited: RTL, Architecture A, Architecture B, CDC, synthesis/P&R, latency claims, production trading logic, and WIRE-013 work.

## Acceptance criteria

- Exact signed imbalance and BUY/SELL crossing boundaries implemented.
- Previous-imbalance, enable, invalid-book, budget, and re-arm semantics tested.
- DecisionEvent metadata comes from the triggering mutation.
- OrderBook→DecisionModel and ITCH→book→decision paths tested.
- Existing 52 tests remain passing; total test count recorded.
- No third-party dependency or RTL added.
- EVID-012, processed evidence, and project state updated.
- Clean working tree and matching local/remote `main` after push.

## Evidence and completion report

Retain raw logs under `results/raw/reference_model/` and processed evidence at `results/processed/WIRE-012-decision-model.md`. Report exact test count, requirement traceability, WIRE-D010 status, remaining unproven work, and the next task without starting WIRE-013.
