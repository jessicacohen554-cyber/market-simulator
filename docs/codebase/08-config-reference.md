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
| `storage_deployment` | `"mid"` | battery deployment rate |
| `retirement_aggressiveness` | `"mid"` | retirement screen aggressiveness |
| `hydro_year` | `"normal"` | `dry`/`normal`/`wet` (forecast water-year multiplier on climatology) |

`renewable_buildout_pace` was listed here until 2026-09-01. It was consumed by
no model code and was DELETED under rule 26 `[R-DELETE]` (capx-T16;
`docs/handoffs/FINDING-capx-t16-driver-2026-09-01.md`). VRE buildout pace is
set by the FF-2A entry growth ladder — `entry_rate_limits`, the ReEDS
200 %-of-prior-max bound over a measured EIA-860 throughput seed that covers
wind and solar — not by a scenario ladder.

### Clean-energy credits (EAC, $/MWh)

`eac_price_nuclear`, `eac_price_wind`, `eac_price_solar`, `eac_price_storage`,
`eac_price_gas_cc_ccs`, `eac_price_offshore_wind`, `eac_price_geothermal` (all
`0.0`). `rps_enabled` (`True`) toggles the RPS LP constraint.

### IRA credits

`ira_ptc_wind=26.0` ($/MWh), `ira_itc_solar=0.30`, `ira_itc_storage=0.30`;
phase-out cliffs `ira_wind_solar_last_year=2027`, the §45Y/§48E OBBBA step
schedule `ira_other_clean_last_full_year=2033` / `75pct=2034` / `50pct=2035` /
`phaseout_end=2036`, `ira_h2_45v_last_year=2027`, `ira_ccus_45q_last_year=2032`.
Credit windows from placed-in-service, both levelized `CRF(life)/CRF(window)`
in the entry screens: `ira_45q_credit_window_years=12` (§45Q(a)(3)-(4)) and
`ira_ptc_credit_window_years=10` (§45(a)(2)(A)(ii); FFR-4C/D-13 — wind entry
LCOE only, `None` = unwindowed control arm; the dispatch-side PTC offer is a
separate surface).

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

`retirement_rule='pipeline'` (the default; `'legacy'` is the alternative)
selects how a failing screen becomes an exit. Under **pipeline**, the per-fuel
physics is the execution lag: `retirement_execution_lag_coal=3`, `gas_ct=2`,
`gas_cc=1`, `gas_st=1`, `oil=1`, `nuclear=3` (`gas_cc_ccs=None`, inheriting
gas_cc). Under **legacy only**, the per-fuel grace periods apply:
`retirement_years_coal=3`, `gas_ct=2`, `gas_cc=3`, `gas_st=2`, `oil=2`,
`gas_cc_ccs=3`, `nuclear=3`. Per-fuel FOM multipliers (coal 1.3×). Going-forward
FOM: `fixed_om_gas_cc=12.0`, `fixed_om_coal=40.0`, `fixed_om_nuclear=130.0`
($/kW-yr). `fossil_announced_exits_enabled=True` since 2026-09-02 — an owner-filed
EIA-860 Schedule-3 fossil date is an exogenous step-1b exit and its plant is
**exempt** from the economic screen, so `forecast_fossil_retirement_economic=True`
now governs only the residual **undated** fossil fleet.
`reserve_margin_build_enabled=None` (**tri-state** — resolves ON for the five
capacity-market ISOs, OFF for energy-only ERCOT and for any ISO absent from
`MARKET_DESIGN`, which since 2026-09-06 includes energy-only SPP),
`planning_reserve_margin=0.1375` (the per-ISO `PLANNING_RESERVE_MARGIN_BY_ISO`
registry leads: ERCOT 0.1375, CAISO 0.15, PJM 0.178, MISO 0.157, NYISO 0.244,
NEISO 0.1277, SPP 0.16). (`retirement_reserve_margin` was **deleted** with the
floor-accreditation rebuild — rule 26 `[R-DELETE]`; it is no longer a field.)

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
- **SPP**: **none, deliberately.** SPP registered with an empty
  `default_scenario_overrides` (owner rulings P4/P5, 2026-09-06): no scarcity
  seed, and reserve co-optimization deferred. SPP's scarcity ceiling is its VRL
  stack, which lever SPP-55 designs; co-optimization is lever SPP-56, queued
  last. `voll=2000.0` = the FERC Order 831 cost-verified ceiling (ruling P10;
  SPP's posted Safety-Net Energy Offer Cap is the lower $1,000/MWh).
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
- **SPP**: none. No floor, bridge or derate is registered for SPP — its first
  keeper (lane SPP-40) is built without one, so any later floor arrives through
  rule 17 `[R-FLOOR-WINDOW]` with its own driver and window.

### Transmission / interchange

`interchange_shaping`, `interchange_shaping_export_only`,
`reference_price_interface` (forecast-grade priced interchange; PJM/MISO).

SPP is served by the **measured EIA-930 `Total interchange` schedule**
(`_SCALAR_INTERCHANGE_ISOS`, owner ruling P2 — the PJM/NYISO/NEISO precedent,
positive = net export) rather than a priced seam. Its four
`INTERFACE_NEIGHBORS["SPP"]` blocks (MISO_West / MISO_South — the MISO seam
split per bordering MISO zone by SPP-51 — / AECI / ERCOT, the last carrying the
DC ties of ruling P3 at the measured 835 MW clip) are registered
**default-off** with measured `hr_by_year` and HH+basis flat heat rates. SPP has
no `IMPORT_ZONE` / `IMPORT_NODE_LINKS` entry, so `--priced-interchange` builds
no seam for SPP at HEAD; lane SPP-51 (2026-09-07) killed the spread-clearing
arm at rule-29 phase 0 on the measured record and routed the two-bus topology
any LP test needs (`docs/handoffs/FINDING-spp-51-2026-09-07.md`).

## 8.2 ISO topology (`iso_configs.py`)

Pydantic models — `Zone(name, iso, load_share)`, `TransferLink(from_zone, to_zone,
ttc_mw, is_bidirectional)`, `InterfaceLimit(name, links, cap_mw, bidirectional)`,
`ISOConfig(name, zones, links, voll, interface_limits)`. `get_iso_config(name)`
(case-insensitive) builds and calls `validate_topology()`.

The **nine registered regions** (`_ISO_BUILDERS`, registration order). Every
name downstream says "ISO", but the last two are not ISOs: **NWPP** is a pool of
~17 balancing authorities and **SOCO** is a single balancing authority.

| ISO | Zones | Links | Notable topology |
|-----|-------|-------|------------------|
| **ERCOT** | 7: West, Panhandle, North, Northeast, Houston, South_Central, South | 10 | calibrated reference; WESTEX/NE_LOB interfaces; VOLL $5,000 |
| **CAISO** | 6: NP15, ZP26, LA_BASIN, SDGE, SP15_rest, WECC_import | 6 | Path 15/26 cutsets; WECC import bubble, `WECC_import_simultaneous` 7,500 MW cap; VOLL $2,000 |
| **PJM** | 8: ComEd, AEP_Ohio, ATSI, West_APS, Central_PA, Dominion, EMAAC, SWMAAC | 11 | 8-zone split captures AP-South / Eastern-Hub gradients |
| **MISO** | 6: West, Plains, Illinois, Indiana, East, South | 8 | RDT one-way links (3,000 N→S / 2,500 S→N); five per-zone CIL/CEL interface groups |
| **NYISO** | 5: Upstate_West, Capital_Hudson, Lower_Hudson, NYC, Long_Island | 4 | nested downstate import cutsets; cable-limited LI |
| **NEISO** | 5: North, Central, Boston, Connecticut, HQ_import | 7 | import pockets + HQ Phase-II HVDC node; `HQ_import_simultaneous` 3,850 MW cap |
| **SPP** | 2: SPP-North, SPP-South | 1 | registered 2026-09-06 (lane SPP-20, owner rulings P1/P10). The single N↔S link's TTC is **3,400 MW** — the rule-14 `[R-ACCURATE]` reconciled corridor limit lever **SPP-53** derived from SPP's own published flowgate limits, which replaced SPP-20's 48,700 MW Tier-3 placeholder. Unlike that placeholder it **can** bind. No import node: the seams are the served EIA-930 `Total interchange` schedule plus three default-off `NeighborInterface` blocks (MISO / AECI / ERCOT). VOLL $2,000 |
| **NWPP** | 5: NWPP-NW, NWPP-OR, NWPP-INLAND, NWPP-EAST, NWPP-SNV | 9 | registered 2026-09-14 (lane NWPP-20, owner rulings N1/N3–N8). **A pool of ~17 balancing authorities, not an ISO** — each zone is a BA group. Six of the nine links are cited WECC path limits (Tier-1 Path 35 / Path 16, Tier-2 Path 20 and the aggregated Paths 8+6+14); the symmetric NW↔OR link is a **Tier-3 documented-absence placeholder that cannot bind** (43,600 MW). No import node. VOLL $2,000 — **DECLARED INTERIM** and a ledgered rule-21 `[R-DOF]` free parameter: FERC Order 831's $2,000 applies by its terms to RTOs/ISOs and NWPP is neither, so the value is the WEIM hard offer cap standing in for a customer damage function that does not exist |
| **SOCO** | 3: SOCO_AL, SOCO_GA, SOCO_MS | 2 | registered 2026-09-14 (lane SOCO-20). **A single balancing authority, not an ISO** — Southern Company's operating companies are dispatched as one integrated system under the IIC, so no inter-OpCo transfer limit is published and both TTCs register **Tier-3 and cannot bind**. VOLL $2,000 |

Zone names above are shown unprefixed for readability; in `iso_configs.py` the
literal `Zone.name` strings for PJM, MISO, SPP, NWPP and SOCO carry a region
prefix — `PJM_ComEd`, `MISO-West`, `SPP-North`, `NWPP-NW`, `SOCO_AL`, etc.
(ERCOT, CAISO, NYISO, NEISO zone names are unprefixed as listed).

VOLL is $2,000/MWh for all eight non-ERCOT regions (FERC Order 831 / tariff
caps) — with the NWPP caveat noted in its row: Order 831 does not reach a pool
that is neither an RTO nor an ISO, so NWPP's $2,000 is interim and ledgered.

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
- Lookups: `class_label`, `fuel930_of`, `fossil_classes`,
  `nonfossil_classes`, `classes_for_fuel930`.
- Coal-rank chain: `COAL_CODE_TO_SUPPLY` (BIT→bituminous, SUB→prb, LIG→lignite, …)
  → `COAL_SUPPLY_TO_CLASS` → `coal_code_to_class`.
- `classify_plant(fuel, prime_mover, chp_flag, plant_id, coal_class_resolver=None)`
  — the canonical classifier used identically by the ERCOT bin override, the
  non-ERCOT EIA-860 fleet, and the EIA-923 benchmark, so all three bucket plants
  the same way (no drift).
</content>
