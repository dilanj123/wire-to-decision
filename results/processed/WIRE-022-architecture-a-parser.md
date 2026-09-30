# WIRE-022 — Architecture-A Parser Integration and Phase-2 Closure

## A. Starting state and authority

Starting HEAD: `cdaee3ac49654160de13413d420db8316adf6882`; branch `main`, clean and equal to `origin/main`. Protected `kg-g0-env^{}` remained `06f5643a940ac2c6fcfab0e377169b48ce700107`. WIRE-020 and WIRE-021 were already PASS, pushed and documented. Repository authority and stage contracts were reviewed; no conflict found.

## B. WIRE-D018

WIRE-D018 freezes immediate parser-wide fatal suppression/recovery, current external frame drain only, no acceptance of a subsequent frame before explicit rearm/reset, independence of ITCH semantic failure from Mold structural success, and no rollback of complete events already handshaken before a later failure. Rearm clears transient/recovery parser state and loads a known configuration epoch; it is not automatic protocol recovery.

## C. Complete parser architecture

The new `rtl/arch_a/wire_arch_a_parser_top.sv` connects:

`64-bit framed ingress → two-entry ingress buffer → 64-to-8 gearbox → Ethernet II → IPv4 → UDP → Mold header/sequence → Mold message framer → ITCH decoder → WIRE-D017 event`.

Inputs include synchronous `clk/rst`, `rearm`, destination IPv4/UDP port, active Mold session/expected sequence, tracked Stock Locate, symbol-check enable/expected 8-byte symbol, and `rx_data[63:0]/rx_keep[7:0]/rx_valid/rx_ready/rx_last`. Output event interface exactly forwards WIRE-D017 fields. Additional outputs expose parser validity/recovery stage/current Mold expected sequence and stage reject observations.

## D. Recovery, filtering and event policy

Fatal Ethernet, IPv4, UDP, Mold header/sequence, Mold structural, or ITCH semantic errors latch parser recovery. Nonfatal unsupported EtherType, IPv4 profile/destination filters, wrong UDP destination, and unsupported nonzero UDP checksum are consumed without recovery. Mold structural failure drives WIRE-019 packet-result failure; ITCH semantic recovery is separate and does not modify that structural result. A fatal result immediately masks event-valid and event-ready. Prior handshaken events are not retracted; no rollback is implemented.

The top tracks accepted external frame boundaries. When recovery becomes known mid-frame, it continues to accept only that frame’s remaining beats, subject to ingress-buffer readiness, through accepted `rx_last`. It then blocks the next frame. If the frame had already fully transferred at detection, input is blocked immediately. Reset/rearm synchronously resets all parser stages and the top recovery epoch.

## E. End-to-end simulation

Full post-MAC 64-bit ingress cocotb: **6/6 PASS** with Verilator 5.053 and cocotb 2.1.0.dev0+41564633. Directed coverage is organized into tests for A/F/E/C/X/D/U and every event field with WIRE-010 Python comparison; P, other Stock Locate, heartbeat, multi-message and nonfatal filter/reuse; structural late suffix and ITCH quarantine; semantic and outer fatal/rearm; Mold header/EOS/trailing; and replayable random frames. Random seeds: **1, 7, 19, 42, 97**. Consumer `event_ready` stalls are deterministically randomized. Raw replay output is retained in `cocotb_full_ingress.log`.

For the late malformed suffix, two complete valid mutation messages handshook events before a third structurally truncated message. No third event appeared; WIRE-020 structural result failed; Mold expected sequence did not advance; parser recovery asserted; the external frame was drained; a following frame was blocked until rearm. Earlier event handshakes remained committed. For a structurally valid Mold packet with unsupported ITCH content, WIRE-020 succeeded and WIRE-019 advanced by the structural message count while ITCH/top recovery asserted and later semantic events were suppressed.

The seven event mappings are compared field-by-field with the existing WIRE-010 decoder. Python model regression: **71/71 PASS**. No production Python behavior was changed.

## F. Formal evidence and limits

Top-level public-port safety harness: depth-20 BMC PASS with SBY 0.69, `smtbmc yices`, Yices 2.7.0. It assumes reset initially and legal source stability while `rx_valid && !rx_ready`; event readiness is unconstrained. It checks stalled event stability, event suppression in recovery, blocking new frame acceptance after recovery/current-frame close, and rearm clearing recovery. No DUT-private state is used.

The full-top fixed-vector late-suffix BMC used depth 270 and was solver-bound after step 69 / about 2:06, with no counterexample observed. It is neither PASS nor FAIL. Its raw SBY log/workspace is retained. The scenario passes full-ingress cocotb and is supported by independently rerun decomposed lower-stage public-interface formal jobs from WIRE-019/020/021. Those local bounded/fixed-vector checks do not constitute an end-to-end unbounded proof.

All established WIRE-014..021 formal jobs were rerun: **68 PASS**, excluding the historical WIRE-017 monolithic IPv4 BMC (solver-bound after step 22 by WIRE-017A record). Stage-local jobs include their documented assumptions and bounded/fixed-vector scopes; no claim of complete parser formal proof is made.

## G. Tool and regression results

- Strict Verilator full-top lint (`--lint-only --Wall`): PASS, no warnings.
- Yosys 0.69+154 full-top hierarchy, process, synthesis and `check -assert`: PASS; eight stage submodules, 8,554 generic cells. Component synthesis sanity only.
- Standalone cocotb WIRE-014..021: respectively 6/6, 5/5, 4/4, 5/5, 5/5, 14/14, 10/10, 6/6 PASS.
- Prior composition regressions WIRE-015..021: respectively 1/1, 1/1, 3/3, 3/3, 2/2, 2/2, 2/2 PASS. WIRE-022 full ingress: 6/6 PASS.
- Python reference suite: 71/71 PASS.
- No application P&R or performance measurement was run.

## H. Requirement traceability and evidence classification

EVID-022 supports integrated parser-stage behavior across applicable REQ-IF-001..005, REQ-ETH-001..003, REQ-IP-001..007, REQ-UDP-001..004, REQ-MOLD-001..009, REQ-ITCH-001..004 and REQ-ERR-001..005. End-to-end mutation rollback/order-state protection is not established; complete earlier event handshakes persist across later suffix failure by WIRE-D018, and no order-state RTL exists.

Classification: complete current Architecture-A parser `RTL-SIMULATED`; named stage and top properties `FORMALLY CHECKED UNDER DOCUMENTED ASSUMPTIONS` at recorded bounded/fixed-vector scopes; complete parser Yosys `SYNTHESISED COMPONENT SANITY`.

Still unproven/not implemented: bounded order state and aggregates RTL, decision RTL, parser-to-state mutation commit gating/rollback, complete parser formal proof, application P&R/timing/latency/throughput, Architecture-B authorization, CDC/RDC, C++ checker, physical FPGA operation. Phase 2 is complete; Phase 3 is next. No Phase-3 work is included.
