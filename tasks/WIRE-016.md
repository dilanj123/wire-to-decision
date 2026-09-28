# WIRE-016 — Architecture A Ethernet II byte parser RTL and verification

Phase: Phase 2 — Parser primitives and complete Architecture A parser

Starting commit: `32d124c671e52fa36a366b1c0bdbffddcf2316ca`

Objective: consume a post-MAC Ethernet byte stream, strip the 14-byte Ethernet II header, accept only IPv4 EtherType `0x0800`, forward payload bytes with `last`, and expose filtered versus fatal local outcomes.

Authority: `docs/REQUIREMENTS.md`, `docs/MICROARCHITECTURE.md`, `docs/VERIFICATION_PLAN.md`, `docs/FORMAL.md`, `docs/DECISIONS.md`, `docs/SPEC_SOURCES.md`, WIRE-002, WIRE-014, and WIRE-015 evidence.

Scope: Ethernet II header/EtherType filtering, payload ready/valid forwarding, rejection status handshake, reset and backpressure, standalone/composed simulation, local formal checks, and synthesis elaboration sanity.

Prohibited: IPv4/UDP/Mold/ITCH parsing, MAC filtering, VLAN parsing, order/decision RTL, Architecture B, CDC, P&R, and performance claims.

Acceptance: standalone and buffer→gearbox→Ethernet cocotb pass; Verilator and Yosys pass; Python 71-test regression and WIRE-014/015 regressions remain passing; local formal safety/reference/cover jobs pass with exact bounded scope recorded; evidence and state bookkeeping updated; clean pushed tree.

Evidence: `results/raw/rtl/eth_parser/`, `results/processed/WIRE-016-ethernet-parser-rtl.md`, and EVID-016.
