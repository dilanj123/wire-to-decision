# Wire-to-Decision — Master Checklist

This is a gate checklist, not a duplicate of the master plan. Future items remain incomplete until evidence is recorded.

## Gate 0 — Phase-0 ready / CLOSED

- [x] Repository bootstrap complete
- [x] Reference workflow audited
- [x] External protocol sources locked
- [x] Third-party provenance policy locked
- [x] Apple-Silicon open-source toolchain qualified
- [x] ECP5 implementation target frozen
- [x] Authoritative specification package complete
- [x] Clean-clone/reproducibility closure demonstrated by WIRE-007

## Functional baseline gate

Phase 2 — Architecture-A parser boundary: COMPLETE (WIRE-022, EVID-022). Phase 3 — bounded order state and deterministic decision: COMPLETE (WIRE-023/WIRE-024, EVID-023/EVID-024). Phase 4 — focused functional verification and bounded formal regression: COMPLETE (WIRE-025, EVID-025). Phase 5 implementation/measurement: COMPLETE (WIRE-026/WIRE-026A/WIRE-027, EVID-026/EVID-026A/EVID-027). The full-capacity design routes on all five seeds; WIRE-027's single write-plan experiment improves Fmax to 45.68–47.66 MHz, but every seed still misses 156.25 MHz.

- [x] Independent Python model — WIRE-013 end-to-end oracle unit-tested
- [x] Architecture-A 64-to-8 gearbox primitive — WIRE-014 RTL simulation and local formal checks
- [x] Architecture A parser — WIRE-022 external-ingress-to-normalized-event boundary RTL-simulated; named bounded integration/local formal evidence indexed
- [x] Bounded order state and decision — WIRE-023 bounded book/aggregates and WIRE-024 deterministic decision/full single-clock MVP RTL-simulated; named formal checks are bounded as indexed
- [x] Functional regression — WIRE-025 relevant Cocotb suites and Python 71/71 passed

## Verification gate

- [x] Directed protocol/state tests
- [x] Randomized valid and malformed traffic
- [x] Backpressure tests
- [x] Formal targets checked under documented assumptions (bounded/fixed scopes; historical monolithic jobs remain solver-bound)
- [x] Processed evidence indexed

## Architecture-A implementation gate

WIRE-026A resolves the initial LUT-RAM fit failure using synchronous packed-row EBR access. WIRE-027 isolates parser/book/decision service cycles and runs one controlled registered write-plan timing experiment. All five routes complete but miss 156.25 MHz; the clock path remains in the book EBR read/update logic. Phase-5 measurement evidence is complete; timing closure is not claimed.

- [x] Yosys `synth_ecp5` full-capacity mapping completed; 16 EBRs inferred
- [x] Five-seed ECP5 placement and routing completed
- [x] Timing and resource reports recorded (all seeds miss 156.25 MHz)
- [x] Latency cycles and accepted-byte throughput recorded
- [x] Bottleneck conclusion recorded: BUILD B justified as a separate controlled parser experiment; production Architecture B remains unauthorized

Timing closure at 156.25 MHz remains unachieved. No board pinout, physical timing, or physical throughput claim is made.

## Architecture experiment gate

- [ ] Architecture B authorized from evidence
- [ ] Identical experiment controls
- [ ] A/B comparison and conclusion

## CDC gate

- [ ] Independent RX and processing domains
- [ ] Original async FIFO
- [ ] Reset/epoch tests and local checks
- [ ] CDC limitations documented

## C++/portfolio gate

- [ ] Independent C++20 checker
- [ ] Reproducible replay and mismatch evidence
- [ ] Clean-clone validation
- [ ] Final evidence package
