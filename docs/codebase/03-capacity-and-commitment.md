# 3. Capacity Evolution, Commitment, Storage & Transmission

This page covers the year-over-year fleet evolution (`model/capacity.py`), the
P0→P1→P2 commitment screen (`model/commitment.py`), and the supporting LP
components: transmission (`model/transmission.py`), storage (`model/storage.py`),
and ancillary-service revenue (`model/ancillary.py`).

## 3.1 Capacity evolution — one pass, six steps

`evolve_fleet(...)` (`capacity.py:1412`) advances the fleet by exactly one year in
a single pass — **no within-year convergence iteration**. It returns the mutated
fleet, an updated economic-loss tracker, renewable additions, and a CCS-retrofit
log. The steps run in this fixed order:

```
0. Confirmed exits            apply_confirmed_exits()  (GATED confirmed_exits_enabled)
1. Announced retirements      apply_announced_retirements()
2. Economic retirements       apply_economic_retirements()
3. Known additions            (planned EIA-860 pipeline; online_year == year)
4. CCS retrofit screen        apply_ccs_retrofit()
5. Economic new entry         apply_economic_new_entry()
6. Reserve-margin backstop    apply_reserve_margin_build()
        │
        ▼
re-aggregate into efficiency bins (aggregate_fleet, n_bins=heat_rate_bin_count)
```

### Step 0 — Confirmed exits (`apply_confirmed_exits`)

The exogenous forecast retirement channel, GATED on `confirmed_exits_enabled`
(default **on**, flipped 2026-07-05 — `docs/handoffs/confirmed-retirement-plan-2026-07.md`
§7) and forecast-mode only. Reads the `confirmed-retirements` registry
(binding public instruments — consent decree, statute, RTO deactivation
acceptance, regulatory order, RMR end — via
`data.confirmed_retirements.load_confirmed_exits`) and, at each unit's instrument
date, force-retires a unit-grain unit or **derates** a plant-binned tranche by the
exiting unit's MW, any fuel, **bypassing the reliability floor**. It runs before
the economic screen, so scarcity from a confirmed exit feeds next year's entry
signal, and it composes as `min(economic_exit, confirmed_date)`. This is the ONLY
exogenous fossil exit channel; superseded registry rows (a counter-instrument
suspends the exit) are dropped by the loader and revert to the economic screen.

### Step 1 — Announced retirements (`apply_announced_retirements`)

Honors an EIA-860 announced `retirement_year ≤ year`. In forecast mode with
`fossil_economic=True` (the default), fossil units (coal/gas_cc/gas_ct/gas_st/oil/
gas_cc_ccs) **ignore** their announced dates — for the whole fossil fleet this
step is a **default no-op** and the economic screen governs them. Non-fossil
(nuclear, hydro, renewables, storage) dates are honored only within the EIA-860
data horizon (`EIA860_OPERABLE_VINTAGE + NONFOSSIL_ANNOUNCED_HORIZON_YEARS`,
default 5); beyond it a non-fossil date is honored only if the unit is in the
confirmed registry (the horizon gate activates with the confirmed channel — off =
honor all non-fossil dates). Renamed from the old `apply_known_retirements`
(RC-3; no alias).

### Step 2 — Economic retirements (`apply_economic_retirements`, line 279)

For each thermal unit, computes a going-forward economic test:

- **Net revenue** = `Σ_t (price[zone,t] − mc[g,t]) · dispatch[g,t]` — the
  *inframarginal energy margin* (threaded as `prior_results["mc_cost"]`, **never**
  gross revenue), plus attribute revenue (`max(exogenous EAC, RPS shadow price)` —
  no stacking), plus capacity revenue (net-CONE × UCAP in capacity-market ISOs;
  zero in energy-only ERCOT), plus ERCOT AS revenue (saturating on storage fleet).
- **Going-forward cost** = `fixed_om_per_kw_yr · fom_multiplier · pmax · 1000`.
  Coal carries a 1.3× FOM multiplier for regulatory/ESG risk.
- A **consecutive-loss counter** per unit; the unit retires once losses persist
  past the per-fuel threshold (`retirement_years_coal=3`, `gas_ct=2`, `gas_cc=3`,
  …). Within a fuel, the highest-heat-rate (least efficient) units retire first.
- A **reliability floor** prevents stripping thermal below
  `(peak_demand − firm_clean) · (1 + retirement_reserve_margin)`; the most
  efficient eligible units are kept online until the floor is met.

### Step 4 — CCS retrofit (`apply_ccs_retrofit`, line 1257)

Screens existing `gas_cc` units to retrofit into `gas_cc_ccs`. Annual net savings
per MW = carbon avoided (`(old−new co2 rate)·carbon_price·cf·8760`) + 45Q/EAC
credit − extra fuel from the heat-rate penalty − capture VOM. Simple payback =
retrofit capex / annual savings; the unit retrofits if payback < remaining life
and it has at least `ccs_retrofit_min_remaining_life` (15) years left. Ranked by
payback (most efficient hosts first), capped at `ccs_retrofit_max_gw_per_year`
(3 GW/yr/ISO), gated on `ccs_retrofit_available_year`. The retrofitted unit is
updated in place: `heat_rate ·= (1+penalty)`, `vom += adder`,
`co2_rate ·= (1−capture_rate)`, `fuel_type → "gas_cc_ccs"`.

### Step 5 — Economic new entry (`apply_economic_new_entry`, line 928)

Candidate techs are screened by margin and built highest-margin first, subject to
per-tech and ISO-level annual queue caps:

- **Classic thermal** (gas_cc, gas_ct): revenue from the price-duration integral
  over scarcity-tail hours minus variable cost, vs annualized fixed cost
  (Wright-adjusted capex × CRF + FOM).
- **Must-run renewables** (wind, solar, nuclear_smr): `expected price × CF +
  attribute payment (max of EAC and RPS shadow)` vs LCOE × MWh. Wind/solar builds
  go into the **zonal `wind_cap`/`solar_cap` pools** (decision-variable upper
  bounds), not as new `Generator` objects.
- **Emerging** (hydrogen, CCUS, geothermal, offshore): `_emerging_lcoe` (line 547)
  + expected revenue at that tech's CF.

LCOE is `compute_lcoe(...)` (line 734): capital annualized by a capital recovery
factor from the discount rate and tech lifetime, capex optionally Wright-adjusted,
IRA ITC/PTC applied, FOM added, spread over annual generation at base CF.

### Step 6 — Reserve-margin backstop (`apply_reserve_margin_build`, line 1176)

An adequacy guarantee: if accredited firm capacity falls below
`peak_demand · (1 + planning_reserve_margin)`, force-build the cheapest firm
dispatchable (a gas_ct peaker) to close the gap, capped at the ISO annual queue
throughput. Disabled by default (`reserve_margin_build_enabled`).

### Learning curves

`CumulativeDeployment` (line 631) tracks global cumulative installed capacity per
tech, seeded from `WRIGHT_REFERENCE_GW` and advanced each year by
`GLOBAL_ANNUAL_DEPLOYMENT_GW` plus local builds. Wright's-Law capex reductions are
a function of cumulative deployment, feeding next year's `compute_lcoe`.

## 3.2 The P0→P1→P2 commitment sequence

Three LP solves per year reconcile clearing prices with start-up economics while
staying pure LP (`commitment.py` + `runner.py`):

| Pass | Cost vector | Purpose |
|------|-------------|---------|
| **P0** | base MC | discover run lengths from the resulting dispatch |
| **P1** | base + amortized startup markup | **sets clearing prices** (cycling reflected) |
| **P2** | bid MC on a committed fleet | optional commitment screen (default off) |

### P1 — startup-amortization markup

`compute_monthly_markup(...)` (line 173) measures run lengths per calendar month
(or season for gas_st) from the P0 dispatch (`dispatch > 5% of pmax`), then sets
`markup = startup_cost / avg_run_length`. Coal/nuclear/non-thermal get zero;
warm-boiler coal with a must-run floor and steam-host CHP are exempt when the
corresponding config flags are set. `mc_bid = mc_base + markup`. P1 warm-starts
from P0's basis.

### P2 — economic commitment screen (`commitment_enabled`, default off)

`compute_commitment(...)` (line 307) decides which CC/CT units stay committed:

- Hourly margin = `p1_price[zone] − base_mc[g]` (base MC, not bid MC, to avoid
  double-counting the markup).
- A **storage-discount weight** down-weights margin in net-charging hours so
  units aren't committed purely to feed batteries.
- Find runs of in-merit hours; drop runs shorter than `min_run_hours`; drop runs
  whose storage-weighted margin sum < `startup_per_mw · (1 + irr_hurdle)`; merge
  runs separated by < `min_down_hours`.
- Coal, nuclear, and non-thermal are always committed.

`apply_commitment_with_coal_pin(...)` (line 716) then builds the P2 `FleetArrays`:
screened units get `availability = 0` in decommitted hours; coal is pinned to its
P1 dispatch (no part-loading) when unscreened; an adequacy backstop restores
decommitted units if committed capacity would fall below P1 thermal dispatch in
any zone-hour (never create unserved demand). P2 re-solves on this fleet; both P1
and P2 are cached (P1 as `year_<year>_p1.parquet`, P2 primary).

Additional adequacy helpers: `reserve_adequacy_commit` (NYISO downstate spinning
reserve), `as_adequacy_commit` (ERCOT multi-product AS), and
`caiso_ra_mustoffer_min_gen` (CAISO RA must-offer bridging short gaps at min-load).

## 3.3 Transmission (`model/transmission.py`)

A pipe-and-bubble network: zones are copper-plate bubbles, links are pipes with
TTC limits.

- `build_incidence_matrix(links, zone_names)` → `(n_zones, n_links)` CSR; entry is
  `−1` for the exporting zone, `+1` for the importing zone (positive flow moves
  from→to).
- `get_ttc_array(links)` → `(n_links,)` transfer capabilities.
- `build_interface_groups(...)` → multi-path aggregate limits (e.g. CAISO WECC
  simultaneous import cap).

**Priced interchange** is modeled as synthetic generators in an external zone:

- `build_import_generators(...)` — stepped import tranches as generators (VOM =
  tranche price + border-carbon adder; CAISO applies a CARB unspecified-import EF).
- `build_export_sinks(...)` — negative-output sinks (export legs).
- `build_caiso_bidir_intertie` / `build_caiso_per_hub_intertie` — WECC tie as a
  single signed flow or split per hub (Malin / Palo Verde), repriced hour-by-hour
  to measured hub LMPs.
- `build_reference_price_node(...)` — flow-responsive seam: import/export split
  into equal-width tranches, each priced at its band's midpoint flow from the
  neighbor's forecast reference price (`data/neighbor_price.py`).

## 3.4 Storage (`model/storage.py`)

`StorageUnit` (per-unit attributes) → `StorageArrays` (vectorized). Fleet sources:
`build_default_storage` (forecast base from `STORAGE_BASE_FLEET_MW`),
`load_eia860_storage` (backcast batteries), `load_eia860_pumped_storage` (PSH,
prime mover `PS`). `storage_cap_profiles` produces static or monthly-ramped
power/energy caps.

**Value-stack new entry** (`apply_storage_new_entry`): not compound growth, but an
economics screen over three revenue streams —
- `estimate_storage_revenue` (line 657): arbitrage, vectorized over windows
  (`window_hours = ceil(duration/12)·24`), charging on the cheapest `duration_hr`
  hours and discharging on the dearest, net of round-trip and degradation;
- `estimate_capacity_value`: ELCC credit × `(1−penetration)^exponent` × net-CONE,
  paid only in capacity-market ISOs;
- ERCOT AS revenue (saturating).

Builds are ranked by margin, diversified across techs
(`STORAGE_TECH_BUILD_SHARE_CAP`), and capped per ISO (annual
`STORAGE_ANNUAL_BUILD_CAP_MW`, cumulative `STORAGE_DEPLOYMENT_CEILING_MW`). ELCC
rises with duration (`STORAGE_ELCC_BY_DURATION`), tilting entry toward
long-duration at high penetration.

## 3.5 Ancillary-service revenue (`model/ancillary.py`)

ERCOT-only, for capacity economics (not an LP constraint). `as_revenue_per_mw_yr`
returns `base_per_kw · as_revenue_multiplier · as_saturation_factor() · 1000`. The
saturation factor `(ref_gw / max(storage_gw, ref_gw))^exponent` decays AS revenue
as the storage fleet grows past the reference size — most ERCOT AS revenue accrues
to storage, and it saturates as more storage enters.
</content>
