# 4. The Data Layer

Source: `src/market_sim/data/`. These modules turn on-disk source data (EIA-860,
EIA-930, EIA-923, EPA CAMPD, eGRID, gas/coal price series) into the numpy arrays
the LP consumes. The central output is `FleetArrays` — the struct-of-arrays the
dispatch builder touches.

## 4.1 Fleet construction (`fleet.py`, ~6,900 lines)

The largest module. It defines the generator model, its vectorized form, and the
binning that turns physical plants into LP units with rising offer curves.

### `Generator` (Pydantic, line 243)

A single unit: `unit_id, name, zone, fuel_type, pmax_mw, pmin_mw, heat_rate, vom,
emission_rate_co2, nox_rate, so2_rate, eford, online_year/month, retirement_year/
month`. CAMPD-bin units carry extra fields: `is_campd_bin, plant_group, bin_label,
min_run_hours, min_down_hours, startup_cost_per_mw, must_run_pct, bin_nameplate_mw,
coal_supply, plant_code, state, chp_grid_pmin_mw, coal_sync_pmin_mw,
coal_sync_online_frac`.

`fuel_type` is one of the 16 codes in `FUEL_TYPE_MAP` (gas_cc, gas_ct, coal,
nuclear, wind, solar, hydro, import, hydrogen_ct, hydrogen_ccgt, gas_cc_ccs, oil,
geothermal, offshore_wind, gas_st, biomass).

### `FleetArrays` (dataclass, line 307)

The struct-of-arrays. `(n_gen,)` arrays: `pmax, pmin, heat_rate, vom,
emission_rate, nox_rate, so2_rate, zone_idx, fuel_type_idx, efficiency_bin,
plant_code`. Optional: `availability[n_gen,T]` (hour-varying, for outages),
`min_gen[n_gen,T]` (reliability/floor dispatch floor), `state`, `plant_group`,
`ramp10`. Property `n_gen`.

`generators_to_fleet_arrays(...)` (line 899) is the vectorizer: builds zone/fuel
indexing, hour-varying availability (age-based POF/WEFOR + outage overlays +
seasonal derates + summer WEFOR redistribution), must-run floors, CHP
steam-following, coal synchronization, and optional 10-min reserve capability.

### CAMPD per-plant binning (the ERCOT default)

When `use_campd_bins=True`, each physical plant becomes **one LP unit split into
tranches** that together form a rising offer curve. Flow:

```
custom-bin-assignments.csv (one row per plant)
   → load_campd_bins(csv, year)         normalize to LP schema
   → bins_to_fleet(bins, zones, config) split into tranches
   → generators_to_fleet_arrays(...)    vectorize
   → apply_coal_tranches(...)           reduce MC for sunk coal fuel
```

`bins_to_fleet(...)` (line 5984) creates these tranches per plant, with capacities
allocated from the bin's `pct_mr / pct_mc / pct_econ / pct_peak`:

| Tranche suffix | Applies to | Role |
|----------------|-----------|------|
| `_mustrun` | coal | mine-mouth take-or-pay floor; bids VOM+carbon+NOx only (fuel sunk) |
| `_sync` | coal | spot (non-contracted) coal at full SRMC |
| `_committed` | all | part-load range when online; carries startup cost + min-run/min-down |
| `_econ` (`_econlo`/`_econhi`) | all | incremental dispatch above committed; rising curve, optional N-slice smoothing |
| `_peak` | all | duct-firing / scarcity band at `HR × peak_mult` |

Heat rates per tranche are `base_hr × multiplier` (committed/econ/peak multipliers
from the offer-curve config or per-plant override sheet).

**Coal take-or-pay + PRB passthrough.** `coal_takeorpay_share()` splits the
must-run capacity into a contracted (`fuel_frac = 0`, fuel sunk) `_mustrun`
tranche and a spot (`fuel_frac = 1.0`) `_sync` tranche. Economic coal tranches use
a supply-specific **logistic passthrough sigmoid** keyed on the gas price (PRB vs
lignite) — `campd_tranche_fuel_frac(...)`, which can return a scalar or a `(T,)`
gas-keyed array. `apply_coal_tranches(...)` (line 2698) then reduces marginal cost
in place: `mc[g,t] −= (1 − fuel_frac[g]) · heat_rate[g] · fuel_price[g,t]`, so the
contracted tranche prices at VOM-only and the spot tranche at full SRMC.

**CHP steam-following** removes behind-the-meter share from the LP and forces a
grid-delivered floor via `chp_grid_pmin_mw`. **Peaking** capacity comes from a
per-plant artifact or the EIA-860 duct-burner gap.

Non-ERCOT ISOs without a CAMPD artifact use `fleet_to_bins(...)` (line 5527) to
synthesize equivalent per-plant bins from the EIA-860 fleet, or legacy equal-width
heat-rate bins. The legacy coal/gas path uses `split_coal_tranches` /
`split_gas_tranches`.

### Fleet loading

`load_fleet_from_csv(iso, iso_config, data_dir, year)` (line 3642) loads the
EIA-860 thermal fleet: per-ISO override CSV → committed EIA-860 generator parquet
(filtered by BA code) → CHP flag from the operable sheet → zones from eGRID 2023
(supplemented from EIA-860 for post-2023 plants). Binned fleets are cached to
`data/raw/_processed-legacy/{iso}_fleet_binned.parquet`.

## 4.2 Fuel prices (`fuel.py`)

Resolves per-generator delivered fuel prices (`$/MMBtu`) for the marginal-cost
assembly:

- **Gas**: `resolve_annual_gas_price` = Henry Hub trajectory + ISO basis ±
  override. Hub-month and hub-daily refinements (`iso_hub_monthly_gas_prices`,
  `iso_hub_daily_gas_prices`) add measured basis shapes (Algonquin/Transco for
  NEISO/NYISO; ERCOT electric-power gas). `gas_daily_shape_factors` injects
  mean-preserving intra-month swing.
- **Coal**: `coal_passthrough_series` / `coal_passthrough_by_supply` — flat or
  logistic-sigmoid-shaped by gas price, per supply class (PRB / lignite /
  bituminous).
- **Oil**: EIA-923 monthly delivered cost (`iso_monthly_oil_prices`) or flat
  fallback, for dual-fuel switching.
- **EIA-923 overlay** (backcast): `iso_monthly_gas_prices` returns volume-weighted
  monthly receipts; `gas_monthly_actuals` mode overlays them onto the annual
  price.
- **Hydrogen** (`hydrogen.py`): self-grounding — `compute_h2_fuel_cost =
  min(wind_lcoe, solar_lcoe) / electrolyzer_efficiency / MMBTU_PER_MWH`. No
  circular pricing.

## 4.3 Renewables (`renewables.py`)

Derives `(n_zones, hours)` capacity-factor arrays in `[0,1]`:

- `derive_cf_profile` scales an EIA-930 generation distribution to hourly CF.
- HSL (uncurtailed potential) sets — `load_hsl_hourly`, `hsl_potential_mw` — let
  HSL-backed ISOs (ERCOT, CAISO) dispatch from full potential so the LP re-curtails
  endogenously. ISOs/years without HSL use EIA-930 delivered generation
  (curtailment embedded).
- `_eia860_monthly_capacity` builds `(n_zones, 12)` operable nameplate with
  per-unit COD on-ramp and retirement off-ramp.
- Forecast years without HSL use `_forecast_uncurtailed_cf` (delivered CF ÷
  `(1 − reference_curtailment_rate)`).
- Per-zone shapes: clear-sky solar geometry (CAISO), MERRA-2 wind power curves
  reconciled to EIA-930 totals (MISO).

Renewables enter the LP as **decision variables** `W[z,t]`, `S[z,t]` with upper
bound `monthly_capacity[zone,month] × cf[zone,hour]`.

## 4.4 Outages (`outages.py`) — backcast only

Turns measured outage records into hourly availability masks
(`outage_source="historic"`):

- `outage_masks_for_year` — sustained (>48 h) coal/CC facility outages → boolean
  masks (zero the `min_gen` floor in outage hours).
- `unit_outage_derate_factors` — ≥5-day unit outages → availability multipliers.
- `partial_outage_derate_factors` — CAMPD CF-ceiling plateaus.
- `retiree_availability_caps` — within-window retirees clamped to measured peak
  monthly CF.
- `ct_deployment_floor_for_year` / `reliability_deployment_floor_for_year` —
  measured out-of-merit CT/thermal deployment floors as sparse `min_gen` bounds.

Forecast mode uses the statistical WEFOR/POF availability model instead.

## 4.5 Hydro (`hydro.py`)

`HydroBudget` (frozen dataclass): `plant_ids, zones, monthly_energy[n_hydro,12],
min_mw, max_mw`. `load_hydro_budget` joins EIA-923 monthly net-gen (the budget) to
EIA-860 nameplate. Enters the LP as the monthly energy constraint family
(`Σ_{t∈month} P[hydro,t] ≤ monthly_energy`) plus a run-of-river `min_mw` floor.
Forecast uses `forecast_monthly_hydro` = climatological mean × wet/normal/dry
multiplier; backcast uses measured EIA-930. Pumped storage (`PS`) is excluded here —
it is modeled as storage.

## 4.6 Supporting loaders

| Module | Provides |
|--------|----------|
| `eia_loader.py` | EIA-930 zonal demand, per-fuel generation, interchange envelopes, load-weighted temperatures (drive reliability floors), import-hub prices |
| `campd.py` | EPA CAMPD hourly CEMS → annual plant totals, parasitic (net/gross) factors, per-plant marginal/no-load emission rates + startup adders, per-plant 8760-hour net-generation benchmark |
| `egrid.py` | `fossil_co2_rate_map(year)` = per-plant CO2 rate (eGRID base + CAMPD override); net-gen-weighted class intensity |
| `zone_assignment.py` | eGRID lat/lon/FIPS → model zone (`build_zone_lookup(iso)`), per-ISO geographic rules |
| `eia923.py` | EIA-923 Schedule-5 monthly fuel costs + Page-1 monthly generation |
| `cod_ramp.py` | `load_cod_map()` = `{plant_code: (online_y/m, retire_y/m)}`; `monthly_online_mask` gates the `min_gen` floor so units don't dispatch before COD or after retirement |
| `neighbor_price.py` | forecast-grade neighbor reference prices (`gas × HR × load_shape`) for seam pricing; flow-responsive tranches; measured neighbor LMP as backcast anchor |
| `ownership.py` / `ownership_config.py` | EIA-860 Schedules 3&4 → generator→parent mapping, M&A overlays, ownership-scaled emission/financial attribution |
| `plant_taxonomy.py` (in `config/`) | canonical plant-class ↔ EIA-930 fuel ↔ EIA-923 coal-rank taxonomy; `classify_plant(...)` used identically by all three ingestion paths |

## 4.7 Marginal-cost assembly

The data layer's payload to the LP is `mc[g,t]`, assembled (in `fleet.py`) as:

```
mc = heat_rate · fuel_price[g,t]
   + vom
   + emission_rate · carbon_price
   + nox_rate · nox_price  (+ so2 …)
   − coal take-or-pay sunk-fuel reduction   (apply_coal_tranches)
   − IRA / EAC credits                       (policy layer, see 05-policy.md)
```

Marginal cost is recomputed even for cached years, because next year's economic
retirement screen needs `(price − mc) · dispatch`.
</content>
