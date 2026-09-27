Task ID: WIRE-010
Phase: Phase 1 — Python reference model
Starting known-good commit: b92e43300597b6fd58371d14c3a229e092c84ead
Protected Gate-0 tag: kg-g0-env -> 06f5643a940ac2c6fcfab0e377169b48ce700107

Objective:
Decode one complete raw ITCH message payload into the frozen WIRE-D008
normalized-event contract, including supported mutation messages, tracked
instrument filtering, P handling, and WIRE-D007 fail-closed behavior.

Authority inputs:
docs/REQUIREMENTS.md, docs/MICROARCHITECTURE.md, docs/DECISIONS.md,
docs/SPEC_SOURCES.md, results/processed/WIRE-002-protocol-spec-lock.md,
results/processed/WIRE-008-reference-model-skeleton.md,
results/processed/WIRE-009-framing-model.md, and the existing Python package.

Supported source messages:
A, F, E, C, X, D, U for mutation events; P for known non-mutating handling.

Allowed modifications:
model/python/wire_to_decision/*, model/python/tests/*, tasks/WIRE-010.md,
results/raw/reference_model/*, results/processed/WIRE-010-itch-decoder.md,
docs/PROJECT_STATE.md, docs/EVIDENCE_INDEX.md, and narrowly required
traceability documentation.

Prohibited work:
Order-state mutation, aggregate or decision logic, Ethernet/IP/UDP/Mold
framing changes, RTL, C++, third-party protocol packages, sockets, pcap
handling, or changes to frozen protocol requirements.

Test requirements:
Retain all 29 WIRE-008/009 tests. Add fixed A/F/E/C/X/D/U/P fixtures,
exact-length checks, numeric/side/timestamp checks, filtering and symbol
checks, unknown-message fail-closed tests, and framing-to-decoder integration.

Acceptance criteria:
Every locked source layout decodes to the exact normalized-event contract;
P is explicit known non-mutating; unknown types fail closed; other instruments
are filtered; raw ITCH payloads are not decoded beyond this boundary.

Evidence requirements:
Record qualified-Python environment, compile/import output, complete tests and
test inventory under results/raw/reference_model/. Create a processed WIRE-010
report and EVID-010 with narrow Python-unit-tested wording.

Stop conditions:
Stop if any exact source length/offset, C normalized representation, P policy,
symbol semantics, Stock Locate filtering, or field-valid layout is missing or
contradictory in repository authority.

Completion report:
Report repository state, decoder boundary, supported messages, normalized
mapping, filtering, integration, tests, traceability, dependencies, unproven
work, conflicts, specification changes, gate status, and WIRE-011 next task.
