# WIRE-018 — Architecture A UDP Byte Parser RTL and Verification

Phase 2 task. Starting HEAD: `91c51ad9fd097795c9a4b53049e240f785a3b416`.

## Scope

Implement only the fixed 8-byte UDP byte parser after the existing Ethernet and IPv4 stages. The stage consumes source port, validates exact UDP Length against its IPv4-payload input, filters configured destination port, accepts checksum zero only, strips the header, forwards nonempty payload, and reports fatal/nonfatal local rejection outcomes. MoldUDP64, ITCH, state, decisions, Architecture B, CDC, P&R, and performance claims are excluded.

## Authority and decisions

- WIRE-D011: synchronous active-high `rst`.
- WIRE-D012: common two-beat ingress buffer remains unchanged.
- WIRE-D013: IPv4 zero-byte project payload is a local fatal representation rule.
- WIRE-D014: an otherwise valid exact 8-byte UDP datagram is locally rejected as fatal `UDP_EMPTY_PROJECT_PAYLOAD`; this is not a general UDP requirement and the Python model remains unchanged.

Validation priority is physical header truncation, UDP Length, destination port, then checksum. A late physical length mismatch may leave an already-forwarded speculative prefix; downstream mutation suppression remains future integration scope.

## Verification

Standalone cocotb uses an independent byte scoreboard with fixed random seeds 1, 7, and 19. Composition verifies buffer→gearbox→Ethernet→IPv4→UDP. Verilator and Yosys are run on the stage and composition. Formal jobs use only public DUT ports, SBY/Yices, and documented bounded/fixed-vector scopes for safety, header priority cases, payload, short/long length, and next-packet behavior; cover is reported separately.

## Acceptance and evidence

Required evidence is retained under `results/raw/rtl/udp_parser/` and summarized in `results/processed/WIRE-018-udp-parser-rtl.md`. Push is permitted only after all required simulation, regression, synthesis-sanity, and formal jobs pass. The next task is WIRE-019; it is not part of this task.
