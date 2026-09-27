Task ID: WIRE-003
Phase: Phase 0 — Bootstrap
Known-good starting commit: 1b8dc248c185b9c1f8354eafc258bb3054b8e0c0

Objective: audit and pin third-party repositories as provenance/reference sources without incorporating source code.

Mandatory repositories:
- alexforencich/verilog-ethernet
- alexforencich/cocotbext-eth
- corundum/corundum
- fpganinja/taxi
- tmlee06/Itch-Parser
- namangoyal-work/fpga-tick-to-trade
- pulp-platform/common_cells

Allowed files:
- tasks/WIRE-003.md
- docs/THIRD_PARTY_MANIFEST.md
- THIRD_PARTY_NOTICES.md
- docs/DECISIONS.md only for a genuine provenance policy decision
- results/raw/third_party/*
- results/processed/WIRE-003-third-party-audit.md
- docs/PROJECT_STATE.md
- docs/EVIDENCE_INDEX.md

Prohibited work:
- RTL, models, tests, formal properties, synthesis, P&R, and C++.
- Copying or vendoring third-party source.
- Git submodules, package installation, forks, or upstream modification.
- Weakening the core-originality rule.

Acceptance criteria:
- Verify the clean repository identity and starting commit.
- Inspect all seven upstreams at immutable full commit SHAs.
- Record default branch, commit date, repository description, licence file, licence hash, and relevant SPDX evidence.
- Verify verilog-ethernet deprecation/successor information and Taxi licence wording.
- Assess test-only, reference-only, direct-overlap, and CDC-benchmark classifications.
- Create the manifest, raw provenance evidence, processed report, notices update, state update, and EVID-003 entry.
- Confirm no source code, submodule, package, or core dependency was added.

Evidence requirements:
- docs/THIRD_PARTY_MANIFEST.md
- results/raw/third_party/repository_heads.txt
- results/raw/third_party/repository_metadata.txt
- results/raw/third_party/license_sha256s.txt
- results/raw/third_party/audit_commands.txt
- results/processed/WIRE-003-third-party-audit.md

Stop conditions:
- Repository identity or clean baseline differs from the verified starting state.
- Third-party source is already present with unknown provenance.
- Licence or source scope cannot be characterized without a legal or technical assumption.
- A proposed reuse would weaken the originality policy.

Completion report:
- Report repository state, all upstream pins/licences/classifications, dependency result, evidence paths, conflicts, unproven claims, and next task.
