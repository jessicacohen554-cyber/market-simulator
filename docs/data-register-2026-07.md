# Data Register & Completeness — 2023-2025 Backcast

**Purpose:** a single inventory of every real-world/measured dataset the model consumes for the
2023-2025 backcast (ERCOT, CAISO, PJM, MISO, NYISO, NEISO), its source and on-disk path, and its
actual calendar coverage in this repo across the window **Jan 1 2018 – Jun 30 2026**. This is a
data-availability snapshot as of 2026-07-07, not an analysis of calibration quality or a change to
any model behavior.

**Reading the completeness table:** `✓` = full calendar-year coverage on disk; `—` = no data;
partial coverage is spelled out (e.g. "Q1 only", "Jan–Apr"). Where coverage differs materially by
ISO, the source is split into per-ISO rows. Static reference/crosswalk tables and forward-looking
registries (not a rolling calendar series) are called out separately at the bottom and excluded
from the year grid.

---

## Part 1 — Data Register: sources used in the 2023-2025 backcast

| # | Dataset | Agency / Source | Used for | On-disk path | Mode |
|---|---|---|---|---|---|
| 1 | EIA-930 Hourly Electric Grid Monitor — system hourly demand & fuel-mix generation | U.S. EIA | System hourly demand driver; per-fuel generation actuals used to score modeled dispatch by class (the primary backcast bench) | `data/raw/eia-930-hourly/<BA> hourly.parquet`, `data/raw/eia-930/EIA930_BALANCE_*`, `<BA>_fueltype/region_<year>.parquet` | Backcast (bench); demand/gen level is backcast-only, wind/solar CF shape reused as forecast climatology |
| 2 | Zone-specific metered/actual load | ERCOT NP3-565-CD native load, CAISO OASIS ACTUAL, NYISO OASIS "pal" actuals, PJM per-zone metered load | Per-zone hourly load shares (replacing static shares) | `data/raw/zone-specific-demand/` (+ `/NYISO`, `/CAISO`) | Backcast-only |
| 3 | PJM DataMiner2 "Generation by Fuel Type" | PJM (owner-exported, no API key) | PJM class-volume bench, cross-checks EIA-930 | `data/raw/ISO-specific-gen-data/PJM_<year>_gen_by_fuel.csv` | Backcast (bench) |
| 4 | EPA CAMPD hourly CEMS — unit-level | EPA Clean Air Markets Program Data | Per-plant/unit fleet binning, same-year emission rates, parasitic (net/gross) factors, per-plant CEMS generation bench, source for outage/tranche/ramp derivations below | `data/raw/campd-unit-level/<STATE>_<YEAR>.parquet` | Backcast-only |
| 5 | EPA CAMPD hourly CEMS — facility-level | EPA CAMPD | Facility-grain cross-check / derivation input for outages | `data/raw/campd-facility-level/<STATE>_<year>.parquet` | Backcast-only |
| 6 | CAMPD-derived facility outage windows | Derived from #4/#5 (`scripts/derive_campd_outages.py`) | Per-plant hourly availability mask (sustained CF<5% ≥2 days) | `data/raw/campd-outages.csv`, `campd-outages-<ISO>.csv`, `ercot-outages.csv` | Backcast-only |
| 7 | CAMPD-derived unit-level outage events | Derived from #4 (`scripts/derive_campd_unit_outages.py`) | Unit-level derate on top of #6 | `data/raw/campd-unit-outages.csv`, `campd-unit-outages-<ISO>.csv` | Backcast-only |
| 8 | CAMPD-derived partial-outage (CF-ceiling) windows | Derived from #4 (`scripts/derive_partial_outages.py`) | Plateau-CF derate windows | `data/raw/campd-partial-outages.csv` | Backcast-only |
| 9 | CAMPD-derived plant tranches / ramp envelopes / CT run-lengths | Derived from #4 | Offer-curve tranche shares, ramp physics, CT startup amortization | `data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`, `campd_ramp_envelopes_<ISO>.csv`, `campd_ct_run_lengths_<ISO>.csv` | Both (physics reused forward) |
| 10 | CAMPD-derived forward emission-rate estimator input (`plant_emission_rates_v2`) | Derived from #4, pooled 2023-2025 | Forecast-year per-plant CO2/NOx/SO2 rate estimator (rule #0's forward-derivation exception) | `data/raw/_processed-legacy/plant_emission_rates.parquet` | Forecast-only (derived from backcast-year CEMS) |
| 11 | EIA-860 generator/plant fleet (Sch. 2/3/4) | U.S. EIA | Thermal/nuclear/hydro/storage/renewable fleet inventory, capacity, prime mover, CHP flag, COD/retirement dates, ownership | `data/raw/eia-860/eia860_*.parquet`, `vintage_<year>/` | Both |
| 12 | EPA eGRID plant-level annual CO2/heat-rate/geography | EPA eGRID workbook | Fossil CO2-rate default (small non-CEMS plants), plant lat/lon/BA zone assignment | `data/raw/fleet-egrid/egrid<vintage>_data.xlsx` | Both |
| 13 | EIA-923 Schedule 2/5 monthly delivered fuel cost | U.S. EIA Form 923 | Measured coal/gas/oil delivered price by plant/ISO-month, overriding AEO trajectory | `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` | Both |
| 14 | EIA-923 Page 1 monthly net generation | U.S. EIA Form 923 | Generation bench, hydro monthly budget, CHP classification, CO2-rate fallback | `data/raw/_processed-legacy/eia923_monthly_generation.parquet` | Both |
| 15 | EIA-923 Schedule 5 gas Purchase-Type (take-or-pay share) | U.S. EIA Form 923 | Contract-vs-spot gas share per plant | `data/raw/_processed-legacy/gas_takeorpay_ERCOT.csv`, `coal_takeorpay_<ISO>.csv` | Both |
| 16 | Henry Hub daily/monthly spot | U.S. EIA (public-domain mirror) | National gas price driver for all ISOs | `data/raw/gas-prices/henry_hub_{daily,monthly}.csv` | Both |
| 17 | Citygate/basis-by-ISO-month | EIA citygate series | Fallback basis differential for ISOs lacking a zonal-hub file | `data/raw/gas_basis_by_iso_month.csv` | Both |
| 18 | ERCOT zonal gas hub (Waha basis) + electric-power gas price | EIA N3045TX3 / Sch. 5 derived, supplemented by EIA "Today in Energy"/Reuters narrative for 2022/2026 gaps | ERCOT per-zone gas MC | `data/raw/ercot_zonal_gas_hub.csv`, `ercot_electric_power_gas_price.csv` | Both |
| 19 | PJM zonal gas hub | EIA N3045 state series | PJM per-zone gas MC | `data/raw/pjm_zonal_gas_hub.csv` | Both |
| 20 | MISO zonal gas hub | EIA N3045 IA/IL/LA state series | MISO per-zone gas MC | `data/raw/miso_zonal_gas_hub.csv` | Both |
| 21 | NYISO zonal gas hub | NYISO SOM (Potomac Economics) Figure A-6 | NYISO per-zone gas MC | `data/raw/nyiso_zonal_gas_hub.csv` | Both |
| 22 | NYISO downstate LDC non-firm transport premium | National Grid tariff archive (KEDNY SC-22, KEDLI SC-19) + Transco Z6 NY daily spot + Henry Hub | NYC/Long Island CT-peaker gas premium | `data/raw/gas-prices/nyiso_downstate_ldc_transport_monthly.csv`, `nyiso_downstate_ct_gas_basis_monthly.csv` | Both |
| 23 | Transco Zone 6 NY daily spot | EIA Natural Gas Weekly Update archive scrape | Within-month NYISO gas-basis shape; Iroquois reconstruction leg | `data/raw/gas-prices/transco_z6_ny_daily.csv` | Both |
| 24 | Algonquin Citygate (AGT) daily spot | EIA NG Weekly narrative scrape | NEISO within-month gas-basis shape | `data/raw/gas-prices/algonquin_citygate_daily.csv` | Both |
| 25 | Iroquois Zone 2 daily/monthly spot | EIA NG Weekly narrative scrape + NYISO SOM annual spread | NYISO reference-zone gas basis | `data/raw/gas-prices/iroquois_z2_daily.csv`, `transco_z6_iroquois_monthly.csv` | Both |
| 26 | CA Composite Average citygate daily spot | NGI Daily GPI via EIA NG Weekly compact table | CAISO within-month gas-price shape | `data/raw/gas-prices/caiso_citygate_daily.csv` | Both |
| 27 | ERCOT NP4-732/737 HSL (High Sustained Limit) wind/solar | ERCOT (2024/2025 uploads); 2023 via UMass 60-Day-SCED reconstruction (no ERCOT upload exists for 2023) | Uncurtailed renewable potential; curtailment calibration | `data/raw/ercot-hsl/ercot_<year>_hsl_hourly.parquet`, `np6/<year>/` | Backcast-only |
| 28 | CAISO delivered generation + reported curtailment | CAISO Production-and-Curtailment workbooks | Same HSL-analogue construction for CAISO | `data/raw/caiso-hsl/`, `data/raw/caiso-curtailment/` | Backcast-only |
| 29 | MISO wind-shape reanalysis | NASA POWER MERRA-2 wind speed, reconciled to EIA-930 MISO total | MISO wind diurnal/seasonal shape | `data/raw/miso-wind-shape/` | Both (shape reused; level always measured) |
| 29b | MISO wind curtailment (annual/quarterly aggregate, added 2026-07-08) | Potomac Economics (MISO IMM) State of the Market + IMM Quarterly reports | Coarse HSL-analogue input (MISO's own curtailment reports stay allowlist-blocked); not yet an hourly series | `data/raw/miso-hsl/miso_wind_curtailment_annual.csv`, `miso_wind_curtailment_quarterly*.csv` | Backcast-only |
| 30 | ERCOT 60-Day DAM cleared Ancillary Services | ERCOT | Measured hourly reserve-withholding MW (system + per-class) | `data/raw/ercot-AS/` | Backcast-only |
| 31 | PJM Ancillary Services (RT Primary Reserve) | PJM | Measured reserve-withholding MW, gas+oil pool | `data/raw/PJM-AS/` | Backcast-only |
| 32 | MISO Ancillary Services market data | MISO | Measured AS clearing | `data/raw/MISO-AS/` | Backcast-only |
| 33 | NYISO Ancillary Services (DA/RT) | NYISO | Measured AS clearing | `data/raw/NYISO-AS/` | Backcast-only |
| 34 | NYISO measured hourly locational reserve requirements | NYISO OASIS RTD/RTC as-enforced series | Replaces published static reserve requirement in the co-opt | `data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_<year>.csv` | Backcast-only |
| 35 | ERCOT NP6-86 SCED binding transmission constraints (GTC) | ERCOT MIS | Measured hourly GTC export-cap; congestion incidence for WTX curtailment share | `data/raw/iso-specific-transmission/*SCEDBTCNP686*`, curated `gtc-limits`, `ercot-wtx-congestion` | Backcast-only |
| 36 | PJM actual/scheduled tie-line interchange + transfer limits | PJM eData | Measured net export schedule closing the energy-only model's export gap | `data/raw/iso-specific-transmission/PJM_<year>_import_export_act_sch_interchange.csv`, `PJM_<year>_transfer_limits_and_flows.csv` | Backcast-only |
| 37 | CAISO WECC intertie scheduling-point LMP (Malin/Palo Verde) | CAISO OASIS | Measured delivered cost of CAISO import tranches | `data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet` | Backcast-only |
| 38 | MISO↔PJM border hub DA LMP | PJM Data Miner hub exports (Chicago Gen/AEP Gen/ATSI Gen) | Measured hourly price for MISO's PJM import seam | `data/raw/_validation-source/pjm_border_lmp_hourly_MISO.parquet` | Backcast-only |
| 39 | EIA-930 BA-to-BA interchange | U.S. EIA | CAISO/MISO/NEISO net-import/export deliverability envelope | `data/raw/eia-930-interchange/` | Backcast-only |
| 40 | Realized hourly LMP (validation only, not fed to the LP) | CAISO OASIS, MISO, PJM DataMiner, NYISO MIS, ISO-NE SMD | Model-vs-actual price scoring | `data/raw/lmp-data/<ISO>/` | Backcast-only (scoring) |
| 41 | Per-ISO daily zone temperature (weather-year pinning) | NOAA/NASA-derived daily TMAX/TMIN | Reliability-floor temperature gates, cold-weather gas derate, NEISO winter must-run gate | `data/raw/<iso>-weather/` | Backcast-only |
| 42 | Locational capacity-deliverability parameters (CETO/CETL, LRR/LCR/CIL, LCR/TSL, LSR/MCL, LCR/MIC) | Published ISO capacity-market filings (PJM/MISO/NYISO/ISO-NE/CAISO; ERCOT n/a — energy-only) | Locational RA-saturation gate, LCR pocket balance | `data/raw/capacity-deliverability/<iso>.csv` | Both |
| 43 | NYISO Gold Book / State-of-Market / NYCA-Generators reports | NYISO / Potomac Economics | Planning parameters, gas-basis annual spreads, local self-supply calibration | `data/raw/NYISO/` | Both |
| 44 | MISO Planning Resource Auction clearing prices | Secondary-sourced (hand-transcribed) | MISO capacity price validation | `data/raw/miso-pra/miso_pra_clearing_prices_2023-2026.csv` | Backcast-only |
| 45 | ISO-NE OFSA / Winter Reliability Program fuel-security studies | ISO-NE published studies (not measured burn/receipts) | NEISO winter oil-burn budget + must-run floor | `data/raw/winter-fuel-inventory/isone/isone.csv` | Backcast-only (NEISO, default off) |
| 46 | Confirmed-retirement binding instruments | RTO deactivation acceptances, consent decrees, statutes, regulatory orders (per ISO) | Force-retirement/derate at instrument date | `data/raw/confirmed-retirements/<iso>.csv` | Forecast-only |
| 47 | RGGI allowance distribution / CARB cap schedule | RGGI Inc. / CARB-Quebec auction results | State carbon price series (NEISO/NYISO/CAISO) | `data/raw/policy/rggi-co2-budgets/`, `carb-cap-schedule/` | Both |
| 48 | NYSDEC 6 NYCRR Subpart 227-3 "peaker rule" compliance schedule | NY DEC regulatory filing (via NYISO Gold Book) | Ozone-season simple-cycle unavailability | `data/raw/reference/nysdec-227-3-peaker-compliance.csv` | Both |
| 49 | NERC GADS EFORd benchmarks | NERC | Class-level forced-outage-rate prior | `data/raw/reference/nerc-gads-eford-2019-2023/`, `nerc-gads-eford-annual-2018-2024/` (per-year 2018-2024), `nerc-gads-eford-2018-2022/`, `nerc-gads-eford-2020-2024/` (5-yr rolling windows) | Both |
| 50 | Master plant registry / CAMPD bin assignments / LCR-area membership | Curated crosswalks (EIA-860 + CAMPD + county rules) | Plant→zone assignment, ERCOT tranche crosswalk, CAISO LCR area membership | `data/raw/reference/master-plant-registry.csv`, `custom-bin-assignments.csv`, `lcr_area_membership_CAISO.csv` | Both |

---

## Part 2 — Data completeness, Jan 2018 – Jun 2026

`✓` full year on disk · `—` no data · otherwise the exact months/quarter present. All findings
below are drawn directly from files in `data/raw/` (or verified with `pandas` where a subagent's
claim needed a direct spot-check), not from documentation claims alone.

### Demand & generation-mix bench (EIA-930)

| Source | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|---|---|---|---|
| ERCOT (`ERCO hourly.parquet`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (thru Jun 30) |
| NEISO (`ISNE hourly.parquet`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | thru ~May 21 |
| NYISO (`NYIS hourly.parquet`) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | thru ~Jun 13 |
| PJM (`PJM hourly.parquet`) | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (thru Jun 30) |
| CAISO (`CISO hourly.parquet`) | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| MISO (`MISO hourly.parquet`) | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |

Verified directly (file min/max timestamp): ERCO/ISNE/NYIS wide files start 2015-07-01;
PJM/CISO/MISO start 2019-01-01. CISO/MISO end 2025-12-31 (no 2026 rows at all). The `eia-930/`
long-form supplemental files (per-BA `fueltype`/`region_<year>.parquet`) additionally confirm 2022
and H1-2026 rows exist for ERCOT and PJM specifically (their calibration-complete holdout intake),
and are **absent** for CAISO/MISO (the parallel `eia-930` BALANCE half-year files corroborate: 2022
rows are present but degenerate for CISO/MISO — 9 and 7 hours respectively, not usable years).

### Zone-specific metered demand

| Source | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|---|---|---|---|
| ERCOT native load | — | — | — | — | ✓ | ✓ | ✓ | ✓ | — |
| PJM zonal metered load | — | — | — | — | — | ✓ | ✓ | ✓ | — |
| CAISO TAC load hourly | — | — | — | — | — | ✓ | ✓ | ✓ | — |
| MISO sub-BA demand | — | — | — | — | — | ✓ | ✓ | ✓ | — |
| NYISO load actuals (per-year) | — | — | — | — | — | ✓ | ✓ | ✓ | — |
| NYISO raw monthly "pal" archives | — | — | — | — | — | ✓ | ✓ | ✓ | ✓ (thru Jun 2026) |

NYISO's raw monthly zip archive (`zone-specific-demand/NYISO/raw/*pal_csv.zip`) is the single
gapless monthly series in the whole tree reaching the Jun 2026 edge; the per-year NYISO CSV product
built from it only currently covers 2023-2025.

### EPA CAMPD hourly CEMS — unit-level (fleet binning / emission rates / outage source)

| ISO footprint | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|---|---|---|---|
| ERCOT (TX) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Q1 only |
| PJM (13 states) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Q1 only |
| NEISO (ME/NH/MA/CT/RI/VT) | ✓ | ✓ | ✓ | ✓ | ✓ (landed 2026-07-07, byte-frozen for in-sample) | ✓ | ✓ | ✓ | — |
| MISO (14 states) | ✓ | ✓ | ✓ | ✓ | states shared with PJM/ERCOT only | ✓ | ✓ | ✓ | states shared with PJM/ERCOT only |
| NYISO (NY, NJ) | ✓ | ✓ | ✓ | ✓ | NJ only | ✓ | ✓ | ✓ | NJ only |
| CAISO (CA) | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | — |

2018-2021 are on disk for **every** state/ISO (confirmed `TX_2018.parquet`, `CA_2018.parquet`
exist). 2022 and H1-2026 are the rule-22 holdout years and are intaked only where an ISO's data
has been separately authorized — currently ERCOT, PJM, and (as of 2026-07-07) NEISO.

### EPA CAMPD hourly CEMS — facility-level (derivation cross-check)

| Source | 2018-2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|
| 13 states (AL/CA/DE/IL/MA/MD/ME/NH/NJ/NY/OR/PA/TX) | — | ✓ | ✓ | ✓ | — |

### CAMPD-derived outage overlays

| Source | 2018-2021 | 2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|---|
| ERCOT (`ercot-outages.csv`) | — | — | ✓ | ✓ | ✓ | — |
| ERCOT/PJM facility outages (`campd-outages.csv`, spans outage_start) | — | ✓ (from 2022-01-01) | ✓ | ✓ | ✓ | Q1 (thru ~Mar 24) |
| PJM (`campd-outages-PJM.csv`) | — | — | ✓ | ✓ | ✓ (thru ~Dec 17) | — |
| Partial outages (`campd-partial-outages.csv`, by `year` column) | — | ✓ | ✓ | ✓ | ✓ | partial |
| Legacy hand-maintained (`reference/tx-jan-aug23-unit-outages.csv`) | — | — | Jan–Aug only | — | — | — |

### Renewable HSL / curtailment

| Source | 2018-2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|
| ERCOT HSL | — | ✓ (3rd-party UMass reconstruction, no ERCOT upload exists) | ✓ | ✓ | — |
| ERCOT NP6 monthly source archives | — | — | ✓ (near-complete monthly) | ✓ (near-complete monthly) | — |
| CAISO HSL / curtailment workbooks | — | ✓ | ✓ | ✓ | — |
| NYISO HSL | — | — | — | — | — |
| MISO HSL (hourly) | — | — | — | — | — |
| MISO wind curtailment (annual/quarterly aggregate) | ✓ (2021-2022 only) | ✓ | ✓ | ✓ | ✓ (Q1 only) |
| MISO wind-shape (reanalysis) | — | ✓ | ✓ | ✓ | — |

NYISO HSL directory is empty (documented `DATA NEEDED`: NYISO only publishes a coarse annual
curtailment aggregate). MISO's own curtailment reports (misoenergy.org) remain blocked by this
environment's network allowlist, but `data/raw/miso-hsl/` was populated 2026-07-08 from a reachable
alternate source — Potomac Economics' (MISO's Independent Market Monitor) State of the Market and
IMM Quarterly reports, which quantify system-wide wind curtailment as annual/quarterly average and
peak MW (2021 onward; 2018-2020 reports don't quantify it at all). This is still coarser than an
hourly series, so `miso_<year>_hsl_hourly.parquet` is not yet built and the loader still falls back
to EIA-930 delivered generation; see `data/raw/miso-hsl/SOURCES.md` for the transcribed figures and
provenance.

### Ancillary services / reserves

| Source | 2018-2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|
| ERCOT-AS | — | ✓ | ✓ | ✓ | — |
| PJM-AS | — | ✓ | ✓ | ✓ | — |
| MISO-AS | — | ✓ | ✓ | ✓ | — |
| NYISO-AS (DA/RT clearing) | — | ✓ | ✓ | ✓ | — |
| NYISO measured hourly reserve requirements (Ask B) | — | not independently confirmed present — flagged unresolved in source docs | | | |

### Fuel — EIA-923 delivered cost & generation, coal/gas derivations

| Source | 2018-2021 | 2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|---|
| `eia923_monthly_fuel_costs.parquet` / `_generation.parquet` | — (raw F923 workbooks for these years not on disk; EIA archive URL not reachable through this environment's proxy) | ✓ (ERCOT+PJM only) | ✓ | ✓ | ✓ | Jan–Apr (ERCOT+PJM only, "early release" vintage) |
| Parasitic load factors | — | +ERCOT/PJM (564 rows) | ✓ | ✓ | ✓ | deferred (CAMPD/F923 window mismatch) |
| Gas/coal take-or-pay derivations | — | — | ✓ | ✓ | ✓ | — |

### Gas price / basis series

| Source | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|---|---|---|---|
| Henry Hub daily/monthly | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (thru Jun 15) |
| Citygate/basis-by-ISO-month (all 7 ISO columns) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (some ISO/months short) | partial (17 of 84 rows) |
| ERCOT zonal gas hub (Waha) / electric-power gas price | — | — | — | — | ✓ (closed 2026-07-04 via EIA "Today in Energy" narrative) | ✓ | ✓ | ✓ | Jan–Apr (Reuters/BOE Report narrative) |
| PJM zonal gas hub (8 zones) | — | — | — | — | ✓ | ✓ | ✓ | ✓ | Jan–Apr |
| MISO zonal gas hub | — | — | — | — | — | ✓ | ✓ | ✓ | — |
| NYISO zonal gas hub | — | — | — | — | — | ✓ | ✓ | ✓ | — |
| NYISO downstate LDC gas (National Grid tariff archive) | not individually re-verified — continuous series per source docs | | | | | | | | |
| NEISO Algonquin citygate daily (EIA NG Weekly scrape) | sparse throughout (~30-50 prints/yr even in-sample) — not year-verified for edges | | | | | | | | |

### Transmission / interchange / validation LMP

| Source | 2018-2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|---|---|---|
| ERCOT NP6-86 GTC/transmission (`iso-specific-transmission`) | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| PJM import/export interchange + transfer limits | — | — | — | — | ✓ | ✓ | ✓ | — |
| CAISO WECC intertie LMP (Malin/Palo Verde) | — | — | — | — | ✓ (documented Jan–Feb OASIS gap, filled by reference formula) | ✓ | ✓ | — |
| MISO↔PJM border LMP | — | — | — | — | ✓ | ✓ | ✓ | — |
| EIA-930 BA-to-BA interchange (CISO/MISO/ISNE) | — | — | — | — | ✓ | ✓ | ✓ | — |
| LMP validation — CAISO | — | — | — | — | ✓ | ✓ | ✓ | — |
| LMP validation — MISO | — | — | — | — | ✓ | ✓ | ✓ | — |
| LMP validation — PJM | — | — | — | — | ✓ | ✓ | ✓ | — |
| LMP validation — NEISO (SMD hourly) | — | orphaned 2020/2021 files present but unread by any script | | ✓ | ✓ | ✓ | ✓ | — |
| LMP validation — NYISO (DART monthly index) | — | — | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| LMP validation — ERCOT | none anywhere in the tree, by explicit design (out of scope for `curate_lmp.py`) | | | | | | | |

*Note:* the CLAUDE.md-referenced measured-data audit flags ERCOT's NP6-86 monthly binding-constraint
archives as largely missing today (`DATA NEEDED` in `data/raw/iso-specific-transmission/README.md`)
even though summary/derived parquets for 2020-2025 remain on disk — i.e. the derived GTC product
is present but its raw monthly source ZIPs were not re-committed after a prior session's fetch.

### Weather (all six ISOs — verified directly)

| Source | 2018-2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|
| ERCOT / CAISO / MISO / NYISO / NEISO / PJM daily zone temperature | — | ✓ | ✓ | ✓ | — |

Verified by direct file read: every `*-weather/*.csv` spans exactly 2023-01-01 to 2025-12-31, with
no exceptions. This is the single gap common to all six ISOs and every one of them (a hard floor
under any holdout-year backcast until it's addressed).

### Capacity market / planning reports

| Source | 2018-2021 | 2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|---|
| Locational capacity-deliverability params (PJM/MISO/NYISO/NEISO/CAISO) | planning-year snapshot table, not a rolling calendar series — current vintage only | | | | | |
| NYISO Gold Book | — | — | ✓ | ✓ | ✓ | — |
| NYISO State-of-Market report | — | ✓ | ✓ | ✓ | ✓ | — |
| NYISO NYCA-Generators | — | — | ✓ | ✓ | ✓ | — |
| MISO PRA clearing prices (secondary-sourced) | — | — | ✓ | ✓ | ✓ | ✓ |

### Non-calendar reference data (static or forward-only — excluded from the year grid above)

- **EIA-860 fleet snapshots** — vintage releases, not a per-year series: **2020, 2023, 2024, 2025**
  vintages on disk (no 2018/2019/2021/2022 vintage, no 2026 vintage yet).
- **EPA eGRID** — vintage releases: **2022, 2023, 2024** (2022 is a true 2022-vintage workbook,
  landed 2026-07-04; previously the model stood in the 2024 vintage for 2022).
- **Confirmed-retirements registry** — forward-looking events (`exit_year >= 2023`); not a
  historical coverage question.
- **RGGI allowance schedule / CARB cap schedule** — forward regulatory compliance-year tables.
- **NYSDEC 227-3 peaker compliance, NERC GADS EFORd (annual brochures now on disk for every
  published year 2018-2024 plus 5-yr rolling windows 2018-2022/2019-2023/2020-2024; NERC has not
  yet published a 2025 or H1-2026 brochure as of 2026-07-08), master plant registry, CAMPD bin
  assignments, LCR-area membership** — static crosswalks/benchmarks, not time series.
- **NEISO winter fuel-security inventory** — hand-curated from ISO-NE's 2018 OFSA study and
  2018-2020 ESI filings; a fixed planning-study snapshot, not a rolling measured series.

**Rule-22 note on the 2026-07-08 GADS collection.** The new annual (2018-2024) and
2018-2022 rolling GADS files span the validation holdout year (2022) and years before the
locked-test boundary (2018). This is a **NERC-wide, class-level** statistical benchmark
(generator technology × nameplate-size band) — it carries no ISO-specific or per-year
realized-dispatch/price information that could leak into backcast tuning, and it is not
wired into any model code path (intake only, no constant/offer-curve/availability input
changed). Authorization for this intake is the user's own task instruction ("collect and
download remaining NERC GADS EFORd benchmarks to cover full 2018-2026 data where
available"). Validation performed was no-LP structural/byte checks only (row counts,
header column-name matching, cross-window continuity checks against the existing
`2019-2023` intake) — no dispatch solve, no scoring against any year.

---

## Headline gaps (2018-2022 / H1-2026 edges)

- **2018-2020, most sources:** on-disk coverage before 2021-2022 is effectively limited to CAMPD
  unit-level CEMS (all states, 2018-2021), Henry Hub gas prices, and the EIA-930 hourly wide files
  for ERCOT/NEISO/NYISO only (which happen to reach back to mid-2015). PJM/CAISO/MISO's EIA-930
  wide files start 2019-01-01. Almost nothing else in the register — LMP, AS, HSL/curtailment, zonal
  demand, weather, gas-hub series, PJM/MISO gen-by-fuel — reaches earlier than 2020 for any ISO.
- **2022 (holdout year):** genuinely bifurcated by rule-22 authorization status. ERCOT and PJM
  (and, as of 2026-07-07, NEISO for CAMPD only) have it across most gated datatypes; CAISO, MISO,
  and NYISO do not (MISO/NYISO's apparent 2022 CAMPD coverage is a side effect of state overlap
  with PJM/ERCOT's own intake, not their own).
- **H1-2026:** ERCOT and PJM again lead (EIA-930, CAMPD Q1, gas price partials, gen-by-fuel); CAISO
  and MISO have essentially nothing past 2025-12-31 in this repo.
- **Weather is the one universal gap:** capped to 2023-2025 for all six ISOs regardless of ISO
  holdout-authorization status.
