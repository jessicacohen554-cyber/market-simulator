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
now. A dummy file's provenance sidecar is loudly marked `synthetic-dummy` —
never present one as a market-sim forecast.

**Correction (2026-07-05, `docs/validation-2026-07-05-ercot-2024-backcast.md`):**
the cache-reading path is wired for **forecast** years only.
`market_sim.results.cache` (`results/{iso}/{cache_key}/year_{year}.parquet`) is
populated by exactly one function, `market_sim.runner.run_scenario_iso`, whose
year loop is hardcoded 2026-2050 regardless of `config.mode` — no code path
populates it for a backcast year (2023-2025), including
`scripts/run_calibration_full.py`, which writes an entirely different,
uncached bundle format. The first real (ERCOT, backcast 2024) sweep required a
one-off bridge script outside this tool to re-solve the current keeper's
config via `scripts.run_calibration.run_year` and populate the standard cache
by hand; see the validation memo for the full diagnosis and a second
canonicalization mismatch it surfaced (`resolve_bau_config`'s ISO-default
heuristic can silently override a keeper's deliberate non-default flag). This
does not block backcast-validation studies (the workaround is scriptable) but
is a real gap for whoever next lifts an ISO's forecast hold.

**Selection decided ahead of need (ADR 0015, PS-12, 2026-07-02)** — when the
hold lifts there are zero new decisions:

- **Years:** five study years, **2030 / 2035 / 2040 / 2045 / 2050**, one
  export file and one portfolio sweep each (tool `config.year` set to match;
  2030 first). All five come from the same cached full-horizon (2026→2050)
  BAU forecast solve per ISO.
- **Scenario:** the **base `ScenarioConfig()`** — no YAML; `mode="forecast"`,
  `gas_price_path="mid"`, `carbon_price=0.0`/`carbon_price_path="zero"`,
  `weather_year=2024`, canonicalized per-ISO by the exporter. The sidecar's
  canonicalized `cache_key` is the recorded identity.
- **Readiness gate (per ISO, lifts the PLAN.md §10 hold):** a current
  calibrated backcast keeper on the dashboard covering all the ISO's
  scoreable years **and** explicit stakeholder sign-off recorded in
  PLAN.md §10. Until both hold, that ISO stays on `--dummy` (or
  `--allow-backcast` for validation studies only).
- **Rollout:** readiness-driven, first-ready-first — expected ERCOT → PJM →
  rest, but any ISO passing the gate sooner goes ahead. The export re-runs
  with the expanded `--iso` list as ISOs join.

The command, per ready ISO set: `python scripts/export_lce_lmp.py --year <Y>
--iso <ISO> [...]` for each of the five years — defaults carry the rest.

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
