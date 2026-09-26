# WIRE-001 — RTL-to-Pixels Reference Workflow Audit

Task ID: WIRE-001

Phase:
Phase 0 — Bootstrap

Known-good starting commit:
9fbd24ec0b9fe6cd32f09312c1ee6905070755aa

Objective:
Audit RTL-to-Pixels as a workflow/style reference and record applicable process lessons for Wire-to-Decision.

Allowed modifications:

- `tasks/WIRE-001.md`
- `results/processed/reference_workflow_audit.md`
- `docs/PROJECT_STATE.md`
- `docs/EVIDENCE_INDEX.md`
- `docs/DECISIONS.md` only for genuine Wire-to-Decision process decisions resulting from the audit

Prohibited:

- application RTL;
- Python reference-model implementation;
- C++ implementation;
- formal properties;
- synthesis/P&R work;
- modification of reference repositories;
- copying Sobel technical requirements;
- copying third-party RTL.

## Acceptance criteria

- Verify the Wire-to-Decision starting commit and clean working tree.
- Verify the RTL-to-Pixels repository state read-only.
- Read all five mandatory RTL-to-Pixels planning files completely.
- Inspect the implemented RTL-to-Pixels process, state, evidence, formal, implementation, reuse, and reproducibility documents.
- Create a source-grounded workflow audit with explicit source-derived, inference, and recommendation distinctions.
- Complete an adoption table for Wire-to-Decision.
- Record supported workflow weaknesses and later-project improvements.
- Update Wire-to-Decision state and evidence index only for the audit completion.
- Add no application RTL or functional/tool result claims.

## Evidence requirements

- Exact source paths and read status.
- RTL-to-Pixels Git branch, commit, remote, and clean status.
- Audit report at `results/processed/reference_workflow_audit.md`.
- Evidence-index entry identifying the audit commit and report.
- Final clean Git status and commit history.

## Completion boundary

This task establishes process/reference-audit evidence only. It does not execute WIRE-002 and does not establish protocol, model, RTL, simulation, formal, synthesis, P&R, timing, latency, throughput, or CDC results.
