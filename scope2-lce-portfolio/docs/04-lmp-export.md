# 04 — BAU LMP Export from the Market Simulator

How the BAU LMP file this tool prices against is produced. The exporter lives
on the **market-sim side** of the fence (`scripts/export_lce_lmp.py`, repo
root); this tool only ever reads the resulting file — it never imports
`market_sim`, and the exporter never imports `lce_portfolio` (ADR 0011).

## Status: wiring stub

The market simulator's BAU **forecast** run is not yet production-ready. Until
it is, the exporter's `--dummy` mode is the working source: it emits a
deterministic **synthetic** LMP series per (iso, year) in the exact contract
format so intake, validation, and portfolio runs can be exercised end-to-end
now. The cache-reading path is fully wired and smoke-tested; flipping from
stub to real data is dropping the `--dummy` flag once the forecast is blessed.
A dummy file's provenance sidecar is loudly marked `synthetic-dummy` — never
present one as a market-sim forecast.

## The contract (ADR 0011)

- **File**: long-form CSV, columns `(hour, iso, lmp)` — one price per
  ISO-hour, one block per ISO. `hour` is an integer `0..8759`, local standard
  time, non-leap calendar (ADR 0010); full coverage required, duplicates are
  an error (validated on read by `lce_portfolio.intake.prepare_lmp`).
- **Series**: the calibrated market-sim **forecast** run for the modeled year.
  Backcast years are diagnostic/validation only (exporter requires an explicit
  `--allow-backcast`). **No escalation** — the LMP vintage is the modeled
  year's, as-is.
- **Zonal → ISO reconciliation**: the market-sim dispatch is zonal; the ISO
  price is the **load-weighted average** of zonal LMPs (weights = that hour's
  zonal load, reconstructed exactly as the runner builds the LP's
  energy-balance RHS). An hour with zero total zonal load falls back to the
  simple mean — the same rule as this tool's `collapse_zonal_lmp` seam.
  Import/export pseudo-zones (CAISO `WECC_import`, PJM's external node) carry
  zero load share and therefore never move the ISO price.
- **Prices are LP duals** on the zonal energy-balance constraints of the
  cached `DispatchResult` (`results/{iso}/{cache_key}/year_{year}.parquet` on
  the market-sim side). No separate pricing model.

## Provenance (ADR 0011 rule)

Which scenario and year produced the series **must be recorded with the
file**. The exporter writes a sidecar JSON next to the CSV
(`<name>.csv.provenance.json`) carrying, per ISO: the scenario `cache_key`,
mode, weather year, simulation year, source parquet path, the collapse rule,
and min/mean/max LMP. A `#` comment header inside the CSV would break this
tool's plain `pd.read_csv` intake, hence the sidecar. Dummy files carry
`"source": "synthetic-dummy"` and a warning instead of a cache key.

## Usage

```bash
# Wiring stub (current default while the forecast matures):
python scripts/export_lce_lmp.py --dummy --year 2026 \
    --iso ERCOT --iso CAISO --iso PJM --iso MISO --iso NYISO --iso NEISO
# -> scope2-lce-portfolio/data/inputs/bau_lmp_2026_dummy.csv (+ sidecar)

# Real export (once the BAU forecast is blessed): same command minus --dummy.
# Reads the cached forecast result for the base/BAU ScenarioConfig (or
# --scenario <yaml>); a missing (scenario, iso, year) cache is skipped and
# reported, never solved implicitly.
python scripts/export_lce_lmp.py --iso ERCOT --year 2026
# -> scope2-lce-portfolio/data/inputs/bau_lmp_2026.csv (+ sidecar)
```

Outputs land in `data/inputs/` here, which is **gitignored** — exported data
is never committed on either side of the fence.

## What the market simulator must produce (the upstream ask)

For a full 6-ISO real export at year Y, market-sim needs one cached final
`DispatchResult` per ISO for the BAU forecast scenario at year Y (zonal
`prices` duals + the scenario `config.yaml` beside it, which the exporter uses
to reconstruct zonal load weights). The exporter validates that the cached
price array's zone set matches the reconstructed demand topology and refuses
to export a mismatch.
