Task ID: WIRE-008
Phase: Phase 1 — Python reference model
Starting known-good commit: 06f5643a940ac2c6fcfab0e377169b48ce700107
Protected Gate-0 tag: kg-g0-env -> 06f5643a940ac2c6fcfab0e377169b48ce700107

Objective:
Create the original project-owned Python reference-model skeleton and freeze
the canonical software data representations used by later model and RTL
verification work.

Authority inputs:
docs/REQUIREMENTS.md, docs/MICROARCHITECTURE.md, docs/DECISIONS.md,
docs/VERIFICATION_PLAN.md, docs/PROJECT_STATE.md, docs/EVIDENCE_INDEX.md,
and the Phase-1 boundary in 00_MASTER_PROJECT_PLAN.md.

Allowed files:
model/python/*, tasks/WIRE-008.md, results/raw/reference_model/*,
results/processed/WIRE-008-reference-model-skeleton.md,
docs/PROJECT_STATE.md, docs/EVIDENCE_INDEX.md, and a narrowly necessary
.gitignore change.

Prohibited work:
Complete protocol parsing, MoldUDP sequencing, ITCH decoding, order-store
mutation, aggregate updates, decision crossing logic, RTL, C++, formal
harnesses, tests beyond the canonical data primitives, and new dependencies.

Acceptance criteria:
The package imports, compiles, validates the frozen canonical data contracts,
implements the exact WIRE-D006 hash, and all standard-library unit tests pass.
No parser, book engine or decision engine is implemented.

Evidence requirements:
Retain concise environment, compile, import and unit-test logs under
results/raw/reference_model/ and a processed WIRE-008 report. Add EVID-008
with narrow Python-unit-tested-primitives wording.

Stop conditions:
Stop and report if an authority contradiction, missing frozen contract, or
need to change functional specification is discovered.

Completion report:
Report repository/baseline, files and commits, package/data model, validation,
hash vectors, test count/result, evidence, unproven behaviour, conflicts,
specification changes and the next task.
