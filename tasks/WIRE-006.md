Task ID: WIRE-006
Phase: Phase 0 — Bootstrap
Starting known-good commit: 76e9ef3ab0cd951d594dcf5afcf81d407b084003

Objective:
Create the authoritative Wire-to-Decision project specification package from the already-frozen protocol, provenance, toolchain, target, and engineering-method decisions.

Authority inputs:
- Existing repository documents and WIRE-000 through WIRE-005 evidence.
- `docs/SPEC_SOURCES.md`, `docs/IMPLEMENTATION_TARGET.md`, and `docs/DECISIONS.md`.

Allowed modifications:
- `00_MASTER_PROJECT_PLAN.md`
- `01_CHATGPT_PROJECT_OPERATING_INSTRUCTIONS.md`
- `04_MASTER_CHECKLIST.md`
- `docs/REQUIREMENTS.md`
- `docs/MICROARCHITECTURE.md`
- `docs/VERIFICATION_PLAN.md`
- `docs/FORMAL.md`
- `docs/DECISIONS.md`
- `docs/PROJECT_STATE.md`
- `docs/EVIDENCE_INDEX.md`
- `tasks/WIRE-006.md`
- `results/processed/WIRE-006-specification-package.md`

Prohibited work:
- Application RTL, Python, C++, tests, formal harnesses, synthesis, P&R, or toolchain changes.
- Re-auditing WIRE-001 through WIRE-005.
- Changing protocol, toolchain, or WIRE-005 target decisions silently.
- Authorizing Architecture B.

Acceptance criteria:
- Authority hierarchy and phase plan are explicit.
- Normative requirements have stable identifiers and are traceable to planned verification.
- Ingress, protocol, Mold recovery, ITCH subset, bounded book, decision, normalized event, Architecture A, latency, throughput, and CDC sequencing are specified.
- Architecture B remains unauthorized.
- Formal assumptions/evidence discipline and implementation evidence rules are explicit.
- Hostile consistency review is recorded.
- No implementation or functional evidence is claimed.
- Project state and EVID-006 are updated; Gate 0 remains open.

Evidence requirements:
- The seven authoritative documents.
- `results/processed/WIRE-006-specification-package.md`.
- Any new decisions in `docs/DECISIONS.md`.

Stop conditions:
- A previously frozen protocol, toolchain, or implementation-target decision conflicts with this task.
- Specification cannot be made internally consistent without changing frozen scope.
- The task would require implementation or verification execution.

Completion report:
Report repository state, package files, frozen functional/microarchitectural contract, traceability counts, new decisions, hostile-review result, evidence, unproven claims, Gate 0 status, and WIRE-007 as next task.
