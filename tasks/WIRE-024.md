# WIRE-024 — Deterministic Decision / Risk-Budget RTL and Functional MVP

## Scope

Implement the deterministic decision engine and integrate the existing
Architecture-A parser and bounded order state into a single-clock
Ethernet-to-decision functional MVP. Correct the two factual WIRE-023
documentation statements described in the authoritative handoff.

Do not start WIRE-025, ECP5 P&R, Architecture B, CDC/RDC, or modify Gate-0.
The existing parser, Mold/ITCH behavior, order-state RTL, Python oracle, and
third-party provenance remain authoritative.

## Required semantics

- A successful `commit_valid && commit_ready` order mutation is the sole
  decision evaluation boundary and supplies post-mutation 48-bit bid/ask
  totals.
- Compute signed imbalance as exactly 49-bit
  `signed({1'b0,bid_total}) - signed({1'b0,ask_total})`.
- BUY: `previous < +threshold && current >= +threshold`.
- SELL: `previous > -threshold && current <= -threshold`.
- `previous_imbalance` advances after every accepted successful mutation,
  including while disabled or budget-exhausted.
- `decision_enable` is sampled on the commit handshake; disabled crossings
  are not replayed later.
- Each qualifying decision consumes one 32-bit budget credit at creation,
  remains stable while stalled, and is never retroactively cancelled by a
  later parser/book recovery. Rearm/reset clears the pending output and starts
  a new epoch with the configured initial budget.
- Decision metadata is copied from the triggering commit. `action=0` is BUY
  and `action=1` is SELL.

## Allowed implementation scope

- New/updated decision RTL and the parser→book→decision functional top.
- Standalone and integration cocotb tests, formal jobs, and focused build
  evidence for this task.
- Required WIRE-024 task/evidence documentation and the two WIRE-023 factual
  bookkeeping corrections.

## Acceptance

- Directed and randomized standalone decision tests pass for seeds 1, 7, 19,
  42, and 97, including boundary, zero-threshold, enable, budget, metadata,
  stall, rearm, maximum-width, and no-rollback cases.
- Full external-ingress parser→book→decision tests match the existing Python
  ReferenceOracle, including failures, late malformed suffixes, unsupported
  ITCH, and rearm.
- Required formal property groups pass under documented bounded/fixed-vector
  scopes without overstating the result.
- Verilator and Yosys component/top sanity pass with warnings reviewed.
- WIRE-023 and earlier regressions remain passing; Python remains 71/71.
- Gate-0 is unchanged. If all mandatory evidence passes, update Phase 3 to
  COMPLETE and leave functional-regression items for Phase 4.
- Final result includes exact commands, exit codes, evidence paths, changed
  files, base/ending SHA, and explicit unproven limitations.

## Verification classification

Classify achieved evidence only as RTL-SIMULATED, FORMALLY CHECKED UNDER
DOCUMENTED ASSUMPTIONS, or SYNTHESISED COMPONENT SANITY as applicable. Do not
claim timing closure, throughput, latency, placement, routing, Architecture B,
or application-wide formal proof.
