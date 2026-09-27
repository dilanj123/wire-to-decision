Task ID: WIRE-009
Phase: Phase 1 — Python reference model
Starting known-good commit: 22b68f38fd907b8599ca9112cd29a9e30befa789
Protected Gate-0 tag: kg-g0-env -> 06f5643a940ac2c6fcfab0e377169b48ce700107

Objective:
Implement and unit-test the original Python post-MAC Ethernet II, IPv4, UDP,
and MoldUDP64 framing/sequence model, stopping at opaque raw ITCH payloads.

Authority inputs:
docs/REQUIREMENTS.md, docs/MICROARCHITECTURE.md, docs/DECISIONS.md,
docs/SPEC_SOURCES.md, docs/VERIFICATION_PLAN.md,
results/processed/WIRE-002-protocol-spec-lock.md, and the completed WIRE-008
canonical Python package.

Scope:
Complete post-MAC frame bytes through Ethernet II, IPv4, UDP, and MoldUDP64
header/message framing, session/sequence state, heartbeat, end-of-session,
explicit length/checksum checks, and late-malformed-prefix retention.

Allowed modifications:
model/python/wire_to_decision/*, model/python/tests/*, tasks/WIRE-009.md,
results/raw/reference_model/*, results/processed/WIRE-009-framing-model.md,
docs/PROJECT_STATE.md, docs/EVIDENCE_INDEX.md, and narrowly required
traceability documentation.

Prohibited work:
ITCH field decoding, normalized-event generation, order-state mutation,
aggregate or decision logic, RTL, C++, third-party protocol packages, sockets,
pcap handling, and changes to frozen protocol requirements.

Test requirements:
Retain all 18 WIRE-008 tests. Add independent fixed checksum/byte-layout,
positive framing, negative profile, sequence, heartbeat, end-of-session,
truncation, trailing-byte, and late-malformed-suffix tests.

Evidence requirements:
Record qualified-Python environment, compile/import output, complete unit-test
output and test inventory under results/raw/reference_model/. Create a
processed WIRE-009 framing report and EVID-009 with narrow Python-unit-tested
wording.

Acceptance criteria:
The complete post-MAC framing path passes all tests, preserves completed Mold
prefix messages on a malformed suffix, propagates fail-closed framing state as
specified, and leaves raw ITCH payloads opaque. No ITCH/book/decision/RTL work
is included.

Stop conditions:
Stop if the authoritative documents leave a required length, padding, trailing
byte, sequence, or end-of-session behaviour ambiguous or contradictory.

Completion report:
Report repository state, framing modules, Ethernet/IPv4/UDP/Mold behaviour,
malformed-suffix evidence, tests, requirement traceability, dependencies,
unproven work, conflicts, specification changes, gate status, and WIRE-010 as
the next task.
