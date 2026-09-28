# WIRE-018 — UDP Parser RTL Evidence

## A. Starting state and authority

The task started on `main` at `91c51ad9fd097795c9a4b53049e240f785a3b416`, with local `main == origin/main` and a clean tree. Authority included the frozen protocol/profile documents, WIRE-017 evidence, the Python framing model, and existing ingress/gearbox/Ethernet/IPv4 RTL.

## B. Architecture and semantics

`rtl/arch_a/wire_udp_parser.sv` consumes the IPv4 byte stream and exposes configured destination-port input, byte ready/valid input and output, and a local rejection ready/valid channel. It consumes the 8-byte header, ignores source port, decodes fields big-endian, requires Length >= 8 and exact physical length, accepts only checksum zero, and forwards only nonempty UDP payload bytes. Length mismatch has priority over destination/checksum; destination mismatch has priority over checksum.

`UDP_EMPTY_PROJECT_PAYLOAD` is the WIRE-D014 local fatal result for exact valid UDP Length 8. This represents the project byte-stream boundary and is not a claim about UDP generally. The Python model remains unchanged and reaches its later empty MoldUDP64 failure.

## C. Error and backpressure behavior

Header truncation, length mismatch, and empty project payload are fatal. Wrong destination and nonzero checksum are nonfatal filters. Rejections are held stable until handshake and block new input/output. Accepted payload output is held stable under backpressure. A declared-boundary/physical-extra case is dropped and reported as fatal length; an early physical end can leave a speculative prefix already transferred, with no successful terminal marker.

## D. Verification

Standalone cocotb: 5/5 PASS. Composition cocotb: 3/3 PASS. Random seeds 1, 7, and 19 are retained. The composition checks the full current five-stage path and no header leakage, loss, duplication, reordering, or incorrect final marking.

Verilator lint/build passed with no meaningful warnings. Yosys standalone and composition synthesis/elaboration sanity passed. Python regression remained 71/71.

## E. Formal scope

The decomposed public-interface-only jobs use SBY 0.69, `smtbmc yices`, Yices 2.7.0. Passing bounded jobs are: safety depth 20; fixed header/priority cases depth 20; accepted payload correspondence depth 24; physical-short length depth 20; physical-long length depth 24; next-packet behavior depth 32; cover depth 24. The jobs use synchronous reset initialization and normal upstream ready/valid stability; targeted fixed-vector jobs hold downstream ready high and document that scope. No DUT-private state is used. Covers are reachability evidence, not proofs. Numeric/header-space coverage is not exhaustive.

## F. Limitations and classification

The UDP stage is RTL-simulated. Named local UDP properties are formally checked under documented bounded/fixed-vector assumptions and scopes. The five-stage composition is RTL-simulated and Yosys is component synthesis sanity only. WIRE-018 does not establish end-to-end mutation suppression for late UDP length errors, before-ITCH mutation gating, MoldUDP64, ITCH, order state, decisions, P&R, timing, latency, or throughput.

## G. Conclusion

WIRE-018 stage and composition evidence passed its recorded local scope. No protocol scope beyond UDP was added. Next smallest task: WIRE-019 — Architecture A MoldUDP64 packet-header and sequence-controller RTL and verification.
