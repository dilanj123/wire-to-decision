# Third-Party Notices

No third-party source code has been incorporated into the repository at this stage.

The following upstream projects were audited as references during WIRE-003; their source remains outside this repository and no dependency was installed:

- verilog-ethernet — MIT-style `COPYING`; deprecated upstream, superseded by Taxi.
- cocotbext-eth — MIT `LICENSE`; potential future test-only dependency, not installed.
- Corundum — BSD-style `LICENSE` with mixed per-file SPDX headers; reference only.
- Taxi — CERN-OHL-S-2.0 or commercial option, with some less restrictive components; reference only.
- Itch-Parser — README states MIT, but no licence file was found at the audited commit; direct-overlap reference only.
- fpga-tick-to-trade — MIT `LICENSE`; direct-overlap reference only.
- PULP common_cells — SHL-0.51 `LICENSE` with mixed support-file SPDX headers; CDC benchmark only.

Full attribution and applicable notices must be added if source is actually incorporated later. Auditing or studying an upstream repository does not make its code part of Wire-to-Decision.

See `docs/THIRD_PARTY_MANIFEST.md` for immutable commit pins, licence fingerprints, classifications, and reuse restrictions.
