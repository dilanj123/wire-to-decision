# Project State

## Phase

Phase 4 — COMPLETE: focused single-clock functional regression, targeted formal strengthening, and checklist closure recorded by WIRE-025/EVID-025.

Phase 5 — COMPLETE for Architecture-A implementation and bottleneck measurement (WIRE-026/WIRE-026A/WIRE-027). The full-capacity design places and routes on all five frozen seeds. The WIRE-027 write-plan experiment improves routed Fmax to 45.68–47.66 MHz, but all seeds still miss 156.25 MHz; timing closure is not achieved.

CDC/RDC learning extension — WIRE-029 COMPLETE at the documented RTL-simulation and bounded-local-check scope. The original single-clock Architecture-A baseline is unchanged; commercial CDC/RDC signoff and physical Gray-bus skew remain unproven.

Phase 10 — COMPLETE: independent C++20 packet replay checker, actual RTL decision-log comparison and portfolio evidence audit (WIRE-030/EVID-030). Phase 11 vendor-flow/physical FPGA extensions remain OPTIONAL.

Phase 1: COMPLETE — 71-test Python end-to-end oracle baseline

Phase 2: COMPLETE — Architecture-A parser boundary through normalized events

Phase 3: COMPLETE — bounded order state, aggregates, and deterministic decision RTL (WIRE-023/WIRE-024)


## Gate

Gate 0 — CLOSED; WIRE-000 through WIRE-007 complete

## Known-good commit

9fbd24ec0b9fe6cd32f09312c1ee6905070755aa (WIRE-000 known-good baseline)

## Architecture

Architecture-A parser boundary is implemented and RTL-simulated from the common two-beat ingress buffer through Ethernet II, IPv4, UDP, MoldUDP64 header/sequence control, message-block framing, and ITCH normalized events. WIRE-022 composes these stages in a production-style top and adds parser-wide fatal recovery/rearm and external-frame drain gating. WIRE-023 adds the bounded order store, checked aggregates, successful-mutation commit boundary, and parser-fatal integration. WIRE-024 adds deterministic decision and risk-budget RTL in a single-clock functional top.

Baseline candidate:

64-bit framed packet stream
→ Architecture A byte-serial parser
→ normalized event
→ bounded order state
→ deterministic decision

WIRE-028's controlled Architecture-B experiment is complete. The two-byte-per-cycle experimental parser passed its documented functional checks, synthesized and routed for five seeds. The measured result rejects B for this project baseline; Architecture A remains the production implementation. B production replacement remains unauthorized.

## Application status

Application RTL: Architecture-A parser boundary, WIRE-023 bounded order-state/aggregate block, and WIRE-024 deterministic decision/functional top are implemented and RTL-simulated. WIRE-025 closes the focused Phase-4 functional regression campaign. WIRE-026/WIRE-026A provide full-capacity ECP5 synthesis and five-seed place/route evidence plus updated functional-top cycle measurements. All seeds route but miss the 156.25 MHz objective; the critical path is the EBR-based order-store read/compare/aggregate/write path. No timing-closure or physical-operation claim is made.

Bounded order-state / aggregate RTL: WIRE-023 implemented and RTL-simulated; local fixed-vector and reduced-store formal checks are bounded under documented assumptions. The production default is 512 sets × 2 ways; the 1,024-entry capacity test is RTL-simulated.

Parser→book integration: RTL-simulated for successful mutation sequences, complete-prefix retention after late Mold structural failure, ITCH semantic failure with independent Mold structural success, outer fatal before mutation, and explicit rearm.

Parser→book→decision integration: WIRE-024 RTL-simulated from complete external 64-bit ingress frames against the Python ReferenceOracle, including prefix decisions retained across later fatal recovery.

Decision engine: WIRE-024 RTL-simulated; signed 49-bit crossing, live enable, finite budget, output stability, and epoch rearm are checked. Named public-interface formal correspondence is BMC depth 16; reduced two-set book→decision prefix/recovery is fixed-vector BMC depth 8.

Deterministic decision RTL: WIRE-024 implemented and RTL-simulated; no timing, throughput, or application performance claim.

MoldUDP64 header/sequence controller: RTL-simulated; fatal session/sequence and heartbeat/EOS trailing-byte conditions immediately clear stage validity and assert recovery while the current malformed packet drains; named header/control, deferred-commit, recovery, stall, and wrap properties checked under documented bounded/fixed-vector assumptions

MoldUDP64 message-block framer: RTL-simulated; preserves per-message boundaries and opaque payloads, supports zero-length structural messages, and reports exact-count/truncation/trailing errors. Named fixed-vector public-interface checks and bounded ready/valid safety checks pass; structural result drives WIRE-019 deferred sequence commit/recovery in seven-stage simulation.

ITCH decoder / normalized-event boundary: RTL-simulated; A/F/E/C/X/D/U mappings, P handling, tracked-locate filtering, exact symbol policy, and stage-local fail-closed drain are exercised. Events are gated on WIRE-D016 complete-message boundaries. Named fixed-vector/safety public-interface formal checks pass; Mold header→framer→ITCH composition confirms semantic ITCH failure does not alter Mold structural success.

ITCH decoder RTL: implemented for the frozen A/F/E/C/X/D/U/P subset; broader ITCH remains unsupported by design

Reference-model package: created

WIRE-008: complete. The initial task/specification conflict was resolved by
retaining higher-authority WIRE-D008 and correcting the Python implementation
and task interpretation.

Python canonical data model: implemented and unit-tested

WIRE-D006 hash: implemented and unit-tested in Python

WIRE-009: complete

Ethernet/IPv4/UDP/Mold framing model: unit-tested

Mold session/sequence handling: unit-tested

ITCH decoding beyond the supported subset: not started

WIRE-010: complete

ITCH A/F/E/C/X/D/U decoder: unit-tested

Normalized events from ITCH bytes: unit-tested

P known non-mutating handling: unit-tested

WIRE-011: complete functionally

Bounded order-state model: unit-tested

Bid/ask aggregates: unit-tested

Canonical GitHub repository: https://github.com/dilanj123/wire-to-decision

GitHub publication: complete; public repository, `main` and `kg-g0-env` pushed

Order-store mutation model: Python-unit-tested

WIRE-012: complete

Deterministic decision model: unit-tested

Risk-budget model: unit-tested

Full end-to-end Python oracle: unit-tested

WIRE-013: complete

End-to-end Python oracle: unit-tested

Packet-level fail-closed/recovery integration: unit-tested

Python component regression: 71 tests passing

64-to-8 gearbox: RTL-simulated

Common ingress buffer: RTL-simulated; two-beat registered FIFO frozen by WIRE-D012

Buffer→gearbox integration: RTL-simulated

Ethernet II parser: RTL-simulated

Buffer→gearbox→Ethernet integration: RTL-simulated

IPv4 parser: RTL-simulated; named public-interface formal correspondence closed with decomposed bounded checks under documented assumptions

Buffer→gearbox→Ethernet→IPv4 integration: RTL-simulated

UDP parser: RTL-simulated; named local properties checked with documented bounded/fixed-vector formal jobs

Buffer→gearbox→Ethernet→IPv4→UDP integration: RTL-simulated

Ingress-buffer local formal: reset-empty safety inductively checked; public-interface correspondence bounded-checked through depth 10

Gearbox local formal: closed under documented assumptions for ordering, accepted valid-byte conservation, exact last-marker behavior, stall stability, and refill safety; reference correspondence bounded-checked through depth 20

Application RTL functional evidence: WIRE-014..022 parser stages/composition, WIRE-023 order-book/aggregate and parser→book boundary, WIRE-024 decision engine/full parser→book→decision simulation, and WIRE-025 focused end-to-end, malformed-traffic, reset/rearm, backpressure, Python and regression campaign. Named local formal checks are bounded/fixed-vector as individually recorded. No complete parser/book/decision formal proof is claimed.

Formal parser evidence: named stage-local and top-level safety properties checked with documented bounded/fixed-vector scopes; no complete parser proof or application-level formal proof is claimed.

Application synthesis/P&R evidence: full-capacity ECP5 synthesis and five-seed placement/routing completed by WIRE-026/026A and repeated after the WIRE-027 order-book timing experiment. All five runs route; none meets the 156.25 MHz objective. No board pinout, timing closure, or physical operation is claimed.

## Regression status

Python component regression: 71/71 passing

## Formal status

WIRE-014 gearbox local properties checked with SBY/Yices under documented legal-input assumptions. WIRE-015 ingress-buffer reset-empty safety is inductively checked and its independent public-interface queue correspondence is bounded-checked through depth 10. WIRE-016 Ethernet parser local safety is bounded-checked through depth 20 and public-interface correspondence through depth 40 under documented assumptions. WIRE-017 local safety is bounded-checked through depth 20; WIRE-017A decomposed public-interface checks cover classification, checksum, payload, Total-Length boundary, padding, truncation and restart at recorded depths. The original monolithic correspondence job remains solver-bound after step 22. WIRE-018 uses decomposed fixed-vector and bounded checks. WIRE-019/019A and WIRE-020/021 retain their named bounded/fixed-vector public-interface suites. WIRE-022 parser safety is BMC depth 20; its full-top late-suffix BMC remains solver-bound after step 69. WIRE-023 adds reduced two-set public-port BMCs (depths 12, 20 and 28) for commit/error/recovery/reset safety, hash vectors, duplicate/full-set behavior, successful mutation accounting, atomic full-destination replacement failure, unknown-reference failure, and upstream-fatal ordering. WIRE-023 formal results are bounded/fixed-vector checks, not proofs of all 512 sets or all event sequences. WIRE-024 decision/reference correspondence is BMC depth 16; a fixed-vector reduced two-set book→decision pending-prefix/recovery check is BMC depth 8. WIRE-025 reran 79 established/decomposed SBY jobs and added decision reference depth 16, reduced two-set prefix-recovery depth 8, and reduced two-set early-fatal depth 5. These are bounded/fixed-vector checks, not unbounded proofs; the IPv4 monolithic reference and full-parser late-suffix BMC remain historical solver-bound jobs excluded from the WIRE-025 pass count.

WIRE-025 campaign: 109/109 Cocotb tests across WIRE-014..024 passed; 79 executed SBY jobs passed; functional-top Verilator lint passed. Two historical monolithic solver-bound jobs remain excluded and are not PASS.

## Synthesis / P&R status

Application P&R and cycle-based latency/throughput evidence exist from WIRE-026/026A/027. The five-seed implementation routes but misses the frozen clock objective. Cycle measurements are simulation evidence, not physical latency or throughput measurements.

## Latest evidence

WIRE-004 native Apple Silicon open-source toolchain qualification completed in commit `89e2841` for the trivial smoke design. Canonical suite: OSS CAD Suite `2026-09-27`; details are in `results/processed/toolchain_smoke.md`. This is toolchain-smoke evidence only.

WIRE-005 froze LFE5U-85F-8BG381C / `--85k --package CABGA381 --speed 8` with a 156.25 MHz / 6.4 ns timing objective. WIRE-026/026A/027 produced full-capacity Architecture-A synthesis and five-seed route evidence; WIRE-028B produced matched Architecture-B synthesis and five-seed route evidence. A routes at 45.68–47.66 MHz; B routes at 19.997–21.047 MHz. Neither meets the objective. WIRE-025's 79-job formal campaign passed under its recorded bounded scopes; two historical monolithic jobs remain solver-bound. Cycle-based latency/throughput and routed implementation estimates exist; physical operation, physical latency/throughput, physical CDC/RDC signoff and C++ integration with live networking remain outside the evidence. WIRE-030 adds an independent replay checker. See EVID-026/026A/027/028B/030.

WIRE-029 updates CDC status: asynchronous FIFO and Architecture-A wrapper simulation, bounded local properties, and Yosys sanity passed. Commercial CDC/RDC signoff, physical Gray-bus skew, and operation on hardware remain unproven.

WIRE-030 closes the independent software/portfolio gate: C++20 parses the canonical post-MAC replay, compares actual functional-top decisions and state, and summarizes RTL simulation-cycle latency. The canonical comparison is 4 frames / 3 Mold messages / 2 decisions / 0 mismatches; a corrupted actual RTL decision log is detected. Clean-clone commands and outputs are indexed by EVID-030.

## Open bugs

None recorded.

## Open decisions

- WIRE-028/028A/028B controlled A/B experiment is closed: REJECT B for this baseline; Architecture A remains production. Rationale and bounded evidence are in `docs/DECISIONS.md` and `EVID-028B`.
- WIRE-001 process adoption details are recorded in `docs/DECISIONS.md`.
- WIRE-002 external source authority and MVP protocol restrictions are recorded in `docs/DECISIONS.md`.
- WIRE-003 originality and third-party provenance policy are recorded in `docs/DECISIONS.md`.
- WIRE-004 canonical toolchain decision is recorded in `docs/DECISIONS.md`.
- WIRE-005 canonical implementation target and experiment invariants are recorded in `docs/DECISIONS.md` and `docs/IMPLEMENTATION_TARGET.md`.
- WIRE-006 authoritative requirements, microarchitecture, verification, and formal package is recorded in the master/specification documents. WIRE-014 added the single-clock reset convention and gearbox evidence.
- WIRE-D012 common ingress buffer depth decision is recorded in `docs/DECISIONS.md` and WIRE-015 evidence.
- WIRE-D015 deferred Mold normal-packet sequence commit is recorded in `docs/DECISIONS.md` and WIRE-019 evidence.
- WIRE-D016 Mold complete-message boundaries and structural packet-result semantics are recorded in `docs/DECISIONS.md` and WIRE-020 evidence.
- WIRE-D017 ITCH normalized-event RTL encoding and complete-message commit boundary are recorded in `docs/DECISIONS.md` and WIRE-021 evidence.
- WIRE-D018 parser-wide fatal recovery, current-frame drain, event-boundary no-rollback, and explicit rearm are recorded in `docs/DECISIONS.md` and WIRE-022 evidence.
- WIRE-D019 bounded-book atomic mutation commit and parser-fatal ordering are recorded in `docs/DECISIONS.md` and WIRE-023 evidence.
- WIRE-D020 decision commit evaluation, configuration epochs, live enable, budget consumption, and pending-prefix/no-rollback semantics are recorded in `docs/DECISIONS.md` and WIRE-024 evidence.
- WIRE-D021 asynchronous FIFO reset/epoch recovery is recorded in `docs/DECISIONS.md` and WIRE-029 evidence.

## Current bottleneck

WIRE-026A mapped the 512 × 2 store to 16 EBRs. WIRE-027's registered write-plan experiment reduced full-top LUT4 to 7,376 and improved five-seed Fmax to 45.68–47.66 MHz; the A critical path remained in the book EBR read/update logic. WIRE-027 measured parser service intervals of 86–107 cycles/event versus 5 cycles for ordinary book service and 1 cycle for decision creation. The completed WIRE-028 experiment tested a two-byte-per-cycle direct-beat parser against the same book/decision subsystem. B halves simulation cycles on matched workloads but routes at 19.997–21.047 MHz, with a critical path from ingress beat selection through parser control to `ip_index_q`; it uses 14,559 LUT4. The comparison rejects B for this baseline: its clock estimate and LUT cost outweigh the cycle reduction, yielding lower derived byte rate at each architecture's conservative minimum seed estimate. Neither architecture meets 156.25 MHz. See `results/processed/WIRE-027-bottleneck-experiment.md` and `results/processed/WIRE-028-architecture-ab-comparison.md`.

## Next task

No further mandatory task is open. Phase 11 vendor-flow and physical FPGA extensions are OPTIONAL. Architecture A remains production; timing closure, physical operation, and commercial CDC/RDC signoff are not claimed.
