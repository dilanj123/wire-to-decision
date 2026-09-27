Task ID: WIRE-011
Phase: Phase 1 — Python reference model
Starting known-good commit: 0d69fe2a31ceae133ea045ec642a2dcc5d5a2eaf
Protected Gate-0 tag: kg-g0-env -> 06f5643a940ac2c6fcfab0e377169b48ce700107

Objectives:
1. Implement and unit-test the bounded 512-set x 2-way Python order-state
   model with checked 48-bit bid/ask aggregates, consuming NormalizedEvent.
2. Publish the canonical repository as public dilanj123/wire-to-decision when
   GitHub authentication permits, without rewriting local history or moving
   kg-g0-env.

Authority inputs:
docs/REQUIREMENTS.md, docs/MICROARCHITECTURE.md, docs/FORMAL.md,
docs/VERIFICATION_PLAN.md, docs/DECISIONS.md, WIRE-008/009/010 evidence, and
the existing canonical Python types.

Allowed modifications:
model/python/wire_to_decision/*, model/python/tests/*, tasks/WIRE-011.md,
results/raw/reference_model/*, results/processed/WIRE-011-book-model.md,
docs/PROJECT_STATE.md, docs/EVIDENCE_INDEX.md, and narrowly required
repository-publication records.

Prohibited work:
Decision-threshold or risk-budget logic, RTL, C++, protocol parser changes,
third-party dependencies, history rewriting, Gate-0 tag changes, and blind
GitHub mirror pushes.

Test requirements:
Retain all 41 prior tests. Add bounded-store, WIRE-D006 collision, deterministic
way selection, ADD/E/C/X/D/U, aggregate, atomic replacement, fail-closed,
re-arm, and decoder-to-book integration tests.

GitHub publication procedure:
Audit tracked files for secrets/private artifacts, check `gh` authentication,
inspect the target repository, create it public only if authenticated and
absent, push main and kg-g0-env explicitly, and verify local/remote identity.
If authentication fails, keep engineering work local and report publication as
blocked; do not invent a remote.

Acceptance criteria:
The bounded store and 48-bit aggregates reproduce frozen mutation semantics,
never evict, fail closed on integrity/capacity errors, and reset explicitly.
GitHub publication is reported independently and cannot strengthen functional
evidence.

Evidence requirements:
Record qualified-Python compile/import/tests, test inventory, safety audit,
and GitHub status under results/raw/. Create the processed WIRE-011 report and
EVID-011 with narrow Python-unit-tested wording.

Stop conditions:
Stop if authoritative order-state/U/aggregate/recovery semantics conflict or
if public-repository safety audit finds a genuine secret/private artifact.

Completion report:
Report repository and GitHub state, bounded store, mutations, failures,
aggregates, tests, traceability, evidence, unproven behavior, conflicts,
specification changes, gate status, and WIRE-012 as next task.
