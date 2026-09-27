# WIRE-013 — Python End-to-End Reference Oracle and Recovery Integration

## Task

- Phase: Phase 1 — Python reference model
- Starting HEAD: `faeef5177488a6e31da54f6ba40e93a97d237fe4`
- Objective: integrate the existing framing, ITCH, bounded-book, aggregate, and decision components into a persistent complete-frame Python oracle with fail-closed recovery.

## Authority and boundaries

Use the authoritative requirements, microarchitecture, decisions, and completed WIRE-009 through WIRE-012 component contracts. The oracle consumes whole post-MAC frame bytes. It does not model RTL ready/valid timing and does not add protocol or strategy functionality.

## Scope

Allowed: top-level oracle/result types, explicit book invalidation API, end-to-end integration tests, raw/processed evidence, task/state/checklist/evidence-index updates.

Prohibited: RTL, Architecture A/B, CDC, cycle modeling, latency/throughput claims, application formal, synthesis/P&R, and new protocol/trading functionality.

## Acceptance criteria

- Persistent `FramingState`, `OrderBook`, and `DecisionModel` are owned without duplicated functional implementations.
- Complete frames, multi-message ordering, multi-frame state, filtering, heartbeat, P, fatal failures, quarantine, re-arm, and post-rearm processing are tested.
- Late malformed suffixes process completed prefixes first, retain prefix mutations/decisions, and then quarantine without rollback.
- Existing 61 tests remain passing; total test count recorded.
- No third-party dependency or RTL added.
- EVID-013, processed evidence, project state, and checklist updated.
- Clean working tree and matching local/remote `main` after push.

## Completion

Report the exact 71-test result, integration/error/recovery behavior, requirement traceability, evidence classification, remaining unproven hardware work, and next task without executing WIRE-014.
