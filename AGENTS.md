# Repository Agent Instructions

## Engineering method

```text
specify
→ build the simplest complete baseline
→ verify
→ synthesize/implement
→ measure
→ identify the bottleneck
→ form a hypothesis
→ make one controlled change
→ re-verify
→ re-measure
→ retain/modify/reject
→ compare
→ conclude
```

## Evidence rules

Agents must never claim:

```text
PASS
zero mismatches
formal proof
synthesis success
timing closure
Fmax
latency
throughput
resource figures
```

without corresponding tool evidence.

## Scope rule

Implementation must remain inside the active:

```text
tasks/WIRE-xxx.md
```

## Original project work

The following are expected to remain original project work unless explicitly changed by authoritative documentation:

- parser architecture;
- MoldUDP64 sequencing/control;
- ITCH decoder;
- bounded order-state architecture;
- decision logic;
- CDC architecture;
- asynchronous FIFO;
- reset/recovery logic;
- project-specific formal properties;
- Python reference model;
- C++ replay/checking;
- project-specific verification.

## Third-party rule

Third-party code must not be copied unless the licence, upstream commit, original path, local path, modifications, and classification are recorded.

## Stop-on-conflict rule

If specifications conflict, stop and report the conflict rather than silently choosing one.
