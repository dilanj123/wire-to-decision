# Evidence Index

Python-unit-tested reference-model evidence exists. Application RTL evidence exists for EVID-014 gearbox and EVID-015 common ingress-buffer/composition primitives; protocol-parser RTL evidence begins with WIRE-016.

| Evidence ID | Phase | Claim / purpose | Status | Source |
|---|---|---|---|---|
| EVID-000 | Phase 0 | Repository scaffold created | Complete — scaffold commit `999e04fbbd36db9c7556187876551f4b40833dd3` | tasks/WIRE-000.md; results/processed/WIRE-000-bootstrap.md |
| EVID-001 | Phase 0 | RTL-to-Pixels workflow/style audit completed | Complete — audit commit `8d2a5cc41abb0913c6069d7333989a70a0133d87` | tasks/WIRE-001.md; results/processed/reference_workflow_audit.md |
| EVID-002 | Phase 0 | External protocol source basis and MVP restrictions locked | Complete — source-lock commit `8af65aa` | tasks/WIRE-002.md; docs/SPEC_SOURCES.md; results/processed/WIRE-002-protocol-spec-lock.md |
| EVID-003 | Phase 0 | Third-party provenance audit, upstream pins, licence review, and reuse classification | Complete — audit commit `54e6aac` | tasks/WIRE-003.md; docs/THIRD_PARTY_MANIFEST.md; results/processed/WIRE-003-third-party-audit.md |
| EVID-004 | Phase 0 | Native Apple Silicon open-source toolchain qualification on trivial smoke design | Complete — smoke commit `89e2841` | tasks/WIRE-004.md; results/processed/toolchain_smoke.md; results/raw/toolchain/ |
| EVID-005 | Phase 0 | Canonical FPGA implementation target and timing objective frozen; exact target validated with trivial smoke P&R | Complete — target-freeze commit `c4ba1964049b6c104fbc80a1c8991a7476c51b16` | tasks/WIRE-005.md; docs/IMPLEMENTATION_TARGET.md; results/processed/WIRE-005-implementation-target.md; results/raw/implementation_target/ |
| EVID-006 | Phase 0 | Authoritative Wire-to-Decision project specification package created and internally consistency-reviewed | Complete — specification commit `a6ddb1f36ec945b8506e95a5c4935d1776806bbd` | 00_MASTER_PROJECT_PLAN.md; 01_CHATGPT_PROJECT_OPERATING_INSTRUCTIONS.md; 04_MASTER_CHECKLIST.md; docs/REQUIREMENTS.md; docs/MICROARCHITECTURE.md; docs/VERIFICATION_PLAN.md; docs/FORMAL.md; results/processed/WIRE-006-specification-package.md |
| EVID-007 | Phase 0 | Phase-0 repository/environment reproducibility from a clean clone | Complete — closure candidate `e9123ea24a6a3314441bec3617cdb5da559cb775` | tasks/WIRE-007.md; results/processed/WIRE-007-clean-clone.md; results/raw/reproducibility/ |
| EVID-008 | Phase 1 | Python canonical reference-model data representations, validation primitives and WIRE-D006 hash unit-tested against the frozen normalized-event contract | Complete — WIRE-008 correction | tasks/WIRE-008.md; results/processed/WIRE-008-reference-model-skeleton.md; results/raw/reference_model/ |
| EVID-009 | Phase 1 | Project-owned Python Ethernet II / IPv4 / UDP / MoldUDP64 framing and sequence model exercised by unit tests against the frozen Wire-to-Decision profile | Complete — WIRE-009 framing evidence | tasks/WIRE-009.md; results/processed/WIRE-009-framing-model.md; results/raw/reference_model/ |
| EVID-010 | Phase 1 | Project-owned Python decoder for the frozen TotalView-ITCH A/F/E/C/X/D/U subset, P non-mutating classification, tracked-instrument filtering and normalized-event mapping exercised by unit tests | Complete — WIRE-010 decoder evidence | tasks/WIRE-010.md; results/processed/WIRE-010-itch-decoder.md; results/raw/reference_model/ |
| EVID-011 | Phase 1 | Bounded 512-set × 2-way Python order-state model and 48-bit aggregate accounting exercised by unit tests against frozen mutation semantics | Complete — GitHub publication separately verified | tasks/WIRE-011.md; results/processed/WIRE-011-book-model.md; results/raw/reference_model/ |
| EVID-012 | Phase 1 | Python deterministic imbalance-crossing decision and risk-budget model exercised by unit tests against frozen decision requirements and bounded-order aggregates | Complete — PYTHON-UNIT-TESTED | tasks/WIRE-012.md; results/processed/WIRE-012-decision-model.md; results/raw/reference_model/ |
| EVID-013 | Phase 1 | Project-owned Python end-to-end reference oracle integrating framing, ITCH decoding, bounded order state, aggregates, deterministic decisions, fail-closed behavior, recovery, and late-suffix no-rollback | Complete — PYTHON-UNIT-TESTED | tasks/WIRE-013.md; results/processed/WIRE-013-end-to-end-oracle.md; results/raw/reference_model/ |
| EVID-014 | Phase 2 | Architecture-A 64-to-8 gearbox preserves legal beat byte order, accepted valid-byte conservation, and exact frame-final marker under ready/valid simulation; local safety properties are inductively checked and the independent public-interface correspondence is bounded-checked through depth 20 under documented assumptions | Complete — RTL-SIMULATED; FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS | tasks/WIRE-014.md; tasks/WIRE-014A.md; results/processed/WIRE-014-gearbox-rtl.md; results/raw/rtl/gearbox/ |
| EVID-015 | Phase 2 | Common two-entry synchronous ingress beat buffer preserves accepted `{data, keep, last}` ordering and ready/valid behavior under backpressure; buffer-to-gearbox composition preserves the framed byte stream | Complete — RTL-SIMULATED; FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS; public-interface correspondence bounded through depth 10 | tasks/WIRE-015.md; results/processed/WIRE-015-ingress-buffer-rtl.md; results/raw/rtl/ingress_buffer/ |
| EVID-016 | Phase 2 | Architecture-A Ethernet II byte parser accepts only IPv4 EtherType `0x0800`, strips the Ethernet header, preserves payload framing under backpressure, and distinguishes filtered from fatal Ethernet outcomes | Complete — RTL-SIMULATED; FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS; public-interface correspondence bounded through depth 40 | tasks/WIRE-016.md; results/processed/WIRE-016-ethernet-parser-rtl.md; results/raw/rtl/eth_parser/ |
| EVID-017 | Phase 2 | Architecture-A IPv4 fixed-profile stage validates and classifies IPv4 headers, strips the header, bounds payload by Total Length, suppresses padding, and integrates with the prior byte pipeline | RTL-SIMULATED; decomposed public-interface checks for classification, checksum, payload, Total-Length boundary, padding, truncation and restart FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS at recorded bounded depths; REQ-IP-007 remains unproven | tasks/WIRE-017.md; tasks/WIRE-017A.md; results/processed/WIRE-017-ipv4-parser-rtl.md; results/raw/rtl/ipv4_parser/ |
| EVID-018 | Phase 2 | Architecture-A UDP byte parser validates the fixed UDP header, exact UDP Length versus IPv4 payload boundary, configured destination port and zero-only checksum policy; strips the UDP header and preserves accepted payload ordering/final marking under backpressure | RTL-SIMULATED; named local properties FORMALLY CHECKED UNDER DOCUMENTED BOUNDED/FIXED-VECTOR SCOPES; downstream mutation protection remains unproven | tasks/WIRE-018.md; results/processed/WIRE-018-udp-parser-rtl.md; results/raw/rtl/udp_parser/ |

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
- Python-unit-tested primitives

Do not promote an item to a stronger classification without corresponding evidence.
