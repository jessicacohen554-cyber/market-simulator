# 8. Configuration Reference

Source: `src/market_sim/config/`. This page is the field reference for
`ScenarioConfig`, the per-ISO topology in `iso_configs.py`, the constants
catalogue, path resolution, and the plant taxonomy.

All monetary parameters are **2026 real USD** anchored to Jan 1, 2026
(`REAL_DOLLAR_BASE_YEAR = 2026`).

## 8.1 `ScenarioConfig` (`scenarios.py`)

The complete run specification, loaded via `ScenarioConfig.from_yaml(path)`;
`config.cache_key()` is the deterministic results-cache hash. Fields are grouped
below by purpose (defaults shown).

### Structural

| Field | Default | Controls |
|-------|---------|----------|
| `mode` | `"forecast"` | `"forecast"` vs `"backcast"` — the explicit forecast/backcast switch (never inferred) |
| `iso` | `"ERCOT"` | target ISO |
| `weather_year` | `2024` | which historical year's load/VRE profiles to use |
| `voll` | `5000.0` | value of lost load ($/MWh); ISO-specific |
| `hours` | `8760` | dispatch horizon (smaller only for smoke tests) |

`mode="backcast"` gates a coherent set of behaviors: renewable capacity → that
year's EIA-860 actuals, measured hourly profiles, no planned-addition injection,
measured fuel/outage/hydro overlays. It is independent of any price override — a
forecast with a pinned gas price is still a forecast.

### Pricing & carbon

| Field | Default | Controls |
|-------|---------|----------|
| `gas_price_path` | `"mid"` | Henry Hub trajectory (`low`/`mid`/`high` or CSV path) |
| `carbon_price` | `0.0` | flat federal $/tCO2 (non-zero takes priority) |
| `carbon_price_path` | `"zero"` | trajectory used when `carbon_price == 0` |
| `state_carbon_pricing` | `True` | apply CA cap-and-trade / RGGI measured prices |
| `nox_price`, `so2_price` | `0.0` | $/ton adders |
| `gas_seasonality` | `True` | monthly Henry Hub seasonality |

### Demand, deployment & water

| Field | Default | Controls |
|-------|---------|----------|
| `demand_growth_rate` | `0.01` | flat override (only when no structured rate exists) |
| `demand_growth_path` | `"mid"` | per-ISO escalation path |
| `renewable_buildout_pace` | `"mid"` | `slow`/`mid`/`aggressive` |
| `storage_deployment` | `"mid"` | battery deployment rate |
| `retirement_aggressiveness` | `"mid"` | retirement screen aggressiveness |
| `hydro_year` | `"normal"` | `dry`/`normal`/`wet` (forecast water-year multiplier on climatology) |

### Clean-energy credits (EAC, $/MWh)

`eac_price_nuclear`, `eac_price_wind`, `eac_price_solar`, `eac_price_storage`,
`eac_price_gas_cc_ccs`, `eac_price_offshore_wind`, `eac_price_geothermal` (all
`0.0`). `rps_enabled` (`True`) toggles the RPS LP constraint.

### IRA credits

`ira_ptc_wind=26.0` ($/MWh), `ira_itc_solar=0.30`, `ira_itc_storage=0.30`;
phase-out cliffs `ira_wind_solar_last_year=2027`,
`ira_other_clean_last_full_year=2028`, `ira_other_clean_phaseout_end=2033`,
`ira_h2_45v_last_year=2027`, `ira_ccus_45q_last_year=2032`.

### Fleet representation

| Field | Default | Controls |
|-------|---------|----------|
| `use_campd_bins` | `True` | CAMPD 4-tranche per-plant binning vs legacy heat-rate bins |
| `campd_bins_path` | `CAMPD_BINS_CSV` | bin-assignment CSV |
| `heat_rate_bin_count` | `None` | legacy bin count (default 3) |
| `cod_ramp_enabled` | `True` | month-precise commercial-operation-date masking |
| `eia860_vintage_year` | `None` | year-matched EIA-860 vintage for backcast |
| `use_plant_emission_rates` | `True` | single-plant generators take that plant's measured CO2/NOx/SO2 |
| `historic_outage_overlay` | `True` | hard-zero CAMPD tranches on facility CEMS dropout (per-ISO registry gates) |

### Economic retirement & adequacy

Per-fuel grace periods: `retirement_years_coal=1`, `gas_ct=2`, `gas_cc=3`,
`gas_st=2`, `oil=2`, `gas_cc_ccs=3`, `nuclear=3`. `retirement_reserve_margin=0.15`
(reliability floor). Per-fuel FOM multipliers (coal 1.3×). Going-forward FOM:
`fixed_om_gas_cc=12.0`, `fixed_om_coal=40.0`, `fixed_om_nuclear=130.0` ($/kW-yr).
`forecast_fossil_retirement_economic=True` (fossils retire on economics, not
announced dates). `reserve_margin_build_enabled=False`,
`planning_reserve_margin=0.1375` (the per-ISO registry leads).

### Storage

`storage_rte_4hr=0.85`, `storage_rte_8hr=0.80`, `storage_capacity_value=True`,
`storage_degradation=True`, `storage_daily_cycling=False` (bound arbitrage to
within-day SOC).

### CCS retrofit

`ccs_retrofit_hr_penalty=0.12`, `ccs_retrofit_capex_kw=900.0`,
`ccs_retrofit_vom_adder=8.0`, `ccs_retrofit_capture_rate=0.90`,
`ccs_retrofit_available_year=2028`, `ccs_retrofit_max_gw_per_year=3.0`,
`ccs_retrofit_min_remaining_life=15`.

### Emerging tech availability

`electrolyzer_type="pem"`, `h2_available_year=2035`, `ccs_available_year=2030`,
`egs_available_year=2030`, `offshore_wind_available_year=2030`,
`offshore_wind_eligible_isos=["CAISO"]`, `egs_pmin_fraction=0.20`.

### Thermal dispatch calibration (heat-rate tranche multipliers)

Peaking penalties: `cc_peak_hr_penalty=1.15`, `ct_peak_hr_penalty=1.10`,
`coal_peak_hr_penalty=1.08`. Committed/economic multipliers (convex input-output
curves): `cc_committed_hr_mult=1.23` / `cc_econ_hr_mult=0.96`, with `ct_*`,
`gas_st_*`, `coal_*` analogues. `must_run_cf=0.85`.

### Unit commitment (P2)

`commitment_enabled=False` (master gate), `commitment_irr_hurdle=0.07`,
`commitment_storage_weight=1.0`, `commitment_storage_in_merit_floor=0.0`,
`commitment_screen_coal=True`.

### Scarcity & reserve overlays

- **ERCOT ORDC**: `scarcity_pricing_enabled=False`, `ordc_voll=5000.0`,
  `ordc_mcl_mw=3000.0`, `ordc_lolp_sigma_mw=1400.0`, `ordc_lolp_mu_mw=0.0`,
  `ordc_lolp_shift_sigma=0.5`, `ordc_multistep_floor=True`,
  `as_revenue_enabled=False`, `as_revenue_multiplier=1.0`,
  `ercot_market_design="auto"` (`ordc`/`rtcb`/`auto`).
- **NYISO RCPF**: `nyiso_rcpf_enabled=False` (+ optional product/locational
  overrides).
- **NEISO RCPF**: `neiso_rcpf_enabled=False`.
- **Reserve co-optimization**: `energy_reserve_coopt`,
  `ercot_multiproduct_as_coopt`.

### Reliability floors

**Unified temperature/net-load floor** (replaces all legacy per-ISO floor
bools — `caiso_ct_reliability_floor`, `nyiso_ct/st_reliability_floor`,
`neiso_temp_reliability_floor`, `miso_temp_reliability_floor`, which are
removed):
- `reliability_floor: bool = False` — master switch; arms all enabled limbs
  from `RELIABILITY_FLOOR_REGISTRY` (CSV-seeded per-(zone, class, driver)
  specs). See `docs/multi-iso/reliability-floor-feature.md`.
- `reliability_floor_overrides: dict` — per-limb overrides keyed
  `"<ZONE>:<CLASS>:<driver>"`.
- `class_commitment_overrides: dict` — per-class commitment params
  (min_run/min_down) for steam-gas event bridging.

**Other ISO-specific min_gen mechanisms** (not part of the reliability floor):
- **CAISO**: `caiso_gas_commitment_floor`, `caiso_ra_mustoffer`
  (`caiso_ra_min_load_frac=0.40`).
- **NYISO**: `nyiso_local_selfsupply`.
- **NEISO**: `neiso_gas_coldsnap_derate` (gas-pipeline availability derate,
  not a commitment floor).

### Transmission / interchange

`interchange_shaping`, `interchange_shaping_export_only`,
`reference_price_interface` (forecast-grade priced interchange; PJM/MISO).

## 8.2 ISO topology (`iso_configs.py`)

Pydantic models — `Zone(name, iso, load_share)`, `TransferLink(from_zone, to_zone,
ttc_mw, is_bidirectional)`, `InterfaceLimit(name, links, cap_mw, bidirectional)`,
`ISOConfig(name, zones, links, voll, interface_limits)`. `get_iso_config(name)`
(case-insensitive) builds and calls `validate_topology()`.

The seven registered ISOs:

| ISO | Zones | Notable topology |
|-----|-------|------------------|
| **ERCOT** | 7: West, Panhandle, North, Northeast, Houston, South_Central, South | calibrated reference; WESTEX/NE_LOB interfaces; VOLL $5,000 |
| **CAISO** | 4: NP15, ZP26, SP15, WECC_import | Path 15/26 cutsets; WECC import bubble, 8,300 MW simultaneous cap; VOLL $2,000 |
| **PJM** | 8: ComEd, AEP_Ohio, ATSI, West_APS, Central_PA, Dominion, EMAAC, SWMAAC | 8-zone split captures AP-South / Eastern-Hub gradients |
| **MISO** | 3: North, Central, South | RDT one-way links (3,000 N→S / 2,500 S→N) |
| **NYISO** | 5: Upstate_West, Capital_Hudson, Lower_Hudson, NYC, Long_Island | nested downstate import cutsets; cable-limited LI |
| **NEISO** | 5: North, Central, Boston, Connecticut, HQ_import | import pockets + HQ Phase-II HVDC node |

Zone names above are shown unprefixed for readability; in `iso_configs.py` the
literal `Zone.name` strings for PJM/MISO carry an ISO prefix — `PJM_ComEd`,
`MISO-North`, etc. (ERCOT, CAISO, NYISO, NEISO zone names are
unprefixed as listed).

VOLL is $2,000/MWh for all non-ERCOT ISOs (FERC Order 831 / tariff caps).

## 8.3 Constants catalogue (`constants.py`, ~3,900 lines)

A cited registry; major groups:

| Group | Examples |
|-------|----------|
| Heat rates | `HEAT_RATE_BINS` (gas_cc H-class 6.3, coal supercritical 8.8, …) |
| Commitment | `CC/CT/ST_GAS_COMMITMENT_PARAMS` (startup $, min-run/min-down), `COAL_TRANCHES` |
| Emissions | `CO2_RATES`, `NOX_RATES`, `FUEL_CO2_FACTOR_PER_MMBTU` |
| Variable cost | `VOM` by fuel |
| Availability | `THERMAL_AVAILABILITY` (POF/WEFOR/DERATE 7-tuples), `EFORD`, `MAINTENANCE_MONTHLY_SHAPE`, `NUCLEAR_MONTHLY_CF[_BY_YEAR]` |
| Demand | `DEMAND_GROWTH_RATES` (ISO × path × near/long), `DEMAND_GROWTH_TRANSITION_YEAR=2030` |
| Gas | `HENRY_HUB_TRAJECTORIES` (AEO2025), `GAS_BASIS_DIFFERENTIAL`, `GAS_MONTHLY_SEASONALITY` |
| Coal / oil | `COAL_PRICE_BASE`, `COAL_PRICE_ESCALATION=0.01`, `OIL_PRICE_PER_MMBTU=18.0`, `BIOMASS_PRICE_PER_MMBTU=2.5` |
| Carbon | `CARBON_PRICE_PATHS` (RFF), `STATE_CARBON_PRICE_BY_ISO`, `CARB_UNSPECIFIED_IMPORT_EF=0.428` |
| Storage | `STORAGE_TECHS`, `STORAGE_BASE_FLEET_MW`, `STORAGE_*_CEILING/BUILD_CAP_MW`, `STORAGE_ELCC_BY_DURATION` |
| Market design | `MARKET_DESIGN` (per-ISO capacity_market + net_cone), `DEFAULT_MARKET_DESIGN` (energy-only) |
| Reserve margins | `PLANNING_RESERVE_MARGIN_BY_ISO` (ERCOT 13.75% … NYISO 24.4%) |
| ERCOT AS | `ERCOT_AS_REVENUE_PER_KW_YR`, saturation ref/exponent |
| RPS | `STATE_RPS_FLOORS` (CA SB100, NY CLCPA, MA CES) |
| Queue caps | `QUEUE_CAP_GW`, `QUEUE_CAP_PER_TECH_GW` |
| New entry | `NEW_ENTRY_COSTS` (NREL ATB 2024), `WRIGHT_REFERENCE_GW`, `GLOBAL_ANNUAL_DEPLOYMENT_GW` |
| Emerging | `HYDROGEN_TURBINE_PARAMS`, `ELECTROLYZER_PARAMS`, `CCUS_PARAMS`, `GEOTHERMAL_PARAMS`, `OFFSHORE_WIND_PARAMS` |
| Registries | `CAMPD_BINNING_ISOS`, `HISTORIC_OUTAGE_OVERLAY_BY_ISO`, `IMPORT_TRANCHES`/`EXPORT_TRANCHES` |
| Horizon | `START_YEAR=2026`, `END_YEAR=2050`, `HOURS_PER_YEAR=8760`, `WEATHER_YEAR_POOL=(2023,2024,2025)`, `WEATHER_YEAR_POOL_BY_ISO` (per-ISO widened pool, see `docs/weather-pool-coverage-2026-07.md`) |

Every value carries a citation comment; provenance is traced in
`docs/parameter-citations.md`.

## 8.4 Path resolution (`paths.py`)

A single registry — never `Path(__file__).parents[...]` scattered through the code.
`REPO_ROOT = parents[3]`; `DATA_ROOT = $MARKET_SIM_DATA_ROOT or REPO_ROOT`. The
single consolidated raw root is `RAW_DATA_DIR = DATA_ROOT/data/raw` (W1 collapsed
the old `inputs/` + `data/` roots). Derived subdirs: `PROCESSED_DIR`
(`_processed-legacy`), `CALIBRATION_DIR` (`_validation-source`), plus
`EIA_860_DIR`, `EIA_930_DIR`, `ZONE_DEMAND_DIR`, `GAS_PRICES_DIR`, the per-ISO HSL
dirs, etc. Curated reference files: `PLANT_REGISTRY_CSV`, `CAMPD_BINS_CSV`.

EIA-860 has a two-level vintage seam: a canonical 2025 Early Release (filtered by
COD ramp for backcasts) and optional year-matched `vintage_<year>/` releases.
`active_eia860_dir()` / `set_eia860_vintage(year)` switch the active vintage;
vintage-keyed caches auto-pick up the switch. `CLEAN_DIR` / `DICTIONARY_DIR` and
`clean_path(...)` are the forward (W3) curated-Parquet layout, gated by
`MARKET_SIM_USE_CLEAN`.

## 8.5 Plant taxonomy (`plant_taxonomy.py`)

The single source of truth for fuel/class buckets — no scattered hardcoded fuel
lists. Three aligned axes: model plant class (`Plant_Group`/dispatch `klass`),
EIA-930 fuel bucket (`coal, gas, nuclear, hydro, wind, solar, oil, other,
storage`), and EIA-923 coal-rank code.

- `PLANT_CLASSES` — registry of `PlantClass(key, fuel930, label, fossil)` for all
  classes (COAL*, CC_REGULAR/CC_CHP, CT_PEAKER/CT_CHP, ST_GAS/ST_CHP, nuclear,
  hydro, wind, offshore_wind, solar, oil, biomass, geothermal, storage, OTHER).
- Lookups: `class_label`, `fuel930_of`, `is_fossil`, `fossil_classes`,
  `nonfossil_classes`, `classes_for_fuel930`.
- Coal-rank chain: `COAL_CODE_TO_SUPPLY` (BIT→bituminous, SUB→prb, LIG→lignite, …)
  → `COAL_SUPPLY_TO_CLASS` → `coal_code_to_class`.
- `classify_plant(fuel, prime_mover, chp_flag, plant_id, coal_class_resolver=None)`
  — the canonical classifier used identically by the ERCOT bin override, the
  non-ERCOT EIA-860 fleet, and the EIA-923 benchmark, so all three bucket plants
  the same way (no drift).
</content>
