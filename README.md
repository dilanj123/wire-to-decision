# Wire-to-Decision

An evidence-driven single-clock FPGA network-processor MVP. The design accepts complete Ethernet frames at a post-MAC 64-bit ready/valid boundary, parses a frozen IPv4/UDP/MoldUDP64/ITCH subset, updates a bounded order store, and emits deterministic threshold-crossing decisions.

```text
64-bit post-MAC beats
  → ingress buffer → byte gearbox → Ethernet / IPv4 / UDP
  → MoldUDP64 header + message blocks → ITCH subset
  → normalized mutation → 512 × 2 order book / aggregates
  → risk-budgeted BUY / SELL decision
```

## Scope and implementation

The production baseline is Architecture A. It supports IPv4 over Ethernet II, UDP with the project’s zero-only checksum policy, MoldUDP64 framing, and ITCH A/F/E/C/X/D/U mutations plus P as non-mutating traffic. The order store has 512 sets × 2 ways, the WIRE-D006 XOR-fold hash, no eviction, and checked 48-bit bid/ask aggregates. This is a synthetic functional project, not a trading strategy or live market-data client.

Important RTL: [functional top](rtl/arch_a/wire_arch_a_functional_top.sv), [parser top](rtl/arch_a/wire_arch_a_parser_top.sv), [bounded order book](rtl/common/wire_order_book.sv), and [decision engine](rtl/common/wire_decision_engine.sv). The separate [CDC wrapper](rtl/arch_a/wire_arch_a_cdc_top.sv) demonstrates an 8 × 73-bit asynchronous ingress FIFO; it does not change the single-clock baseline.

## Reproduce key checks

Commands below use the qualified OSS CAD Suite selected by WIRE-004. Set `WIRE_TO_DECISION_OSS_CAD_SUITE` if it is installed outside the default path.

```bash
source tools/env/setup_oss_cad_suite.sh
set -e

# Python reference regression
PYTHONPATH=model/python python3 -m unittest discover -s model/python/tests -v

# Independent C++20 checker and hand-calculated replay tests
make -C tools/cpp clean test

# Generate a real functional-top decision log, then compare it to packet replay
run_cocotb() {
  local test_dir="$1"
  ln -s "$WIRE_TO_DECISION_OSS_CAD_SUITE/lib" "$test_dir/lib"
  local result=0
  if (cd "$test_dir" && make clean && make SIM=verilator); then
    result=0
  else
    result=$?
  fi
  unlink "$test_dir/lib"
  return "$result"
}
run_cocotb tb/cpp_replay
tools/cpp/build/w2d_checker compare \
  tools/cpp/replays/canonical.w2d \
  results/raw/cpp/rtl_decisions.log \
  results/raw/cpp/summary.json

# Representative full Architecture-A functional-top regression
run_cocotb tb/functional_mvp

# Representative bounded formal check (not a whole-design proof)
(cd formal/decision_engine && sby -f decision_reference.sby)
```

The C++ tool reads `WIRE_REPLAY_V1` text: one configuration line followed by `FRAME <hex>` records and optional `ENABLE`/`REARM` actions. It derives expected decisions from packet bytes, compares them with `WIRE_RTL_LOG_V1` records emitted by the Cocotb functional-top run, and writes JSON counts, final aggregate/sequence state, mismatch status, and latency distributions. Latency is in simulation cycles: L1 first ITCH payload-byte transfer to its normalized-event valid/handshake; L2 final ITCH payload-byte transfer to decision valid; L3 first accepted external frame beat to decision valid. Median is the midpoint (average for even sample counts); p95 uses nearest rank (`ceil(0.95 × n)`). These are not physical FPGA latency measurements.

## Verification and implementation evidence

- Python oracle: 71 unit tests passed.
- WIRE-025 focused campaign: 109 Cocotb tests and 79 executed bounded/fixed/reduced SBY jobs passed. Two historical monolithic jobs remain solver-bound and are not counted as passes.
- WIRE-030 C++ replay: hand-calculated fixtures pass; canonical RTL replay compares 4 frames, 3 Mold messages, and 2 decisions with zero mismatches. A corrupted decision log is detected. See [WIRE-030 report](results/processed/WIRE-030-cpp-and-closeout.md) and [raw C++ evidence](results/raw/cpp/).
- Architecture A: full-capacity ECP5 synthesis and five-seed place/route completed. WIRE-027 routed Fmax was **45.68–47.66 MHz**; all seeds missed the **156.25 MHz** objective. The measured critical path was in the EBR-based order-store read/update logic.
- Architecture B was implemented only as a controlled experiment and rejected: it used about 1.97× Architecture-A LUT4 and routed more slowly, despite fewer simulation cycles. See [A/B comparison](results/processed/WIRE-028-architecture-ab-comparison.md).
- WIRE-029 CDC learning wrapper and local bounded checks passed. Physical Gray-bus skew and commercial CDC/RDC signoff remain open.

Primary evidence index: [docs/EVIDENCE_INDEX.md](docs/EVIDENCE_INDEX.md). Implementation target and saved commands/reports: [docs/IMPLEMENTATION_TARGET.md](docs/IMPLEMENTATION_TARGET.md), [WIRE-027 raw implementation evidence](results/raw/implementation/wire027/), and [Architecture-B raw experiment evidence](results/raw/implementation/arch_b/). The exact synthesis and P&R command records are `results/raw/implementation/wire027/synthesis_command.txt` and `results/raw/implementation/wire027/pnr_command.txt`.

## Engineering retrospective

Architecture A was selected as a readable byte-serial parser baseline with a shared bounded book and deterministic decision stage. The first full ECP5 synthesis exposed a LUT-RAM fit failure; WIRE-026A changed the order-store access to synchronous packed rows and mapped the 1,024-entry data to 16 EBRs. A registered write-plan experiment improved the five-seed routed Fmax range from 42.70–45.45 MHz to 45.68–47.66 MHz, but did not close timing. Parser service was then isolated from book service, motivating a small direct-beat B experiment. B reduced simulated cycles but added parser complexity and LUT cost while reducing routed clock frequency, so it was rejected for this baseline. Verification work emphasized public ready/valid boundaries, malformed suffixes, backpressure, explicit rearm, and bounded formal claims; the CDC extension also made the remote reset-observation delay explicit.

## Limitations

- The 156.25 MHz target is not met; no timing closure is claimed.
- No physical FPGA operation, physical latency/throughput measurement, board pinout, or package I/O timing validation exists.
- Formal results are bounded or fixed/reduced-scope checks, not a whole-design proof; historical solver-bound jobs remain unresolved.
- CDC simulation/formal checks do not prove metastability resolution, physical Gray-pointer bus skew, or commercial CDC/RDC signoff.
- No live market connectivity, exchange recovery service, trading strategy, or trading functionality is implemented.
- Phase 11 vendor-flow and physical-board extensions are optional and have not been started.
