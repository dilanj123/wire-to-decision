# WIRE-012 — Python Deterministic Decision Model

## A. Starting state

SOURCE-DERIVED: Started on `main` at `0c95d8e9571551c6ea315fdd9b7936a608c1e34e` with a clean tree. Local `main` matched `origin/main`; `kg-g0-env` remained annotated and peeled to `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. Authority used

SOURCE-DERIVED: Used REQ-DEC-001 through REQ-DEC-007, the decision subsystem microarchitecture, canonical `DecisionEvent`/`ModelConfig` types, and WIRE-011 bounded-order behavior. No authority conflict was found.

## C. Decision-state representation

IMPLEMENTED / PYTHON-UNIT-TESTED: `DecisionModel` maintains `previous_imbalance`, `current_budget`, and `decision_count`. Re-arm resets them to zero, `initial_budget`, and zero respectively. `DecisionResult` combines the book result with zero or one `DecisionEvent`.

## D. Imbalance calculation

IMPLEMENTED / PYTHON-UNIT-TESTED: Imbalance is the checked signed integer `bid_total - ask_total`, supporting the full `-MAX_U48` through `+MAX_U48` range without truncation or wrap.

## E. BUY crossing

PYTHON-UNIT-TESTED: BUY requires valid book, enabled decisions, nonzero budget, `previous < +T`, and `current >= +T`.

## F. SELL crossing

PYTHON-UNIT-TESTED: SELL requires valid book, enabled decisions, nonzero budget, `previous > -T`, and `current <= -T`.

## G. Previous-imbalance semantics

DECISION-FROZEN / PYTHON-UNIT-TESTED: WIRE-D010 sets previous imbalance to the resulting current imbalance after every successful tracked mutation, including suppressed emissions. Failed, non-mutating, filtered, and quarantined events do not advance it.

## H. Decision-enable suppression

PYTHON-UNIT-TESTED: Disabled decisions suppress emission while successful mutation trajectory state advances, preventing stale crossings after re-enable.

## I. Budget model

PYTHON-UNIT-TESTED: One credit is consumed per emitted event. Budget never becomes negative and `decision_count <= initial_budget` is exercised through deterministic crossing stress sequences.

## J. Re-arm/reset

PYTHON-UNIT-TESTED: Explicit `DecisionModel.reset()` restores zero previous imbalance, the configured initial budget, and zero decision count. It does not implicitly reset on failed mutation.

## K. Book integration

PYTHON-UNIT-TESTED: `apply_and_evaluate()` invokes `OrderBook.apply()` and evaluates only after `applied == True`. Failed book mutations emit no decision and do not advance decision state.

## L. ITCH→book→decision integration

PYTHON-UNIT-TESTED: A real WIRE-010 A message was decoded, applied by WIRE-011, and crossed the configured threshold. The resulting event preserved Mold sequence, ITCH timestamp, and signed imbalance.

## M. Boundary/corner cases

PYTHON-UNIT-TESTED: Coverage includes no repeated level decisions, cross-back/recross in both directions, threshold zero, exact boundaries, enable suppression, zero budget, invalid status, aggregate extremes, and re-arm.

## N. Test coverage

PYTHON-UNIT-TESTED: The complete suite contains 61 tests: 52 prior tests plus 9 WIRE-012 decision-model tests. All passed under Python 3.11.6.

## O. Requirement traceability

PYTHON-UNIT-TESTED: WIRE-012 exercises REQ-DEC-002 through REQ-DEC-006. REQ-DEC-001 aggregate representation was exercised by WIRE-011. REQ-ERR-002/003 are covered only for decision suppression and explicit decision-state re-arm; packet-level recovery remains future work.

## P. Documentation correction

IMPLEMENTED: Corrected stale project-state statements that still described order-store mutation as not started, regression as not run, and decision modeling as not started. RTL evidence remains explicitly absent.

## Q. Dependencies

IMPLEMENTED: No third-party Python dependency was added. The model uses the standard library and project-owned types.

## R. Problems/conflicts

No specification conflict was found. No RTL, formal application run, synthesis/P&R, or Architecture A work was performed.

## S. What remains unproven

UNPROVEN: Full end-to-end Python oracle, packet-level recovery integration, RTL correctness/simulation, application formal verification, synthesis/P&R, timing, latency, throughput, Architecture-A bottleneck, Architecture-B authorization, CDC, C++ integration, and physical FPGA operation.

## T. WIRE-012 conclusion

PASS: The deterministic imbalance-crossing and risk-budget model, including bounded-order integration, passes 61 Python unit tests. Evidence is Python-unit-tested only; no RTL or performance claim is made.
