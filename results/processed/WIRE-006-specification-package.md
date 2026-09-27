# WIRE-006 — Specification Package Evidence

## A. Starting state

SOURCE-DERIVED: Repository `/Users/Dilan/Projects/wire-to-decision`, branch `main`, started at clean HEAD `76e9ef3ab0cd951d594dcf5afcf81d407b084003`.

No application RTL, Python model, C++, tests, formal harness, synthesis, or P&R work was performed.

## B. Authority sources used

The existing WIRE-000 through WIRE-005 task/evidence package was read before drafting. The authoritative inputs were `docs/DECISIONS.md`, `docs/PROJECT_STATE.md`, `docs/EVIDENCE_INDEX.md`, `docs/SPEC_SOURCES.md`, `docs/IMPLEMENTATION_TARGET.md`, the WIRE-002 protocol evidence, the WIRE-003 provenance evidence, the WIRE-004 toolchain evidence, and the WIRE-005 target evidence. No prior master plan or application requirements package existed.

The resulting authority order is explicitly recorded in both the master plan and operating instructions.

## C. Documents created/updated

Created:

- `00_MASTER_PROJECT_PLAN.md`
- `01_CHATGPT_PROJECT_OPERATING_INSTRUCTIONS.md`
- `04_MASTER_CHECKLIST.md`
- `docs/REQUIREMENTS.md`
- `docs/MICROARCHITECTURE.md`
- `docs/VERIFICATION_PLAN.md`
- `docs/FORMAL.md`
- `tasks/WIRE-006.md`
- this processed evidence report

Updated:

- `docs/DECISIONS.md`
- `docs/PROJECT_STATE.md`
- `docs/EVIDENCE_INDEX.md`

Supporting WIRE-000 through WIRE-005 source records were preserved unchanged.

## D. Requirements summary

The package specifies the project-owned 64-bit post-MAC ingress, Ethernet II/IPv4/UDP profile, MoldUDP64 framing and fail-closed sequencing, supported A/F/E/C/X/D/U subset, P non-mutation, one configured Stock Locate, bounded 1024-order state, side aggregates, threshold-crossing decision, budget suppression, malformed-suffix limitation, recovery state, latency boundaries, throughput distinctions, CDC sequencing, software roles, provenance, and implementation evidence rules.

There are 71 stable normative requirement identifiers. All are `SPECIFIED / NOT YET VERIFIED`.

## E. Microarchitecture summary

Architecture A is frozen as common ingress buffering → 64-to-8 gearbox → one-byte-per-parser-cycle FSM → normalized ready/valid event → common bounded order state → common aggregate/decision logic. The normalized event fields and field-valid semantics are frozen, while exact RTL encoding and pipeline schedule remain implementation details.

The order store is 512 sets × 2 ways with no eviction. WIRE-D006 freezes the exact 64-bit-to-9-bit XOR-fold hash. Aggregate state is 48-bit bid/ask totals. Architecture B remains unauthorized and can only be proposed after Architecture-A evidence identifies parser serialization/alignment as the bottleneck.

## F. Verification strategy

The plan separates protocol/framing, normalized events, book/aggregates, decision, error/recovery, backpressure, and end-to-end verification. It requires directed, constrained-random, malformed, long-stateful, reproducible-seed, and backpressure tests. Separate scoreboards are planned for parser/events, order state, aggregates, and decisions.

## G. Formal strategy

The formal plan scopes local ready/valid, gearbox, Mold sequencing, order-state, decision, and future async-FIFO properties. Each task must record assumptions, assertions, covers, engine, solver, mode, depth, scope, result, and limitations. Yices 2.7.0 remains the qualified initial solver. No application property has been run.

## H. New decisions made

- WIRE-D006: exact deterministic 64-to-9-bit XOR-fold order hash.
- WIRE-D007: `P` is explicitly non-mutating; unsupported/unclassified message types fail closed rather than being silently skipped.
- WIRE-D008: common normalized mutation-event contract for Architecture A and any future authorized B.

These are specification/process decisions, not implementation or functional results.

## I. Traceability status

The verification matrix covers all 71 requirement identifiers using grouped ranges with stable individual IDs. Verified application requirements: 0. Specified/not-yet-verified application requirements: 71. No requirement is marked PASS, simulated, formally checked, synthesized, placed/routed, timing-clean, or physically measured.

## J. Hostile-review findings

The review checked protocol consistency, third-party normativity, WIRE-004 toolchain, WIRE-005 target, Architecture-B authorization, CDC sequencing, no BBO/price-level or multi-symbol scope creep, live-recovery exclusion, zero-only UDP checksum wording, malformed-suffix rollback wording, latency boundaries, raw 10 Gbit/s arithmetic, formal overclaiming, and physical-hardware optionality.

No contradiction with WIRE-002, WIRE-003, WIRE-004, or WIRE-005 was found. The following ambiguities were resolved narrowly:

- The previously unspecified set-index hash is now exact and reproducible.
- The previously unclassified ITCH-type policy now fails closed; `P` remains the explicit exception because WIRE-002 classifies it as non-mutating.
- The normalized event contract is now explicit for controlled A/B comparison.

No Architecture B detail was authorized and no CDC was added to the A/B experiment.

## K. Conflicts / resolutions

No conflicts requiring a change to previously frozen protocol, provenance, toolchain, or implementation-target scope were found. The new decisions are recorded rather than silently embedded only in requirements text.

## L. Remaining open implementation parameters

Exact ingress buffer depth, RTL state/module names, pipeline register placement, external software register mapping, and implementation-specific cycle schedules remain open. They must be frozen before the implementation task that needs them. Mold sequence arithmetic is not open: it is specified as unsigned 64-bit modular arithmetic. No open item may contradict the authoritative requirements or normalized-event contract.

## M. What remains unproven

Python reference-model correctness, RTL correctness, RTL simulation, application formal properties, application synthesis, application P&R, timing closure, latency, throughput, CDC correctness, C++ integration, and physical FPGA operation remain unproven.

## N. WIRE-006 conclusion

PASS: The authoritative specification package was created and internally consistency-reviewed. It makes the previously frozen protocol, toolchain, target, provenance, and engineering-method rules authoritative for later work, resolves the identified hash/message/event ambiguities, and introduces no application implementation or functional evidence.
