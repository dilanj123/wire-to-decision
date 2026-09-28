# WIRE-017A — IPv4 Formal Correspondence Closure

## Status

Corrective subtask of WIRE-017. The existing local WIRE-017 commits remain
unchanged and unpushed. Production IPv4 RTL was not modified.

## Starting state

- Local HEAD: `13cfc83033df61dc52e1bd9feca1b0d3e8fde2e5`
- `origin/main`: `1acca7d0493dcdd1e4a75b6645f6190406bf14c9`
- Gate-0 peeled commit: `06f5643a940ac2c6fcfab0e377169b48ce700107`
- Initial working tree: clean

## Objective and blocker

The original monolithic public-interface WIRE-017 correspondence BMC used
SBY 0.69, `smtbmc yices`, depth 32, and became solver-bound after step 22.
It produced no RTL counterexample and was not a PASS. WIRE-017A decomposes
the proof obligations into smaller public-interface jobs.

## Decomposition

- Header/classification vectors: depth 28; validation priority, rejection
  code/fatal result, and no payload output.
- Checksum outcome vectors: depth 28; valid and corrupted fixed headers.
- Payload correspondence: depth 32; symbolic four-byte payload values after
  a constrained valid profile header.
- Padding: depth 40; declared payload followed by physical padding.
- Late physical truncation: depth 32; declared length exceeds physical input.
- Next-packet behavior: depth 44; two consecutive rejected packets.
- Existing local safety: depth 20; output and rejection stall safety.
- Existing cover: depth 32; payload/drop/padding/reject reachability.

All new reference logic uses public DUT ports only. Targeted jobs document
the fixed destination configuration, upstream stability assumption, and,
where used to isolate data-path correspondence, downstream ready signals
held high. The reduced header cases and fixed vectors are not claims over
all 16-bit lengths or all 160-bit headers.

## Scope exclusions

No production RTL change, UDP work, Architecture B, CDC, P&R, timing,
throughput, or application-level mutation-suppression claim.

## Acceptance and push condition

All mandatory decomposed jobs and regressions must pass before publishing the
two existing WIRE-017 commits plus the WIRE-017A closure commit. Gate-0 must
remain unmoved. `REQ-IP-007` end-to-end mutation suppression remains outside
this stage and unproven.
