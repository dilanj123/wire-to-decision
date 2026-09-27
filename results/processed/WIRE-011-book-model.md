# WIRE-011 — Python Bounded Order-State and Aggregate Model

## A. Starting state

SOURCE-DERIVED: Started at `/Users/Dilan/Projects/wire-to-decision`, branch
`main`, commit `0d69fe2a31ceae133ea045ec642a2dcc5d5a2eaf`, with a clean tree.
The protected `kg-g0-env` tag remained unchanged and peeled to
`06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. GitHub publication

SAFETY AUDIT: Tracked files contained no detected secrets, private keys,
credentials, prohibited PDFs, third-party source snapshots, or large binary
archives. The configured GitHub CLI token for `dilanj123` was invalid, so the
target repository was not created or pushed. No remote was invented.

## C. Authority used

SOURCE-DERIVED: Used the bounded-store, mutation, aggregate, failure, and
re-arm sections of the repository requirements/microarchitecture/decisions,
plus the WIRE-008/009/010 canonical types and evidence. No specification
conflict was found.

## D. Bounded-store architecture

IMPLEMENTED: `OrderBook` stores exactly 512 sets with 2 ways each. An empty
way contains `None`; a live way contains the canonical immutable `OrderEntry`.
There is no authoritative unbounded dictionary. Capacity is 1024 live entries.

## E. WIRE-D006 integration

PYTHON-UNIT-TESTED: Lookup and allocation call the existing
`order_set_index()` implementation. Fixed collisions include references
`0x1`, `0x200`, and `0x40000`, all mapping to set 1; no duplicate hash logic
was added to the book model.

## F. Lookup/allocation semantics

IMPLEMENTED / PYTHON-UNIT-TESTED: Lookup searches only the selected set's two
ways. When both are free, way 0 is selected; otherwise the only free way is
selected. A full set with a different reference fails closed and never evicts.

## G. ADD semantics

PYTHON-UNIT-TESTED: A/F-normalized ADD uses `new_order_reference`, quantity,
price, and side. Duplicate references fail with state-integrity status; a full
collision set fails with hash-capacity status. Successful allocation updates
the matching side total.

## H. EXECUTE/EWC semantics

PYTHON-UNIT-TESTED: EXECUTE and EXECUTE_WITH_PRICE locate the old reference,
reject unknown/over-executed quantities, decrement the matching aggregate, and
remove zero-remainder entries. C/EXECUTE_WITH_PRICE does not modify the stored
resting Price(4).

## I. CANCEL/DELETE semantics

PYTHON-UNIT-TESTED: CANCEL supports partial/full reduction and rejects unknown
or over-cancelled references. DELETE subtracts the complete remaining quantity
from the inherited side and removes the entry; it does not use a quantity from
the event.

## J. REPLACE semantics

PYTHON-UNIT-TESTED: U removes the old reference and creates the new reference
with new quantity/price while inheriting side. Same-set and different-set
replacement are covered. New-reference conflict and full destination-set
collision fail atomically; the old entry remains because staged state is not
committed on failure.

## K. Aggregate model

IMPLEMENTED / PYTHON-UNIT-TESTED: `bid_total` and `ask_total` are checked
unsigned 48-bit integers. Each successful mutation updates the entry and side
total as one staged operation. A recomputation helper independently sums all
bounded valid entries; tests compare it after successful mutations.

## L. Collision/capacity behaviour

PYTHON-UNIT-TESTED: Two colliding references fill both ways; a third distinct
reference produces `COLLISION_CAPACITY`, invalidates the book, and leaves both
existing entries intact. No eviction occurs.

## M. Fail-closed/re-arm behaviour

PYTHON-UNIT-TESTED: Duplicate, unknown-reference, over-subtract, aggregate
range, replacement conflict, and capacity failures enter
`book_valid = false`, `recovery_required = true`. Later events are quarantined
until explicit `reset()`, which clears all ways and aggregates and restores a
known empty valid state.

## N. Integration tests

PYTHON-UNIT-TESTED: A real WIRE-010 normalized ADD event creates a bounded
entry and updates the BUY aggregate. WIRE-009/010 prefix framing/decoding
remains covered by the prior suite; final malformed-suffix state invalidation
remains owned by the higher framing/control model and is not duplicated here.

## O. Test coverage

PYTHON-UNIT-TESTED: The complete suite contains 52 tests: 41 prior WIRE-008/
WIRE-009/
WIRE-010 tests plus 11 WIRE-011 book tests. Coverage includes both ways,
collisions, all mutation classes, U atomicity, aggregates, quarantine, reset,
and decoder integration.

## P. Requirement traceability

PYTHON-UNIT-TESTED: WIRE-011 exercises REQ-BOOK-001 through REQ-BOOK-007,
REQ-DEC-001 aggregate representation, and the order-state portions of
REQ-ERR-001 through REQ-ERR-004. No decision-crossing requirement is marked
verified.

## Q. Dependencies

IMPLEMENTED: No third-party Python dependency was added. The model uses the
standard library and existing project-owned types only.

## R. Problems/conflicts

No functional specification conflict was found. GitHub publication was blocked
by invalid `gh` authentication, independently of the functional model result.

## S. What remains unproven

UNPROVEN: Decision crossing, risk-budget behavior, full end-to-end Python
oracle, RTL, formal application properties, synthesis/P&R, timing, latency,
throughput, CDC, C++ integration, and physical FPGA operation.

## T. WIRE-011 conclusion

PASS FUNCTIONALLY: The bounded 512-set x 2-way order model and checked 48-bit
aggregate accounting pass 52 unit tests. GitHub publication is BLOCKED pending
valid GitHub authentication and was not falsely represented as complete.
