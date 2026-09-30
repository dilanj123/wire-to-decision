# WIRE-019A — Immediate fail-closed Mold control repair

## Starting state

Started from clean `main` at `a97ca0a0c23f04e41a0dd198363779f370d2256e`, equal to `origin/main`. Gate-0 peeled commit was `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## Finding and repair

Review found that a fatal completed-header condition with trailing physical bytes entered `S_DROP` before updating stage control outputs. Session mismatch, sequence mismatch, heartbeat trailing bytes, and EOS trailing bytes therefore left `controller_valid` asserted and `recovery_required` clear while the already-invalid packet drained.

The four `S_DROP` entry branches in `rtl/arch_a/wire_mold_header_seq.sv` now clear `controller_valid_q` and assert `recovery_required_q` on the detection edge. `S_DROP` remains input-ready to consume the current malformed packet through `in_last`; metadata, body, and packet-result outputs remain blocked. Expected sequence is unchanged. WIRE-D015 and successful deferred sequence commit are unchanged.

Reset/re-arm retains priority and can discard the pending drain, load configured session/sequence, clear recovery, and restart at header byte zero. A directed test covers re-arm while in drain.

## Verification

- Standalone cocotb: 14/14 PASS. This updates the prior stale 8/8 evidence; source had 9 tests at WIRE-019, then WIRE-019A added four error-drain checks and one drain re-arm check. Random body seeds remain 1, 7, 19.
- Six-stage composition: 2/2 PASS.
- SBY/Yices public-interface formal: safety BMC depth 36 PASS, cover depth 40 PASS. Session mismatch, sequence mismatch, heartbeat trailing, and EOS trailing fixed-vector BMC jobs each PASS at depth 28. References use public ports only; DUT-private state: NO.
- Assumptions: synchronous reset initialization and upstream ready/data/last stability while stalled. Fixed-vector jobs hold the source sequence and session to explicit values; downstream readiness is set ready for these fixed scenarios. Drain `in_ready` is expected high until physical last.
- Verilator standalone/composition lint: PASS, no RTL warnings. Yosys standalone/composition component sanity: PASS.
- Python: 71/71 PASS.
- Prior primitive cocotb jobs: WIRE-014 6/6, WIRE-015 standalone 5/5 + integration 1/1, WIRE-016 standalone 4/4 + composition 1/1, WIRE-017 standalone 5/5 + composition 3/3, WIRE-018 standalone 5/5 + composition 3/3.
- Prior primitive formal jobs: gearbox, ingress-buffer, Ethernet, decomposed IPv4 checks, and UDP jobs passed. The original monolithic IPv4 correspondence job was interrupted after reproducing its documented solver-bound behavior beyond step 22; decomposed IPv4 checks passed. It is not classified as a property failure or PASS.

## Evidence and scope

Raw WIRE-019A logs are under `results/raw/rtl/mold_header_seq/wire019a_*`. The WIRE-019 processed report contains the formal/control repair addendum. EVID-019 and PROJECT_STATE were updated. Evidence is RTL-SIMULATED plus BOUNDED/FIXED-VECTOR formal checks under the stated assumptions. No WIRE-020 message-block parsing, ITCH/state/decision logic, P&R, or application performance work was performed.

## Acceptance and publication

WIRE-019A passes its scoped criteria. Commit and GitHub push are recorded in the completion report; local and remote `main` must match, and Gate-0 remains fixed.
