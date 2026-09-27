# Process Decisions

## WIRE-D001 — Adopt audited workflow controls

- Date: 2026-09-26
- Source: WIRE-001 reference workflow audit
- Decision: Adopt the audit's process controls for task scoping, evidence classification, raw/processed evidence, exact-commit reproducibility, compact project state, requirements traceability, and controlled experiments.
- Scope: Workflow only. No protocol, RTL, toolchain, or architecture requirement is changed.
- Rationale: These controls are supported by the inspected RTL-to-Pixels workflow and strengthened by later repository references.
- Status: ADOPTED

## WIRE-D002 — Lock external protocol source basis and explicit MVP restrictions

- Date: 2026-09-27
- Source: WIRE-002 external protocol specification lock
- Decision: Use RFC 894, RFC 791, RFC 768, the current Nasdaq MoldUDP64 V 1.00 artifact, and the current Nasdaq-linked TotalView-ITCH 5.0 artifact as the external source basis. Keep the MVP restrictions and validation rules documented in the WIRE-002 evidence report.
- Scope: External source authority and Phase-0 MVP protocol profile only. No RTL, model, verification, timing, or performance requirement is established by this decision.
- Rationale: The source audit distinguishes protocol facts from deliberate project restrictions, including Ethernet II/IPv4 only, non-fragmented IPv4, zero-only UDP checksums, fail-closed Mold discontinuities, and one configured ITCH Stock Locate.
- Status: ADOPTED
