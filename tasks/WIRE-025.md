# WIRE-025 — Focused Functional Verification and Phase-4 Closure

## Scope and starting state

Starting `main` and `origin/main`: `cc3c99c20c9695f81418837611cf36b9fe516042`; clean tree; protected `kg-g0-env^{}`: `06f5643a940ac2c6fcfab0e377169b48ce700107`. WIRE-024 and Phase 3 were complete. This task reuses the existing functional MVP and verification infrastructure; it does not change parser/book/decision architecture.

## Requirement/formal clarification

REQ-DEC-005 and the related REQ-ERR wording now define suppression at the mutation-commit/decision-creation boundary. No new commit or decision can originate from an invalid/quarantined book. A decision already created from an earlier successful commit in a valid epoch remains pending until handshake or explicit reset/rearm and is not a post-recovery decision. The clarification preserves WIRE-D018/D019/D020 no-rollback semantics. `docs/FORMAL.md` and `docs/VERIFICATION_PLAN.md` use the same distinction.

## Verification additions

- `tb/functional_mvp/test_functional_mvp.py`: added long multi-frame A/F/E/C/X/D/U oracle comparison; mixed filter/fatal/rearm paths; commit-before-fatal versus fatal-before-commit suffix orderings; and one-edge rearm with a pending stalled decision. Existing five fixed seeds (1, 7, 19, 42, 97) remain. The bench checks external ready/valid source stability, output stability, commit state, and final order/aggregate/decision state.
- `rtl/arch_a/wire_arch_a_functional_top.sv`: exposes successful book-commit transaction observability to the verification top without changing the functional datapath.
- `formal/decision_engine/early_fatal.sv/.sby`: fixed schedule, two-set reduced book; BMC depth 5 checks upstream fatal blocks an unaccepted mutation and creates no commit/decision.
- `formal/decision_engine/prefix_recovery.sv`: strengthened fixed-vector, two-set reduced prefix check; BMC depth 8 checks a previously created stalled decision survives later recovery, with no later event/commit and unchanged budget/count.

No production parser, order-book, or decision-engine behavior required correction. The only RTL interface change is diagnostic commit observability at the functional top.

During test development the first expanded run was 12/14 because two scoreboard expectations were incorrect (the long stream queried the wrong replacement reference, and the mixed-error test conflated parser recovery with book-local state-integrity recovery). The assertions were corrected using the actual replacement reference and distinct book recovery status. The final suite is 14/14, with no RTL functional defect found. The first campaign attempt also exposed mixed source-path conventions in existing SBY files; the runner now selects the correct working directory per job.

## Regression execution

Run the reproducible campaign with:

```bash
bash scripts/run_wire025_regression.sh
```

It executes all listed WIRE-014..024 Cocotb standalone/composition suites, the 71-test Python suite, all discovered SBY jobs except the two historically solver-bound monolithic jobs explicitly listed in the script, and strict Verilator lint for the functional top. Formal jobs are selected from their documented working-directory conventions. Tool versions and result summaries are in `results/raw/wire025/`.

Results: 109/109 Cocotb tests passed across 20 standalone/composition runs; Python 71/71 passed; 79/79 executed formal jobs returned PASS; functional-top Verilator 5.053 lint passed without warnings. The two excluded historical jobs remain solver-bound evidence, not PASS: the IPv4 monolithic reference and full-parser late-suffix BMC. Focused functional top: 14/14 PASS, including the five seeds.

## Prefix/fatal scheduling result

Two distinct late-suffix schedules pass. If earlier complete mutations handshake into the book before the later malformed suffix becomes fatal, their book state and already-created decision remain. If the fatal suffix becomes known before a complete earlier ITCH event reaches the book commit boundary, that event produces no commit or decision. The Python oracle predicts the complete-prefix result without modeling cycle scheduling; this second case is therefore an intentional timing-boundary difference, not an unexplained protocol mismatch. The RTL behavior follows REQ-ERR-004 and the frozen commit boundary. No rollback is claimed for already committed prefix state.

## Formal scope and limitations

Formal checks are bounded/fixed-vector or reduced-instance evidence, not a whole-design proof. New targeted decision jobs use SBY 0.69, `smtbmc yices`, Yices 2.7.0: decision reference depth 16; prefix/recovery depth 8 with two book sets and fixed transaction schedule; early-fatal depth 5 with two sets and fixed schedule. Existing jobs were rerun without weakening assumptions. Covers remain reachability evidence. The two historical monolithic jobs above remain excluded from mandatory PASS count.

## Acceptance and exclusions

Phase 4 closes with full relevant Cocotb/Python regression, bounded formal campaign, focused targeted tests, and Verilator lint. No P&R, timing, latency, throughput, complete-design formal proof, CDC/RDC, C++ checker, or physical FPGA operation is claimed. Next task: WIRE-026 — ECP5 Architecture-A implementation and measurement.
