# Wire-to-Decision — Master Project Plan

## Authority and scope

This document is the top-level project authority. The repository authority order is:

1. `00_MASTER_PROJECT_PLAN.md`
2. `01_CHATGPT_PROJECT_OPERATING_INSTRUCTIONS.md`
3. `docs/REQUIREMENTS.md`
4. `docs/MICROARCHITECTURE.md`
5. `docs/VERIFICATION_PLAN.md`
6. `docs/FORMAL.md`
7. `docs/DECISIONS.md`
8. `docs/PROJECT_STATE.md`
9. `docs/EVIDENCE_INDEX.md`
10. implementation, test, and build files

Supporting source/provenance records are `docs/SPEC_SOURCES.md`, `docs/THIRD_PARTY_MANIFEST.md`, and `docs/IMPLEMENTATION_TARGET.md`. If documents conflict, stop and report the conflict; do not silently choose an interpretation.

## Purpose

Wire-to-Decision is an evidence-driven SystemVerilog/FPGA portfolio project investigating deterministic low-latency network processing from a post-MAC Ethernet frame stream through IPv4, UDP, MoldUDP64, and a bounded TotalView-ITCH subset into deterministic state updates and a deliberately simple decision event.

The project focuses on SystemVerilog RTL, streaming microarchitecture, network protocol parsing, deterministic latency, bounded state, ready/valid design, formal verification, CDC/RDC, reset-domain behaviour, FPGA timing/PPA, Python/C++ hardware-software integration, and controlled architecture experiments. It is not a trading-strategy project.

## Mandatory MVP chain

```text
64-bit post-MAC framed stream
→ Ethernet II validation
→ IPv4 validation
→ UDP validation
→ MoldUDP64 framing/sequence handling
→ TotalView-ITCH supported subset
→ normalized mutation event
→ bounded single-instrument order state
→ aggregate bid/ask totals
→ deterministic threshold-crossing decision event
```

The mandatory CV-ready design excludes PHY, MAC, PCIe, Linux drivers, live exchange connectivity, production trading strategy, order entry, full ITCH coverage, GLIMPSE, Mold retransmission requester, multi-symbol books, price-level/BBO logic, and unnecessary PHY/MAC implementation.

## Frozen environment and target

The canonical flow is the native Apple Silicon OSS CAD Suite qualified by WIRE-004. The canonical implementation target is `LFE5U-85F-8BG381C`, mapped as `--85k --package CABGA381 --speed 8`, with a 156.25 MHz / 6.4 ns timing objective. These are experiment controls, not application timing or fit evidence.

## Phases

### Phase 0 — Bootstrap/specification/environment

WIRE-000 through WIRE-007 establish the repository, workflow, external sources, provenance policy, toolchain, implementation target, authoritative specification package, and clean-clone/reproducibility closure. Gate 0 remains open until WIRE-007.

### Phase 1 — Python reference model

Implement the independent protocol/state/decision oracle before application RTL.

### Phase 2 — Parser primitives and complete Architecture A parser

Implement the simplest complete byte-serial baseline against the normalized-event contract.

### Phase 3 — Bounded order state and deterministic decision

Complete the single-clock functional MVP.

### Phase 4 — Deep verification and targeted formal

Run layered directed, randomized, malformed, backpressure, and documented local formal checks.

### Phase 5 — Architecture-A ECP5 implementation/P&R evidence

Run synthesis, five fixed seeds, P&R, timing/resource extraction, latency and throughput measurement, and bottleneck identification.

### Phase 6 — Architecture experiment decision

Choose `BUILD B`, `MODIFY HYPOTHESIS`, or `REJECT B` from Architecture-A evidence.

### Phase 7 — Architecture B only if authorized

No Architecture-B implementation is authorized by this document alone.

### Phase 8 — Controlled Architecture A/B comparison

Use identical target, toolchain, workload, controls, and reporting.

### Phase 9 — CDC/RDC extension

Add independently clocked RX and processing domains with original CDC/FIFO work after the single-clock comparison.

### Phase 10 — Independent C++ checker and portfolio closeout

Add implementation-diverse replay/checking and package evidence.

### Phase 11 — Optional vendor-flow/physical FPGA extensions

Optional only; not part of the CV-ready gate.

## Engineering method

```text
specify
→ build simplest complete baseline
→ verify
→ synthesize/implement
→ measure
→ identify bottleneck
→ form a hypothesis
→ make one controlled change
→ re-verify
→ re-measure
→ retain/modify/reject
→ compare
→ conclude
```

Writing RTL alone is never completion evidence. Claims use the evidence labels in `docs/EVIDENCE_INDEX.md`; no stronger label may be used than the recorded tool evidence supports.

## Evidence boundary

At WIRE-006, application RTL, Python model, C++ checker, functional simulation, application formal, application synthesis/P&R, timing, latency, throughput, CDC, and physical evidence are all absent. This package specifies future work; it does not claim that work has passed.
