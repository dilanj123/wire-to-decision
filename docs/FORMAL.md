# Wire-to-Decision Formal Plan

## Status and scope

This document defines intended local formal targets. No application formal property has been implemented or run. A result is valid only for the named property, model, assumptions, engine, solver, mode, depth, and scope.

## Required evidence record

Every formal task SHALL record assumptions, assertions, covers, engine, solver, mode, depth, scope, result, and limitations. The qualified initial solver is Yices 2.7.0 from WIRE-004 unless a later evidence-backed decision changes it. A bounded local PASS is never a whole-design proof.

## Candidate local targets

### Ready/valid safety

- Payload is stable while `valid && !ready`.
- No transfer occurs without `valid && ready`.
- No local duplication or loss under documented interface assumptions.
- Bounded token conservation where tractable.

### 64-to-8 gearbox

- Accepted byte ordering is preserved.
- Valid-byte count is conserved.
- `rx_keep` and `rx_last` semantics are preserved.
- No invented bytes or dropped accepted bytes under documented assumptions.

### Mold sequence controller

- Book cannot remain valid after detected session/sequence error.
- Expected sequence advances only for accepted normal message counts.
- Heartbeat does not advance expected sequence.
- End-of-session suppresses later decisions until recovery.

### Order state

Use reduced/local abstractions when full-scale proof is impractical:

- No two valid copies of one reference.
- Valid quantity is nonzero.
- Aggregate changes correspond to accepted state mutations.
- Unknown-reference mutation cannot silently succeed.
- Collision/full condition cannot silently evict a live entry.

### Decision logic

- Decision implies `book_valid` and `decision_enable`.
- Decision implies pre-event budget is nonzero.
- Decision count never exceeds initial budget.
- BUY/SELL occurs only on the specified crossing.
- No decision occurs without a qualifying mutation/crossing.

### Future async FIFO

- Gray pointer assumptions/properties are documented.
- No read occurs from logical empty.
- No write occurs to logical full.
- Local pointers are monotonic under local-clock assumptions.
- Reset/epoch behavior is safe under documented one-sided-reset assumptions.

## Assumption discipline

Assumptions must be explicit and minimal. Clock relationships, legal ready/valid behavior, reset release, bounded packet framing, and environment configuration are assumptions only when recorded in the task and evidence. Covers are not proofs. Abstraction and reduced models must be labelled as such.

## Formal versus other evidence

Formal evidence complements Python/reference-model, RTL simulation, synthesis, and P&R evidence. It does not replace protocol regression, does not prove unmodeled software behavior, and does not establish CDC/RDC signoff. Commercial CDC/RDC signoff is not claimed.
