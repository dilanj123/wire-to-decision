# Figure provenance

## `architecture_ab_fmax.svg`

- **Caption:** Five-seed nextpnr routed Fmax for the selected Architecture-A baseline and the experimental Architecture B, with the frozen 156.25 MHz objective. Every route completed; neither architecture met the objective.
- **Source CSV A:** `results/raw/implementation/wire027/five_seed_results_027.csv`

  SHA-256: `911c8e2ecbb91dc5bb6fccec3368dc125e43bd8d76250d5644f83ec28fef6583`
- **Source CSV B:** `results/raw/implementation/arch_b/five_seed_results_028b.csv`

  SHA-256: `f5d167b22b55e0243b3f5eda39d29882b1366017f69407b759114616aee2bcea`
- **Generator:** `tools/analysis/plot_ab_fmax.py`, version 1.0, Python 3.14.0 standard library. Script SHA-256: `16fbe859c0b1559d5da862a9ec03f3e1f45de2966d0bcb4d96a1f85ab36cebd4`.
- **Exact command:** `python3 tools/analysis/plot_ab_fmax.py` from repository root.
- **Output:** `images/architecture_ab_fmax.svg`

  SHA-256: `61b46d543eee9c940894860e9efdbcd37ec0c67a8ffd822765216f66bdaaa7d6`
- **Reproduction check:** regenerated twice from the committed CSV inputs; output SHA-256 was identical both times. Previewed locally with macOS Quick Look; the chart values match both CSVs.
