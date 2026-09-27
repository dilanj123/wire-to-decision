Task ID: WIRE-007
Phase: Phase 0 — Bootstrap closure
Starting known-good commit: 43189dd01442af9cfc12a6cd169b9fb0f4223712

Objective:
Demonstrate repository, specification, evidence, external-toolchain, smoke-flow, and implementation-target reproducibility from a final fresh local Git clone.

Clone strategy:
Use an existing configured remote if one is positively identified. This repository currently has no remote, so use Git clone semantics from the canonical local repository into a unique disposable directory outside the repository.

Allowed modifications:
- tasks/WIRE-007.md
- tools/repro/*
- tools/env/* only for narrow reproducibility corrections
- tools/smoke/* only for demonstrated reproducibility corrections
- README.md only for Phase-0 navigation
- .gitignore only for narrow generated-artifact hygiene
- results/raw/reproducibility/*
- results/processed/WIRE-007-clean-clone.md
- docs/PROJECT_STATE.md
- docs/EVIDENCE_INDEX.md
- 04_MASTER_CHECKLIST.md
- docs/DECISIONS.md only if genuinely required

Prohibited work:
- Application RTL, Python model, C++, application tests, formal properties, synthesis/P&R, or architecture logic.
- Rewriting WIRE-000 through WIRE-006 history.
- Installing or committing the OSS CAD Suite.
- Adding a public remote or guessing a remote URL.
- Making protocol, microarchitecture, toolchain, or FPGA-target changes.

Clean-clone procedure:
1. Inspect remote state and clone source.
2. Clone the final candidate commit outside the canonical repository.
3. Audit tracked authority, task, evidence, and structure files.
4. Activate the explicit external OSS CAD Suite contract.
5. Run the repository smoke and exact WIRE-005 target validation.
6. Confirm generated outputs are disposable/ignored and the clone remains clean.
7. Record concise raw and processed evidence.

Acceptance criteria:
- Final tested clone corresponds to the final executable candidate commit.
- Required authority/evidence files and directory structure are present.
- No reference-project runtime dependency exists.
- External suite path handling is explicit and strict.
- Toolchain smoke and exact WIRE-005 target validation pass from the clone.
- EVID-000 through EVID-007, decision IDs, and 71 requirement IDs are traceable.
- No application implementation or functional claim is added.
- Gate 0 closes only after all mandatory checks pass.

Evidence requirements:
- results/raw/reproducibility/clone_metadata.txt
- results/raw/reproducibility/tracked_file_audit.txt
- results/raw/reproducibility/tool_version_check.txt
- results/raw/reproducibility/smoke_run.log
- results/raw/reproducibility/target_check.log
- results/raw/reproducibility/git_status_after_smoke.txt
- results/raw/reproducibility/reproducibility_commands.txt
- results/processed/WIRE-007-clean-clone.md

Gate-0 closure conditions:
Repository/specification reproducibility, explicit toolchain contract, smoke PASS, target recognition, controlled Git tree, and structural evidence/decision traceability must all pass. This does not close any application correctness claim.

Tag policy:
Inspect for `kg-g0-env`. If no existing tag conflicts and repository authority permits, create one annotated tag on the final closure commit after the final evidence commit. Never move an existing tag.

Stop conditions:
- Unexpected starting repository state.
- Existing conflicting tag.
- Hidden runtime dependency on another project.
- Missing external suite or materially mismatched toolchain.
- Smoke/target validation failure.
- Any need to broaden into application implementation.

Completion report:
Report repository and clone state, each reproducibility capability, evidence, Gate-0 status/tag, remaining unproven application claims, problems fixed, specification changes, and the next Phase-1 task.
