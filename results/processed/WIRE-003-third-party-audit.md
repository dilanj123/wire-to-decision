# WIRE-003 — Third-Party Reference/Reuse Audit and Pinning

Status: PASS — provenance, licence, and reuse-policy evidence only. No source was incorporated and no implementation work was performed.

## A. Audit scope

The audit covered the seven mandatory repositories named by WIRE-003. The goal was to establish canonical identity, immutable inspected revision, licence evidence, relevance, maintenance/deprecation observations, and conservative project classification. No optional repository was added.

Starting Wire-to-Decision state: `/Users/Dilan/Projects/wire-to-decision`, branch `main`, HEAD `1b8dc248c185b9c1f8354eafc258bb3054b8e0c0`, clean working tree. The current authority documents were read first; missing authority files were not fabricated.

## B. Audit method

Each repository was cloned read-only with `git clone --depth 1` into `/tmp/wire-to-decision-third-party-audit.GtKoNw/`. Default branch, HEAD, commit date, remote, README, licence files, source SPDX headers, and relevant directories were inspected. GitHub API metadata was used only for repository description, default branch, archive state, and API licence field. Licence files were hashed with SHA-256. Raw commands and observations are in `results/raw/third_party/`.

The shallow clone was not placed under `third_party/`; no package was installed; no submodule, fork, tarball, or source snapshot was created.

## C. Repository identity and pins

| ID | Repository | Default branch | Inspected commit | Commit date | Archived |
|---|---|---|---|---|---|
| TP-001 | `alexforencich/verilog-ethernet` | `master` | `77320a9471d19c7dd383914bc049e02d9f4f1ffb` | 2025-02-27 | no |
| TP-002 | `alexforencich/cocotbext-eth` | `master` | `2ae8a17903e31206140429c036e68cb4d4a0cf24` | 2026-08-28 | no |
| TP-003 | `corundum/corundum` | `master` | `1ca0151b97af85aa5dd306d74b6bcec65904d2ce` | 2023-12-02 | no |
| TP-004 | `fpganinja/taxi` | `master` | `cc70b270b910d369ab1ad7b3855e76399fd461f1` | 2026-08-28 | no |
| TP-005 | `tmlee06/Itch-Parser` | `main` | `6aebfc3e37c58f4d965ef80e4689a30541bca68e` | 2026-06-16 | no |
| TP-006 | `namangoyal-work/fpga-tick-to-trade` | `main` | `ee3ef5fab4d82127c74733e037231e2c7f1f8f58` | 2026-07-05 | no |
| TP-007 | `pulp-platform/common_cells` | `master` | `e73baaec2ca665cd80c3c384e9258e35242b829c` | 2026-09-18 | no |

The full URLs, descriptions, exact timestamps, and licence hashes are in the raw evidence and manifest.

## D. Licence findings

### UPSTREAM FACT

- TP-001 has an MIT-style `COPYING`; GitHub API reports MIT.
- TP-002 has an MIT-style `LICENSE`; setup metadata identifies MIT.
- TP-003 has BSD-2-Clause-style top-level text. Source headers include BSD-2-Clause-Views, with some Apache-2.0 and MIT files; the API does not assert one single licence.
- TP-004 has CERN-OHL-S-2.0 text in `LICENSE`. The README states CERN-OHL-S 2.0 or a paid commercial option and warns that some components may have less restrictive licences. Observed source identifiers include CERN-OHL-S-2.0, BSD-3-Clause, MIT, and GPL.
- TP-005 has no licence file at the pinned commit. Its README states “MIT — free to use, modify, and build on.” This is recorded as repository evidence, not upgraded into legal advice.
- TP-006 has an MIT `LICENSE`.
- TP-007 has Solderpad Hardware License version 0.51 / SHL-0.51. Common source/formal/test files use SHL-0.51; selected support files use Apache-2.0.

Licence file names and SHA-256 fingerprints are in `results/raw/third_party/license_sha256s.txt`.

### PROJECT POLICY

Licence permission is separate from Wire-to-Decision originality policy. A permissive licence does not authorize copying or structural derivation of the mandatory datapath. Any future reuse would require a new review of the exact file, commit, licence, path, modifications, and notices.

## E. Deprecation/maintenance findings

### UPSTREAM FACT

TP-001 README explicitly says verilog-ethernet is deprecated and superseded by `https://github.com/fpganinja/taxi`; new features and bug fixes are stated to move there. This reduces its value as a current dependency but not as a historical architectural reference.

All seven repositories reported `archived=false` through GitHub API at audit time. Recent inspected commits were present for TP-002, TP-004, TP-005, TP-006, and TP-007. TP-003’s inspected tip is older than the others. These observations do not establish a support guarantee.

## F. Direct-overlap/originality findings

### UPSTREAM FACT

TP-005 contains an FPGA ITCH decoder and order book. TP-006 describes Ethernet/IPv4/UDP parsing, market-data processing, formal verification, and low-latency decision output. Both are directly adjacent to Wire-to-Decision’s intended portfolio scope.

### INFERENCE

Direct overlap creates provenance ambiguity even where a permissive licence appears in the repository: later similarity in parser state machines, field muxes, order-state structures, formal properties, or reference models would be difficult to distinguish from structural derivation.

### PROJECT POLICY

TP-005 and TP-006 are `REFERENCE_ONLY_DIRECT_OVERLAP`. They may inform high-level comparison, but not Wire-to-Decision parser FSMs, order-book architecture, module partitioning, field mux structure, decision logic, formal properties, verification properties, or reference-model structure.

## G. Permitted-use classification

| ID | Classification | Permitted use |
|---|---|---|
| TP-001 | REFERENCE_ONLY | Historical Ethernet/IP/UDP interfaces, streaming patterns, testbench organization |
| TP-002 | POTENTIAL_TEST_ONLY_DEPENDENCY | Future pinned cocotb Ethernet infrastructure, with independent project-owned expected values |
| TP-003 | REFERENCE_ONLY | System/testbench organization and implementation methodology; PCIe/NIC scope is outside this project |
| TP-004 | REFERENCE_ONLY | Modern successor comparison and high-level networking reference; no mandatory datapath reuse |
| TP-005 | REFERENCE_ONLY_DIRECT_OVERLAP | High-level comparison only |
| TP-006 | REFERENCE_ONLY_DIRECT_OVERLAP | High-level workflow and portfolio comparison only |
| TP-007 | REFERENCE_ONLY_CDC_BENCHMARK | CDC/reset/FIFO concepts and later benchmark comparison only |

## H. Prohibited-use classification

No audited source is approved for core reuse by WIRE-003. Prohibited without a later authoritative decision and a new file-level audit:

- copied or structurally derived Ethernet/IP/UDP/parser RTL;
- copied MoldUDP64/ITCH decoder or order-book logic;
- copied normalized-event or decision logic;
- copied CDC, reset, asynchronous FIFO, or recovery architecture;
- copied project-specific formal properties, Python reference models, C++ checkers, or tests;
- unpinned test packages or use of a third-party model as the sole expected-value oracle.

## I. Dependency policy

### PROJECT POLICY

- Mandatory core RTL dependencies: NONE.
- Mandatory third-party parser/book/decision dependencies: NONE.
- Approved installed dependencies added by WIRE-003: NONE.
- cocotbext-eth is audited and pinned as a potential test-only dependency but is not installed.
- Generic infrastructure references do not become project dependencies merely because they were audited.
- If cocotbext-eth is used later, its version must remain pinned and packet construction/reference checking must remain independently owned where required by the verification plan.

## J. Third-party manifest summary

`docs/THIRD_PARTY_MANIFEST.md` contains the detailed per-source record: URL, full SHA, branch/date, licence file and hash, observed SPDX identifiers, relevant directories, classification, allowed/prohibited use, incorporation status, and refresh policy.

Expected incorporation status is confirmed:

- all source repositories: `NOT_INCORPORATED`;
- cocotbext-eth: `TEST_DEPENDENCY_NOT_YET_INSTALLED`.

## K. Risks / unresolved questions

- TP-005’s README licence statement has no corresponding licence file at the pinned commit; this is sufficient for a conservative reference-only classification, not for future incorporation.
- TP-003, TP-004, and TP-007 have mixed or per-file licensing evidence; any future file reuse would require individual header review.
- “Not archived” is not equivalent to a maintenance or support commitment.
- Future test dependency selection must be made in a separate task with pinned versions and independent expected-value logic.

## L. Conflicts with Wire-to-Decision authority

No conflict was found. The audit reinforces the existing core-originality rule and does not alter the WIRE-002 protocol basis, parser scope, or architecture authorization. No source code was incorporated.

## M. WIRE-003 conclusion

The seven mandatory repositories have immutable inspected commit pins, branch/date metadata, licence evidence, relevance, maintenance/deprecation observations, classifications, and incorporation status. The originality firewall is explicit. WIRE-003 establishes provenance/reuse-policy evidence only; it establishes no toolchain, model, RTL, simulation, formal, synthesis, P&R, timing, performance, CDC, or integration result.
