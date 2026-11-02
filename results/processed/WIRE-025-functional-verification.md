# WIRE-025 — Focused Functional Verification

## Result

**PASS — Phase 4 closed.** Starting revision was `cc3c99c20c9695f81418837611cf36b9fe516042`; Gate-0 remained `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## Specification clarification

REQ-DEC-005 and the related REQ-ERR/formal wording now distinguish decision creation from delivery of a pending decision. An invalid/quarantined book cannot accept a new mutation or generate a new commit/decision. A decision already created from a successful valid-epoch commit remains pending through later recovery until handshake or explicit rearm/reset. It is not a new post-recovery decision. This preserves WIRE-D018/D019/D020 no-rollback semantics.

## Functional regression

`bash scripts/run_wire025_regression.sh` passed: 109/109 Cocotb tests across WIRE-014..024 suites, Python 71/71, and strict functional-top Verilator lint (5.053). The focused functional top is 14/14, including all mutation types A/F/E/C/X/D/U in a multi-frame stream, filters/failures/rearm, ready/valid stalls, the two late-suffix orderings, pending-decision rearm, and seeds `1, 7, 19, 42, 97`. The five-seed randomized traffic is bounded and replayable by the fixed seeds.

The Python ReferenceOracle matched outcomes for the long valid stream, ordinary filters/failures, rearm and commit-before-fatal prefix case. In the deliberately distinct fatal-before-commit suffix schedule, the Python model still predicts the complete prefix transaction because it does not model cycle ordering; RTL suppresses the mutation because fatal recovery is visible before its book commit handshake. That is the required REQ-ERR-004 commit-boundary behavior, not an unexplained mismatch. The dedicated assertions check no commit, decision, aggregate mutation, or order insertion in this case.

The initial test-development run was 12/14 because two scoreboard expectations were incorrect: the long stream queried the wrong expected replacement reference, and the mixed-error test expected parser recovery for book-local duplicate/collision failures. The assertions were corrected to use the actual replacement reference and the distinct book recovery status; the retained final run is 14/14. No RTL functional defect was found. An initial campaign-script attempt also exposed mixed historical SBY path conventions; the runner was corrected and the complete formal campaign then passed.

## Formal and tools

79/79 executed SBY jobs passed with their existing bounded/fixed-vector/reduced scopes and assumptions. The two historical solver-bound monolithic jobs were excluded from the mandatory pass count and remain explicitly not-PASS: `formal/ipv4_parser/wire_ipv4_parser_reference.sby` and `formal/arch_a_parser/wire_arch_a_parser_late_suffix.sby`. New public-interface targeted checks: decision reference BMC depth 16; prefix decision retained across later recovery BMC depth 8 with a reduced two-set book; early fatal blocks a new mutation/commit/decision BMC depth 5 with a reduced two-set book. These are not unbounded proofs. SBY v0.69, `smtbmc yices`, Yices 2.7.0. No DUT-private state is used in the new assertions.

Verilator full functional-top lint passed without warnings. No P&R or application timing/latency/throughput measurements were run.

## Evidence and limitations

Runner: `scripts/run_wire025_regression.sh`.

Raw logs and formal job results: `results/raw/wire025/`; focused test-development history is retained in `results/raw/wire025_functional_initial.log` and `results/raw/wire025_mixed_investigation.log`.

Task record: `tasks/WIRE-025.md`. Evidence index: EVID-025.

This campaign does not establish whole-design formal proof, ECP5 placement/routing, timing closure, latency, throughput, CDC/RDC, independent C++ checking, or physical FPGA operation. Those remain for later work. Next task: **WIRE-026 — ECP5 Architecture-A implementation and measurement**.
