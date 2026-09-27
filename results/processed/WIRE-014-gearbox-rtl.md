# WIRE-014 — Architecture A 64-to-8 gearbox RTL and verification

## A. Starting state

Repository started clean at `7268fe898f27950aec2470523c698c8f464fd845`; `main` matched `origin/main`; `kg-g0-env` remained peeled at `06f5643a940ac2c6fcfab0e377169b48ce700107`.

## B. Authority and documentation corrections

Requirements and microarchitecture define lane 0 as the earliest byte, legal contiguous `keep`, and ready/valid transfer semantics. WIRE-D011 freezes synchronous active-high `rst` for Phase-2 single-clock primitives. Stale project-state Python-oracle/regression text and the evidence-index opening were corrected without changing functional requirements.

## C. Gearbox interface and implementation

`rtl/arch_a/wire_gearbox_64to8.sv` accepts `in_data[63:0]`, `in_keep[7:0]`, `in_valid`, `in_last`, and `in_ready`; it emits `out_data[7:0]`, `out_valid`, `out_last`, and accepts `out_ready`. One local beat register serializes lane 0 through the legal keep count. Beat retirement is distinct from frame termination, allowing same-cycle refill across non-final beats while asserting `out_last` only for the final valid byte of a frame.

## D. Cocotb/Verilator result

The independent scoreboard passed six tests: all eight legal final keep masks, multi-beat/back-to-back frames, output stalls and input pressure, same-cycle retire/refill, reset while idle/stalled/partial, and deterministic randomized legal frames with seeds 1, 7, and 19. Verilator 5.053 lint/build passed without meaningful warnings. The cocotb test count is 6.

## E. Formal result

SBY v0.69 with `smtbmc yices`, Yices 2.7.0, depth 20 passed both prove and cover. The safety harness assumes legal keep masks and stable upstream payload while `in_valid && !in_ready`. Assertions cover stalled output payload stability, `out_last` validity, first-byte loading, and same-cycle final-frame refill; cover demonstrates refill reachability. The independent byte-order/count/last conservation oracle is the cocotb scoreboard; no claim is made that the local harness proves the complete parser.

## F. Synthesis sanity

Yosys 0.69+154 successfully elaborated and optimized the gearbox as a component sanity check. No application P&R, timing, or PPA run was performed.

## G. Evidence classification

- Gearbox functional behavior: `RTL-SIMULATED`.
- Named local properties: `FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS`.
- Gearbox elaboration: `SYNTHESISED COMPONENT SANITY`.
- Python reference model remains `PYTHON-UNIT-TESTED`; the 71-test regression passed.

## H. Scope remaining

Common ingress buffering, protocol parser RTL, normalized-event integration, bounded-state RTL, decision RTL, full Architecture-A regression, application formal properties, P&R/timing/latency/throughput, CDC/RDC, C++ integration, and physical FPGA operation remain unproven.

## I. Conclusion

WIRE-014 passes its scoped gearbox simulation and local formal acceptance criteria. No protocol scope or Architecture-B authorization changed.
