# Validation memo — first real priced result (ERCOT, backcast 2024)

- **Date:** 2026-07-05
- **Scope:** W3-P4 (`PLAN.md` §10 / `docs/fable-repo-audit-2026-07.md` S2-1)
- **Result:** `results/ercot_backcast2024_premiumcap/` (committed results store, ADR 0014 §5)

## What this is

The tool has 238 tests passing and an end-to-end sample sweep, but had **never
priced a portfolio against a real market-sim LMP series** — every run to date
used the exporter's `--dummy` synthetic stub or synthetic CF shapes. This is
the first run against **real** ERCOT CF profiles (EIA-930-derived) and a
**real, calibrated backcast LMP series** (not the forecast — the forecast path
stays on hold per `PLAN.md` §10; ADR 0015 explicitly permits a backcast export
for validation studies).

ISO: **ERCOT** (the calibrated reference, first in ADR 0015's readiness-driven
rollout order). Year: **2024** (mid-span of the current keeper's covered
years 2023–2025; avoids first/last-year edge effects).

## Gate 0 (discovered, not part of the original plan): the backcast export path was never wired

`scripts/export_lce_lmp.py`'s non-`--dummy` path reads
`market_sim.results.cache.load_result(iso, cache_key, year)`, i.e.
`results/{iso}/{cache_key}/year_{year}.parquet`. That cache is populated by
exactly one function, `market_sim.runner.run_scenario_iso` — and its year
loop is hardcoded `for year in range(START_YEAR, END_YEAR + 1)` = **2026–2050
only**, regardless of `config.mode`. The backcast calibration pipeline
(`scripts/run_calibration_full.py` → `scripts/run_calibration.run_year`) solves
2023–2025 but writes to a completely different, uncached bundle format
(`results/calibration/<name>/{dispatch,system}.parquet`, gitignored/heavy) and
never calls `cache.save_result`. **No code path in the repo has ever
populated the standard cache for a backcast year**, and this container had no
locally-solved data either. ADR 0015's "zero code changes" claim is true only
for the forecast years; the backcast-for-validation path it also describes was
never actually exercised end-to-end before this session.

This is a **tool-side (market-sim) gap**, not a scope2-tool defect, and not
something to paper over by loosening scope2's own validation. Diagnosis and
what was done about it, in order of increasing surface area:

1. **Bridge script, zero edits to `run_calibration.py`/`run_calibration_full.py`
   / `runner.py`.** A one-off script reconstructed the current ERCOT keeper's
   exact resolved `ScenarioConfig` from the committed
   `results/calibration/ercot_ordc_total_rtolcap_v1/run_config.json`
   (`scenario_config`: a full `dataclasses.asdict` of the keeper's config),
   overrode `weather_year`/`gas_price_override` to 2024, and called the
   existing `scripts.run_calibration.run_year(...)` (already imported and used
   by `run_calibration_full.py` — this is a read-only, already-public
   function) to re-solve 2024 fresh in-container. The result was then written
   through `market_sim.results.cache.save_result`, populating
   `results/ERCOT/1c564cefa607e84c/year_2024.parquet` + `config.yaml`.
   - **Container-reproducibility caveat (already documented,
     `docs/calibration-log.md` 2026-07-05 entry):** replaying the ercot32
     keeper recipe in this container is known not to be byte-identical to the
     originally-registered numbers. One field present in the committed
     `run_config.json` (`ordc_reliability_deployment_mw`) no longer exists on
     the current `ScenarioConfig` dataclass (schema drift since 2026-07-03);
     it was dropped (its recorded value was `0.0`, a no-op either way). No
     other field required dropping. This re-solve is **not** presented as a
     byte-exact reproduction of the dashboard keeper — it is a fresh,
     structurally-identical calibration solve for validation purposes only,
     and is not registered as a keeper or probe on the dashboard (rule #16:
     single-year solves are diagnostic-only, never a keeper).
2. **A second, real mismatch surfaced when exporting:** `export_lce_lmp.py`'s
   `resolve_bau_config()` re-applies each ISO's `default_scenario_overrides`
   to any field sitting at `ScenarioConfig()`'s plain dataclass default — it
   cannot distinguish "left unset" from "explicitly chosen to equal the
   default." ERCOT's `default_scenario_overrides` sets
   `scarcity_price_overlay=True` for any config reading `False` (its own
   default). The ercot32 keeper **deliberately** sets
   `scarcity_price_overlay=False` — the keeper's lumped ORDC total-reserve
   family already prices scarcity, and the generic overlay would double-count
   it (see the keeper's `model_changes_note`). Running the reconstructed
   config through `resolve_bau_config` would have silently flipped this back
   to `True` and mislabeled the export as coming from a config that was never
   solved. Rather than accept that drift (or, worse, "fix" it by re-solving
   with `scarcity_price_overlay=True`, which would be tuning the input away
   from the calibrated market design to make the plumbing line up), the
   export was built by calling `export_lce_lmp.py`'s own
   `collapse_zonal_prices`/`load_zonal_demand`/`write_export` functions
   directly against the config that was **actually solved**, skipping only
   the `resolve_bau_config` re-canonicalization step. The written provenance
   sidecar (`data/inputs/bau_lmp_2024.csv.provenance.json`, reproduced below)
   documents this explicitly.
3. Neither `run_calibration.py`, `run_calibration_full.py`, nor
   `runner.py`/`export_lce_lmp.py` were modified. Everything above lives in
   two throwaway scripts outside the repo (not committed) that only call
   existing, already-public functions.

**Recommendation for whoever next lifts an ISO's forecast hold (out of scope
here):** `export_lce_lmp.py`'s docstring and ADR 0015 should be corrected —
the cache-reading path is wired for forecast years only; a real backcast
export requires either (a) teaching `run_calibration.py` to optionally call
`cache.save_result`, or (b) accepting that `resolve_bau_config`'s
default-override heuristic cannot safely apply to calibration-sourced configs
and building a dedicated calibration-to-cache adapter. Filed here rather than
fixed in `runner.py`/`run_calibration.py` directly to avoid touching
fast-moving, shared calibration scripts other sessions are actively editing.

Provenance sidecar written alongside the (gitignored) LMP CSV:

```json
{
  "iso": "ERCOT",
  "scenario_cache_key": "1c564cefa607e84c",
  "mode": "backcast",
  "weather_year": 2024,
  "simulation_year": 2024,
  "hours": 8760,
  "lmp_mean": 30.14,
  "lmp_min": 8.63,
  "lmp_max": 5000.00,
  "annual_load_twh": 462.59,
  "backcast_validation_only": true
}
```

$30.14/MWh mean, $8.63–$5,000 range (VOLL-capped scarcity hours) is in the
right neighborhood for ERCOT's actual 2024 system-average price — plausible,
though this P1-only (no-commitment), current-keeper solve carries the same
determination caveats as the registered dashboard keeper itself ("NOT-YET":
C1/C2 hard caveats, C8 forced-energy share) — this is a validation input, not
a claim of forecast-grade price skill.

## Inputs built

- `scripts/build_profiles.py --year 2024` — real per-ISO CF profiles for all
  six ISOs (EIA-930-derived), not just ERCOT (see printed sanity table:
  ERCOT/CAISO/PJM/MISO/NYISO/NEISO solar/onshore/offshore CFs, all in
  documented ranges).
- `scripts/make_reference_load.py` — stylized 100 MW reference load (all 6
  ISOs, flat ±10%; this is a synthetic facility shape, not real metering —
  the same reference load every other ADR-ratification validation run uses).
- `scripts/build_fossil_avg_co2_rate.py --iso ERCOT --year 2024` — hourly
  fossil-only average CO₂ rate from the same cached dispatch: mean 0.560,
  range 0.440–0.692 tCO₂/MWh, 0 zero-fossil hours (ERCOT's gas-heavy fossil
  margin is essentially always present) — plausible for a fleet mixing
  efficient CCs (~0.35–0.40 tCO₂/MWh) with older gas steam/peakers and some
  coal at the top of the range.

## The sweep

`run_portfolio.py --config data/inputs/ercot_2024_sweep_config.json --iso
ERCOT --results --run-id ercot_backcast2024_premiumcap`, Mode A (premium-cap),
extended premium range `{1,2,5,7,10,15,20,30,40,50,75,100,150}` $/MWh (wider
than the demo's `{1,2,5,7,10,20}` specifically to reach the near-100%-matching
tail the sanity check needs).

| premium $/MWh | matching % | residual CO₂ (t) | build mix (MW) |
|---:|---:|---:|---|
| 1 | 9.24% | 444,559 | solar_pv=34 |
| 2 | 18.48% | 398,802 | solar_pv=68 |
| 5 | 40.64% | 289,985 | solar_pv=128, wind=22 |
| 7 | 51.69% | 236,490 | solar_pv=117, wind=62 |
| 10 | 67.23% | 161,275 | solar_pv=102, wind=121 |
| 15 | 83.33% | 82,706 | solar_pv=116, wind=200 |
| 20 | 89.86% | 50,501 | solar_pv=126, wind=281 |
| 30 | 95.78% | 21,085 | solar_pv=149, wind=388, **battery_4h=26** |
| 40 | 98.38% | 8,162 | solar_pv=178, wind=476, battery_4h=60 |
| 50 | 99.41% | 3,028 | solar_pv=198, wind=550, battery_4h=102 |
| 75 | 99.98% | 115 | solar_pv=254, wind=707, battery_4h=199 |
| 100 | 100.00% | 0 | solar_pv=173, wind=1,079, battery_4h=194 |
| 150 | 100.00% | 0 | solar_pv=218, wind=2,303, battery_4h=45 |

All 13 solves report `status: Optimal`.

## Sanity checks against published 24/7 CFE study shapes

- **Monotonic premium-vs-matching:** PASS — strictly non-decreasing across
  every point.
- **Steeply rising premium past ~90% matching:** PASS — matching rises from
  89.86% to 100% only as the premium cap rises 5× ($20 → $100/MWh); the
  marginal cost per matching-point in the 90→100% band is far higher than in
  the 0→90% band, exactly the convex tail the 24/7 CFE literature (e.g.
  Google/Princeton-style studies) reports.
- **Storage entering at high targets:** PASS — `battery_4h` first enters at
  95.78% matching ($30/MWh) and grows monotonically through the tail
  (26→60→102→199 MW) before the LP substitutes toward more wind at $100–150
  (a solver degeneracy/substitution effect at the very top of the frontier,
  not a monotonicity violation — matching itself is still monotonic).
- **"Firm" resource entering at high targets:** **NOT observed** — only
  solar/wind/battery_4h ever build, even at $150/MWh with 100% matching;
  LDES, hydrogen, nuclear, geothermal, and gas-CC+CCS never enter. This is
  flagged rather than forced. Plausible explanation (ISO-specific, not a tool
  defect): ERCOT has the best onshore wind resource in the US and the sweep's
  reference load is a small, flat synthetic 100 MW shape — the LP can reach
  100% matching by overbuilding wind (23× the load's nameplate at $150/MWh)
  stacked with short-duration batteries, without ever needing multi-day
  firm/long-duration coverage. This is a known real-world pattern for
  wind-resource-rich systems (unlike solar-heavy/wind-poor systems such as
  CAISO, where the literature's "firm enters near 100%" narrative is
  typically drawn from). Whether a **real** facility load shape (vs. the
  flat synthetic 100 MW reference) or a CAISO/PJM run would surface LDES/firm
  entry is future work, not resolved here.

## What this does and doesn't validate

**Validates:** the tool's intake → LP → sweep → outputs pipeline behaves
correctly end-to-end against a real, non-trivial priced input (not just
synthetic data the tool's own defaults were tuned against); the frontier
shape and storage-entry timing match expectations from real published 24/7
CFE studies.

**Does not validate:** ERCOT's absolute price/premium levels as
forecast-grade (the underlying LMP series carries the same keeper-level
caveats as the dashboard's `ercot32` determination: "NOT-YET" — C1/C2 hard
caveats, C8 forced-energy share FAIL); nor does it validate any other ISO
(CAISO/PJM/MISO/NYISO/NEISO CF profiles were built, but no LMP export or
sweep was run for them — each would need its own bridge re-solve, and each
keeper likely has its own container-reproducibility drift to work through,
same as ERCOT's one dropped field here).

## Files

- `results/ercot_backcast2024_premiumcap/` — committed results store
  (`ERCOT_frontier.parquet`, `ERCOT_build_mix.parquet`,
  `ERCOT_run_metadata.json`, `report.json`, `report.html`).
- `data/inputs/ercot_2024_sweep_config.json` — the sweep config used (kept
  local; `data/inputs/` is gitignored per this tool's convention).
- `data/inputs/bau_lmp_2024.csv` (+ `.provenance.json`) and
  `data/emissions/ERCOT_2024_fossil_avg_co2_rate.parquet` — real exports,
  gitignored (reproducible/disposable per this tool's convention); the
  provenance sidecar is reproduced above for the permanent record.
