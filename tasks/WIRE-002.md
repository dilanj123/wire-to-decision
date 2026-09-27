Task ID: WIRE-002
Phase: Phase 0 — Bootstrap
Known-good starting commit: 2417ae8f338e6ee2c4df88be62b927c7f5a95bac

Objective: lock the authoritative external protocol sources and the proposed MVP protocol restrictions.

Authoritative external sources:
- RFC 894, RFC 791, RFC 768, RFC Editor.
- Nasdaq MoldUDP64 Protocol Specification V 1.00, current official artifact.
- Nasdaq TotalView-ITCH 5.0, current official artifact and current Nasdaq linking notice.

Allowed files:
- tasks/WIRE-002.md
- docs/SPEC_SOURCES.md
- results/raw/spec_sources/*
- results/processed/WIRE-002-protocol-spec-lock.md
- docs/PROJECT_STATE.md
- docs/EVIDENCE_INDEX.md
- docs/DECISIONS.md only if a genuine source-backed process/specification decision is required.

Prohibited work:
- RTL, reference models, tests, formal properties, synthesis, P&R, and C++.
- Full requirements, microarchitecture, verification, or formal-plan authoring.
- Copying or committing source PDFs.
- Expanding the MVP protocol scope.

Acceptance criteria:
- Verify the clean repository identity and starting commit.
- Read and fingerprint the required official sources and inspect applicable errata/updates.
- Record exact source metadata and any Nasdaq publication/revision discrepancy.
- Validate the Ethernet, IPv4, UDP, MoldUDP64, and ITCH MVP profile.
- Record source requirements separately from project restrictions and validation rules.
- Create processed evidence, update project state and evidence index, and leave a clean tree.

Required evidence:
- docs/SPEC_SOURCES.md
- results/raw/spec_sources/source_metadata.txt
- results/raw/spec_sources/sha256sums.txt
- results/raw/spec_sources/retrieval_notes.txt
- results/processed/WIRE-002-protocol-spec-lock.md

Stop conditions:
- Repository identity or clean baseline differs from the verified starting state.
- An authoritative source contradicts the current Wire-to-Decision definition.
- A requested conclusion requires silently expanding project scope.

Completion report:
- Report repository state, sources and fingerprints, locked findings, discrepancies, evidence paths, conflicts, remaining unproven claims, and next task.
