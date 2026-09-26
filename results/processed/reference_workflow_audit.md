# RTL-to-Pixels Reference Workflow Audit

Audit scope: workflow and evidence practice only. No Sobel arithmetic, image-processing interface, implementation target, performance target, or RTL design requirement is imported into Wire-to-Decision.

## A. Sources audited

### Mandatory planning sources

| Source | Absolute path | Role | Read completely |
|---|---|---|---|
| `00_MASTER_PROJECT_PLAN.md` | `/Users/Dilan/Downloads/00_MASTER_PROJECT_PLAN.md` | Master contract, authority order, phases/gates, evidence policy, reproducibility and experiment method | yes |
| `01_CHATGPT_PROJECT_OPERATING_INSTRUCTIONS.md` | `/Users/Dilan/Downloads/01_CHATGPT_PROJECT_OPERATING_INSTRUCTIONS.md` | Fresh-project reading order, task format, responsibility split, review/debug rules, state/evidence maintenance | yes |
| `02_PHASE0_BOOTSTRAP_TASK.md` | `/Users/Dilan/Downloads/02_PHASE0_BOOTSTRAP_TASK.md` | Bootstrap actions, tool inventory, doctor target, initial evidence and prohibitions | yes |
| `04_MASTER_CHECKLIST.md` | `/Users/Dilan/Downloads/04_MASTER_CHECKLIST.md` | Gate-by-gate completion checklist | yes |
| `MASTER_CHATGPT_HANDOFF_PROMPT.md` | `/Users/Dilan/Downloads/MASTER_CHATGPT_HANDOFF_PROMPT.md` | Project handoff, proposed repository/process structure, AI responsibility split, gate narrative | yes |

The duplicate handoff file `/Users/Dilan/Downloads/from-rtl-to-pixels-handoff/MASTER_CHATGPT_HANDOFF_PROMPT.md` was compared with `cmp` and was byte-identical; it was not separately analysed.

### Implemented reference repository

| Field | Observed value |
|---|---|
| Path | `/Users/Dilan/Projects/from-rtl-to-pixels` |
| Branch | `main` |
| HEAD | `ad35514c990f6e1c9eb9fa18aee9d906f9df7721` |
| Working tree | clean; `git status --short` produced no entries |
| Remote | `origin` = `https://github.com/dilanj123/from-rtl-to-pixels.git` for fetch and push |
| Process documents inspected | `README.md`, `docs/PROJECT_STATE.md`, `docs/EVIDENCE_INDEX.md`, `docs/REQUIREMENTS.md`, `docs/THIRD_PARTY_MANIFEST.md`, `THIRD_PARTY_NOTICES.md`, plus formal/timing/comparison/decision/limitation documents and relevant scripts/logs |
| Organisation inspected | `formal/`, `reports/`, `results/raw/`, `results/processed/`, `scripts/`, `tb/` |

### Secondary process references

Targeted process inspection only; no technical requirements were imported.

- `/Users/Dilan/Projects/fabric-under-pressure`: `AGENTS.md`, `docs/PROJECT_STATE.md`, `docs/EVIDENCE_INDEX.md`, `docs/DECISIONS.md`, and planning/operating-instruction excerpts. Useful mechanisms include stable repository behaviour, explicit raw/processed evidence, narrow tasks, and compact state.
- `/Users/Dilan/Projects/Power-to-GDS`: `00_MASTER_PROJECT_PLAN.md`, `01_CHATGPT_PROJECT_OPERATING_INSTRUCTIONS.md`, `docs/PROJECT_STATE.md`, and `docs/EVIDENCE_INDEX.md`. Useful mechanisms include explicit evidence-state vocabulary, backend decision gates, pinned configuration control, and stop-on-unproven rules.

## B. RTL-to-Pixels authority/document hierarchy

### Source-derived

The reference master plan defines this order:

1. master project plan;
2. `docs/REQUIREMENTS.md`;
3. `docs/MICROARCHITECTURE.md`;
4. `docs/VERIFICATION_PLAN.md`;
5. `docs/DECISIONS.md`;
6. `docs/PROJECT_STATE.md`;
7. RTL/test/build files;
8. earlier planning/handoff notes.

The plan requires contradictions to be identified, resolved in the authoritative specification, recorded in the decision log, and reflected in tests.

The implemented repository uses the following practical roles:

- master plan: original contract and phase/gate narrative;
- requirements: frozen behavioural contract;
- microarchitecture: implementation decomposition and interface detail;
- verification plan: requirement-to-test/formal traceability;
- decisions: rationale and experiment outcomes;
- project state: current milestone/status summary;
- evidence index: claim-to-artifact map;
- checklist: gate closure inventory;
- handoff prompt: context and working method for a fresh ChatGPT project.

### Inference

The hierarchy was useful because it separates normative behaviour from current status and from implementation files. The implemented repository's README, state file, evidence index, and decision/formal/timing documents show that the structure survived into the advanced project rather than remaining only in the planning package.

### Wire-to-Decision recommendation

Retain the hierarchy, but make the new project's authority order explicit in one small repository document or task convention. Keep `PROJECT_STATE.md` and `EVIDENCE_INDEX.md` as navigational summaries, never as substitutes for requirements or tool output.

## C. Phase and gate methodology

### Source-derived

The reference plan defines a sequence from Phase 0 bootstrap, Gate-1 contract freeze, independent reference model, primitive RTL, integration, deep regression, selected formal, baseline implementation, bottleneck review, controlled Architecture-B change, A/B comparison, debug case studies, publication, and optional hardware. Gates are evidence states, not activity labels. The checklist explicitly requires environment evidence, architecture documents, MVP functional evidence, deep regression, formal/implementation comparison, and clean-clone/publication evidence.

The implemented history contains narrow milestone commits for bootstrap, Gate 1, Gate 2, Gate 3, formal bootstrap/proofs, Architecture A implementation, bottleneck review, Architecture B, A/B comparison, debug studies, release audit, and clean-clone/tooling repairs.

### Inference

The strongest transferable feature is the admission gate before optimization: the later architecture was introduced only after a baseline, a measured bottleneck, and a written hypothesis. The commit sequence also shows that process corrections were retained rather than hidden: the timing-search control-flow defect and critical-path-domain classification issue are preserved in evidence/log history.

### Wire-to-Decision recommendation

Adopt phase/gate progression and require each gate transition to name its evidence and remaining unproven claims. For Wire-to-Decision, keep Phase 0 process work separate from protocol specification and do not allow architecture alternatives before a measured baseline exists.

## D. ChatGPT/Codex division

### Source-derived

The operating instructions assign ChatGPT most planning, specification, architecture, test/formal drafting, review, interpretation, and documentation work. Codex/local execution is reserved for actual filesystem/repository inspection, patches, tool execution, Git operations, and evidence generation. The required local-task format names one objective, authoritative inputs, allowed files, tests, commands, acceptance criteria, and returned evidence.

### Inference

This split is useful because it makes local execution an evidence boundary: claims should originate from commands and artifacts, while planning remains reviewable before mutation. It is less clear in the completed RTL-to-Pixels repository how every historical local task was represented, because the final repository has no `tasks/` directory and no root `AGENTS.md`.

### Wire-to-Decision recommendation

Retain the split and enforce it with active task files in `tasks/`. The local task must state exactly what may change and must return status, diff, commands, exit codes, and evidence paths. ChatGPT/local execution should not silently widen scope.

## E. Narrow-task methodology

### Source-derived

The planning instructions require narrow, observable local tasks with known-good commits, explicit allowed/disallowed files, acceptance criteria, and evidence to return. The reference repository history shows many focused commits, including individual primitive/formal/implementation/debug milestones. The RTL-to-Pixels repository README and evidence index also preserve the distinction between targeted formal claims, full regression claims, and implementation claims.

### Inference

The task method appears to have supported incremental recovery from real issues: logs identify a timing-search bug, a critical-path parser classification issue, and formal induction wiring weakness. However, because task files are not present in the final repository, scope enforcement cannot be audited from the repository alone.

### Wire-to-Decision recommendation

Keep task files, known-good starting commits, stop conditions, and two-level acceptance checks: focused evidence plus relevant regression. Require an explicit “no technical result established” section for documentation-only tasks.

## F. Evidence architecture

### Source-derived

The reference repository separates preserved execution artifacts under `results/raw/` from reviewed outputs under `results/processed/`. Raw artifacts include bootstrap logs, simulation/formal logs, synthesis/P&R reports, frequency searches, debug fail/pass logs, publication checks, and clean-clone validation. Processed artifacts include comparison images and selected result images. `docs/EVIDENCE_INDEX.md` maps claims to logs/reports/images and assigns classifications such as reference-model verified, RTL simulation verified, formal property passed under assumptions, synthesised, placed/routed timing evidence, derived, and clean-checkout reproduction verified.

### Inference

The split is useful and scales better than putting raw command output in state documents. The evidence index is the main navigation layer. However, the raw directory is much richer than the processed directory: `reports/reference/` is only a placeholder, and many raw logs are linked directly from the index without a small processed summary per experiment. A fresh reviewer can navigate the evidence, but the audit burden remains high.

### Wire-to-Decision recommendation

Adopt `results/raw/` and `results/processed/`. Require each meaningful experiment to produce one concise processed summary containing commit, command, conditions, classification, result, limitations, and raw-artifact links. Keep raw logs immutable and do not rewrite historical results into current-state prose.

## G. `PROJECT_STATE.md`

### Source-derived

The reference state file is 85 lines and records Gate 5 status, retained architectures, verification/formal/implementation status, major evidence paths, release status, known limitations, and links to history/evidence/decisions/formal records. It is materially smaller than the master plan and is intended as a current-state summary.

### Inference

The state file is useful as a fresh-chat bootstrap because it answers current status, strongest evidence, limitations, and where to look next. It also duplicates some headline numbers from the README and evidence index. The duplication is manageable at the observed size, but it creates a maintenance risk when results or commit references change.

### Wire-to-Decision recommendation

Keep Wire-to-Decision's deliberately small state file. Include only phase/gate, known-good commit, architecture status, regression/formal/implementation status, latest evidence, open issues/decisions, bottleneck, and next task. Link outward rather than repeating result tables.

## H. Requirements and verification traceability

### Source-derived

The reference requirements file freezes behavioural requirements and the verification plan defines a requirement-to-test/formal/evidence matrix. The evidence index includes a requirements traceability section linking arithmetic, transfers/metadata/drain, reset, configuration, formal boundaries, and frozen architecture to evidence. The raw logs preserve focused tests for primitives, geometry, streaming, reset, configuration, and complete images.

### Inference

This provides a credible path from requirement to test to evidence, but some traceability is area-level rather than one unique requirement ID per claim. The evidence index often points to groups of logs, so reconstructing the exact test-to-requirement path can still require reading multiple files.

### Wire-to-Decision recommendation

Adopt stable requirement IDs and a compact matrix with columns for requirement, implementation location, test/property, raw evidence, processed summary, and classification. Do not import any reference technical requirements; apply the mechanism later to Wire-to-Decision protocol requirements.

## I. Formal verification workflow

### Source-derived

The reference formal document states that claims are local, explicit, reproducible, and assumption-bounded. It records property, assumptions, engine, mode/depth, result, cover/vacuity considerations, limitations, and evidence paths. The evidence index distinguishes targeted property passes from a whole-accelerator claim. The formal toolchain smoke log explicitly says it is environment evidence only, not production-design proof. A later integration proof records that an induction weakness was repaired by adding bridge assertions without changing production RTL or adding an environmental assumption.

### Inference

This is one of the strongest process elements: it prevents local proof results from being marketed as whole-design verification and preserves proof-debug history. The remaining limitation is that a reviewer must consult separate formal records and raw logs to understand the full boundary.

### Wire-to-Decision recommendation

Adopt per-property evidence records with assumptions, scope, engine/depth, cover/vacuity review, limitations, and raw log links. Use “formally checked under documented assumptions” rather than “formally verified” for local properties.

## J. Implementation / timing methodology

### Source-derived

The reference plan freezes device/package/speed, tool versions, top wrapper, dimensions, options, constraints, seed policy, and accounting boundary for A/B comparison. The implementation evidence uses a frequency search rather than one arbitrary timing run. The comparison log records the tested clean/fail brackets, tool versions, seed, resource counts, path data, latency, initiation interval, derived throughput, and decision. A bottleneck review separates synchronous clock-to-clock timing from unconstrained asynchronous input-to-clock paths before selecting the critical path.

### Inference

The method is strong because it makes the comparison auditable and records both the initial defect and its repair. It also correctly separates derived throughput from physical measurement. The single-seed and coarse frequency grid remain limitations explicitly acknowledged by the repository.

### Wire-to-Decision recommendation

Adopt controlled-experiment records and the retain/modify/reject/inconclusive decision vocabulary. Require a written bottleneck before any microarchitecture alternative. Keep timing, throughput, and physical measurement classifications separate.

## K. Third-party/reuse workflow

### Source-derived

The reference plan requires upstream project, URL, source path, commit/tag, copyright, licence, modification status, and local path for every copied/derived file. The implemented manifest and notices record the one public-domain image, its upstream location, author/status, local hash, purpose, and generated derivatives; they also identify the project-owned generated image. The README distinguishes original project work from the external media.

### Inference

The provenance rule is useful even when reuse is limited because it makes the original/third-party boundary explicit. The reference project demonstrates media provenance as well as source-code provenance.

### Wire-to-Decision recommendation

Adopt the manifest/notices boundary before any reuse. Record upstream immutable identity, licence/status, local path, modifications, and purpose. Do not copy reference-project code or technical documents into Wire-to-Decision during workflow auditing.

## L. Reproducibility

### Source-derived

The reference bootstrap records host/OS/architecture, executable paths and versions, missing tools, and external toolchain location. The repository provides Make targets, scripts, pinned Python dependencies, CI, raw logs, and a clean-clone validation script. The clean-clone log records environment creation, package versions, tool versions, commands, and a validated commit. The project distinguishes local virtual-device results from physical FPGA measurement.

### Inference

This is a useful reproducibility spine, but the inspected clean-clone log validates `f9598f3a92a998a416c08ca36653ed8bf73bf5d8`, while the inspected repository HEAD is `ad35514c990f6e1c9eb9fa18aee9d906f9df7721`. The repository notes that a final-commit run is recorded elsewhere in release history, but the mismatch means a reviewer must perform an extra reconciliation step. This is a supported workflow weakness, not a claim that the final commit is invalid.

### Wire-to-Decision recommendation

Adopt clean-clone validation, but require the final evidence report to name the exact validated commit and require that it equal the release/known-good commit, or explicitly label the validation as candidate/earlier-commit evidence. Pin project dependencies and record commands without assuming that a current checkout reproduces an older log.

## M. Problems encountered / workflow weaknesses

The following are supported by inspected files/history rather than assumed:

1. **Task enforcement is not visible in the final reference repository.** The planning package specifies narrow Codex task files, but the final repository has no `tasks/` directory and no root `AGENTS.md`. This weakens repository-local enforcement and fresh-review traceability.
2. **Clean-clone evidence is commit-sensitive.** The preserved clean-clone log names an earlier commit than the inspected HEAD. The relationship is documented enough to investigate, but not as direct as a single current-HEAD validation record.
3. **Processed summaries are sparse relative to raw evidence.** The raw log set is extensive, while processed output is mostly images and the evidence index. A reviewer often has to open raw logs to reconstruct command/condition/result context.
4. **Tooling defects required correction.** The timing-comparison log preserves a search-control-flow repair, and the bottleneck review records correction of an async-versus-synchronous path classification issue. This is positive evidence of repair discipline, but it shows that result parsers and experiment scripts need their own focused checks.
5. **State/README/evidence duplication exists.** Headline implementation numbers appear in multiple documents. The duplication improves presentation but increases stale-copy risk.
6. **Some evidence scopes remain deliberately narrow.** The formal and timing documents explicitly limit claims by property, dimensions, seed, or virtual target. This is a strength in claim discipline, but it requires continued boundary labeling whenever summaries are updated.

No inspected file supports claims that the workflow was perfect or that a particular process step alone caused the final engineering result.

## N. Improvements observed in later projects

| Reference project | Observed mechanism | Why it is better | Should Wire-to-Decision adopt it |
|---|---|---|---|
| Fabric Under Pressure | `AGENTS.md` states authority order, claim discipline, original-work boundaries, narrow tasks, raw/processed evidence, frozen comparison variables, and stop rules | Repository-local behaviour is visible and enforceable without loading the full planning package | YES |
| Fabric Under Pressure | `docs/PROJECT_STATE.md` is a compact dated state with evidence-now-exists, still-unproven, risks, specification changes, and next smallest task | Better fresh-chat bootstrap and clearer separation of proven from unproven | YES |
| Fabric Under Pressure | `docs/EVIDENCE_INDEX.md` uses stable IDs/classes/statuses and explicitly says no functional correctness/performance evidence exists during early phases | Stronger claim navigation and less ambiguity about gate-level evidence | YES |
| Power-to-GDS | Evidence-state vocabulary distinguishes specified, researched, execution-qualified, simulated, formally checked, synthesised, routed, timing-clean, derived, and physical states | Prevents accidental promotion of a weaker evidence class into a stronger claim | ADOPT WITH MODIFICATION |
| Power-to-GDS | Pinned configuration-control freeze and backend decision tree require rerunning qualification after changes | Makes environment changes auditable and avoids incomparable experiment results | ADOPT WITH MODIFICATION |
| Power-to-GDS | Explicit “UNPROVEN” language and stop-on-conflict rules | Makes blockers and unresolved capability gaps visible | YES |

These are process observations only; no AXI or ASIC requirements are imported.

## O. Wire-to-Decision adoption table

| Workflow mechanism | Source | Adopt? | Wire-to-Decision treatment |
|---|---|---:|---|
| authority hierarchy | RTL-to-Pixels plan; later AGENTS files | ADOPT | Keep master contract above requirements/state/code and stop on conflict. |
| known-good commits | RTL-to-Pixels plan/history | ADOPT | Every task names its starting commit; final claims name the exact evidence commit. |
| narrow task files | RTL-to-Pixels operating instructions; Fabric AGENTS | ADOPT | Active `tasks/WIRE-xxx.md` names allowed files, prohibitions, acceptance, evidence, and stop conditions. |
| gate checklist | RTL-to-Pixels checklist | ADOPT WITH MODIFICATION | Use small gate checklists and require evidence per item; do not duplicate large technical plans. |
| PROJECT_STATE | RTL-to-Pixels; improved in Fabric | ADOPT WITH MODIFICATION | Keep a small current-state file with proven/unproven, risks, decisions, bottleneck, and next task. |
| EVIDENCE_INDEX | RTL-to-Pixels; improved in Fabric | ADOPT WITH MODIFICATION | Use stable IDs, classification, exact commit, command, conditions, raw artifact, and processed summary. |
| raw/processed split | RTL-to-Pixels | ADOPT | Preserve raw logs; add one concise processed summary per meaningful experiment. |
| formal evidence format | RTL-to-Pixels `docs/FORMAL.md` | ADOPT | Record local property, assumptions, engine/depth, result, cover/vacuity, limitations, and log. |
| third-party manifest | RTL-to-Pixels | ADOPT | Require immutable upstream identity, licence/status, local path, modifications, and purpose before reuse. |
| clean-clone validation | RTL-to-Pixels; Power-to-GDS backend discipline | ADOPT WITH MODIFICATION | Validate the exact intended release/known-good commit and label older-commit evidence explicitly. |
| ChatGPT/Codex split | RTL-to-Pixels plan | ADOPT | ChatGPT prepares/reviews; local execution inspects, patches, runs, and records actual evidence. |
| requirements traceability | RTL-to-Pixels verification/evidence docs | ADOPT WITH MODIFICATION | Use stable IDs and direct requirement→implementation→test/property→evidence links. |
| architecture-experiment control | RTL-to-Pixels A/B method | ADOPT | Freeze variables, write a bottleneck hypothesis, change one mechanism, re-verify, re-measure, conclude. |
| context/token discipline | RTL-to-Pixels fresh-reading/task rules; Fabric compact state | ADOPT WITH MODIFICATION | Read authoritative files as required, but use compact state/index/task summaries for routine continuation. |

The classifications above are Wire-to-Decision process recommendations recorded by this audit, not technical-result claims.

## P. Conflicts with current Wire-to-Decision plan

### Source-derived comparison

The WIRE-000 repository already requires evidence-backed claims, narrow task scope, a small `PROJECT_STATE.md`, an `EVIDENCE_INDEX.md`, third-party controls, and a known-good commit. The audited reference workflow and later projects reinforce those mechanisms.

### Result

No material conflict with the current Wire-to-Decision bootstrap contract was found. The audit recommends additions in enforcement/detail, not a change to technical scope. In particular, the audit does not authorize protocol requirements, RTL, tool installation, Architecture B, or any other technical expansion.

## Q. Resulting process recommendations

1. Keep the active task file as the scope boundary for every implementation or audit task.
2. Require every task and evidence record to name the exact starting/ending commit and working-tree state.
3. Maintain a small state file; put detailed claims in the evidence index and processed evidence reports.
4. Preserve raw logs, but create concise processed summaries for meaningful experiments.
5. Use explicit evidence classifications and never promote a claim without matching output.
6. Require requirement IDs to connect specification, implementation, tests/properties, and evidence once technical work begins.
7. Treat formal results as local and assumption-bounded unless a broader claim is separately evidenced.
8. Freeze controlled-experiment variables and require a written bottleneck/hypothesis before architecture alternatives.
9. Validate clean clones at the exact intended known-good commit, with dependency/tool versions recorded.
10. Stop on conflicts, provenance gaps, or unexplained baseline changes rather than resolving them silently.

These recommendations are process-only. WIRE-001 does not establish any Wire-to-Decision protocol or implementation result.
