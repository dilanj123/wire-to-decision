# WIRE-015 — Architecture A common ingress beat buffer RTL and verification

## Phase

Phase 2 — Parser primitives and complete Architecture A parser.

## Starting state

- Starting HEAD: `185c487c5547014ec7bb90273e0a2ec33e37bc9c`
- Branch: `main`
- `origin/main`: same starting commit
- Gate-0 peeled commit: `06f5643a940ac2c6fcfab0e377169b48ce700107`
- Starting tree: clean after preflight reconciliation; no pre-existing files were found in the reported untracked paths.

## Objective and authority

Implement and verify the common synchronous two-beat ingress FIFO between the external 64-bit framed ready/valid interface and the Architecture-A gearbox. Authority is the Phase-0 specification package, WIRE-D011, and WIRE-D012.

## WIRE-D012 contract

The buffer depth is exactly two beats. Each entry stores `data[63:0]`, `keep[7:0]`, and `last`. Output is registered storage with no empty fall-through. Full plus same-cycle output transfer permits replacement input.

## Scope

Included: common FIFO RTL, ready/valid behavior, reset flush, independent cocotb FIFO scoreboard, deterministic random traffic with seeds 1/7/19, buffer-to-gearbox composition simulation, local formal reference queue, and Yosys component sanity.

Excluded: protocol parsing, Architecture B, CDC, P&R, timing, throughput, latency, and application-level claims.

## Formal scope

The reference harness uses only public DUT ports. The local safety harness proves reset-empty behavior inductively at depth 20. The independent payload/order/ready reference correspondence is bounded-checked through depth 10, with covers for occupancy-one and full simultaneous push/pop. This distinction is retained in evidence.

## Acceptance/evidence

Required evidence is retained under `results/raw/rtl/ingress_buffer/` and `results/processed/WIRE-015-ingress-buffer-rtl.md`. EVID-015 is limited to common-buffer simulation, named formal properties under documented assumptions, composition simulation, and component synthesis sanity.

## Completion boundary

WIRE-015 does not establish protocol parser RTL, normalized-event integration, bounded-state RTL, decision RTL, Architecture-A completeness, or performance closure. Next task: WIRE-016 — Architecture A Ethernet II byte parser RTL and verification.
