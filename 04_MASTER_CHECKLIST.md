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

Phase 2 — Architecture-A parser boundary: COMPLETE (WIRE-022, EVID-022). Phase 3 is next; downstream order-state/decision and later gates remain open.

- [x] Independent Python model — WIRE-013 end-to-end oracle unit-tested
- [x] Architecture-A 64-to-8 gearbox primitive — WIRE-014 RTL simulation and local formal checks
- [x] Architecture A parser — WIRE-022 external-ingress-to-normalized-event boundary RTL-simulated; named bounded integration/local formal evidence indexed
- [ ] Bounded order state and decision
- [ ] Functional regression

## Verification gate

- [ ] Directed protocol/state tests
- [ ] Randomized valid and malformed traffic
- [ ] Backpressure tests
- [ ] Formal targets checked under documented assumptions
- [ ] Processed evidence indexed

## Architecture-A implementation gate

- [ ] Yosys synthesis
- [ ] Five-seed ECP5 P&R
- [ ] Timing and resource reports
- [ ] Latency cycles and throughput
- [ ] Bottleneck conclusion

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
