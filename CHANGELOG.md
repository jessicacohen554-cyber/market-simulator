# Changelog

## 2026-06-11 (CAISO backcast P5 — grid-battery fleet: COD ramp + EIA-930 battery benchmark wiring)

CAISO prompt-pack P5 (Wave 1). The CAISO BESS fleet was already loaded from
the EIA-860 energy-storage schedule (11.1 GW / 38.5 GWh by end-2024 in the
CISO BA, matching CAISO's published ~11 GW and the CEC's 10-GW-crossed-in-2024
milestone); this pack adds what the year-end snapshot missed. The pack's
cycling-cost item landed independently as ERCOT E2's `battery_dispatch_adder`
(PR #312) — P5 adopts that knob (no duplicate field) and adds the cycle-aging
citation to its registry entry. ERCOT/PJM backcasts are unchanged
(regression-guarded by tests). **Cache keys rotate**: `ScenarioConfig` gained
`storage_vintage_ramp`, so previously cached scenario-years re-solve on
first touch.

- **Intra-year COD capacity ramp (`storage_vintage_ramp`).** CAISO
  commissioned 3.0 GW of batteries during 2023 and 3.6 GW during 2024, so a
  flat year-end fleet overstates spring capability by ~2 GW.
  `load_eia860_storage` now aggregates each zone's capacity per EIA-860
  Operating Month (the renewables `vintage_capacity_ramp` convention) and the
  new `storage.storage_cap_profiles` expands the monthly steps into
  hour-varying `(n_storage, T)` charge/discharge/SOC bounds, which
  `dispatch.build_variable_bounds` now accepts alongside the static 1-D form.
  Tier-3 toggle, on for CAISO only in `_calibration_config`; ERCOT/PJM keep
  their calibrated flat year-end fleets until a recalibration pass (pack E2).
- **EIA-930 battery benchmark wired "if present" for every ISO.** Neither
  `data/eia_hourly/CISO hourly.parquet` nor `inputs/raw-data/CISO_fueltype.parquet`
  carries the EIA-930 `BAT`/`PS` storage split yet (CISO batteries currently
  ride in `OTH`, which swings −8.5 to +9.7 GW with a clear charge-midday /
  discharge-evening shape). The generic `load_eia_hourly_benchmark` now maps
  `NG: BAT`→`battery` and `NG: PS`→`pumped_storage` (net series, + =
  discharge), picked up automatically once a regenerated extract carries
  them — complementing E2's ERCOT-specific `load_ercot_battery_gen`. The
  non-ERCOT calibration report gains a `[2b] Battery cycling` section off
  the bundle's `storage.parquet` (E2's frame): model vs EIA-930
  discharge/charge TWh, evening (h17-22) discharge share, and hourly-net
  Pearson r — model-only with a note while the benchmark columns are absent.
- **Tests.** CAISO 2024 fleet vs published capacity (>10 GW, CEC/CAISO DMM);
  per-year power+energy totals reconciled against an independent EIA-860
  recomputation (acceptance); ramp monotonicity, December == year-end caps,
  profile expansion, and an LP check that a unit is idle before COD;
  ERCOT/PJM fleets carry no ramp and zero cycling cost under defaults;
  EIA-930 battery columns wired when present, skipped when absent.

## 2026-06-11 (ERCOT E2 — storage throughput cost + nuclear refuel validation)

ERCOT backcast realism for storage and nuclear (backlog item E2); PJM
unchanged (knob defaults to 0 and PJM bundles are untouched).

- **`ScenarioConfig.battery_dispatch_adder`** (Tier 3, default 0): per-MWh-
  discharged throughput/cycling cost on the EIA-860 grid-battery fleet — the
  battery analogue of `pumped_storage_dispatch_adder` (cycling degradation +
  ancillary-service opportunity cost the energy-only LP ignores). Wired
  `load_eia860_storage` → `StorageUnit.vom` → the LP discharge slot;
  `run_calibration_full.py --battery-adder`. Without it the LP over-cycled
  the ERCOT BESS fleet +48% vs the EIA-930 measured 2025 discharge; at the
  calibrated $10/MWh the model lands −1.5% (5.36 vs 5.44 TWh).
- **Storage observability:** calibration bundles persist per-unit hourly
  charge/discharge (`storage.parquet`, P1/P2 incl. `--run-p2`), carry the
  EIA-930 battery benchmark series (`NG: BAT`/`NG: UES`, NaN over unreported
  hours so partial years benchmark their reported window), and the report
  gains a §3d storage-throughput section.
- **ERCOT keeper re-tuned** (dashboard `run79 storage retune`): battery
  adder $10 + Jacobian joint-move on the non-CHP bands. 2023/2025 thermal
  classes land within ±3% (lignite and 2024's cheap-gas coal deficit → E1);
  nuclear −0.7% all years.
- **`scripts/derive_nuclear_monthly_cf.py`**: backcast analogue of
  `forecast_nuclear_refuel.py` — derives `NUCLEAR_MONTHLY_CF_BY_YEAR` from
  EIA-923 monthly actuals and `--check`-validates the committed table
  (ERCOT 2023–2025 reproduce exactly; the audit's +2.4% nuclear overshoot
  predated the overlay landing in PR #252).
- **Solver provenance:** `meta.json` records `highspy_version`. An
  identical-config Run-77 re-run on highspy 1.14.0 moved class splits
  several TWh at an equal objective (cheap-gas PRB/gas committed bid
  plateau admits alternate optima) — see the calibration-log E2 entry.
- **Docs realigned** (sync-docs): methodology-spec storage section now
  documents the per-unit discharge-cost adders (the "flag if unrealistic
  cycling appears" sensitivity fired and was resolved); claude.md objective
  carries the `dis_cost×Dis` term; parameter registry regenerated
  (battery_dispatch_adder + upstream dual-fuel/import params).

## 2026-06-11 (CAISO P6 — uncurtailed renewable potential, the HSL analogue)

CAISO backcasts now feed the dispatch *uncurtailed* wind/solar potential so
it re-curtails endogenously (playbook §8.3), instead of inheriting the
historical curtailment baked into EIA-930 delivered output. ERCOT's NP6 HSL
path is byte-for-byte unchanged (regression-tested).

- **`scripts/build_caiso_hsl.py`** builds
  `inputs/raw-data/caiso-hsl/caiso_<year>_hsl_hourly.parquet` (same schema
  as `ercot-hsl/`): uncurtailed = EIA-930 `CISO hourly` delivered +
  CAISO's reported 5-minute wind/solar curtailment
  (`inputs/raw-data/caiso-curtailment/`, upload U3), mapped onto the
  model's non-leap 8760 clock. 2023 and 2024 are built and committed
  (curtailment 2.66 / 3.40 TWh — matches CAISO's published totals;
  solar ~6.3 / 6.6% of potential, spring-peaked). 2025's workbook ends in
  May, so the year is **skipped with a data-needed marker** rather than
  fabricating zero curtailment for Jun–Dec; CAISO 2025 keeps the
  delivered-profile fallback.
- **`renewables.py`**: the HSL file lookup is generalized (`_hsl_file`);
  `load_renewable_profiles` now resolves CAISO backcast years to the
  uncurtailed parquet, zone-shaped by EIA-860 capacity exactly like the
  delivered path. New `load_hsl_hourly(iso, year)` exposes the GEN/HSL
  frame to the report and tests.
- **Calibration report**: new headline table `[1b] Renewable curtailment`
  in the generic (non-ERCOT) report — modeled re-curtailment
  (potential − dispatched) vs ISO-reported (HSL − delivered), annual TWh
  per fuel plus the monthly GWh shape. Prints only for HSL-backed
  ISO-years.
- **Tests**: CAISO backcast profile reconstructs the zero-floored HSL and
  sits ≥ delivered every hour; every committed CAISO HSL parquet has
  HSL ≥ delivered hourly with multi-TWh solar curtailment; ERCOT 2023
  still reconstructs the rescaled NP6 targets (110 / 32 TWh).

## 2026-06-11 (CAISO backcast — demand series and zonal disaggregation)

CAISO prompt-pack P8 (doc 06 §P8): system demand and zonal load split.

- **System demand from the EIA-930 `CISO hourly` extract.** `load_demand`
  gains a CAISO branch (`_load_caiso_hourly_demand`) reading
  `data/eia_hourly/CISO hourly.parquet`, so demand shares the
  chronological clock of the wind/solar/benchmark series read off the
  same rows (ERCOT precedent: the demand-profiles parquet is hour-shifted,
  which would desynchronize the duck curve). Generation-side convention,
  `td_loss_factor = 0.0`; **no interchange netting** — CAISO imports are
  supply via the `WECC_import` node, netting them into demand would
  double count. Net-load convention documented (playbook §8.1, data
  dictionary): the series is net of ~15+ GW BTM PV; backcasts model
  front-of-meter resources only.
- **Measured zonal load split from TAC-area load (upload U4, partial).**
  `eia_loader.caiso_zonal_load_shares` maps OASIS `SLD_FCST` ACTUAL
  TAC-area hourly load onto the trading hubs (PGE-TAC split 0.86/0.14
  onto NP15/ZP26 — no TAC boundary at Path 15, ratio preserved from the
  prior split, Tier 3; SCE+SDGE+VEA→SP15) and serves measured hourly
  zonal shapes for covered hours; uncovered hours carry the
  sample-average shares. Only 2023-01 has landed, so the static
  `load_share` fallback is now *measured* from that sample via the
  generalized `scripts/derive_load_shares.py caiso`:
  NP15/ZP26/SP15 = 0.43/0.07/0.50 → 0.3969/0.0646/0.5385 (Tier 2,
  winter-month sample — summer shifts share south). Refresh path:
  complete the U4 monthly pulls; shapes upgrade automatically.
- Tests: CAISO hourly shares sum to 1.0 each hour, measured window moves
  while the fallback stays static, missing-file year falls back, and
  zonal demand reconciles to the CISO system series within rounding.
## 2026-06-11 (PJM J1 — generalized priced import/export node)

Closes backlog item J1 (doc 06 §6). The +40 TWh PJM net-export structural
gap itself was already served by the measured tie-line schedule (2026-06-05,
Module M4) — the pjm-6 baseline carries it (2023 demand 823 TWh = 783
internal + 40 export) and gas dispatch already rose accordingly. What was
missing is the **price-responsive** node: forward PJM scenarios fell back to
*zero* interchange, and the CAISO WECC machinery was not reusable. ERCOT is
untouched (no import node; full suite green minus the known-stale
`test_coal_supply_pricing_uses_year_trajectory`, doc 06 E1).

- **Generalized machinery** (`model/transmission.py`): per-ISO
  `IMPORT_TRANCHES` / `EXPORT_TRANCHES` / `IMPORT_ZONE` / `IMPORT_NODE_LINKS`
  / `IMPORT_EFORD` constants drive `build_import_generators(iso)`,
  `build_export_sinks(iso)` (priced negative-generation blocks — a sink's
  $/MWh rides in `vom`, so absorbing exports credits the neighbors'
  willingness-to-pay) and `extend_with_import_node(iso_config)`. CAISO's
  WECC entries moved into the dicts unchanged (`build_wecc_*` remain as
  wrappers); NYISO/NEISO only need constants entries.
- **PJM node, calibrated to the 2023 net-interchange duration curve.**
  `PJM_external` zone + 5 border links (TTCs bounding the measured per-zone
  tie flows) joined on demand. Two scarcity import tranches (4 GW @ $46/$60)
  + six export sinks (9.8 GW @ $18–42), fitted by the new
  `scripts/derive_import_tranches.py`: measured net export is hourly
  price-orthogonal (corr −0.06), so the fit pairs the pjm_6 price duration
  curve with the measured interchange duration curve quantile-by-quantile.
  Static fit: 2023 annual 100% of actual, duration RMSE ~570 MW, diurnal
  corr 0.49; the same curve over-exports 2024 by ~+37% (load growth cut
  exports at an unchanged price level) — Tier 3, re-fit per vintage.
- **No double counting.** `load_demand` gained `include_interchange`; the
  runner and `--priced-interchange` calibration runs disable the measured
  schedule when the node serves interchange. Backcasts keep the measured
  schedule (data-first; exact); `run_calibration_full.py --priced-interchange`
  validates the node's calibration and the report's [2] section now prints
  the node's net position, duration-curve RMSE and import-hour share.
- **Forward runs**: `runner.run_scenario_iso` builds the node for any ISO
  with constants entries — PJM forecasts now carry price-responsive
  interchange (previously zero), and CAISO forward runs gain the export
  sink that `build_wecc_export_sink` documented but never wired in.
- **Bug fix:** `generators_to_fleet_arrays` pinned export sinks to a zero
  floor whenever any CHP/ST_GAS `min_gen` floor was active (the min_gen
  matrix replaces `pmin` as the LP lower bound for *every* generator, and
  PJM fleets always carry CHP floors). Sinks now keep their negative range.
- **Runs:** `results/calibration/pjm_j1_baseline` (pjm-6 config re-run,
  measured schedule — regression check) and
  `results/calibration/pjm_j1_priced` (same config through the priced node —
  calibration validation). Priced 2023: net export +39.0 TWh = 97.6% of
  actual (duration RMSE 647 MW); 2024 drifts +26% as fitted. The priced run
  also flattens zonal spreads (the external node wheels around the internal
  interfaces; all zones land at one price vs the baseline's ~$5 spread) and
  caps scarcity at the $46 import tranche (baseline max $695) — two more
  reasons backcasts keep the measured schedule.
## 2026-06-11 (PJM J3 — hourly LMP overlay + scarcity-residual localization)

- **J3a — true duration-curve overlay.** `scripts/derive_actual_lmp.py` now
  also writes `inputs/calibration/actual_lmp_hourly_PJM.parquet` (hub-mean
  hourly RT/DA LMP, 2023–2025, on the model's fixed 8760-hour local
  calendar) and adds `da_pct`/`rt_pct` duration-curve percentiles to
  `actual_lmp.json` (existing keys unchanged). The PJM `lmp-data/` exports
  were already hourly — the `_monthly_` filename is a misnomer.
- **New `scripts/analyze_lmp_residual.py`** compares a calibration bundle's
  hourly system price against the actual hourly series: monthly residuals,
  duration-curve overlay, and a Jul/Aug (configurable) localization by
  hour-of-day and actual-price band. Findings for pjm-9/pjm-10d in
  `docs/multi-iso/pjm-lmp-residual.md`: the Jul/Aug residual (−4.9 / −6.4
  $/MWh in 2023/2024) is a missing afternoon $75–200 price regime
  (16:00–17:00 −35/−39; actual-≥$75 hours carry 92% of the 2024 gap), not
  a level bias (p50 matches) — quantified before any reserve/ORDC work, per
  the J-series sequencing.
- **J3b prep.** Added TN to `campd.ISO_STATES["PJM"]`; the unit-outage
  derivation still awaits MD/DE/NC/TN (+ MI 2023/2025) CAMPD unit-level
  extracts before `campd-unit-outages-PJM.csv` can be regenerated.

## 2026-06-11 (PJM winter fidelity — dual-fuel switching, doc 03 Pack G)

Implements oil/gas dual-fuel switching for the PJM backcast (J2 winter
fidelity cluster: CT runtime −16/−21%, ST_GAS 2024 winter −15%, oil 0 vs
0.9 TWh). Objective-only — an `assemble_mc` fuel-price extension, no LP
structural change. Gated on `ScenarioConfig.dual_fuel_switching` (default
off; the calibration harness enables it for PJM only), so ERCOT and all
existing forecasts are byte-identical.

- **Dual-fuel flag from EIA-860 multiple-energy-source fields.** New
  `fleet.dual_fuel_plant_groups()` reads the committed EIA-860 Multifuel
  schedule parquet (`eia860_multifuel_operable.parquet`) and flags every
  operable gas-primary unit ("Energy Source 1" = NG) whose "Switch
  Between Oil and Natural Gas?" field is Y, classing each with the
  canonical gas classifier so the `(plant_code, plant_group)` keys line
  up with both the per-unit EIA-860 fleet and the per-plant tranche
  fleet. 577 keys nationally; 101 in PJM (~27 GW of switch-capable gas).
- **Oil price series with citations.** New `fuel.iso_monthly_oil_prices()`
  — the volume-weighted EIA-923 Schedule 5 monthly Petroleum receipt cost
  across the ISO's plants (PJM ~$17–23/MMBtu over 2023–2025; consistent
  with EIA's distillate ~$20 / residual ~$14 per MMBtu delivered to the
  electric power sector, 2023–2024) — sharing one resolver with
  `iso_monthly_gas_prices`. Unreported months and forward years fall back
  to the cited flat `OIL_PRICE_PER_MMBTU` ($18).
- **MC = min(gas, oil) per hour for capable units.** New
  `fuel.apply_dual_fuel_pricing()` caps each capable gas tranche's hourly
  fuel price at the delivered oil price (idempotent elementwise min,
  applied after the per-plant EIA-923 monthly gas overwrite so it sees
  the final delivered gas price). Emissions/heat rate stay on the gas
  characterization (known simplification). On the PJM 2024 calibration
  fleet the cap binds where reported delivered gas spiked past oil parity
  (e.g. plant 56807's CC tranches, 628 MW, ~12k unit-hours at an average
  −$32/MMBtu); with monthly ISO/plant-average gas it binds for few
  plant-months, so most of the modeled-oil gap awaits finer-than-monthly
  winter gas pricing.
- **Tests.** `test_fuel.py`: switch above parity / no switch below / off
  by default (ERCOT unchanged) / per-hour cap granularity. `test_fleet.py`:
  real-parquet capability extract and missing-parquet fallback.
## 2026-06-11 (CAISO hydro energy budgets + pumped storage — multi-iso P4)

Verifies the CAISO hydro/PS data through the generic PJM-built machinery
and makes the pumped-storage dispatch adder a per-ISO default. Full detail
in `docs/calibration-log.md` (2026-06-11 CAISO entry). **Cache keys
rotate**: `ScenarioConfig.pumped_storage_dispatch_adder` default changed
`10.0 → None`.

- **CAISO hydro budgets verified** (no loader changes needed): EIA-923
  CISO `HY` monthlies give 166 plants / 23.90 TWh (2023, extreme wet) and
  160 / 21.48 TWh (2024), within −2.0% / −5.6% of EIA-930 CISO hydro; all
  plants resolve to NP15/ZP26/SP15. Regression anchors added to
  `tests/test_hydro.py` (incl. an end-to-end solve pinning monthly
  dispatch ≤ budget on real CAISO budgets, and PJM/ERCOT-unchanged
  checks).
- **`load_hydro_budget(..., backfill_year=)`** (default off): the 2025
  EIA-923 early release covers only monthly-survey reporters (CAISO: 26 of
  ~185 plants, 12.3 of ~21.4 TWh); backfilling non-reporters from 2024
  recovers 20.39 TWh (−4.5% vs EIA-930). For the CAISO 2025 backcast.
- **Per-ISO PS dispatch adder** (`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`):
  PJM keeps its calibrated $10/MWh reserve-duty proxy; CAISO (2,078 MW
  EIA-860 PS fleet, Helms 1,053 MW, all NP15; 10 h / RTE 0.80 fleet
  params) resolves to $0 until its calibration says otherwise. The
  `ScenarioConfig` field is now `None` = per-ISO; a number overrides all.
- **`HydroBudget.monthly_min_energy` clips to the monthly budget** so a
  nameplate-fraction min-flow floor can't make a low-inflow month
  infeasible. Small-vs-large hydro split judged not warranted (≤30 MW =
  14% of CAISO capacity, ~13% of energy; see calibration log).
- Parameter registry regenerated; `validate_parameters.py` passes again
  (the new constants plus three previously missing scenario fields are
  registered).
## 2026-06-11 (CAISO pack P2 — per-plant offer-curve tranches & bin assignments)

CAISO backcast, 2024-first. ERCOT/PJM committed artifacts are untouched
(byte-identical); one runtime fix below also applies to PJM.

- **CEMS→EIA split-plant remap** (`campd.CAMPD_UNIT_PLANT_REMAP`): the AES
  Alamitos / Huntington Beach CCGTs (EIA 62115/62116) report CEMS under the
  legacy boiler ORIS codes (315/335). Their units (CT1/CT2) are re-keyed
  wherever unit identity is known, and facility-level loads substitute the
  companion unit-level rows for the split facilities (gross conserved).
  ~5.0 TWh/yr of CC history now attaches to the right fleet rows.
- **ST_GAS peaker exclusions**: AES Alamitos (315), AES Huntington Beach
  (335) and Ormond Beach (350) — the last once-through-cooling steamers,
  online 0.4–2.5% of CAMPD 2024–25 hours — join
  `outages.ST_GAS_PEAKER_PLANTS`: no outage overlay, no reliability floor,
  purely economic dispatch. `campd-unit-outages-CAISO.csv` regenerated:
  1,386 → 1,321 windows (126 economic-idleness rows dropped, 61 measured
  CC windows added for 62115/62116; all other rows byte-identical).
- **`thermal_tranches_CAISO.csv` re-derived from 2024–25** (2023 deferred
  with U1) with the remap in place: 83 measured plant-groups. Huntington's
  ST_GAS committed drops 68.2 → 8.9% (was polluted by the colocated CC);
  62115/62116 get measured committed 28.2/29.8%. CHP steam floors are
  **consumed, not re-derived** (`--chp-floors-from`): all 86 P3 floors
  byte-preserved.
- **Per-plant CC peaking (duct-firing) shares**: new `peaking_pct` column —
  the share of a CC's demonstrated sustained maximum (P99.5 of online net
  MW) cleared in <5% of online hours, capped at 25 — consumed by
  `fleet.thermal_tranche_peaking` under `cc_peaking_per_plant`, superseding
  the offer curve's class `pct_peaking`. CAISO CCs derive 0–6% (they cycle
  on the solar ramp; duct-fire headroom is thin) with Malburg at the 25 cap.
- **Bin assignments emitted**: `inputs/processed/bin_assignments_CAISO.csv`
  (`scripts/export_iso_bin_assignments.py`), 258 rows
  (Plant_Code, Plant_Group, Pct_Must_Run/Committed/Economic/Peaking, source
  tags). Measured committed covers 92.5% of CC_REGULAR, 100% of ST_GAS,
  78.6% of CT_PEAKER MW. Mixed facilities split per Plant_Group (Glenarm
  422 CC+CT flagged; no cross-fuel re-key needed).
- **CHP grid-share clamp in `bins_to_fleet`** (fix, affects PJM too): under
  `chp_steam_following`, a cogen whose measured committed floor exceeds the
  grid share net of the BTM pull-out (Elk Hills, Salinas River; PJM Marcus
  Hook, Grays Ferry) carried more LP capacity than its grid-facing share
  (up to +13%). Committed + peaking now clamp into `grid_cap` (committed
  keeps its measured level; the scarcity peak gives way).
- **Geothermal verification** (audit §2c): the biomass/OTHER must-run
  injection carries CISO geothermal at 8.05/7.81 TWh (2023/24) in a
  monthly-shaped 835–969 MW baseload band — not a flat annual average. The
  dedicated EIA-930 GEO column is only populated from mid-Dec 2025 (CISO
  folds geothermal into the 930 NG aggregate before that); where populated
  it reads 740 MW flat (CV 4.4%) vs the injection's 746 MW — within 1%.
- Tests: `tests/test_caiso_bins.py` (remap routing, artifact bounds, bin
  shares sum to 100, CHP BTM removed from LP capacity, per-plant peaking
  survives the offer-curve override).

## 2026-06-09 (Forecast mode — P0 fixes from the peer review)

Implements the P0 "fix before quoting any forward run" items from
`docs/peer-review-2026-06.md` (§F). Backcast behavior is unchanged (the
full suite passes; backcasts solve the weather year itself, where every
fix below is a no-op); forward runs change materially. **Cache keys
rotate**: `ScenarioConfig` gained a `mode` field, so previously cached
scenario-years re-solve on first touch.

- **B1 — retirement screens margin, not gross revenue.** The economic
  retirement screen now nets each unit's *full* variable cost (fuel + VOM +
  emission prices; computed even on cached years and threaded as
  `prior_results["mc_cost"]`) against price before comparing with
  going-forward fixed cost. Gross revenue let units "cover" FOM with money
  already spent on fuel — only units that barely ran could ever retire.
  Take-or-pay coal is charged full fuel cost here (avoidable on a
  retirement horizon) even though it bids below it in dispatch. The
  `mc=None` fallback (gross + a warning) survives only for callers that
  cannot supply costs. Spec §5.2 updated — it documented the same bug.
  Measured magnitude (ERCOT 2027 screen on 2026 dispatch): 28.0 GW of
  tranche capacity flags a loss year under the margin screen vs 10.3 GW
  under gross — 17.7 GW was mis-assessed. PJM barely moves (~34 MW)
  because its full-net-CONE capacity payment (finding B6, P1 scope)
  dominates the screen there.
- **B2/C8 — eastern-ISO forward runs no longer crash.** `QUEUE_CAP_GW` /
  `QUEUE_CAP_PER_TECH_GW`, `RENEWABLE_INSTALLED_MW`, `RENEWABLE_AVG_CF`
  and `RENEWABLE_ZONE_ALLOCATION` now carry PJM/MISO/SPP/NYISO/NEISO
  entries (Tier 3, flagged needs-citation), and `apply_economic_new_entry`
  raises a clear `KeyError` for any ISO missing queue caps instead of
  silently building nothing. A 2-year PJM forecast smoke run completes.
- **C1 — demand growth gap closed.** `_scale_demand` compounds from
  `config.weather_year`, not `START_YEAR`: 2026 demand is now 2024 actuals
  × two years of growth instead of 2024 actuals verbatim (an error that
  compounded through 2050).
- **B8 — Wright's-Law exponent.** `wright_cost` uses
  `-log2(1 − learning_rate)`, so a documented "20%/doubling" rate now
  yields exactly ×0.80 per doubling (was ×0.87); matches the CCS-retrofit
  path, which already used the correct form and now delegates to it.
- **B3 — vintage survives aggregation.** All three fleet aggregators carry
  a capacity-weighted `online_year` into bin representatives (was: reset
  to the 2000 default, which permanently disqualified every aggregated
  gas-CC bin from the CCS-retrofit screen and broke local learning
  attribution).
- **A3 — storage daily-cycling flag wired in the runner.**
  `storage_daily_cycling=True` now bounds forecast storage to within-day
  arbitrage (the backcast script already honored it; the runner ignored
  it, leaving full-year perfect foresight).
- **C9 — explicit `ScenarioConfig.mode`.** `"forecast"` (default) /
  `"backcast"`, validated in `__post_init__`; the renewables loader reads
  it instead of inferring backcast from `gas_price_override`, so a
  pinned-gas forecast sensitivity stays a forecast. The calibration
  scripts set it explicitly.
- **B10 — known-additions pipeline wired.** New
  `fleet.load_planned_additions()`: EIA-860 proposed units with
  construction-committed statuses (U/V/TS), BA-mapped to the ISO,
  post-snapshot effective years (`EIA860_OPERABLE_VINTAGE`, bumped to
  2025 with the 2025 Early Release parquets — older effective dates are
  slipped projects the snapshot has overtaken), zoned by plant lat/lon,
  injected in their online year (units already due join the first-year
  fleet). Forecast mode only; an all-non-thermal pipeline (CAISO)
  returns empty. `runner.py` no longer hard-codes
  `planned_additions=[]`. ERCOT pipeline: 30 units / 3.95 GW, 2026-29.
- **Registry**: `parameters.json` / `docs/parameter-citations.md`
  regenerated for the new constants (and 10 pre-existing missing entries).
  New tests: retirement margin semantics, queue-cap coverage + loud
  failure, PJM entry smoke, wright doubling, vintage preservation,
  planned-additions loader, mode validation, demand-scaling pins.

## 2026-06-09 (Backcast dashboard — single-run report redesign + diagnostics)

Redesigns the backcast results page around interpreting **one run across all
testing years at once**, replacing the comparison-centric layout. The run data
schema and the registry/regen pipeline are untouched, so concurrently pushed
ERCOT/PJM bundles render without any regeneration of their payloads.

- **Run report view (new default).** A per-year scorecard (classes in
  tolerance, system volume error, generation-weighted fleet dispatch r, model
  vs actual avg LMP), a **class-tolerance heatmap** (class × year, signed
  volume error with the ±5% deadband in gray) and a **dispatch-correlation
  heatmap** (class × year, hourly r vs CAMPD in green/amber/red bands at
  0.85/0.70), plus per-year monthly LMP model-vs-DA/RT charts — no more
  clicking through years to remember how a run did.
- **Auto-generated diagnostics.** The report decomposes every failing class by
  month, zone and plant (from the existing `volErr` payload + per-plant Δ923)
  and writes plain-language pointers: level shift vs seasonal concentration
  (→ committed vs peak/econ tranche), zone concentration (→ zonal load/basis),
  single-plant misses (→ outage overlay/capacity), weak-r classes split into
  timing-vs-volume problems with hour-of-day bias (too flat / too peaky), and
  LMP bias months tied to the coincident class volume miss. Computed
  client-side, so diagnostics appear automatically for every pushed bundle.
- **Comparison mode retired.** The Comparison/Single toggle, multi-run picker
  and run-over-run slope chart are gone; the sidebar is a simple newest-first
  run radio list. The old signed-volume-error matrix (Year/Month/Zone/Run
  column selector) is replaced by per-class **month and zone miss bars**
  ("Where the volume miss lives") on the Charts view.
- **Charts/Tables kept.** All deep-dive charts (commitment heatmaps, daily
  profile, hours-at-CF with tranche markers, monthly + annual generation)
  remain on Charts; the generation-mix, fuel-vs-930, fossil-class, monthly-LMP
  and per-plant tables remain on Tables. Year/class controls hide on the
  report (it spans years); zone chips steer every zone-aware metric on all
  views. Mobile: single-column cards/grids, tap-to-pin tooltips kept.

## 2026-06-09 (PJM backcast diagnostics — hydro/pumped storage in the LP, fresh dashboard benchmark, EIA-860 2025 ER)

Root-causes the "wildly off" PJM dashboard results: a stale shared benchmark
in the report layer, and ~14 TWh of supply (hydro + residual OTHER) plus ~8 GW
of peak capability (pumped storage + hydro) missing from the non-ERCOT LP,
which drove July/August VOLL price spikes that never happened.

- **Dashboard benchmark now comes from the newest bundle.**
  `render_calibration_html.build_payload` rebuilt the shared per-ISO benchmark
  only from registry run 0 — the *oldest* bundle — freezing plant→group
  classification and EIA-923 class totals to pre-coal-split code (PJM coal as
  one generic `COAL`, `COAL_SUB` before the SUB→`COAL_PRB` rename). Newer runs
  then rendered "Coal: model 0.00 vs actual ~116 TWh (−100%)" while the split
  coal classes had no benchmark plants and vanished from the heatmaps. The
  benchmark is now rebuilt per run so the newest bundle covering each year
  wins. The stale `pjm_8zone` bundle and its registry/run artifacts are
  removed.
- **Conventional hydro dispatches in the LP for every ISO.**
  `run_calibration.run_year` now builds one LP unit per EIA-923-reporting
  hydro plant (`_hydro_fleet`: EIA-860 nameplate power cap, EIA-923 monthly
  net generation as the dispatch LP's hydro energy-budget rows), replacing
  the flat-monthly ERCOT-only must-run injection — hydro can now peak-shave.
  PJM: 76 plants, ~3.3 GW, ~8.9 TWh.
- **Pumped storage joins the storage fleet.** New
  `storage.load_eia860_pumped_storage` reads prime-mover `PS` units off the
  EIA-860 generator schedule (the battery schedule does not carry them) into
  per-zone `StorageUnit`s with cited duration/RTE constants
  (`PUMPED_STORAGE_DURATION_HOURS` = 10 h, `PUMPED_STORAGE_RTE` = 0.80). PJM
  gains its ~5.0 GW (Bath County, Muddy Run, Yards Creek, Seneca, Smith
  Mountain).
- **Must-run injection un-gated from ERCOT.** The biomass/OTHER residual
  injection (`run_calibration_full._must_run_profiles`) now applies to every
  ISO; classes the LP fleet already carries as units are skipped (biomass for
  the per-plant non-ERCOT fleets), and pumped-storage plants are held out of
  OTHER (they dispatch as LP storage). Hydro is no longer an injected class
  anywhere. `--rebuild-benchmark` also stops using the ERCOT bin sheet for
  non-ERCOT plant→group maps.
- **Dead `COAL_SUB` knob removed and guarded.** Sub-bituminous routes to
  `COAL_PRB` (one PRB name across ISOs), so `COAL_SUB` offer-curve entries
  silently tuned nothing; the defaults are scrubbed and
  `--offer-curve-json` / `--offer-curve-delta-json` now reject unknown class
  keys loudly.
- **EIA-860 2025 Early Release.** `process_eia860.py` locates the header row
  by anchor columns (the ER adds a disclaimer preamble) and the committed
  parquet extracts are regenerated from `eia8602025ER.zip` (operating years
  through 2025).

## 2026-06-08 (Backcast — multi-ISO toggle + color-coded market chrome)

Makes the ISO axis a real, prominent toggle and registers a PJM run alongside
the ERCOT set so the dashboard ships with more than one market.

- **PJM on the dashboard.** Registered `pjm_8zone` (2023+2024) as `pjm 1 8zone`
  via `dashboard_add_run.py`, so the ISO toggle now switches between **ERCOT**
  (Run-58 / Run-59 / run57-canonical) and **PJM**. Both markets carry the new
  actual-LMP benchmark (PJM hub average, ERCOT `HB_HUBAVG`).
- **Color-coded market toggle.** The sidebar "Market (ISO)" control is now a set
  of prominent, color-coded buttons (canonical ISO colors from
  `docs/DESIGN_SYSTEM.md` — ERCOT green, PJM sky) with a per-ISO run count and a
  one-line hint listing the other loaded markets. The active market is echoed in
  a colored header badge next to the title and in a dynamic subtitle
  (`ERCOT · 3 runs · …`), so it is always clear which ISO is on screen.
- **`scripts/_backcast_shell`.** Added the ISO color tokens, `.isobtn` /
  `.isobadge` styles, and `isoColorVar` / `isoRunCount` / `updateIsoChrome`
  helpers; `selectIso` now repaints the header chrome on every switch. No change
  to the run data shape.

## 2026-06-08 (Backcast summary — looser class tolerance + actual-LMP comparison)

Loosens the backcast dashboard **Summary** page's per-class pass band and adds a
model-vs-actual average-LMP comparison.

- **Class tolerance.** A fossil class on the summary now passes within **±3%
  _or_ 1 TWh** of the actual (`SUM_TOL_PCT` / `SUM_TOL_TWH` in
  `scripts/_backcast_shell`), so small-volume classes that are off by a larger %
  but within a TWh no longer count against the headline. This summary band is
  separate from — and looser than — the per-cell heatmap deadband
  (`TOLERANCE_PCT`, unchanged at 0.02). The "Classes in tolerance" KPI, the
  worst-class color, the tornado band and its caption all reflect the dual band.
- **Average LMP comparison.** New `scripts/derive_actual_lmp.py` reduces the raw
  ERCOT settlement-point workbooks (`HB_HUBAVG`, DAM hourly / RTM 15-min) and the
  PJM hub LMP export to a small committed reference,
  `inputs/calibration/actual_lmp.json` (`{iso: {year: {da, rt}}}`, $/MWh).
  `build_payload` attaches it to each benchmark year as `avgLMP`, and the summary
  gains an "Avg LMP — model vs actual historical" KPI + panel showing the model
  (load-weighted over the selected zones) against the actual day-ahead /
  real-time system hub average with the signed Δ. Diagnostic only — LMP level is
  not a calibration target. Absent for an ISO-year with no price file (card shows
  model only).

## 2026-06-08 (Backcast — signed volume-error heatmap on the Charts view)

Adds a Plotly heatmap to the backcast dashboard's Charts view showing each
asset class's signed volume error — `(model_TWh − actual_TWh) / actual_TWh` —
with a class-row × axis-toggle (Year / Month / Zone / Run) layout, a diverging
cool→white→warm scale built from the dashboard color tokens, a neutral-gray
deadband, and a ±20% color cap. Each cell is annotated with its absolute model
TWh.

- **`market_sim.results.calibration`.** New canonical source-authority rule:
  `actuals_source(klass)` returns EIA-923 for every class except solar, which
  uses EIA-930 (utility + distributed PV is under-reported in 923). Added
  `signed_volume_error`, a thin wrapper over the existing `_pct_diff` so the
  export computes the delta with the same sign/zero-actual convention as the
  other diagnostics. The choice lives here, not in JS.
- **`scripts/render_calibration_html.build_payload`.** Each run-year now emits a
  `volErr` field: per fossil class, model vs EIA-923 TWh decomposed by zone and
  month (so the heatmap re-aggregates to any axis); solar carries a system
  annual vs EIA-930. Non-finite errors (nonzero model over a zero actual) are
  stored as `null` so the browser's `JSON.parse` never sees a bare `Infinity`.
- **`scripts/_backcast_shell`.** One `TOLERANCE_PCT` const at the top of the
  script (default 0.02; spec target 0.05) drives the deadband. The heatmap is
  Plotly-only and reuses the `--accent` / `--danger` / `--mr` design tokens —
  no new palette. The LP/dispatch/capacity code, the calibration
  source-authority logic, the Tables view and the existing run data are
  untouched (run data files only gain `volErr`).

## 2026-06-06 (CC peak — tweakable flat band instead of per-class duct burner)

Makes the CC_REGULAR / CC_CHP peak band a tunable offer-curve `peak` key
(default **2.25**, the F-class duct-burner multiplier and modal CC class)
instead of the hardcoded per-turbine-class table. So `CC_REGULAR.peak` /
`CC_CHP.peak` can now be nudged from the calibration workflow like every other
group's peak.

- **`scripts/run_calibration`.** Added `"peak": 2.25` to the CC_REGULAR and
  CC_CHP offer-curve entries. `fleet.bins_to_fleet` already honored an explicit
  `peak` key over the duct-burner fallback, so no model-code change was needed.
- **Behavior change at default:** all CC plants now peak at 2.25× regardless of
  turbine class — G/H-class CCs drop 2.50→2.25 (cheaper peak) and E-class rise
  2.00→2.25. The ERCOT fleet is overwhelmingly F-class, so the shift is small;
  a recalibration captures it. The per-class `cc_duct_burner_peak_mult` stays as
  the fallback when no `peak` key is set (e.g. other ISOs).

## 2026-06-06 (Uniform gas pricing — drop per-plant gas fuel cost by default)

Gas generators now all pay the **same** delivered price for a year (AEO
Henry Hub trajectory + ISO basis, optionally seasonal). Per-plant EIA-923
monthly *gas* costs are now **off by default** behind a new flag
`ScenarioConfig.gas_plant_monthly_fuel_pricing` (default `False`).

- **Why.** EIA-923 Schedule-5 gas-cost reporting is sparse in ERCOT (~12%
  of CC capacity), and merchant CCs in a hub all buy gas in the same
  market. Giving the few reporting plants their own (often higher,
  winter-spiking) cost while suppressed peers paid the smoothed trajectory
  split same-zone units on a reporting artifact, not real economics — e.g.
  Jack County (the only reporting CC among its North-zone neighbours) paid
  ~$2.69/$2.46 in 2023/2024 vs the $2.54/$2.19 everyone else paid,
  penalising it in 7/12 and 5/12 months and contributing to its under-run.
- **What changed.** `apply_plant_monthly_fuel_prices` skips gas unless the
  new flag is set; Jack now pays exactly the same uniform price as
  Freestone, Colorado Bend II, etc. **Coal is unchanged** — lignite
  mine-mouth vs railed PRB are physically distinct costs, so per-plant coal
  pricing (`coal_plant_monthly_pricing`) stays on by default.
- **Docstrings fixed.** Corrected the inaccurate "ERCOT — whose plants
  overwhelmingly report — is unchanged" note on `nearby_fuel_price_fallback`
  and updated `fuel.py` / `binning-methodology.md` to describe gas as
  uniform-by-default.
- Tests updated: the gas-overwrite mechanism tests now opt in via the flag;
  added a test asserting gas is uniform by default. All fuel tests pass.

## 2026-06-06 (Docs/data cleanup — kill the "bin dispatch" confusion)

Removes stale artifacts that misrepresented how the ERCOT CC fleet
dispatches. The model has dispatched **one LP generator per plant** on each
plant's **own** measured heat rate for some time, with the economic block
rendered as a 6-slice rising offer-curve ramp (`offer_curve_smoothing_n=6`,
linear) and the committed/min-load floor sized per-plant from CAMPD
(`cc_committed_per_plant`). But several legacy columns and doc sections
still described a multi-plant, bin-weighted-HR, flat-4-tranche, `pmin`-floor
model — enough to mislead a fresh reader (and an LLM) into the wrong mental
model.

- **`inputs/custom-bin-assignments.csv`** — dropped 12 columns that the
  loader never reads and that encoded the misleading picture:
  `Bin_Zone_Weighted_Avg_HR` (implies a bin-weighted dispatch HR — never
  used), `Dispatch_Mode`, `Must_Run`, the four absolute `HR_Must_Run/
  Committed/Economic/Peaking` (the dispatched band HRs come from the offer
  curve, not these), and `Plant_Age`/`POF_pct`/`WEFOR_pct`/`Derate_pct`/
  `EAF_pct` (availability comes from the age model + CAMPD outage overlays,
  not the CSV). `load_campd_bins` and all 117 bin/fleet/outage/fuel tests
  pass unchanged.
- **`docs/binning-methodology.md`** — retitled and rewritten to lead with
  "one plant = one LP generator", correct the tranche table (no `pmin`
  floors), add an **Economic ramp** section documenting the actual default
  (`_econ_curve_steps`, `offer_curve_smoothing_n`/`_exp`, peak folded for
  CC), fix the wrong `N=12`/`p=3` smoothing claim, and mark the flat
  per-group tranche table as legacy fallback.
- **`model-methodology-spec.md`** — corrected the §3.3 tranche bullets so
  Economic is the default rising N-slice ramp and Committed is the
  CAMPD-derived per-plant floor; flagged that no bin-weighted HR / `pmin`
  is used.
- **Docstrings** — `load_campd_bins` now states which CSV columns are
  overridden downstream; `disaggregate_dispatch` now states it is an
  identity no-op for the per-plant ERCOT fleet (a legacy multi-plant path),
  so its pro-rata split is not read into per-plant results.

No dispatch behaviour changes — this is documentation and dead-data only.

## 2026-06-06 (Unified offer-curve ramp — econ_low → econ_high, separate peak)

Makes every thermal group's offer curve behave identically: the n-slice
economic ramp spans **`econ_low → econ_high`** (its slope set by those two
endpoints), and the duct-firing / scarcity **peak is always a separate flat
tranche that jumps up above the ramp** — never folded into the ramp top.

- **Why.** Previously `_CURVE_FOLD_PEAK = (CC_REGULAR, CC_CHP, COAL)` ran the
  ramp from `econ_low` straight up to the duct-burner peak and emitted **no**
  separate peak tranche, so `econ_high` was **dead** for CC and coal — tuning
  it did nothing — and the LP disagreed with the dashboard (which already drew
  `econ_low → econ_high` + a separate peak). Only `CT_PEAKER` / `ST_GAS` did the
  intended thing. Now all groups share the `CT/ST` structure.
- **`data/fleet.bins_to_fleet`.** Removed the `_CURVE_FOLD_PEAK` /
  `_CURVE_ECON_ONLY` split (and `peak_in_curve`): the ramp always spans
  `econ_cap` from `econ_low` to `econ_high`, and the peak band is always
  emitted. `econ_high` is now the live ramp endpoint for CC and coal.
- **Configurable bands.** New optional offer-curve keys: **`pct_committed`**
  (committed capacity %, overrides the CSV; per-plant CC grounding still wins)
  and, for CC, an explicit **`peak`** HR multiplier (overrides the per-turbine-
  class duct-burner default, which is retained when `peak` is omitted). The peak
  capacity % (`pct_peaking`) was already configurable.
- **CT_CHP folded into the offer curve.** CT_CHP was the last group still on the
  legacy single-value overrides (`ct_committed/econ/peak_hr_override`); it now has
  an `offer_curve_by_group` entry (committed 1.10, econ_low = econ_high = 1.20,
  peak 1.40) mapped from those values, so its econ ramp and peak are tweakable
  like every other group. `econ_low == econ_high` makes the default a flat 1.20
  block — no dispatch change until the endpoints are pulled apart. The
  `ct_*_hr_override` config fields are now inert for CT_CHP.
- **Calibration impact.** CC and coal dispatch shifts — the ramp top drops from
  ~2.0–2.5× (duct burner) to `econ_high`, with the peak re-added as a separate
  slab above it. A recalibration run is expected to re-settle the band values.
- Tests: `TestUnifiedOfferCurve` (ramp tops at `econ_high`, separate peak band,
  `pct_committed` and CC `peak` configurable). Docstrings in
  `config/scenarios` and `scripts/run_calibration` updated.

## 2026-06-05 (ERCOT Northeast zone — NE_LOB trapped-generation lobe)

Splits a seventh ERCOT zone, **Northeast**, out of North to model the NE_LOB
generic transmission constraint — the single biggest piece of ERCOT congestion
the 6-zone topology was missing (binds 17.4% of 2023–24 SCED intervals).

- **Why.** NE Texas (the EAST weather zone) is a generation-rich lobe: ~4.2 GW
  of coal (Martin Lake, Welsh, Pirkey) + ~3.9 GW of gas (Tenaska Gateway CC,
  Wilkes, …) serving only ~3.4% of system load, behind a ~1,300 MW export limit.
  The six-zone model let all ~8 GW pour into North as if unconstrained, over-
  running Martin Lake (PRB) and mis-dispatching the NE combined-cycles. This is
  the carve-out the data-first rule calls out — real congestion the aggregation
  couldn't represent.
- **`config/iso_configs._ercot_config`.** New `Northeast` zone (load_share
  0.0335 = the EAST weather zone; North drops to 0.3081) and a
  `Northeast→North` link at **1,300 MW** (the NE_LOB limit). 7 zones, 9 links.
- **`data/eia_loader._ERCOT_LOAD_ZONE_GROUPS`.** EAST weather zone → Northeast,
  so the zone gets its own measured hourly load shape.
- **`data/zone_assignment._ercot_zone`.** NE-Texas box (lat 31.3–34.0,
  lon −95.55…−93.0) routes the lobe's plants to Northeast before the North
  catch-all; DFW / central-Texas (Limestone) stay in North.
- Tests updated to the 7-zone / 9-link topology, plus NE plant-assignment
  coverage. Baselined with the smooth offer curve (PRB sigmoid off) before any
  economic re-tuning.

## 2026-06-05 (ERCOT export TTCs from full-year SCED; data-first rule)

Sets the ERCOT West/Panhandle export TTCs to the **measured** GTC limits from
the full 2023–2024 NP6-86 SCED binding-constraint archive
(`inputs/raw-data/iso-specific-transmission/`, 202,512 SCED intervals), and
codifies the principle behind it.

- **New non-negotiable rule (`claude.md`): prefer accurate/measured data over
  estimates; never revert to an estimate because it fits the backcast better.**
  If real data makes the backcast worse, that's a *discovered bug* elsewhere in
  the model (the estimate was masking it) — keep the real input and fix the root
  cause. The only exception is genuine misalignment to our representation
  (different boundary/aggregation/units than our zones), which must be
  documented and reconciled rather than guessed.
- **`config/iso_configs._ercot_config` links.** West→North 7,300 + West→SC 2,700
  (WESTEX ~10,000 MW, binds 9.3%); Panhandle→North 2,680 (PNHNDL, 10.2%) — both
  measured. North→Houston **kept at 8,000** as the documented carve-out: the
  single N_TO_H GTC (~4,810, binds 0.21%) is one of several parallel 345 kV
  paths the six-zone reduction collapses into one link, so using it literally
  would understate the real interface.
- **West TTC effect is negligible (correction).** An earlier revision of this
  entry blamed the accurate West limit for a coal overshoot — that was a
  confounded comparison (`run33` predates the n=6 econ-curve smoothing). Clean
  isolation from existing bundles: `run34` (old TTC, smoothing on) and `run37`
  (new TTC, smoothing on) give an **identical** coal mix (70.4 TWh, +13% vs
  EIA-930), while `run33` (old TTC, **smoothing off**) is +3%. So the West TTC
  has ~zero effect on dispatch; the +13% coal overshoot is the **n=6 offer-curve
  smoothing** (`offer_curve_smoothing_n`, introduced run34), whose rising econ
  ramp cheapens the bottom of PRB's curve and pulls in ~+5.7 TWh of baseload
  PRB. The accurate West/Panhandle TTCs are kept as data-first hygiene.
- **PRB offer-curve experiment (run38).** Dropping the gas-keyed PRB passthrough
  sigmoid and relying on the static `offer_curve_by_group` COAL_PRB bands (with
  smoothing on) gives coal **−4.4%** vs EIA — closer than the sigmoid+smoothing
  default's +13%, and removes the eight sigmoid magic numbers. A small downward
  nudge to the PRB bands would close the remaining gap. Candidate replacement
  for the sigmoid, pending sign-off.
- **`scripts/derive_ttc_limits.py`** rewritten to scan the full multi-year
  NP6-86 set, report every GTC's binding frequency and mean limit, and print the
  derived `ttc_mw`; hardened against off-schema / latin-1 daily files.
- **Caveat (in the config comment).** ERCOT's *most*-binding GTCs are intra-zone
  pockets the six-zone topology cannot represent — NE_LOB (NE-Texas export,
  ~1,300 MW, 17.4%), VALEXP (5.9%), EASTEX (0.5%), TRDWEL — so intra-ERCOT
  dispatch is near copper-plate, faithful to ERCOT; a zone split (e.g. a NE lobe
  out of North) is the only way to capture that pocket congestion.

## 2026-06-05 (PJM refinements: CHP classification, border-zone exports, gas offer curves)

Three PJM fidelity refinements on top of the 8-zone topology + import/export
node. ERCOT untouched (full suite green).

- **CHP classification.** EIA-860's "Associated with Combined Heat and Power
  System" flag (joined plant-level from the operable sheet, dropped from the
  processed parquet) now maps gas cogens to CC_CHP / CT_CHP / ST_CHP instead of
  the merchant variants — 202 PJM CHP units (47 CC, 155 CT). CHP CC/CT/ST are in
  the outage-overlay QUALIFYING set, so they now get the historic overlay too.
  ERCOT is unaffected (its thermal comes from CAMPD bins; CHP grouping only
  reaches the filtered-out non-thermal subset of `load_fleet_from_csv`).
- **Border-zone export attribution.** `pjm_zonal_interchange` attributes each
  tie's measured net flow to the border zone it interconnects (NYISO→EMAAC,
  MISO-west→ComEd, Indiana/Ohio→AEP-Ohio, Michigan→ATSI, Carolinas/TVA→
  Dominion) instead of spreading the system total by load share. Total is
  conserved (40 TWh) but now realistic per zone: ComEd +17, AEP-Ohio +16,
  EMAAC +18.5 TWh export; Dominion −11.6 (net import from the Carolinas) —
  sharpening inter-zone congestion. `load_demand` adds the per-zone matrix for
  PJM, falling back to the system-net scalar when the tie file is absent.
- **Gas offer curves (`gas_offer_curve`, default off).** `split_gas_tranches`
  gives the per-plant gas fleet a stepped offer curve — a part-load committed
  band (heat rate × `cc_/ct_/gas_st_committed_hr_mult`), an efficient economic
  band, and a small duct-fired peaking top slice (× `ct_peak_hr_penalty`) —
  instead of a single flat block. Capacity-conserving; runs after the coal
  tranche split and preserves its passthrough fracs. Off by default so the
  current calibration is unchanged; enabling it shifts the gas merit order and
  wants a tuning pass on `_GAS_TRANCHE_SHARES`.

## 2026-06-05 (PJM import/export node — measured net interchange)

Closes the PJM backcast's largest structural gap (Module M4). PJM is a large
net exporter (~40 TWh / +4,564 MW avg in 2023), but the energy-only LP served
only internal load, so it under-generated by the export and mis-attributed the
missing marginal gas to coal. ERCOT and other ISOs are unaffected.

- **`data/eia_loader.pjm_net_interchange`** reads PJM's hourly actual tie-line
  interchange (`inputs/raw-data/iso-specific-transmission/
  PJM_{year}_import_export_act_sch_interchange.csv`), sums `actual_flow` across
  all 22 ties per hour and returns it export-positive on the 8760-hour clock.
  `load_demand` adds it to PJM's internal-load demand (the same interchange
  mechanism ERCOT uses for its DC ties), so the fleet now generates internal
  load **plus** the measured net export. The 2023 schedule (+4,564 MW = 40 TWh)
  matches the EIA-930 figure exactly. Modeled as the *measured* schedule (a
  backcast reproduces actual flows), not a price-responsive offer; absent a
  file (forward years) PJM falls back to zero interchange. Border-zone
  attribution of the export (vs the current system-net allocation) is the
  natural next refinement now that the 8-zone topology exists.
## 2026-06-05 (ERCOT per-zone hourly load shapes)

Gives each of ERCOT's six model transmission zones its **own measured hourly
demand shape** instead of a single ERCOT-wide demand curve scaled by a fixed
per-zone `load_share`. Mirrors the PJM per-zone-load change. Every other ISO is
untouched (full suite green, 701 tests).

- **Per-zone shapes** (`data/eia_loader.ercot_zonal_load_shares` + the
  `load_demand` hook): reads ERCOT's hourly *Actual System Load by Weather Zone*
  (NP3-565-CD, `inputs/raw-data/zone-specific-demand/ERCOT_Native_Load_<year>.xlsx`,
  2022–2025) and aggregates the eight weather zones onto the six model zones —
  West ← FAR_WEST+WEST, North ← EAST+NORTH+NORTH_C, Houston ← COAST,
  South_Central ← SOUTH_C, South ← SOUTHERN; Panhandle keeps no load (ERCOT has
  no Panhandle weather zone). For each hour, each zone gets its fraction of
  system load, and those time-varying shares multiply the existing EIA-930
  system demand total — so the **system level is unchanged** but zones now peak
  at different hours (the hot, wind-belt West and coastal Houston no longer track
  North Central's shape). This removes the single shared demand curve that was
  driving the previously-observed zonal-price artifacts.
- The eight-weather-zone → six-transmission-zone map matches
  `scripts/derive_load_shares.py`, which seeded the static `load_share` values;
  the full-year native-load annual averages reproduce those static shares to
  within ~1 pt, so only the *intra-year shape* changes, not the levels.
- Falls back to the static `load_share` split when the native-load file is
  absent, so non-ERCOT ISOs and missing-year ERCOT runs are unaffected.
- Refactored the shared normalize/back-fill tail (`_hourly_shares_from_groups`)
  out of `pjm_zonal_load_shares`; updated `tests/test_eia_loader.py` (CAISO now
  guards the static-share split; ERCOT gains per-zone-shape coverage).
- Re-ran the run32 configuration with the new per-zone demand
  (`results/calibration/run33_ercot_zonal_load`).

## 2026-06-05 (PJM 8-zone topology + per-zone hourly load shapes)

Replaces PJM's 4-zone pipe-and-bubble with an 8-zone, LDA-aligned topology
derived from the uploaded PJM transmission/LMP/load data, and gives each zone
its own measured hourly load shape. ERCOT and every other ISO are untouched
(full suite green, 699 tests).

- **Eight zones** (`config/iso_configs._pjm_config`): ComEd · AEP-Ohio · ATSI ·
  West-APS · Central-PA · Dominion · EMAAC · SWMAAC. The old `PJM_West` (half
  the load) blended ComEd ($24/MWh, export-congested), the AEP coal belt ($30)
  and import-constrained western PA ($33) — a ~$9/MWh spread across the
  AP-South / Bedington-BlackOak interfaces (the most-binding ones in the 2024
  transfer-limits data) that the 4-zone model erased. Cross-hub LMP std is
  ~$6.4/MWh, so the locational signal is real. Load shares and the inter-zone
  TTC/link mesh are seeded from the PJM metered-load and transfer-limits files
  (AEP/DOM ~4,069 MW, AP-South ~4,453 MW, Bedington-BlackOak ~1,947 MW).
- **Plant→zone crosswalk** (`data/zone_assignment._pjm_zone`): rewritten for the
  eight zones, splitting OH (ATSI north of ~40.9°), WV (APS north of ~39.0°), PA
  (Philadelphia metro → EMAAC, west of ~-79° → West-APS, else Central-PA) and MD
  (western panhandle → West-APS, else SWMAAC) by eGRID lat/lon/county. 29 of
  PJM's ~36 GW of coal correctly lands in AEP-Ohio (17 GW) + West-APS (12 GW).
  Tier 3 — approximates utility territories; verify against a PJM zone-county
  crosswalk.
- **Per-zone hourly load** (`data/eia_loader.pjm_zonal_load_shares`): reads
  PJM's hourly metered-load file, aggregates the 20 real transmission zones to
  the 8 model zones, and gives each its own hourly *share* of system load (zones
  peak at different times — EMAAC summer-peaking, West/ATSI flat). The shares
  multiply the existing system-demand total, so zonal *shape* comes from real
  data while the demand *level* stays tied to the existing series. Falls back to
  the static per-zone share when the file is absent. **Data note:** the uploaded
  `PJM2024_hrl_load_metered.csv` currently contains 2023 data — its (stable)
  zonal shape is used against 2024 demand and a warning is logged; a real 2024
  re-upload will refine the shapes.

## 2026-06-04 (Unit-level ERCOT outage backcast from CAMPD)

Replaces the hand-maintained, Jan–Aug-2023-only unit-outage extract with a
CAMPD-derived one covering **full 2023 and 2024**, so the ERCOT backcast's
unit-level derate layer now removes each generating unit's capacity during its
*own* observed outages — including the coal-unit outages the facility-summed
overlay structurally cannot see. ERCOT-only; no other ISO has unit-level CAMPD
extracts, so their plant codes never match and behaviour is unchanged.

- **`scripts/derive_campd_unit_outages.py` (new).** Detects an outage on each
  *unit's* own CAMPD hourly gross (`inputs/raw-data/campd-unit-level/
  {STATE}_{YEAR}.parquet`) and writes `inputs/raw-data/campd-unit-outages.csv`
  in the schema `unit_outage_derate_factors` consumes. Each unit's capacity is
  the EIA-860 generator nameplate (matched on plant code + normalised unit id —
  CAMPD `WAP5`↔EIA `5`, CAMPD `1`↔EIA `OG1`), falling back to the unit's
  observed CAMPD peak when no generator matches. The detector is chosen by the
  unit's own fuel: **coal** (baseload) uses the averaged real-run rule, so a
  sustained sub-5%-CF gap is an outage; **CC / gas-steam** (load-following) use
  the event-based rule (any hour above ~2% CF breaks the window), so a unit is
  flagged only when it goes genuinely dead and an economically idle CC turbine
  is *not* mistaken for an outage. CT peakers and the ST_GAS peaker plants are
  excluded, matching the overlay's convention.
- **`data/outages.py`.** `UNIT_OUTAGE_CSV` now points at
  `campd-unit-outages.csv`; the per-row `(outage_start, outage_end)` windows
  carry the calendar year and are clipped to the run year, so one file feeds
  every backcast year (2024 previously had *no* unit-level coverage). The
  hand-curated `inputs/tx-jan-aug23-unit-outages.csv` stays in the repo for
  reference (and is still read by `scripts/derive_cc_committed_pct.py`) but is
  no longer the model's source.
- **W A Parish coal units now resolve.** The facility-summed overlay misses a
  WAP coal-unit outage because the gas units keep the CEMS series running; the
  unit layer detects WAP5–8 directly (e.g. WAP8 offline Jan–Aug 2023, matching
  the old hand entry, plus the previously uncovered 2024 windows).
- **Backcast effect (apples-to-apples, untuned `run_calibration.py`,
  unit-outage source the only change).** Coal and gas-steam move toward
  EIA-923 in both years: 2023 coal −13.7%→−11.9% and gas-steam +27.7%→+18.0%;
  2024 coal −24.4%→−22.2% and gas-steam +29.0%→+9.6%. Total energy balance and
  the full test suite are unchanged.
- **Tuned-config validation (`run32_unitoutage` = run 31's tuned config +
  CAMPD unit outages; both on the dashboard).** In the calibrated config the
  largest-biased gas-steam class drops sharply (2023 ST_GAS +10.2%→+2.6%) and
  2024 lignite improves (−7.2%→−5.3%); the freed energy flows to CT peakers,
  which the no-commitment config already over-runs (2023 CT_PEAKER
  +18.6%→+42.5%), so a light CT-peaker / ST_GAS re-tune is the natural
  follow-up. Coal totals stay close (2023 +6.2%, 2024 +1.8% combined) and the
  grid energy balance holds at ~+1%.

## 2026-06-04 (PJM backcast: per-plant fuel costs, CAMPD outages, capacity payments)

Makes the PJM 2023/2024 backcast bind to real per-plant data instead of the
energy-only stub. Every change defaults off / no-op for ERCOT, whose fleet,
fuel costs and outage overlay are bit-for-bit unchanged (verified: identical
F923 rows, no oil units, both new flags off, full suite green).

- **National EIA-923 fuel-cost table.** `scripts/process_f923_fuel_costs.py`
  now defaults to all balancing authorities (was `--ba ERCO`), so PJM plants
  and the **Petroleum (oil)** fuel group flow through; it also carries each
  plant's `state` and drops anomalous receipts outside a per-fuel plausibility
  band (gas ≤ $200, petroleum ≤ $120, coal ≤ $60 /MMBtu — set above the real
  ~$118/~$59/~$27 maxima in this window so legitimate constrained-winter gas
  survives while order-of-magnitude data-entry errors, e.g. gas at
  $99,241/MMBtu in May, are removed). 98 bad receipts dropped; the 25 ERCOT
  plants' rows are byte-identical.
- **Oil priced from EIA-923.** `data/fuel.py` maps `oil → "Petroleum"`, so
  oil-fired units pay their own measured monthly delivered cost where reported
  (flat `OIL_PRICE_PER_MMBTU` otherwise). ERCOT has no oil dispatch units, so
  this is a no-op there.
- **"Nearby plant" fuel-cost fallback (`nearby_fuel_price_fallback`).** A
  gas/coal/oil plant with no EIA-923 cost of its own for a month is filled —
  before the Henry Hub / coal / oil trajectory — from the quantity-weighted
  average of the other plants that reported: its own state first (≥
  `nearby_fuel_price_min_state_plants`), else its model zone, restricted to the
  ISO's own fleet. Essential for merchant-heavy PJM, where PA/NJ/DE plants file
  almost no Schedule-5 cost. Off for ERCOT (its plants overwhelmingly report).
- **ISO-generic CAMPD historic-outage overlay.** EIA-860 generators now carry
  `plant_code`, `plant_group` and `state` (previously unset for every non-ERCOT
  ISO, which silently disabled both the F923 lookup and the outage overlay).
  `scripts/derive_campd_outages.py --iso PJM` derives
  `inputs/raw-data/campd-outages-PJM.csv` from the CAMPD CEMS state extracts
  (building nameplate/group from the EIA-860 fleet); the overlay reads a
  per-ISO `campd-outages-{ISO}.csv` (ERCOT keeps its legacy file + bin
  intersection, unchanged). The CAMPD loader now also reads unit-level uploads
  from `inputs/raw-data/campd-unit-level/{STATE}_{YEAR}.parquet` (flat dir
  first, so ERCOT/PA/NJ/MD/DE/IL are unchanged even where TX appears in both;
  unit rows are summed to the facility). PJM's full state footprint is listed;
  states whose parquet is not yet uploaded (currently OH, WV, KY, VA, NC, MI)
  skip with a warning and keep statistical availability until added. The PJM
  outage extract presently covers PA/NJ/MD/DE/IL/IN/DC (70 plants).
- **Note:** the EIA-923 *fuel-cost* parquet is regenerated national (the
  feature's input); the *generation* parquet is kept at its prior ERCOT scope
  (it only feeds hydro/offline reference-building, not PJM dispatch) — rebuild
  it national with `process_f923_fuel_costs.py --ba ""` when needed.
- **Per-plant calibration fleet (`plant_level_fleet`).** Non-ERCOT calibration
  runs the EIA-860 fleet at full per-plant granularity (no efficiency-bin
  aggregation) so plant identity reaches dispatch — required for the per-plant
  fuel cost and outage overlay to bind. Off by default (forward runs keep the
  faster aggregated fleet); ERCOT is unaffected (it builds from CAMPD bins).
- **Module M1: capacity-payment revenue.** `capacity.py` adds a per-ISO
  resource-adequacy payment (net-CONE × UCAP, gated on `MARKET_DESIGN`) to the
  thermal retirement and new-entry economics, so PJM/NYISO/ISO-NE/CAISO units
  are no longer over-retired on energy margin alone. Zero for energy-only ERCOT.
- **Effect on the PJM 2024 backcast:** outage overlay zeroes 233 coal/CC
  tranches (64 plants); 241 generators price from their own EIA-923 cost and
  1,119 gap-fill from nearby plants; modeled coal falls 149.4 → 140.5 TWh
  toward the ~122/116 actuals. The per-plant solve is slower (minutes, larger
  LP) — acceptable for a backcast.

## 2026-06-04 (storage daily-cycling toggle)

- **Added the `storage_daily_cycling` foresight toggle.** A new LP constraint
  family (`dispatch._build_storage_daily_cycle_rows`) optionally pins each
  storage unit's SOC back to its day-start level every 24 h, so storage cannot
  arbitrage across days — bounding the single-LP perfect-foresight advantage to
  within-day spreads (the realistic limit for short-duration storage). Off by
  default (annual-cyclic, unchanged). Exposed as `ScenarioConfig.storage_daily_cycling`
  and `run_calibration_full.py --storage-daily-cycling`; recorded in each run's
  `meta.json`/`run_config.json`. Covered by `TestStorageDailyCycling`.

## 2026-06-03 (storage backcast RTE fix + perfect-foresight docs)

- **Fixed: storage RTE override now reaches the backcast.** `load_eia860_storage`
  hard-coded round-trip efficiency from the `STORAGE_TECHS["li_ion_4hr"]`
  constant (0.86), so a calibration sweep of `config.storage_rte_4hr` (e.g. the
  0.85 in the run configs) never changed the backcast battery fleet — the lever
  was silently decoupled from the model. It now reads RTE through `_storage_rte`,
  matching the forward new-entry path; the function takes `config` and the
  calibration call site passes it. Magnitude is small (√0.86→√0.85) but the
  knob now actually binds.
- **Documented the storage perfect-foresight assumption.** The full 8760-hour
  horizon is solved as one LP, so storage is co-optimized against the whole
  year's prices (an upper bound on realized arbitrage that over-flattens net
  load). Added the limitation and the standard mitigations (daily SOC cycling
  caps, rolling/receding horizon, day-ahead+real-time, price-taker pass,
  stochastic, empirical haircut) to `model-methodology-spec.md` §storage and a
  note in `dispatch.build_constraints`. Bounded for the short-duration 2023
  fleet by the `SOC ≤ energy_cap` constraint; grows with long-duration storage.

## 2026-06-03 (storage + offer-curve docs)

- Documented the storage new-entry overhaul (PR #180): the value stack
  (duration-sized arbitrage net of cycling degradation **+** resource-adequacy
  capacity value via the per-ISO `MARKET_DESIGN` registry, net-CONE × ELCC ×
  saturation derate), tech-diversified build budget, and per-tech learning
  curves. Methodology spec §5.5 was updated in that PR; this pass aligns
  `claude.md`, the multi-ISO market-design catalogue (`MARKET_DESIGN` registry
  note), and `docs/binning-methodology.md` (smooth N-slice offer curve now
  spanning CC/coal/CT/ST, exponent p=3 — runs 25–26).
- **Parameter-citation registry back-filled — CI green.** Added
  `scripts/generate_parameter_registry.py`, which reuses the validator's exact
  `expected_param_ids()` derivation, preserves the 133 curated entries, and
  registers the 401 missing parameters with values plus citations harvested
  from each constant's inline comment. `validate_parameters.py` now exits 0.
  534 entries total; 232 auto-entries are flagged `needs-citation` (no dated
  primary source in the comment) for later human review. The human view
  `docs/parameter-citations.md` is now rendered from the registry by the same
  generator, so the two stay consistent — re-run after adding constants.

## 2026-06-03

- **Documentation reconciliation.** Realigned the prose docs with the as-built
  code after the code had outpaced them. Methodology spec, `claude.md`, the
  calibration logs and the multi-ISO baseline now reflect: the opt-in
  three-solve unit-commitment layer (still pure LP, no MIP), CAMPD per-plant
  binning with tranche-based rising offer curves (ERCOT default), config-driven
  retirement plus the CCS-retrofit pathway, forecast-vs-backcast outage
  modelling, hydro monthly energy budgets, EAC/REC attribute credits, and the
  seven registered ISO topologies (ERCOT, CAISO, PJM, MISO, SPP, NYISO, NEISO).
- Added the `/sync-docs` skill — a manually-invoked, end-of-session doc
  reconciler (deliberately not a hook) with a code→doc map.
- Roadmap noted: derive forecast-mode spring/autumn maintenance shaping from
  historic outage data (replacing the flat shoulder-POF heuristic).
- Documented the per-plant tranche-config system added across the run5–run24
  calibration series (`inputs/plant-tranche-config.csv`,
  `plant_tranche_config_path`, `cc_peaking_per_plant`,
  `fleet.load_plant_tranche_config`/`plant_tranche_bands`): an optional
  per-plant **five-slice rising offer curve** (Econ split into Low/High) that
  overrides the per-group tranche defaults for flagship-plant calibration.
  See `docs/binning-methodology.md` and methodology spec §3.3.

## 2026-05-16

- Phase 0 started.
