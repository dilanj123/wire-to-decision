# WIRE-028A — Simplify Architecture-B synthesis

## Historical result

WIRE-028A's packed 352-bit ITCH message-buffer change was a valid narrow investigation but did not by itself close synthesis. The first report's `PROC_MEMWR` diagnosis was corrected: that pass completed, and the original eight-lane unrolled control graph remained the synthesis obstacle. Its parser-only ECP5 run stopped in `FSM_EXTRACT` after 461.10 s.

The final WIRE-028B follow-up limited the source-ordered parser walk to two byte lanes per cycle. It completed functional checks, full benchmark synthesis and five-seed routing. The combined WIRE-028 experiment is now complete and rejects B for the current baseline based on measured LUT cost, routed frequency and derived throughput. See `tasks/WIRE-028B.md` and `results/processed/WIRE-028-architecture-ab-comparison.md`.

The original WIRE-028A raw logs are preserved.
