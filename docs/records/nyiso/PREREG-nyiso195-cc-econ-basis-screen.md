# PREREG nyiso-195 — the `CC_REGULAR` econ ramp at its own measured marginal heat-rate basis: phase 0 and ONE 2024 screen (2026-09-05)

Pre-registration frozen and pushed BEFORE the solve. Owner instructions (in
session 2026-09-05, verbatim): *"Only run 2024 to see if it fixes the c1 gas cc
miss. C3c is an acceptable caveat and known limitation of this model type."* and
*"No control arm just use the last keeper"*. Keeper (the control, rule 29(b)
form 4): `2026-09-05-nyiso-192-astoria-panel`, bundle
`results/calibration/nyiso192_astoria_panel`, solved at `d5bba63b`,
determination NOT-YET (C1-2024 `CC_REGULAR` +3.68 TWh / +3.0 pp; C3c 3/0/4 h,
not lone). The object is the top of the §5.5 queue as handed forward by
nyiso-194 §3.

Phase 0 (zero LP): `scripts/probes/nyiso195_econ_basis_phase0.py` →
`results/calibration/_nyiso195_econ_basis_phase0.json`. Inputs are the
keeper's COMMITTED artifacts only — an on-recipe `run_year(fleet_only=True)`
rebuild of its 2024 fleet (`scripts/lib/bundle_fleet.reconstruct_bundle_fleet`,
the same assembled `mc_base` the LP solved on), its per-plant hourly MW decoded
from the committed run payload (the `legitimacy_diagnostics` decode, annual-
rescaled), its `hourly/system_2024.parquet` zonal prices, its
`hourly/class_band_hourly_*.parquet` sidecars, and CAMPD unit-level hourly
2024. The keeper's `dispatch/` parquet is gitignored and absent from this clone;
no control solve was spent (owner instruction; rule 29(b)).

## 1. The arithmetic of the delta (computed, not typed)

Under the keeper's armed `gas_offer_net_revenue_margin`, each `CC_REGULAR` econ
slice `k` (six slices, `offer_curve_smoothing_n = 6`, position
`t_k = (k + 0.5)/6`) offers

    mc_k(t) = phys_k × HR_base × fuel(t) + markup_k × HR_base × anchor + vom (+ carbon/NOx adders)

with `phys_k = 0.784 + 0.141 t_k` (the registered NYISO `phys_econ_*` p50s
interpolated at the slice's ramp position) and `markup_k = mult_k − phys_k`,
`mult_k = 0.95 + 0.05 t_k`. Phase 0 verified this identity on all 96 econ
rows of the 2024 rebuild: `offer_markup_hr == (mult − phys) × HR_base` to
0.0 and `mc_base` minus the formula is a per-generator constant (std across
hours 6e-15 — the carbon/NOx adders). The committed (0.90 < phys 0.964) and
peak (2.25 == phys 2.25) bands carry markup 0 already, so **the econ ramp is
the only `CC_REGULAR` band carrying any markup**.

Class-level (cap-weighted over the 506.5 MW per slice), 2024 mean delivered fuel
2.42 $/MMBtu, per-tranche anchors as the keeper carries them (3.9046 reference
zone; 2.7612 / 2.0346 in the basis-shifted zones — nyiso-109):

| slice | mult | phys | markup HR | fixed margin $/MWh | keeper offer $/MWh | arm offer $/MWh |
|---|---|---|---|---|---|---|
| 0 | 0.9542 | 0.7958 | 1.171 | 4.03 | 28.94 | 24.91 |
| 1 | 0.9625 | 0.8193 | 1.059 | 3.64 | 28.99 | 25.34 |
| 2 | 0.9708 | 0.8427 | 0.947 | 3.26 | 29.03 | 25.78 |
| 3 | 0.9792 | 0.8663 | 0.835 | 2.87 | 29.08 | 26.21 |
| 4 | 0.9875 | 0.8898 | 0.722 | 2.49 | 29.13 | 26.65 |
| 5 | 0.9958 | 0.9133 | 0.610 | 2.10 | 29.18 | 27.08 |

Two facts follow. (a) **The keeper's econ ramp is priced almost FLAT**: the
falling fixed markup (4.03 → 2.10 $/MWh) cancels the rising fuel-scaled
physical basis almost exactly — top minus bottom slice **$0.25/MWh**. That is
why the six slices carry identical energy in the committed 2024 band sidecar
(2.782 … 2.801 TWh each; top/bottom ratio 1.007) — the ramp switches on and off
as a block. (b) **The arm is a pure price CUT on every slice** (markup → 0):
−4.03 $/MWh at the bottom, −2.10 at the top, re-sloping the ramp to a
$2.17/MWh spread. Nothing in the delta raises any offer.

## 2. What phase 0 measured on the keeper's own 2024 dispatch

**The nyiso-194 §3 hypothesis — "the LP parks each plant where its econ ramp's
marginal slice meets the LMP" — does NOT hold on the keeper's committed
dispatch.** Of the class's 28,778 plant-hours in the 80–90 % loading bin
(payload-decoded, MW-weighted class share 33.8 % vs the parquet's 33.0 — the
self-check):

| where the plant sits in its 80–90 % hours | plant-hours | share | MWh |
|---|---|---|---|
| AT the top of its AVAILABLE econ ramp (the wall, after unit-outage / derate availability) | 20,672 | 71.8 % | 10.38 TWh |
| ABOVE the available wall — partial duct (peak-band) dispatch | 7,897 | 27.4 % | — |
| MID-RAMP on a marginal econ slice | **209** | **0.7 %** | 0.05 TWh |
| below committed | 0 | 0 | — |

The 80–90 % pile-up is the top of the *available* econ ramp: the static wall
(`1 − pct_peak`) sits at 0.910 / 0.849 / 0.831 of pmax at Bethlehem 2539 / CPV
56940 / Astoria II 57664, but the availability-weighted wall the plant actually
reaches averages 0.841 / 0.734 / 0.729, and 4,288 / 4,075 / 2,998 of their
80–90 % hours are exactly there. The remaining quarter is the peak band's own
partial dispatch. **The econ ramp's shape is therefore not what places the mass
in 80–90 %: a plant already at the top of its ramp cannot be moved up it by
making the ramp cheaper, and the band above it (peak, `phys_peak == peak`) is
untouched by this delta.**

**Where the arm's footprint actually lands** (keeper zone LMP vs each slice's
keeper and arm offer): 74,783 slice-hours across the class are newly in the
money (LMP between the arm and keeper offers) — hours the slice was NOT
dispatched in the keeper — an energy **upper bound of +0.95 TWh** of added
`CC_REGULAR` dispatch, concentrated at Cricket Valley 57185 (+261 GWh), 55405
(+234), Bethlehem 2539 (+177), 7314 (+138). The keeper-zone LMP at which slice
0 / slice 5 is marginal (within ±$2 of its offer) has a cap-weighted median of
26.8 / 37.0 $/MWh.

**CAMPD ramp-slope sign (heat vs gross load, 50–95 % of each plant's own p99.5,
quadratic incremental fit):** 10 of 14 fitted plants show a marginal heat rate
that RISES with load; cap-weighted marginal/average-full-load HR 0.833 at 55 %
→ 1.056 at 92 %. The SIGN of the registered `0.784 → 0.925` ramp is confirmed;
the level is not re-derived here (rule 23 — the derive is frozen against
residuals) and no value from this fit enters the arm.

**Footprint census (committed band sidecars):** econ-slice energy 14.47 /
**16.76** / 15.76 TWh (2023 / 2024 / 2025); hours in which some plant is
mid-ramp 3,441 / 1,009 / 2,812 with a mid-ramp MW gap of 0.17 / 0.04 / 0.16
TWh. The delta reprices the whole econ block, so its measured footprint is the
block's energy → **2024**, which is also the year the owner named. (Had the
mechanism's object been the marginal-slice hours, 2023 would be the screen
year; that object is 0.04–0.17 TWh in every year and is not what this delta
moves.)

## 3. Phase-0 PREDICTION, stated before the solve

1. `CC_REGULAR` energy RISES, by at most ~0.95 TWh (2024), plus whatever the
   cheaper P0 run pattern adds through the `nyiso_gas_commitment_bridge` floors
   (more bridged online hours) — the same sign.
2. The class 80–90 % loading share does NOT fall (the 71.8 % at-wall hours stay
   at the wall; hours that were below the ramp move UP to it) and the 90–100 %
   share does not rise (the peak band is untouched). **Gate E-3 below is
   predicted to FAIL.**
3. **C1-2024 `CC_REGULAR` (+3.68 TWh, already the failing cell) gets WORSE**,
   by up to ~+0.9 TWh. The owner's question — does this fix the C1 gas-CC miss —
   is answered in the negative by the arithmetic: the arm lowers offers on an
   over-running class; an LP never dispatches less of a unit whose cost falls.
   The screen is run as the owner directed, to measure the magnitude, not to
   decide the sign.
4. ST_GAS / CC_CHP / imports give up the displaced energy; the load-weighted
   mean price falls (the econ block was marginal at 27–37 $/MWh).

If the shape moves TOWARD CAMPD instead, phase 0's reading is wrong and the
finding says so.

## 4. The screen (rule 29: ONE year, structural STOP gates only)

**Single delta:** `--offer-curve-json '{"CC_REGULAR": {"econ_low": 0.784, "econ_high": 0.925}}'`
— the econ block offered at its already-registered physical basis (registered
= `phys_*`, markup 0). Zero free parameters (rules 13 / 14 / 21); NYISO's own
`nyiso_campd_marginal_hr_summary.csv` p50s (rule 25 — nothing transfers);
`_deep_merge_offer_curve` keeps every other key (`phys_*`, `committed`,
`peak`, `econ_low_share`, `pct_peaking`) as the keeper carries them.

    python scripts/replay_keeper.py results/calibration/nyiso192_astoria_panel \
        --years 2024 --offer-curve-json '{"CC_REGULAR": {"econ_low": 0.784, "econ_high": 0.925}}' \
        --out-dir results/calibration/nyiso195_screen_2024 --note "nyiso-195 screen: CC_REGULAR econ ramp at phys basis"

**Control = the keeper's committed 2024 (form 4).** No control solve. G-DRIFT
`d5bba63b..HEAD` (153 commits) on the solve path
(`src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`data/raw/_validation-source`, `data/raw/reference`), every hunk classified
INERT for a NYISO 2024 backcast:

* `data/offer_curves.py` — `_with_intermediate_phys` under
  `miso_intermediate_gas_offer_margin`, gated `iso == "MISO"` AND default off;
  the keeper recipe never carries it.
* `config/scenarios.py` — the two new fields above (defaults off / `None`) and
  the `ccs_retrofit_capex_co2_scaling` default flip: `ccs.py::apply_ccs_retrofit`
  returns at `year < 2028`; capacity evolution is never entered by
  `run_calibration.py` (no `evolve_fleet` call on the backcast orchestrator).
* `config/iso_configs.py` — PJM `default_scenario_overrides` (other ISO); NYISO
  `nyiso_requirement_forecast_peak` / `nyiso_requirement_vintage_factors`
  consumed only in `capacity_evolution/retirements.py` (forecast-only), and the
  replay runs the bundle's recorded `scenario_config`, which carries them.
* `config/constants.py` — capacity-market imports, a removed CCS reference dict,
  a `NUCLEAR_MONTHLY_CF_BY_YEAR` **2022** row (not a 2024 key), two removed
  unused ERCOT constants.
* `config/capacity_market.py`, `model/capacity_evolution/{adequacy,ccs,evolve,retirements}.py`,
  `runner.py` (storage-entry clearing price) — capacity evolution / clearing,
  forecast-only.
* `results/cache.py` — cache-key epoch accounting (comments); the replay writes
  a fresh bundle, not a cache lookup.
* `run_calibration_full.py` — a `gas_offer_margin=None` override kwarg (None
  keeps the recipe's value).
* Dead-code deletions with no solve-path caller: `outages.read_clean_outages`,
  `floor_mechanisms.tag_raised`, `som_conduct.py`, `reserve_requirements.load_reserve_requirements`
  (the per-ISO loaders `reserve_config` imports are untouched), `eia923.plant_state_map`,
  `fleet/eia860._committed_vintage_years`, `pipeline/result.py`, `results/metrics.py`,
  `benchmark_corridor.load_benchmark_corridor`, `plant_taxonomy.is_fossil`,
  `paths.TX_UNIT_OUTAGES_CSV`, `miso_outages.FORECAST_PARQUET`.
* Comment / docstring only: `model/interchange/spec.py` (CAISO RA-import note),
  `pipeline/reference.py`, `scripts/lib/{session_score,zonal_sufficiency,reldeploy_zonal_report}.py`.
* `data/raw/reference/nyiso-market-solar-capacity.csv` — **2022 rows added only**
  (0 changed 2023–2025 rows).

All hunks INERT ⇒ form 4 is valid and the keeper is the control.

### Gates (STOP only; the screen never promotes; nothing is gated on any residual)

- **E-1 footprint.** The arm's `2024_P1_fleet.parquet` tranche pmax is
  byte-identical to the keeper's tranche capacities (phase-0 rebuild); the
  arm's `run_config.json` carries exactly the two changed keys on `CC_REGULAR`
  and every other class's offer bands unchanged; class-energy deltas outside
  the gas family and imports are ~0 (nuclear / hydro / wind / solar unchanged).
- **E-2 identity.** On a zero-LP `fleet_only` rebuild of the ARM bundle, every
  `CC_REGULAR` econ slice's `offer_markup_hr` is 0 and its `mc_base` equals the
  keeper's minus the slice's fixed margin (`markup_k × anchor`) hour for hour;
  committed and peak rows are byte-identical.
- **E-3 direction (the mechanism does what it claims).** The class MW-weighted
  80–90 % share FALLS and the 90–100 % share RISES toward CAMPD (16.5 / 33.9),
  measured against the keeper's committed per-plant rows
  (`_nyiso194_screen_gates_S.json` keeper side, `_nyiso194_cc_peak_phase0.json`)
  — the same construction nyiso-194 used. **STOP if the 80–90 % share does not
  fall.** Phase 0 predicts this gate FAILS (§3).
- **E-4 companions (approximate, same-weights construction as nyiso-194):**
  load-weighted mean RT price vs actual (C3a-like) and monthly NRMSE (C3b-like)
  from the arm's `system_2024.parquet` vs the keeper's; gas-family volume
  (C2-like). STOP on a load-bearing companion flipping PASS → FAIL. **C1-2024 is
  reported at full magnitude, never gated** — the owner's question, answered
  as a number. C3c is reported as an accepted caveat (owner, this session), not
  a gate.

### Disposition rule (frozen)

- E-1..E-4 clear → the full 2023–2025 span as ONE bundle, registered,
  attested (G-CTRL form 4 against the keeper), scored; promotion is the owner's
  call under the standing formula.
- Any gate fails (E-3 as predicted) → **no full span**; the screen result IS
  the session result: finding + matrix cells (`offer_curve_by_group`,
  `gas_offer_net_revenue_margin`) + §5.5 + log. The screen bundle
  `results/calibration/nyiso195_screen_2024` is a throwaway probe (rule 29 /
  rule 16), never registered.
- The C1-2024 number is reported whatever it is; a lower residual reached by a
  shape that moves away from CAMPD would be rule-1 forbidden and is not
  expected here in any case (§3.3).

*(nyiso-195, 2026-09-05. Pushed before the screen was launched.)*
