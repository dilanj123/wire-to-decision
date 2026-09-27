# Wire-to-Decision Microarchitecture

## Status

This document freezes externally visible structure and bounded behaviour for the single-clock MVP. It does not prescribe arbitrary RTL coding style, state names, module filenames, or register placement.

## Overall MVP

```text
64-bit framed ingress
        |
        v
 protocol / parser path
        |
        v
 normalized event
        |
        v
 bounded order state
        |
        v
 aggregate totals
        |
        v
 deterministic decision
```

The downstream order/aggregate/decision subsystem is common to Architecture A and any later authorized B experiment.

## Ingress and packet boundary

The project-owned interface is `rx_data[63:0]`, `rx_keep[7:0]`, `rx_valid`, `rx_ready`, and `rx_last`. Lane 0 is the earliest byte. A transfer is `rx_valid && rx_ready`. The first accepted byte is Ethernet destination-MAC byte zero. Preamble, SFD, FCS, MAC, and PHY are outside the core.

Common ingress buffering accepts complete or partial 64-bit beats subject to backpressure and presents a deterministic byte-consumption boundary to the parser. Exact buffer depth is an implementation parameter to be frozen before the Architecture-A implementation task. It is not a CDC FIFO and the A/B experiment is single-clock.

## Protocol path

The parser validates Ethernet II/IPv4/UDP before MoldUDP64. It validates the 20-byte Mold downstream header, then iterates bounded message blocks. Each message length is checked against packet bytes before an ITCH decode can produce an event. Expected-sequence arithmetic is unsigned 64-bit modular arithmetic. A malformed suffix may follow committed earlier messages; no rollback is provided, and the control state is invalidated as specified.

## Architecture A

```text
64-bit beat
    |
    v
ingress buffering
    |
    v
64→8 gearbox
    |
    v
byte parser FSM
    |
    v
normalized event
```

Architecture A is the simplest complete baseline. Once a byte is emitted by the gearbox, the parser consumes at most one valid packet byte per parser cycle. It prioritizes clarity, auditability, bounded behavior, and deterministic state transitions over an assumed line rate. It does not claim 10 Gbit/s parser throughput.

The gearbox SHALL preserve accepted byte order and final-beat `rx_keep`/`rx_last` semantics. Backpressure may reach the external ingress through the common buffering boundary.

## Normalized event contract

The parser-to-state boundary is a ready/valid contract. `event_valid && event_ready` transfers one event. Architecture A and any later authorized Architecture B SHALL produce identical logical event fields and semantics.

Logical fields:

| Field | Meaning |
|---|---|
| `event_kind` | ADD, EXECUTE, EXECUTE_WITH_PRICE, CANCEL, DELETE, or REPLACE |
| `source_type` | Original ITCH type byte (`A/F/E/C/X/D/U`) |
| `mold_sequence` | Sequence number of the containing ITCH message |
| `itch_timestamp` | 48-bit source timestamp |
| `stock_locate` | 16-bit locate |
| `old_order_reference` | Referenced order for E/C/X/D and original reference for U |
| `new_order_reference` | New reference for A/F and replacement reference for U |
| `quantity` | Shares added, executed, cancelled, or replacement quantity as applicable |
| `price` | Stored display price for A/F and replacement price for U; invalid for other event kinds |
| `side` | Buy/sell for A/F; invalid for event kinds that inherit side from state |
| `field_valid` | Logical validity indicators for optional fields |

Field meanings are event-kind-specific; downstream logic SHALL not read an invalid field. `P` produces no mutation event. Unsupported/unclassified types produce profile rejection and no event.

While `event_valid && !event_ready`, all event payload fields SHALL remain stable.

## Bounded order state

The order store has 512 sets and 2 ways per set, with a maximum of 1024 valid entries. A valid entry stores order reference, Price(4), remaining quantity, side, and valid state. A/F allocate; E/C/X reduce; D removes; U logically replaces the old reference with the new reference. No live entry is evicted.

### Set-index hash

WIRE-006 freezes this exact project-owned deterministic hash for implementation, Python, and C++:

```text
h[8:0] = order_ref[8:0]
         XOR order_ref[17:9]
         XOR order_ref[26:18]
         XOR order_ref[35:27]
         XOR order_ref[44:36]
         XOR order_ref[53:45]
         XOR order_ref[62:54]
         XOR zero_extend_9(order_ref[63])
```

There is no runtime seed, modulo, or divider. This is an auditable deterministic fold, not a demonstrated collision-optimal hash. Collision behavior shall be measured later.

On insert, an existing matching reference is a duplicate failure; one free way allocates; two occupied ways with different references are a collision/full failure. Either failure invalidates the book and requires recovery.

## Aggregates

`bid_total` and `ask_total` are unsigned 48-bit totals of remaining displayed shares in valid tracked orders. Accepted mutation and aggregate update are one logical state operation. Overflow or underflow invalidates the book. Price remains stored per order but does not create price levels or BBO.

## Decision subsystem

After a successfully applied tracked mutation, calculate signed `imbalance = signed(bid_total) - signed(ask_total)`. A BUY crossing is from below `+THRESHOLD` to at least it; a SELL crossing is from above `-THRESHOLD` to at most it. Both require valid book, decision enable, and nonzero budget. One budget credit is consumed per emitted event. Non-mutating traffic does not trigger a new crossing evaluation.

Re-arm initializes a known empty order state, zero aggregates, zero previous imbalance, known budget, and valid configuration, unless a later authoritative decision explicitly defines a different recovery mode.

## Decision output

The logical output is ready/valid:

```text
decision_valid
decision_ready
action: BUY or SELL
trigger_mold_sequence[63:0]
itch_timestamp[47:0]
signed_imbalance
```

Payload remains stable while `decision_valid && !decision_ready`. Canonical performance measurements use `decision_ready = 1`; output backpressure is separately verified.

## Control and failure state

Logical configuration/control includes destination IPv4, destination UDP port, tracked Stock Locate, optional expected symbol and enable, active Mold Session, expected sequence, threshold, budget, decision enable, and arm/re-arm. Runtime state includes `book_valid` and `recovery_required`.

Unexpected session/sequence, malformed framing, state-integrity error, aggregate error, collision/full set, end-of-session, or profile rejection clears validity, sets recovery required, suppresses decisions, and prevents silent continuation. There is no live retransmission requester or hidden automatic recovery.

## Architecture B rule

```text
               +--> Parser A --+
common ingress |               |
               +--> Parser B --+--> identical event contract
                                --> identical book/decision
```

Parser B is not authorized. It is only a possible native-64-bit parser experiment if Architecture-A evidence identifies parser serialization/alignment as the relevant bottleneck after full regression, target synthesis/P&R, timing/resource/latency/throughput measurement. The project must then choose `BUILD B`, `MODIFY HYPOTHESIS`, or `REJECT B`. If book/hash/decision logic is the bottleneck, B shall not be built merely because it was imagined.

## Experiment constants

Both architectures use LFE5U-85F-8BG381C, nextpnr `--85k --package CABGA381 --speed 8`, 156.25 MHz objective, the qualified WIRE-004 toolchain, the same protocol subset, ingress contract, normalized-event contract, downstream state/decision logic, workload, P&R options, report extraction, and seeds `1, 7, 19, 42, 97`.

## Latency boundaries

- L1: first ITCH message byte accepted → corresponding normalized event valid.
- L2: final input byte needed to determine the triggering mutation → `decision_valid`.
- L3: first Ethernet frame byte accepted → `decision_valid`.

All are measured in cycles first, under legal no-stall input, armed valid state, and no output stall. L3 is not physical wire latency.

## CDC sequencing

The A/B experiment remains single-clock. A later CDC extension adds independently clocked RX and processing domains with an original async FIFO using power-of-two depth, binary local pointers, Gray crossing pointers, two-flop synchronization, safe full/empty logic, and explicit reset/epoch readiness. One-sided reset or stale-token ambiguity invalidates the stream/state rather than silently resuming.
