# Third-Party Reference and Reuse Manifest

WIRE-003 records immutable upstream revisions reviewed for provenance and workflow/reference purposes. “Pinned” means the exact commit inspected; it does not create a dependency, submodule, or permission to copy source.

## Summary

| ID | Project | Canonical upstream | Pinned commit | Licence | Classification | Incorporated? | Intended use |
|---|---|---|---|---|---|---|---|
| TP-001 | verilog-ethernet | https://github.com/alexforencich/verilog-ethernet | `77320a9471d19c7dd383914bc049e02d9f4f1ffb` | MIT; `COPYING` | REFERENCE_ONLY | NOT_INCORPORATED | Historical Ethernet/IP/UDP and streaming/testbench reference |
| TP-002 | cocotbext-eth | https://github.com/alexforencich/cocotbext-eth | `2ae8a17903e31206140429c036e68cb4d4a0cf24` | MIT; `LICENSE` | POTENTIAL_TEST_ONLY_DEPENDENCY | TEST_DEPENDENCY_NOT_YET_INSTALLED | Possible future Ethernet test infrastructure |
| TP-003 | Corundum | https://github.com/corundum/corundum | `1ca0151b97af85aa5dd306d74b6bcec65904d2ce` | BSD-style; mixed source SPDX | REFERENCE_ONLY | NOT_INCORPORATED | NIC/system testbench and implementation-method reference |
| TP-004 | Taxi | https://github.com/fpganinja/taxi | `cc70b270b910d369ab1ad7b3855e76399fd461f1` | CERN-OHL-S-2.0 or commercial; mixed components | REFERENCE_ONLY | NOT_INCORPORATED | Modern successor and network-component reference |
| TP-005 | Itch-Parser | https://github.com/tmlee06/Itch-Parser | `6aebfc3e37c58f4d965ef80e4689a30541bca68e` | README states MIT; no licence file found | REFERENCE_ONLY_DIRECT_OVERLAP | NOT_INCORPORATED | High-level comparison only; direct ITCH/order-book overlap |
| TP-006 | fpga-tick-to-trade | https://github.com/namangoyal-work/fpga-tick-to-trade | `ee3ef5fab4d82127c74733e037231e2c7f1f8f58` | MIT; `LICENSE` | REFERENCE_ONLY_DIRECT_OVERLAP | NOT_INCORPORATED | High-level portfolio/process comparison only |
| TP-007 | PULP common_cells | https://github.com/pulp-platform/common_cells | `e73baaec2ca665cd80c3c384e9258e35242b829c` | SHL-0.51; mixed support-file SPDX | REFERENCE_ONLY_CDC_BENCHMARK | NOT_INCORPORATED | CDC/reset/FIFO benchmark only |

## Detailed entries

### TP-001 — verilog-ethernet

- Canonical repository: https://github.com/alexforencich/verilog-ethernet
- Pinned commit/date: `77320a9471d19c7dd383914bc049e02d9f4f1ffb`, 2025-02-27T15:50:25-08:00
- Default branch: `master`; description: Verilog Ethernet components for FPGA implementation.
- Licence: `COPYING`, MIT-style text; SHA-256 `8ea57f95365e9b16a5b516f422b71269183a1ae53bab5878ae6d69039e58fe77`; GitHub API reports MIT.
- Relevant areas: `rtl/`, `tb/`, `example/`.
- UPSTREAM FACT: README explicitly marks the repository deprecated and says it is superseded by Taxi; new features and fixes move to Taxi.
- Classification: REFERENCE_ONLY. The deprecation reduces its value as a current dependency but preserves historical value for Ethernet/IP/UDP interfaces, streaming structures, and testbench patterns.
- Allowed use: high-level comparison and citation of public workflow/interface ideas.
- Prohibited use: copied RTL, structural derivation of the mandatory parser, or dependency addition.
- Incorporation status: NOT_INCORPORATED.
- Refresh policy: refresh only through a new task with a new full commit and licence review.

### TP-002 — cocotbext-eth

- Canonical repository: https://github.com/alexforencich/cocotbext-eth
- Pinned commit/date: `2ae8a17903e31206140429c036e68cb4d4a0cf24`, 2026-08-28T11:00:56-07:00
- Default branch: `master`; description: Ethernet interface modules for Cocotb.
- Licence: `LICENSE`, MIT-style text; SHA-256 `d10da1a65b4ba610e3df21fc1b8122dca0043e8ee7715eaf341d5d8a4a560729`; setup metadata identifies MIT.
- Relevant areas: `cocotbext/eth/`, `tests/` including GMII/MII/RGMII/XGMII.
- Classification: POTENTIAL_TEST_ONLY_DEPENDENCY.
- Allowed use: later, pinned verification infrastructure if independently reviewed and explicitly added.
- Prohibited use: installing or adding it in WIRE-003; treating it as the sole expected-value source; using it to define Wire-to-Decision semantics.
- Independent project-owned verification required later: packet builders, protocol fixtures, reference checks, malformed-frame cases, and expected state/decision results must remain independently owned where required by the verification plan.
- Incorporation status: TEST_DEPENDENCY_NOT_YET_INSTALLED.
- Refresh policy: pin a new commit and review licence before installation or version change.

### TP-003 — Corundum

- Canonical repository: https://github.com/corundum/corundum
- Pinned commit/date: `1ca0151b97af85aa5dd306d74b6bcec65904d2ce`, 2023-12-02T01:30:49-08:00
- Default branch: `master`; description: open-source FPGA-based NIC and platform for in-network compute.
- Licence: `LICENSE`, BSD-2-Clause-style text; SHA-256 `e718ce52d815d36c0576b9f759001200731db9b16775286ffc1b66bbf97eb1b6`; source files include BSD-2-Clause-Views and some Apache-2.0/MIT identifiers. GitHub API reports no single licence assertion.
- Relevant areas: `fpga/`, `modules/`, `scripts/`, `docs/`, and system test infrastructure.
- UPSTREAM FACT: README covers high-performance NIC, PCIe, queues, DMA, Ethernet, and broad system simulation.
- Classification: REFERENCE_ONLY.
- Allowed use: high-level system/testbench organisation and implementation methodology.
- Prohibited use: NIC, PCIe, DMA, Ethernet datapath, queue, or driver RTL reuse.
- Incorporation status: NOT_INCORPORATED.
- Refresh policy: re-audit the exact commit and individual file headers before any hypothetical reuse.

### TP-004 — Taxi

- Canonical repository: https://github.com/fpganinja/taxi
- Pinned commit/date: `cc70b270b910d369ab1ad7b3855e76399fd461f1`, 2026-08-28T13:34:16-07:00
- Default branch: `master`; description: AXI, AXI stream, Ethernet, and PCIe components in SystemVerilog.
- Licence: `LICENSE`, CERN Open Hardware Licence Version 2 — Strongly Reciprocal; SHA-256 `253ad3f89603e728abfa60c36fbcaf8225cf55c1eab12725f19fb3d74d647f3a`; README states CERN-OHL-S 2.0 or a paid commercial licence, with some components potentially less restrictive. SPDX identifiers observed include CERN-OHL-S-2.0, BSD-3-Clause, MIT, and GPL.
- Relevant areas: `src/eth/`, `src/axis/`, `src/sync/`, and associated documentation/test infrastructure.
- UPSTREAM FACT: README identifies Taxi as the home of modern network components and the next-generation Corundum ecosystem.
- Classification: REFERENCE_ONLY.
- Project conclusion: the strongly reciprocal licence and mixed-component licensing require file-level review before any reuse; they are a reason to keep Taxi out of the mandatory datapath under the current originality policy. This is a conservative project policy, not legal advice.
- Allowed use: high-level reference and comparison only.
- Prohibited use: Taxi RTL in the mandatory datapath or structural derivation of Wire-to-Decision architecture.
- Incorporation status: NOT_INCORPORATED.
- Refresh policy: refresh commit and per-file licence review before any future consideration.

### TP-005 — Itch-Parser

- Canonical repository: https://github.com/tmlee06/Itch-Parser
- Pinned commit/date: `6aebfc3e37c58f4d965ef80e4689a30541bca68e`, 2026-06-16T17:54:50+09:00
- Default branch: `main`; description directly identifies an FPGA NASDAQ ITCH 5.0 decoder and limit order book.
- Licence: no `LICENSE` file was found at the pinned commit; README states “MIT — free to use, modify, and build on”; SHA-256: not applicable. The README statement is recorded, not independently upgraded into a legal conclusion.
- Relevant files: `itch_decoder.v`, `order_book.v`, stream adapter/top-level files, and testbenches.
- Classification: REFERENCE_ONLY_DIRECT_OVERLAP.
- Allowed use: high-level comparison and acknowledgement that comparable work exists.
- Prohibited use: copying RTL, parser FSMs, order-book architecture, field mux structure, module partitioning, verification properties, or structural design patterns.
- Incorporation status: NOT_INCORPORATED.
- Refresh policy: do not refresh for implementation reuse; any future citation refresh must re-check the repository and licence evidence.

### TP-006 — fpga-tick-to-trade

- Canonical repository: https://github.com/namangoyal-work/fpga-tick-to-trade
- Pinned commit/date: `ee3ef5fab4d82127c74733e037231e2c7f1f8f58`, 2026-07-05T09:59:34+02:00
- Default branch: `main`; description and README describe an FPGA tick-to-trade engine with Ethernet/IPv4/UDP parsing, formal verification, and fixed-latency decisions.
- Licence: `LICENSE`, MIT License; SHA-256 `b4b3bce4fdab7ccc1ffe899b993ce1b8ad25836f8ebe9e420ea12b9179b6960a`.
- Relevant areas: `rtl/`, `tb/`, `formal/`, `synth/`, `tools/`, `docs/`.
- Classification: REFERENCE_ONLY_DIRECT_OVERLAP.
- Allowed use: high-level comparison of published workflow and portfolio positioning.
- Prohibited use: copying or structurally deriving parser, decision, FIFO, formal, verification, or integration design.
- Incorporation status: NOT_INCORPORATED.
- Refresh policy: no implementation reuse; refresh only for a separately approved comparison audit.

### TP-007 — PULP common_cells

- Canonical repository: https://github.com/pulp-platform/common_cells
- Pinned commit/date: `e73baaec2ca665cd80c3c384e9258e35242b829c`, 2026-09-18T17:10:47+00:00
- Default branch: `master`; description: Common SystemVerilog components.
- Licence: `LICENSE`, Solderpad Hardware License version 0.51 / SHL-0.51; SHA-256 `6527a46225891b976fa94f634f6ee0cd22e1c7129d6f11c5c98c997627625fc7`; common source/formal/test files use SHL-0.51, while selected support files use Apache-2.0.
- Relevant areas: `src/` CDC/reset/FIFO cells, `formal/`, `test/`, `include/`.
- Classification: REFERENCE_ONLY_CDC_BENCHMARK.
- Allowed use: benchmark concepts and compare later verification/implementation methodology.
- Prohibited use: common_cells RTL in the mandatory asynchronous FIFO, CDC, reset, or recovery architecture.
- Incorporation status: NOT_INCORPORATED.
- Refresh policy: review individual source-file SPDX headers and licence before any future consideration.

## Project dependency result

- Mandatory core RTL dependencies: NONE.
- Mandatory parser/book/decision dependencies: NONE.
- Approved installed dependencies added by WIRE-003: NONE.
- Potential future test dependency: cocotbext-eth, pinned/audited but not installed.
- All other audited projects remain reference-only.

## Originality firewall

Direct-overlap third-party market-data/parser/order-book projects may be studied for high-level comparison, interface awareness, tool-flow ideas, and published results, but Wire-to-Decision core RTL, parser microarchitecture, book architecture, decision logic, formal properties, and reference models must not be copied or structurally derived from them.

Generic infrastructure references do not become project dependencies merely because they were audited.

Third-party test infrastructure may be used later only when its version is pinned and its role is clearly separated from independent project-owned expected-value/reference logic.
