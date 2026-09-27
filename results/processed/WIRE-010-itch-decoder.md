# WIRE-010 — Python ITCH Subset Decoder to Normalized Events

## A. Starting state

SOURCE-DERIVED: Started at `/Users/Dilan/Projects/wire-to-decision`, branch
`main`, commit `b92e43300597b6fd58371d14c3a229e092c84ead`, with a clean tree.
The protected `kg-g0-env` tag remained unchanged and peeled to
`06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. Authority used

SOURCE-DERIVED: Used the exact ITCH lengths and offsets in
`results/processed/WIRE-002-protocol-spec-lock.md`, plus the requirements,
microarchitecture, WIRE-D007/WIRE-D008 decisions, WIRE-008 canonical types,
and WIRE-009 framed-message boundary. No authority conflict was found.

## C. Decoder architecture

IMPLEMENTED: Added `model/python/wire_to_decision/itch.py` with pure
`decode_itch_message(FramedMessage, ModelConfig) -> DecodeResult`. The result
distinguishes mutation event, known non-mutating, filtered other instrument,
and fail-closed outcomes. No global state or I/O is used.

## D. Common ITCH decoding

SPECIFIED / IMPLEMENTED: Message type, Stock Locate, and 48-bit nanosecond
timestamp are decoded big-endian. Mold sequence is propagated directly from
`FramedMessage`; it is not recomputed. Raw payloads remain available only as
source input and no Tracking Number is added to normalized events.

## E. A implementation

PYTHON-UNIT-TESTED: Exact 36-byte A layout is checked. New reference, side,
shares, Price(4), Stock Locate, timestamp, and optional exact 8-byte symbol
check map to `MutationKind.ADD` with A source type.

## F. F implementation

PYTHON-UNIT-TESTED: Exact 40-byte F layout, including the four-byte attribution
field, is checked. F maps to ADD with the same book-relevant fields as A;
attribution is not retained.

## G. E implementation

PYTHON-UNIT-TESTED: Exact 31-byte E layout maps to EXECUTE with old reference
and quantity valid; new reference, price, and side are invalid.

## H. C implementation

PYTHON-UNIT-TESTED: Exact 36-byte C layout maps to EXECUTE_WITH_PRICE. The
source execution price is not placed in the normalized resting-price field;
that field remains invalid under WIRE-D008, preventing confusion with stored
display price.

## I. X implementation

PYTHON-UNIT-TESTED: Exact 23-byte X layout maps to CANCEL with old reference
and cancelled quantity valid.

## J. D implementation

PYTHON-UNIT-TESTED: Exact 19-byte D layout maps to DELETE with only the old
reference valid.

## K. U implementation

PYTHON-UNIT-TESTED: Exact 35-byte U layout maps to REPLACE with old reference,
new reference, replacement shares, and replacement Price(4) valid. Side is not
decoded and remains invalid because it is inherited later.

## L. P handling

PYTHON-UNIT-TESTED: Exact 44-byte P is recognized as legitimate
`KNOWN_NON_MUTATING`; it emits no event and is not fail-closed.

## M. Unknown-message handling

PYTHON-UNIT-TESTED: An unclassified message type returns `FAIL_CLOSED` with
`UNSUPPORTED_MESSAGE` and `FailureReason.UNSUPPORTED_MESSAGE`, implementing
WIRE-D007 without silently skipping unknown semantics.

## N. Stock-Locate filtering

PYTHON-UNIT-TESTED: Stock-dependent A/F/E/C/X/D/U messages with a non-configured
Stock Locate return `FILTERED_OTHER_INSTRUMENT`, emit no event, and do not
invalidate the decoder status.

## O. Symbol validation

PYTHON-UNIT-TESTED: A/F symbol bytes are compared byte-for-byte only when
enabled. Disabled checking ignores mismatch; enabled exact match passes; an
enabled mismatch returns fail-closed `SYMBOL_MISMATCH`. Padding is not stripped
or normalized.

## P. Normalized-event mapping

SPECIFIED / IMPLEMENTED: The decoder uses the WIRE-D008 event kinds and named
field-valid indicators from WIRE-008. A/F use `new_order_reference`; E/C/X/D
use `old_order_reference`; U uses both. All mutating events carry the supplied
Mold sequence and decoded ITCH timestamp.

## Q. Framing-to-decoder integration

PYTHON-UNIT-TESTED: Real WIRE-009 `FramedMessage` values are decoded. A Mold
packet containing valid A and E messages produces two events. A Mold packet
with valid A/E followed by a truncated third block retains and decodes the
completed prefix while preserving the framing error outside the decoder.

## R. Test coverage

PYTHON-UNIT-TESTED: The complete suite contains 41 tests: 29 prior WIRE-008/
WIRE-009 tests plus 12 WIRE-010 tests. Coverage includes every supported type,
P, unknown types, exact lengths, endian-sensitive values, side validation,
filtering, symbols, sequence/timestamp propagation, and integration.

## S. Requirement traceability

PYTHON-UNIT-TESTED: WIRE-010 exercises REQ-ITCH-001 through REQ-ITCH-004,
including the exact supported A/F/E/C/X/D/U set, P handling, field decoding,
message-length validation, Stock Locate filtering, and normalized mapping. It
also exercises the WIRE-D007 behavior in REQ-ERR-005. No book, aggregate,
decision, RTL, or end-to-end requirement is marked verified.

## T. Dependencies

IMPLEMENTED: No third-party Python dependency was added. The decoder uses only
the standard library and performs no network or file I/O.

## U. Problems/conflicts

No unresolved specification conflict was found. The C execution price is
intentionally not assigned to the normalized `price` field because the frozen
WIRE-D008 contract marks that field invalid for non-add/replace event kinds.

## V. What remains unproven

UNPROVEN: Bounded order-state mutation, hash-table collision behavior in the
state model, aggregates, decisions, full end-to-end Python oracle, RTL,
formal application properties, synthesis/P&R, timing, latency, throughput, CDC,
C++ integration, and physical FPGA operation.

## W. WIRE-010 conclusion

PASS: The project-owned decoder for the frozen A/F/E/C/X/D/U subset, P
classification, tracked-instrument filtering, symbol checking, unknown-type
fail-closed policy, and normalized-event mapping is exercised by 41 tests.
The task stops before book and decision behavior.
