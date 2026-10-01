# PRECOMMIT — R-SOCO: re-solve SOCO on the corrected backcast inputs (F1 + F2)

Charter: `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.8. Base: `main` @
`9210075392a128d14a5efb168ab1f9955a9b6946` (F1 #6572 and F2 #6569 both merged — precondition MET).
Written before any shard is launched. Phase 0 is zero LP; the parent solves nothing (rule 32(a)).

## 0. Summary

- **Years solved: 2023, 2024, 2025. Not 2019–2022.** SOCO has no 2019–2022 inputs apart from the
  CEMS F2 landed. `run_year(2022, "SOCO", fleet_only=True)` fails at the first loader:
  `ValueError: No EIA-930 data for ISO 'SOCO' in year 2022`. The SOCO addition plan's **manifest
  row 9** ("holdout years 2019–2022 of rows 1–4") never landed. §2 lists what is missing. Launching
  2019–2022 shards would only produce four failures, so they are not launched. The intake is routed
  in §7 as its own lane.
- **Recipe = the incumbent keeper + the F1/F2 input corrections. The offer-curve multipliers are
  unchanged** (every `offer_curve_by_group` band stays exactly what the keeper carries; rule 1(c)).
- **Owner instruction honoured wherever inputs exist**: the year-correct EIA-860 vintage (2023 →
  `vintage_2023`, 2024 → `vintage_2024`, 2025 → canonical, since there is no `vintage_2025`); plant heat
  rates on every measured class; granular CAMPD outages (std + short-coal + short-gas + unit-partial).

## 1. Registered years (rules 34(c) / 35(b))

The registry holds two SOCO sidecars: `2026-09-24-soco61-dark-unit` (the keeper, years **2023, 2024,
2025**) and `2026-09-20-soco53g-prb-own-iso` (years 2023–2025). The second is a superseded run that no promotion
pruned: it is not on `KEEP_REQUIRED_UNMAPPED_BUNDLES` and no goldens manifest names it. If the owner
promotes this lane, the rule-35 prune takes it too. **Union = {2023, 2024, 2025}.** This batch covers the union.

## 2. Benchmarks and inputs per year (the 2019–2022 blocker, measured)

| input | path | span on disk |
|---|---|---|
| EIA-930 SOCO hourly (demand, `NG:*` benchmark) | `data/raw/eia-930-hourly/SOCO hourly.parquet` | 2023–2025 |
| EIA-930 SOCO region / fueltype | `data/raw/SOCO_{region,fueltype}.parquet` | 2023–2025 |
| FERC-714 zonal demand (zonal shares) | `data/raw/zone-specific-demand/SOCO/…_2023-2025.parquet` | 2023–2025 |
| BA-to-BA interchange | `data/raw/eia-930-interchange/SOCO interchange hourly.parquet` | 2023–2026 |
| seam reference (DIBA duration, served schedule, HR by year) | `data/raw/reference/soco_seam_*.csv` | 2023–2025 |
| zonal gas hub | `data/raw/soco_zonal_gas_hub.csv` | 2023–2025 |
| delivered gas AL / GA / MS | `data/raw/gas-prices/eia_delivered_gas_{AL,GA,MS}_monthly_2023-2025.csv` | 2023–2025 (the all-state 2018–2026 file exists) |
| solar zone shape | `data/raw/soco-solar-shape/soco_<Y>_solar_zone_shape.parquet` | 2023–2025 |
| renewable capacity (benchmark) | `data/raw/_validation-source/SOCO_<Y>_renewable_capacity.csv` | 2023–2025 |
| CAMPD CEMS AL / GA / MS | `data/raw/campd-unit-level/` | **2019–2025** (F2) |
| CAMPD outage families | `campd-unit-outages-perunitdark-SOCO.csv`, `-short-`, `-shortgas-`, `campd-partial-outages-SOCO.csv` | **2019–2025** (F2) |
| EIA-860 vintages | `data/raw/eia-860/vintage_2019…2024` | **2019–2024** + canonical (F1) |
| price benchmark | none (card S2) | — |

Source material exists for the EIA-930 part: `data/raw/eia-930/EIA930_BALANCE_2019…2022_*.parquet` carry
the `SOCO` BA, so the demand/`NG:*` gap can be derived from committed files. FERC-714 (PUDL), the
interchange (EIA API key, which is unset in this container, or the Grid Monitor CSV) and the gas-hub
series need fetches. The derived seam / solar-shape / zonal-share artifacts need their SOCO-31/32
builders re-run. That is a data-intake lane with its own gates, not a re-solve.

2023–2025 benchmarks are all present; the keeper was scored on them.

## 3. Phase-0 fleet census (zero LP; `scripts/probes/_rsoco_phase0.py`, JSONs beside this file)

`ctl` = the keeper recipe at HEAD with the two F1 flips forced back off (`eia860_vintage_tracks_solve_year`,
`measured_chp_heat_rates` = False) and no new outage family. This is the pre-audit posture as far as HEAD
can express it; F1's re-derived artifacts and eGRID join are live on both sides. `arm` = this lane's
recipe. The cells show ctl → arm: nameplate MW / cap-weighted heat rate (MMBtu/MWh) / availability
energy removed (TWh).

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| EIA-860 source | canonical → **vintage_2023** | canonical → **vintage_2024** | canonical → canonical |
| COAL | 15,159 → **11,512** MW (43 → 28 units) / 11.49 → 11.09 / 75.41 → 44.03 | 15,159 → **11,512** / 11.38 → 10.94 / 72.22 → 40.77 | 15,159 / 11.19 / 72.50 → **73.89** |
| CC_REGULAR | 18,653 → 19,292 / 7.048 → 7.074 / 45.63 → **52.17** | 18,653 → 18,663 / 7.063 / 43.06 → **49.31** | 18,653 / 7.058 / 42.84 → **48.60** |
| ST_GAS | 3,261 → 4,065 / 10.76 → 11.05 / 14.33 → 15.48 | 3,261 → 3,141 / 11.04 → 10.94 / 15.27 → 14.72 | 3,261 / 11.13 / 16.35 → 16.55 |
| CT_PEAKER | 9,640 → 10,824 / 11.28 → 11.36 / 12.79 → 14.30 | 9,640 → 9,646 / 11.25 / 12.78 → 12.73 | 9,640 / 11.46 / 12.78 |
| CC_CHP | 475 / **5.85 → 8.12** / 1.84 → 1.98 | 475 / **5.85 → 8.10** | 475 / **5.85 → 8.10** |
| CT_CHP | 148 / **5.58 → 6.84** | 148 / **5.58 → 6.87** | 148 / **5.58 → 6.87** |

Readings:
- **(a) Vintage.** Each year resolves its own vintage (2025 has none, so it reads the canonical snapshot).
  The 3,647 MW of coal that the canonical snapshot carries in 2023/2024 is **fully dark** there: its
  availability removed falls by 31.4 / 31.5 TWh against 3,647 MW × 8,760 h = 31.9 TWh. The vintage route
  drops those units from the fleet instead of windowing them out, so coal energy capability is
  essentially unchanged; the units just leave the unit list.
- **(b) Class-table heat rates.** 1,043.7 / 1,043.1 / 1,047.8 MW sit at a `HEAT_RATE_BINS` value. That is
  **Dahlberg (EIA 7709, 746.9 MW, 10.5)** and **Hartwell (EIA 54538, 298.1 MW, 11.5)**, plus Inforum
  (54290) and Tech Square (63775), both < 2 MW. F1 listed both CTs as "no eGRID rate in any vintage".
  **They are not absent from CAMPD**: EPA files Dahlberg under CAMD facility **7765** (2023: 257.3 GWh
  gross, 3.09 TBtu → 12.0 MMBtu/MWh gross) and Hartwell under **70454** (2023: 212.0 GWh, 2.53 TBtu →
  11.9). The measured-CT derive keys `plant_code == facilityId`, so it misses them. This is an
  **EPA↔EIA ID-crosswalk defect**, routed in §7. It is not fixed here: the fix is a cross-ISO derive
  change, and rule 23 applies.
- **(c) Outages.** Windows by start year, SOCO, from F2's coverage table (2023 / 2024 / 2025):
  std `-perunitdark-` 332 / 356 / 432 (unchanged); **short-coal 8 / 10 / 16**; **short-gas 324 / 351 /
  314**; **partial 5 / 0 / 7**. Fleet effect: CC_REGULAR availability removed rises by 6.5 / 6.3 /
  5.8 TWh, and coal by 1.4 TWh in 2025.
- **(d) Retirees (F1 D3).** SOCO's retiree channel now yields 143 MW (2023) and 13 MW (2024). Under the
  vintage default, 2023–2024 read the vintage operable sheets.

## 4. G-DRIFT (rule 29(b)) — keeper legs at `1d7edc1b` vs HEAD `92100753`

`git diff 1d7edc1b HEAD --` over `src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` touches 20 files.

| hunk | class | reason |
|---|---|---|
| F1: `data/egrid.py` (new), `fleet/eia860.py`, `fleet/campd_bins.py`, `chp.py`, `scripts/lib/heat_rate_years.py`, `run_calibration.py::_measured_heat_rate_flags` + retiree/mothball threading, `runner.py` `_mhr`, `scenarios.py` six default flips + backcast coercion, `results/cache.py` epoch, `run_calibration_full.py` CLI flags | **LIVE — by design** | the audit's input correction; it is the object of this re-solve |
| F1 data (outside the diff paths, LIVE): re-joined `heat_rate` in every `eia-860/vintage_*` + canonical + retiree parquet; re-derived `campd_{ct,coal,st,cc}_heat_rates_SOCO` + `chp_power_only_heat_rates_SOCO` with per-year rows | **LIVE — by design** | same |
| F2: `data/campd.py` `ISO_MERIT_PANEL_STATES["SOCO"]` pin | INERT at solve | read only by the deriver; SOCO short-gas was byte-identical after the pin (F2 §4) |
| F2 data: `-perunitdark-SOCO` extended 2019–22 (2023–25 byte-identical); new `-short-`, `-shortgas-`, `partial-SOCO` | INERT for the std file on 2023–25; the new families are **LIVE, by design**, and armed here | F2 §3 |
| pjm-h22 `capacity_market.py` 2020–22 zone shares, `fuel_trajectories.py` RGGI 2020–22 | INERT | PJM rows / RGGI; SOCO has no RGGI and no capacity market |
| miso-268 `coal_fuel_inventory_plant_grain` (`coal_fuel_inventory.py`, `lp/{__init__,model,rows}.py`, `pipeline/spec.py`, `run_calibration.py`) | INERT | default-off, absent from the keeper recipe (the SOCO-61 Addendum A classification) |
| `scripts/lib/storage_compare.py`, `forecast_parity_registry.py` | INERT | report-only / forecast-only |
| `run_calibration_full.py` test-path docstring | INERT | comment |

The new legs therefore differ from the keeper only by the F1/F2 corrections and this lane's three
outage arms. The keeper's committed composite remains the control (form 4); no control solve is run.

## 5. The recipe (the solve)

One shard per year (rule 36), replaying the committed keeper composite on `main`:

```
PYTHONPATH=. python3 scripts/data/curate_hydro_plant_modes.py --iso SOCO
python3 scripts/replay_keeper.py results/calibration/soco61_dark_unit_span --years <Y> \
  --out-dir results/calibration/rsoco_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true \
  --note "R-SOCO <Y>: soco61 keeper + F1/F2 corrected backcast inputs (year-matched EIA-860, plant heat rates incl. CHP, CAMPD short-coal/short-gas/partial windows); multipliers unchanged"
```

The two F1 flags are already the backcast default. They are passed explicitly so the leg records them
as declared, not inherited. `measured_{ct,coal,st,cc}_heat_rates`, `egrid_family_heat_rates` and
`campd_dark_unit_year_windows` are carried unchanged from the keeper's `meta.json`. Not armed, and
stated: `retiree_cems_cap` (U; not in the charter) and `carry_operating_mothballs` (F1: inert under
the vintage default).

**Hard stops per leg**: `git rev-parse HEAD` equals this PRECOMMIT's pinned SHA. Resolved
`scenario_config` shows all five `--set` fields True and `measured_{ct,coal,st,cc}_heat_rates`,
`egrid_family_heat_rates` and `campd_dark_unit_year_windows` True. `resolved_inputs` names the
`-perunitdark-SOCO` std extract. Every `offer_curve_by_group` band equals the keeper's.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- E1 2023/2024 coal energy moves by less than ±1.5 TWh (the dropped units were dark; the heat-rate
  moves are small, 11.49 → 11.09 and 11.38 → 10.94).
- E2 CC_CHP and CT_CHP energy falls (heat rate +38 % / +23 %); the size is small (623 MW together).
- E3 the CC_REGULAR share falls or holds (+5.8–6.5 TWh of availability removed, and CC is rarely
  availability-bound, so the move is < 2 TWh).
- E4 no C6 / C8 status moves; C3a/b/c stay UNSCORABLE (no SOCO price).

**Promotion recommendation rule, fixed now:** this is an input correction the owner mandated, so the
re-solve is recommended as the keeper iff it solves cleanly on all three years with the posture
verified, **whatever the gates do** (rule 14: a regression is a root-cause lead, never a reason to keep
the inaccurate input). Every gate move is reported at full magnitude. The owner decides (rule 31).

## 7. Routed, not done here

1. **SOCO 2019–2022 intake (manifest row 9).** EIA-930 SOCO hourly and region/fueltype 2019–22 (derivable
   from the committed BALANCE parquet); FERC-714 zonal demand 2019–22 (PUDL); interchange 2019–22;
   delivered gas AL/GA/MS 2019–22 (the all-state 2018–2026 file may already serve); zonal gas hub, seam
   reference, solar shape, zonal shares and renewable-capacity benchmark 2019–22 (the SOCO-31/32/33
   builders); the calibration-reference SOCO block for 2019–22. When it lands, a successor solves
   2019–2022 one shard per year on this recipe and folds them in.
2. **EPA↔EIA facility-ID crosswalk** for the measured-heat-rate derives (and the outage derives), a
   cross-ISO F1 residual. SOCO: Dahlberg 7709↔7765 and Hartwell 54538↔70454, 1,045 MW of CT at
   class-table 10.5/11.5 against a measured ≈12.0.
