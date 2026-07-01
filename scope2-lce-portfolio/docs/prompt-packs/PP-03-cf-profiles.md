# PP-03 — Capacity-Factor Profiles (first vendoring)

**Upstream:** none (technical). **Targets:** `src/lce_portfolio/profiles.py`,
`src/lce_portfolio/vendored/`.
**Status:** synthetic shapes done; real profiles are the main task here.

## Build

1. **Vendor the renewable-shape logic.** Copy the slice of
   `src/market_sim/data/renewables.py` that turns EIA-930 / HSL data into 8760
   per-zone wind & solar CF into `src/lce_portfolio/vendored/renewable_shapes.py`.
   Header must record: what was copied, the upstream file + `git rev-parse HEAD`,
   and how to re-sync. Copy only what's needed — not the whole module. **No
   `import market_sim`.**
2. **Firm-clean profiles.** Nuclear/geothermal = flat at CF; existing hydro = a
   monthly-budget shape (coordinate with PS-05/PP-02). Offshore wind shape if used.
3. **Wire the seam.** Keep `build_cf_matrix(resources, iso, year)` as the single
   entry point; add a config flag to choose synthetic vs vendored-real so tests
   can stay data-free. Zone→ISO aggregation: collapse zonal CF to the single ISO
   node consistent with how load/LMP were aggregated.
4. **Data paths.** Resolve any copied data via a local `paths.py` in the tool (do
   not reach into market-sim paths); document required raw files.

## Acceptance

`test_profiles` checks CF ∈ [0,1], storage rows zero, annual means match
`cf_assumed` for synthetic, and (if data present, `@pytest.mark.integration`) that
vendored real profiles load and have sane shapes. Synthetic path stays default so
CI needs no external data.
