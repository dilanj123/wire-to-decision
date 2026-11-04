# WIRE-028 — Minimal Architecture-B Native-64 Parser

## Final status

**PASS as a controlled A/B experiment; Architecture B REJECTED for the current project baseline.** Architecture A remains the production implementation. B was authorized only for this experiment and was not integrated as the production path.

The original design note and WIRE-028A investigation are retained as history. Final implementation advances up to two consecutive valid lanes per clock, demonstrated by cursor instrumentation; remaining lanes stay in the registered beat and are not dropped. The 64-bit input interface, protocol subset and shared production 512×2 book/decision logic were retained.

Final evidence: `tasks/WIRE-028B.md` and `results/processed/WIRE-028-architecture-ab-comparison.md`. B parser comparison 8/8, B functional integration 2/2, Python 71/71, formal BMC PASS depth 12, Verilator PASS; full B synthesis completed and five seeds routed. B did not meet the 156.25 MHz objective. It uses 14,559 LUT4 versus A's 7,376, routes at 19.997–21.047 MHz versus A's 45.68–47.66 MHz, and has lower derived end-to-end byte rate at each architecture's conservative routed-frequency estimate. The measured result does not justify B's added complexity/resources. No production replacement or timing closure is claimed.

## Historical stages

- Initial WIRE-028 used an eight-lane source-ordered state walk; synthesis did not complete within the initial run.
- WIRE-028A corrected the pass diagnosis and packed the 44-byte ITCH message buffer; parser-only synthesis remained in FSM extraction.
- WIRE-028B restricted the lane walk to two bytes per cycle and completed parser/full-top synthesis, verification, and five-seed routing.

Earlier raw failed/interrupted runs remain under `results/raw/implementation/arch_b/` and are historical, not final outcomes.
