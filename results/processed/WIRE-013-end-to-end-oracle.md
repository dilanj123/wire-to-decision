# WIRE-013 — Python End-to-End Reference Oracle and Recovery Integration

## A. Starting state

SOURCE-DERIVED: Started on `main` at `faeef5177488a6e31da54f6ba40e93a97d237fe4` with a clean tree and local `main` equal to `origin/main`. The protected `kg-g0-env` tag remained unchanged and peeled to `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. Authority used

SOURCE-DERIVED: Used the authoritative project plan, requirements, microarchitecture, decisions, verification/formal plans, and WIRE-009 through WIRE-012 processed evidence. No specification conflict was found.

## C. Oracle architecture

IMPLEMENTED: `ReferenceOracle` owns persistent `ModelConfig`, `FramingState`, `OrderBook`, and `DecisionModel`. `OracleFrameResult` exposes framing, per-message results, decisions, terminal error, acceptance/filtering, quarantine, status, and expected sequence. `OracleMessageResult` exposes the framed message, decode result, optional book result, and optional decision.

## D. State ownership

IMPLEMENTED: The oracle does not duplicate framing, ITCH, bounded-store, aggregate, or decision logic. It advances existing component objects in message order and adds only the cross-layer quarantine/re-arm control.

## E. Frame-processing flow

PYTHON-UNIT-TESTED: Whole post-MAC frames pass through the existing Ethernet/IPv4/UDP/Mold model. Persistent expected sequence is adopted from each framing result. Nonfatal profile filters return observable filtered results without changing model usability.

## F. Message-processing flow

PYTHON-UNIT-TESTED: Completed `FramedMessage` objects are decoded in order. Known non-mutating and filtered messages produce no book/decision operation. Mutations are applied immediately; only successful applications reach `DecisionModel`.

## G. Successful end-to-end path

PYTHON-UNIT-TESTED: A real Ethernet→IPv4→UDP→Mold→ITCH A→NormalizedEvent→OrderBook→aggregate→DecisionEvent path is covered, including trigger sequence, timestamp, signed imbalance, budget decrement, and expected-sequence progression.

## H. Non-mutating/filter behavior

PYTHON-UNIT-TESTED: Heartbeat and P are no-ops for book/decision state while normal Mold sequence rules apply. Other Stock Locate messages are filtered. Wrong destination IP remains a nonfatal profile filter and leaves framing state usable.

## I. Fatal failure propagation

PYTHON-UNIT-TESTED: Fatal framing/Mold errors, ITCH `FAIL_CLOSED`, and book mutation failures quarantine the model. No subsequent frame is processed normally before explicit re-arm. Source-layer error values remain observable.

## J. Late malformed suffix/no rollback

PYTHON-UNIT-TESTED: A packet with two complete prefix messages and a truncated third retained both prefix messages. ADD and EXECUTE committed in order; one prefix BUY decision was retained; terminal `MESSAGE_TRUNCATED` then set `book_valid = false` and `recovery_required = true`. The remaining order quantity and aggregates were retained; no rollback occurred.

## K. Quarantine behavior

IMPLEMENTED / PYTHON-UNIT-TESTED: Quarantined calls return explicit `RECOVERY_REQUIRED`, emit no decisions, consume no budget, and do not mutate the book.

## L. Explicit recovery/re-arm

PYTHON-UNIT-TESTED: `rearm(config)` replaces framing state, clears the order book and aggregates, resets decision state/budget, installs a new session/sequence, and permits normal processing afterward.

## M. Sequence/session integration

PYTHON-UNIT-TESTED: Normal multi-frame progression, heartbeat, sequence failure, session replacement on re-arm, and end-of-session quarantine are covered.

## N. Book/decision integration

PYTHON-UNIT-TESTED: Duplicate and unknown-reference failures reached through complete frames quarantine globally. Successful mutations retained component-level aggregate and decision invariants.

## O. Test coverage

PYTHON-UNIT-TESTED: The complete suite contains 71 tests: 61 prior component tests plus 10 WIRE-013 integration tests. All passed under Python 3.11.6.

## P. Requirement traceability

PYTHON-UNIT-TESTED: Integration evidence exercises REQ-ERR-001 through REQ-ERR-005, applicable REQ-MOLD-004 through REQ-MOLD-009, REQ-ITCH-002 through REQ-ITCH-004, REQ-BOOK-003 through REQ-BOOK-007, and REQ-DEC-002 through REQ-DEC-006. Earlier tasks provide the component-level evidence for the same requirements.

## Q. Dependencies

IMPLEMENTED: No third-party Python dependency was added.

## R. Problems/conflicts

No specification conflict was found. No RTL, formal application run, synthesis/P&R, or latency/throughput claim was made.

## S. What remains unproven

UNPROVEN: SystemVerilog RTL correctness, cycle-accurate ingress/ready-valid behavior, RTL simulation, formal application properties, application synthesis/P&R, timing closure, L1/L2/L3 latency, throughput, Architecture-A bottleneck, Architecture-B authorization, CDC/RDC, independent C++ checker, and physical FPGA operation.

## T. Phase-1 conclusion

PASS: The project-owned end-to-end Python reference oracle and recovery/no-rollback integration pass 71 Python unit tests. Phase 1 is complete; this is Python-unit-tested evidence only.
