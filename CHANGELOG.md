# Changelog

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
