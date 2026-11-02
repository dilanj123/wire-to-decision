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

## Execution record

- Authorized starting local HEAD: `4e9a98c9b7d2e0b78eb4dc4b000c44c96df970e4`.
- Starting `origin/main`: `50a5e7c68bc383ef719862966dc675ba6c61a79e`.
- The local preparatory commit `docs: define WIRE-024 decision MVP scope` was user-authorized, verified as a direct descendant of `origin/main`, contained only this task record, and was preserved.
- Gate-0 peeled commit: `06f5643a940ac2c6fcfab0e377169b48ce700107`.
- Authority: REQ-DEC-001..007, REQ-ERR-002..004, WIRE-D010/D018/D019; Python `decision.py`, `oracle.py`, `constants.py`; WIRE-012/013/023 evidence and parser/book RTL. No authority conflict found.
- WIRE-D020 adopted in `docs/DECISIONS.md`.

### Implementation

Added `rtl/common/wire_decision_engine.sv` and `rtl/arch_a/wire_arch_a_functional_top.sv`. The engine evaluates only accepted successful book commits. It computes exactly a signed 49-bit difference of unsigned 48-bit aggregates; BUY/SELL crossing equations, WIRE-D010 trajectory updates, captured threshold/budget configuration, live enable sampling, and budget-at-creation semantics are frozen by WIRE-D020. A pending decision blocks later commits and remains stable through later parser/book recovery; explicit rearm/reset starts a new epoch and may discard it.

### Verification and evidence

- Decision cocotb: 7/7 PASS, seeds 1, 7, 19, 42, 97; Cocotb 2.1.0.dev0+41564633; Verilator 5.053.
- Full external-ingress functional top cocotb: 10/10 PASS, including all supported mutation types, filters, heartbeat, BUY/SELL and no-repeat trajectories, enable/budget behavior, book/parser failures, rearm, late malformed suffix, unsupported ITCH, and a decision stalled across later recovery. Random integration seeds 1, 7, 19, 42, 97. Python ReferenceOracle comparison passed on directed and randomized applicable cases.
- Formal: `decision_reference.sby` PASS, `smtbmc yices`, BMC depth 16; `prefix_recovery.sby` PASS, fixed-vector/reduced two-set book→decision BMC depth 8. Scope and assumptions are in `results/raw/rtl/decision_engine/formal_property_inventory.txt`. Neither is unbounded.
- Verilator strict lint: standalone engine and full functional top PASS without meaningful warnings.
- Yosys 0.69+154: standalone engine and full top hierarchy/process/opt/check/stat PASS, zero check problems. Classification is component sanity only.
- Python regression: 71/71 PASS.
- Earlier WIRE-014..023 cocotb regressions passed in the clean sequential runner; WIRE-023 seven formal jobs rerun and PASS. Exact test-suite counts are recorded in the processed report and raw clean regression log.

### Documentation corrections

Corrected PROJECT_STATE to reflect WIRE-023 order-state completion and WIRE-024 decision implementation. Corrected WIRE-023 traceability: REQ-DEC-001 aggregate representation was implemented there; REQ-DEC-002..006 were not. Phase 3 was marked complete only after final test closure; the Phase-4 functional regression item remains unchecked.

### Limitations / exclusions

No Phase-4 deep regression, complete application formal proof, ECP5 application synthesis/P&R, timing closure, latency or throughput measurement, Architecture B, CDC/RDC, C++ checker, or physical FPGA operation. Historical solver-bound WIRE-017 and WIRE-022 monolithic checks remain solver-bound historical evidence. No Python functional behavior was changed.

### Publication

Pushed only after all WIRE-024 acceptance evidence passed. See repository completion SHA and GitHub status in the execution report / processed evidence.

Final details: exact retained commands, parser regression suite counts, initial test-development failures and corrected vector, tool versions, and final exit statuses are in `results/raw/rtl/functional_mvp/run_summary.txt`. The original authorized preparatory commit remains in history as an ancestor.
