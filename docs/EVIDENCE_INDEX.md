# Evidence Index

No functional design evidence exists yet.

| Evidence ID | Phase | Claim / purpose | Status | Source |
|---|---|---|---|---|
| EVID-000 | Phase 0 | Repository scaffold created | Complete — scaffold commit `999e04fbbd36db9c7556187876551f4b40833dd3` | tasks/WIRE-000.md; results/processed/WIRE-000-bootstrap.md |
| EVID-001 | Phase 0 | RTL-to-Pixels workflow/style audit completed | Complete — audit commit `8d2a5cc41abb0913c6069d7333989a70a0133d87` | tasks/WIRE-001.md; results/processed/reference_workflow_audit.md |
| EVID-002 | Phase 0 | External protocol source basis and MVP restrictions locked | Complete — source-lock commit `8af65aa` | tasks/WIRE-002.md; docs/SPEC_SOURCES.md; results/processed/WIRE-002-protocol-spec-lock.md |
| EVID-003 | Phase 0 | Third-party provenance audit, upstream pins, licence review, and reuse classification | Complete — audit commit `54e6aac` | tasks/WIRE-003.md; docs/THIRD_PARTY_MANIFEST.md; results/processed/WIRE-003-third-party-audit.md |
| EVID-004 | Phase 0 | Native Apple Silicon open-source toolchain qualification on trivial smoke design | Complete — smoke commit `89e2841` | tasks/WIRE-004.md; results/processed/toolchain_smoke.md; results/raw/toolchain/ |
| EVID-005 | Phase 0 | Canonical FPGA implementation target and timing objective frozen; exact target validated with trivial smoke P&R | Complete — target-freeze commit `c4ba1964049b6c104fbc80a1c8991a7476c51b16` | tasks/WIRE-005.md; docs/IMPLEMENTATION_TARGET.md; results/processed/WIRE-005-implementation-target.md; results/raw/implementation_target/ |
| EVID-006 | Phase 0 | Authoritative Wire-to-Decision project specification package created and internally consistency-reviewed | Complete — specification commit `a6ddb1f36ec945b8506e95a5c4935d1776806bbd` | 00_MASTER_PROJECT_PLAN.md; 01_CHATGPT_PROJECT_OPERATING_INSTRUCTIONS.md; 04_MASTER_CHECKLIST.md; docs/REQUIREMENTS.md; docs/MICROARCHITECTURE.md; docs/VERIFICATION_PLAN.md; docs/FORMAL.md; results/processed/WIRE-006-specification-package.md |

## Evidence classification

Allowed classifications:

- specified
- assumed
- hypothesised
- reference-model verified
- RTL-simulated
- formally checked under documented assumptions
- synthesised
- placed/routed
- timing-clean
- derived
- physically measured

Do not promote an item to a stronger classification without corresponding evidence.
