# Wire-to-Decision — Project Operating Instructions

## Authority

Use the authority order in `00_MASTER_PROJECT_PLAN.md`. Supporting source records provide provenance but do not silently override normative requirements. If a contradiction is found, stop and report it.

## ChatGPT/Codex division

ChatGPT is responsible for planning, specification, review, reasoning, task preparation, and evidence interpretation. Codex/local execution is responsible for file inspection, narrowly scoped patches, tool execution, Git operations, and evidence generation. Both must preserve the repository contract and distinguish source-derived facts, assumptions, hypotheses, and measured results.

## Context and token discipline

For ordinary tasks, read only:

- `docs/PROJECT_STATE.md`;
- the relevant authoritative section;
- the active `tasks/WIRE-xxx.md`;
- changed source files;
- processed evidence.

Reload the full master plan only when changing specifications, resolving a conflict, transitioning a major gate, or performing an audit. Raw logs remain in `results/raw/`; summaries belong in `results/processed/` and should link to exact commands and source files without copying large logs into context.

## Narrow-task discipline

Work only inside the active task's allowed files. Use the task's known-good starting commit, acceptance criteria, evidence requirements, and stop conditions. Do not broaden a task because an adjacent improvement is attractive. Do not implement Architecture B before explicit authorization from measured Architecture-A evidence.

## Evidence rules

Never claim `PASS`, zero mismatches, formal proof, synthesis success, timing closure, Fmax, latency, throughput, or resource figures without corresponding tool evidence. A requested timing constraint is not a timing result. A bounded local proof is not a whole-design proof. Use exact commands, versions, commits, seeds, assumptions, and limitations.

## Reproducibility

Record starting and ending commits, tool versions, target, commands, inputs, seeds, and raw/processed evidence. Preserve clean working trees at task completion. Do not rewrite historical task commits.

## Originality and third-party firewall

The mandatory parser, protocol sequencing, normalized events, order state, decision logic, CDC/FIFO, reset behaviour, formal properties, Python model, C++ checker, and project-specific tests remain original Wire-to-Decision work. Audited third-party sources remain reference-only or explicitly separated test-only candidates according to `docs/THIRD_PARTY_MANIFEST.md`. Licence permission does not override originality policy.

## Specification and implementation order

Specify → implement the simplest complete baseline → verify → synthesize/implement → measure. Do not import technical requirements from process-reference projects. Do not add PHY, MAC, PCIe, live recovery, multi-symbol state, BBO/price levels, or trading strategy unless a future authoritative task changes scope.

## Stop conditions

Stop and report for conflicting specifications, unexplained existing work, unknown provenance, an operation that would overwrite user work, or a required action outside the active task. Do not resolve conflicts silently.

## Completion language

Every completion report states what changed, evidence actually available, what remains unproven, conflicts/blockers, specification changes, and the next task. A task is complete only when its acceptance criteria are checked and its evidence is committed.
