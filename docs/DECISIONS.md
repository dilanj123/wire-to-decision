# Process Decisions

## WIRE-D001 — Adopt audited workflow controls

- Date: 2026-09-26
- Source: WIRE-001 reference workflow audit
- Decision: Adopt the audit's process controls for task scoping, evidence classification, raw/processed evidence, exact-commit reproducibility, compact project state, requirements traceability, and controlled experiments.
- Scope: Workflow only. No protocol, RTL, toolchain, or architecture requirement is changed.
- Rationale: These controls are supported by the inspected RTL-to-Pixels workflow and strengthened by later repository references.
- Status: ADOPTED

## WIRE-D011 — Freeze Phase-2 single-clock RTL reset convention

- Date: 2026-09-28
- Source: WIRE-014 Architecture-A gearbox implementation
- Context: The first Phase-2 single-clock RTL primitive required an explicit reset convention for portable Verilator, Yosys, and formal execution.
- Decision: Use a synchronous active-high reset named `rst` for Phase-2 single-clock Architecture-A primitives. This convention does not apply to the later CDC/reset-domain implementation.
- Alternatives considered: an asynchronous reset or leaving reset polarity implicit. These were rejected for unnecessary portability ambiguity at the single-clock boundary.
- Consequences: The gearbox and subsequent single-clock primitives use deterministic clocked reset behavior; CDC-specific reset requirements remain a separate future decision.
- Status: ADOPTED

## WIRE-D012 — Freeze common ingress buffer depth

- Date: 2026-09-28
- Source: WIRE-015 common ingress buffer implementation
- Context: The common ingress-buffer depth was intentionally left open until the first shared Phase-2 buffering task.
- Decision: Use a synchronous two-entry 64-bit framed-beat FIFO storing `{data[63:0], keep[7:0], last}`. Use it unchanged by Architecture A and any later authorized Architecture B.
- Rationale: This is the smallest useful elastic buffer beyond the gearbox's active beat, provides real producer/serializer decoupling, keeps RTL/formal state small and auditable, and preserves a controlled common input for a later A/B comparison. It is not claimed to be performance-optimal.
- Consequences: The FIFO has registered/no-empty-fall-through output behavior, accepts full-queue replacement on same-cycle pop/push, and does not validate or transform keep/last fields. It is not a CDC FIFO.
- Status: ADOPTED

## WIRE-D003 — Lock third-party provenance and originality policy

- Date: 2026-09-27
- Source: WIRE-003 third-party reference/reuse audit
- Decision: Keep mandatory Wire-to-Decision datapath, parser, order-state, decision, CDC, formal, reference-model, and project-specific verification work original. Pin audited third-party repositories as reference-only or potential test-only sources without adding dependencies.
- Scope: Provenance and reuse policy only. No protocol or microarchitecture scope changes.
- Rationale: Direct-overlap market-data projects create structural-derivation risk independent of licence permission; generic infrastructure references do not become dependencies merely because they were audited. Any future test infrastructure must be pinned and separated from project-owned expected-value logic.
- Status: ADOPTED

## WIRE-D002 — Lock external protocol source basis and explicit MVP restrictions

- Date: 2026-09-27
- Source: WIRE-002 external protocol specification lock
- Decision: Use RFC 894, RFC 791, RFC 768, the current Nasdaq MoldUDP64 V 1.00 artifact, and the current Nasdaq-linked TotalView-ITCH 5.0 artifact as the external source basis. Keep the MVP restrictions and validation rules documented in the WIRE-002 evidence report.
- Scope: External source authority and Phase-0 MVP protocol profile only. No RTL, model, verification, timing, or performance requirement is established by this decision.
- Rationale: The source audit distinguishes protocol facts from deliberate project restrictions, including Ethernet II/IPv4 only, non-fragmented IPv4, zero-only UDP checksums, fail-closed Mold discontinuities, and one configured ITCH Stock Locate.
- Status: ADOPTED

## WIRE-D004 — Qualify native Apple Silicon open-source toolchain

- Date: 2026-09-27
- Source: WIRE-004 toolchain smoke execution
- Decision: Use the native Apple Silicon OSS CAD Suite build `2026-09-27` as the canonical initial open-source flow for Verilator/cocotb, Yosys/SBY, Yices, Yosys `synth_ecp5`, nextpnr-ECP5, and ecppack.
- Scope: Toolchain environment only. The ECP5 `LFE5U-25F` / `CABGA381` combination used in the smoke test is not the Wire-to-Decision production target.
- Rationale: Each listed flow stage executed successfully on the actual arm64 host using the trivial WIRE-004 smoke design. Exact archive metadata, paths, commands, and logs are retained in the WIRE-004 evidence.
- Status: ADOPTED

## WIRE-D005 — Freeze canonical implementation target

- Date: 2026-09-27
- Source: WIRE-005 implementation-target freeze
- Decision: Use LFE5U-85F-8BG381C as the canonical mandatory implementation target, mapped in nextpnr-ECP5 as `--85k --package CABGA381 --speed 8`, with a primary timing objective of 156.25 MHz (6.4 ns). Architecture A and any later authorized Architecture B comparison must use the same target and controlled P&R methodology. Physical hardware is not required for the CV-ready gate.
- Scope: Implementation target and experiment methodology only. No protocol or microarchitecture scope change; no application fit or timing result is established.
- Rationale: The official Lattice resource tables provide substantially more experimental headroom in 85F than 45F, while LFE5U avoids unused SERDES capability at the post-MAC project boundary. The exact target was accepted and routed by the qualified local OSS CAD Suite using the existing trivial smoke design.
- Status: ADOPTED

## WIRE-D006 — Freeze bounded-order set-index hash

- Date: 2026-09-27
- Source: WIRE-006 authoritative specification package
- Context: The 512-set × 2-way order store required a deterministic 64-bit reference to 9-bit set-index function, but no exact function had previously been frozen.
- Decision: Use the XOR fold `ref[8:0] ^ ref[17:9] ^ ref[26:18] ^ ref[35:27] ^ ref[44:36] ^ ref[53:45] ^ ref[62:54] ^ zero_extend_9(ref[63])`. It is combinational, fixed, seedless, and uses no modulo or divider.
- Alternatives considered: a runtime-seeded hash, division/modulo, or an uncommitted implementation-defined fold. These were rejected for reproducibility or unnecessary complexity.
- Consequences: Python, RTL, and C++ must reproduce this exact fold. Collision behavior is measured later; this decision does not claim optimal hash quality.
- Status: ADOPTED

## WIRE-D007 — Reject unclassified ITCH message types

- Date: 2026-09-27
- Source: WIRE-006 authoritative specification package
- Context: WIRE-002 explicitly classified `P` as non-mutating but left the safe handling of other unclassified message types for the implementation specification.
- Decision: `P` may be consumed without order-state mutation. Any unsupported or unclassified message type shall cause profile rejection, invalidate the book, require explicit re-arm, suppress decisions, and produce no mutation from that message.
- Alternatives considered: silently skip all unknown types or attempt a broad full-ITCH classification. Silent skipping could hide semantics; full coverage is outside MVP scope.
- Consequences: the profile fails closed for future/unclassified types and avoids silently corrupting bounded state. The policy must be tested in the Python model and RTL.
- Status: ADOPTED

## WIRE-D008 — Freeze normalized mutation-event contract

- Date: 2026-09-27
- Source: WIRE-006 authoritative specification package
- Context: Controlled Architecture A/B comparison requires a common downstream boundary without prescribing parser implementation details.
- Decision: A and any later authorized B shall emit the same ready/valid logical event contract: event kind, source type, Mold sequence, ITCH timestamp, Stock Locate, old/new references, quantity, price, side, and field-valid semantics. Invalid fields are not consumed downstream; `P` emits no event.
- Alternatives considered: parser-specific downstream interfaces or reparsing raw ITCH bytes in the book. These would weaken comparison and duplicate protocol knowledge.
- Consequences: the common order/aggregate/decision subsystem can be held constant while parser implementations vary. Exact RTL encoding remains an implementation detail.
- Status: ADOPTED

## WIRE-D009 — Freeze deterministic bounded-store way selection

- Date: 2026-09-27
- Source: WIRE-011 bounded order-state model
- Context: The 512-set × 2-way store requires deterministic allocation when both ways in a target set are free so Python, RTL, and C++ models remain equivalent.
- Decision: Select way 0 when both ways are free; otherwise select the only free way. Never evict a valid entry. A full target set fails closed.
- Alternatives considered: selecting way 1 first, implementation-dependent selection, or eviction. These were rejected because they weaken reproducibility or violate the no-eviction policy.
- Consequences: Free-way selection is deterministic across implementations. This is an implementation-model decision and does not change the 512-set × 2-way architecture or its failure policy.
- Status: ADOPTED

## WIRE-D010 — Freeze previous-imbalance update semantics

- Date: 2026-09-27
- Source: WIRE-012 deterministic decision model
- Context: The crossing equations require a deterministic previous-imbalance state update when emission is suppressed by decision enable or budget.
- Decision: After every successfully applied tracked mutation, set `previous_imbalance` to the resulting signed aggregate imbalance, regardless of whether decision emission is enabled or budget remains. Failed, non-mutating, filtered, and quarantined events do not advance it.
- Alternatives considered: advance only when a decision is emitted, or preserve the prior value while disabled/exhausted. These alternatives can create stale crossings when emission is later enabled or budget is restored.
- Consequences: The state tracks the actual aggregate trajectory, while enable and budget gate only event emission. Re-arm resets the value to zero.
- Status: ADOPTED

## WIRE-D013 — Define zero-byte IPv4 project-payload handling

- Date: 2026-09-28
- Source: WIRE-017 Architecture-A IPv4 parser implementation
- Context: A byte-stream downstream interface represents packet termination with `out_last` on a valid byte and cannot represent an accepted zero-byte project payload.
- Decision: For this pipeline, an otherwise profile-valid IPv4/UDP header with `Total Length == 20` is rejected locally as fatal `IPV4_EMPTY_PROJECT_PAYLOAD`. This is a stage representation decision, not a claim that IPv4 generally requires a non-empty payload.
- Consequences: The RTL stage emits no payload and reports a fatal local status. The Python model is not changed; it may report the later UDP-header truncation for the same bytes. The externally relevant integration outcome remains fatal, with no downstream mutation or decision once later control integration exists.
- Status: ADOPTED
