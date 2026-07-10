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
| 49 | NERC GADS EFORd benchmarks | NERC | Class-level forced-outage-rate prior | `data/raw/reference/nerc-gads-eford-2019-2023/` | Both |
| 50 | Master plant registry / CAMPD bin assignments / LCR-area membership | Curated crosswalks (EIA-860 + CAMPD + county rules) | Plant→zone assignment, ERCOT tranche crosswalk, CAISO LCR area membership | `data/raw/reference/master-plant-registry.csv`, `custom-bin-assignments.csv`, `lcr_area_membership_CAISO.csv` | Both |
| 51 | NYISO NYCA Renewables presentation (annual wind/FTM-solar curtailment) | NYISO Operations Analysis & Services (ICAPWG/MIWG decks, nyiso.com/reports-information) | Coarse NYCA-wide + 4-zone (West/Central/North/Mohawk Valley) annual and monthly curtailed-energy aggregate — a labeled diagnostic, NOT an hourly per-plant HSL series (see row 27's ERCOT/CAISO analog, which NYISO has no equivalent of) | `data/raw/nyiso-renewable-curtailment/nyiso_curtailment_{annual,monthly}.csv` | Backcast-only (diagnostic; not fed to dispatch) |

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
| PJM (`PJM hourly.parquet`) | ✓ (H2 only, phased rollout) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (thru Jun 30) |
| CAISO (`CISO hourly.parquet`) | ✓ (H2 only) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (thru Jun 30) |
| MISO (`MISO hourly.parquet`) | ✓ (H2 only) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (thru Jun 30) |

Verified directly (file min/max timestamp): ERCO/ISNE/NYIS wide files start 2015-07-01;
PJM/CISO/MISO now start 2018-01-01 (backfilled 2026-07-08 via the BALANCE bulk archive — 2018 H1
carries demand/net-generation/interchange only, since EIA-930 per-fuel reporting hadn't started
yet for any of the three; PJM's own per-fuel reporting ramps up gradually across 2018 H2). CISO/MISO
now reach H1-2026 (landed 2026-07-08, same BALANCE-archive fold). The `eia-930/` long-form
supplemental files (per-BA `fueltype`/`region_<year>.parquet`) confirm 2022 and H1-2026 rows now
exist for ERCOT, PJM, **and (as of 2026-07-08) CAISO/MISO** — `api.eia.gov` was re-confirmed
reachable with the repo's configured `EIA_API_KEY` (the earlier "blocked" assessment was stale for
this session). The parallel `eia-930` BALANCE half-year 2022 files remain degenerate for CISO/MISO
specifically (9 and 7 hours respectively — a real EIA archive gap for that product, not fetchable
around); the long-form intake above is the usable 2022 source for those two.

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
| ERCOT HSL | blocked — Data Portal login wall (see `ercot-hsl/README.md`, 2026-07-10) | ✓ (3rd-party UMass reconstruction, no ERCOT upload exists) | ✓ | ✓ | blocked — same Data Portal wall |
| ERCOT NP6 monthly source archives | — | — | ✓ (near-complete monthly) | ✓ (near-complete monthly) | — |
| CAISO HSL / curtailment workbooks | 2018-2022 verified fetchable at source, not committed — see caveat below (2026-07-10) | ✓ | ✓ | ✓ | discontinued by CAISO 6/1/2025, confirmed unfetchable |
| NYISO / MISO hourly per-plant HSL | — | — | — | — | — |
| NYISO NYCA-wide + zonal curtailment aggregate (row 51) | partial — NYCA wind annual+monthly 2018-2022 (2017 also on file); zonal wind annual+monthly 2020-2022 only; no solar | ✓ NYCA+zonal wind; FTM solar GWh only (no pct) | ✓ NYCA wind only — no standalone 2024 deck was found, so no zonal/monthly breakdown; solar with pct | ✓ NYCA+zonal wind; FTM solar with pct | — (no deck published yet) |
| MISO wind-shape (reanalysis) | — | ✓ | ✓ | ✓ | — |
| MISO wind curtailment aggregate (Potomac IMM, `data/raw/miso-hsl/`, not a numbered register row) | ✓ 2018-2022 (annual figures; 2018-2020 have no curtailment MW at all — a genuine SOM-report gap, not an extraction miss) | ✓ | ✓ | ✓ | Winter+Spring 2026 quarterly only |

NYISO/MISO hourly per-plant HSL directories remain empty (documented `DATA NEEDED`: NYISO does not
publish an hourly per-plant uncurtailed-potential series at all — see the new coarse-aggregate row
above, landed 2026-07-08 from the NYCA Renewables presentation series
(`data/raw/nyiso-renewable-curtailment/README.md`), which is the closest primary-source substitute
but stays a NYCA-wide/zonal annual-and-monthly diagnostic, never ingested as dispatch HSL; MISO's
curtailment reports are blocked by this environment's network allowlist).

**2026-07-10 holdout-intake session (rule-22 pre-authorized):**

- **ERCOT HSL 2018-2022 + H1-2026 — confirmed ungettable, not just unattempted.** ERCOT's Data
  Access Portal is a JS SPA behind Incapsula bot-protection requiring sign-in for any historical
  archive (302-redirect on `data.ercot.com/data-product-archive/NP4-732-CD`; the live rolling-window
  API returns an empty listing for this report type). Same wall already documented for NP6-86 and
  for the 2024/2025 HSL data itself (pulled by hand via an `apiexplorer.ercot.com` account). The
  UMass fallback used for 2023 is confirmed 2023-only by construction (cloned the dataset directly —
  its `data/` holds only `*-2023.csv` files); extending it to other years is a new per-plant
  reconstruction project, not a fetch.
- **CAISO HSL/curtailment 2018-2022 — verified fetchable, not committed.** All five years' source
  workbooks (`productionandcurtailmentsdata_<year>.xlsx`) fetched and verified as genuine, full
  Jan1-Dec31 workbooks at the same stable URL already used for 2023-2025 (also corrected the
  register's stale source URL — `library/managing-oversupply` now 404s; the live page is
  `library/production-curtailments-data`). Building the derived HSL series
  (`scripts/build_caiso_hsl.py`) against them: **2019-2021 built clean** (committed as
  `data/raw/caiso-hsl/caiso_<year>_hsl_hourly.csv` — CSV, not parquet, because this session's only
  available push mechanism cannot transport binary content without corruption; see
  `data/raw/caiso-hsl/README.md`); **2018 flagged, not committed** — its derived wind total (24.9
  TWh) is 60%+ above every neighboring year in the wrong direction (CAISO wind buildout only grew),
  traced to a pre-existing `eia_loader.load_eia_hourly_renewable_gen` bfill/ffill artifact that
  flat-fills the entire missing-H1 CISO per-fuel window rather than genuinely measuring it — a
  discovered defect, not something this intake papers over; **2022 confirmed genuinely
  unavailable** by the builder's own no-full-year-EIA-930 check. **H1-2026 confirmed unfetchable**:
  CAISO's own library page states the report was discontinued 2025-06-01. The raw xlsx workbooks
  themselves (~118MB across 5 years) were not committed for the same binary-transport reason —
  re-fetch from the unchanged, unauthenticated URL to regenerate them.
- **MISO wind aggregate 2018-2020 — already complete, no new fetch needed.** Verified
  `data/raw/miso-hsl/miso_wind_curtailment_annual.csv` already carries cited 2018-2025 rows (landed
  in an earlier session, before this one); this session only confirmed it, did not add to it.

### Ancillary services / reserves

| Source | 2018-2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|
| ERCOT-AS | — | ✓ | ✓ | ✓ | — |
| PJM-AS | — | ✓ | ✓ | ✓ | — |
| MISO-AS | 2022 confirmed **ungettable** (see note) | ✓ | ✓ | ✓ | — |
| NYISO-AS (DA/RT clearing) | — | ✓ | ✓ | ✓ | — |
| NYISO measured hourly reserve requirements (Ask B) | — | not independently confirmed present — flagged unresolved in source docs | | | |

**MISO-AS 2022 — confirmed ungettable, not just unattempted (2026-07-09).** All three per-day
report endpoints `scripts/fetch_miso_asm.py` reads (`asm_exante_damcp`, `asm_rtmcp_final`,
`asm_rt_co`) return genuine `BlobNotFound` from `docs.misoenergy.org` for every day of 2022
(1,095/1,095 requests), while the identical URL pattern is HTTP 200 starting exactly 2023-01-01 —
this is a **rolling retention purge**, not a naming/format change: a 2021-08-14 `asm_rt_co.zip`
that Wayback Machine had crawled as HTTP 200 in March 2024 is now *also* 404 on the live host,
confirming MISO ages out old daily report files. Checked and ruled out: 5 legacy report-name
variants (`asm_expost_damcp`, `asm_rtmcp_prelim`, etc.) across 2022 — all 404; a consolidated
annual `_HIST` rollup (the pattern MISO uses for some other datasets, e.g. `2019_da_bc_HIST.csv`)
— no ASM equivalent exists; Wayback Machine CDX search for all three report types across all of
2022 — zero captures, so no archive-recoverable copy either. MISO's official API platform
(`data-exchange.misoenergy.org`) doesn't bypass this: it requires account registration we don't
have, and MISO's own FAQ states historical data beyond a "limited online retention window"
requires a manual Help Center/ITOC request — i.e. the API reads the same live store, not a deeper
archive. The only remaining path is a human-filed MISO historical-data request (ITOC
1-866-296-6476 opt. 1, or `help.misoenergy.org`); not something a fetch script or API credential
can resolve. Do not re-attempt an automated fetch for this year without new information.

### Fuel — EIA-923 delivered cost & generation, coal/gas derivations

| Source | 2018-2021 | 2022 | 2023 | 2024 | 2025 | H1 2026 |
|---|---|---|---|---|---|---|
| `eia923_monthly_fuel_costs.parquet` / `_generation.parquet` | ✓ (landed 2026-07-08, all 6 ISOs — `f923_2018.zip`…`f923_2021.zip`, merged via `process_f923_fuel_costs.py --merge-years --include-generation`) | ✓ (all 6 ISOs, all 12 months — direct file check 2026-07-08 corrected the prior "ERCOT+PJM only" entry, which was stale) | ✓ | ✓ | ✓ | Jan–Apr (all 6 ISOs — direct file check 2026-07-08 corrected the prior "ERCOT+PJM only" entry; May–Jun genuinely unreleased by EIA yet, not a fetch gap) |
| Parasitic load factors | source gap closed (F923 2018-2021 above); re-derive (`derive_parasitic_load.py --years 2018 2019 2020 2021`) not yet run — 2018-2021 v2 rows still use the documented pooled-factor fallback | +ERCOT/PJM (564 rows) | ✓ | ✓ | ✓ | deferred (CAMPD/F923 window mismatch) |
| Gas/coal take-or-pay derivations | — (out of scope for the 2026-07-08 923/860 intake; `derive_coal_takeorpay.py`/`derive_gas_takeorpay.py` per-ISO reruns not done) | — | ✓ | ✓ | ✓ | — |

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

- **EIA-860 fleet snapshots** — vintage releases, not a per-year series: **2018, 2019, 2020, 2021,
  2022, 2023, 2024, 2025** vintages on disk (2018/2019/2021/2022 landed 2026-07-08, data-register
  intake — closes the pre-2020 vintage gap; no 2026 vintage yet, since EIA has not published the
  calendar-2025 annual release).
- **EPA eGRID** — vintage releases: **2022, 2023, 2024** (2022 is a true 2022-vintage workbook,
  landed 2026-07-04; previously the model stood in the 2024 vintage for 2022).
- **Confirmed-retirements registry** — forward-looking events (`exit_year >= 2023`); not a
  historical coverage question.
- **RGGI allowance schedule / CARB cap schedule** — forward regulatory compliance-year tables.
- **NYSDEC 227-3 peaker compliance, NERC GADS EFORd (2019-2023 only, no 2018/2024+), master
  plant registry, CAMPD bin assignments, LCR-area membership** — static crosswalks/benchmarks, not
  time series.
- **NEISO winter fuel-security inventory** — hand-curated from ISO-NE's 2018 OFSA study and
  2018-2020 ESI filings; a fixed planning-study snapshot, not a rolling measured series.

---

## Headline gaps (2018-2022 / H1-2026 edges)

- **2018-2020, most sources:** on-disk coverage before 2021-2022 is effectively limited to CAMPD
  unit-level CEMS (all states, 2018-2021), Henry Hub gas prices, EIA-923 delivered fuel
  cost/generation and EIA-860 fleet vintages (all closed 2026-07-08, data-register intake), and the
  EIA-930 hourly wide files for ERCOT/NEISO/NYISO (mid-2015 on) plus, as of 2026-07-08,
  PJM/CAISO/MISO (2018 H2 on for per-fuel columns; demand/net-gen/interchange-only for 2018 H1, a
  real source gap — see the EIA-930 section above). Almost nothing else in the register — LMP, AS,
  HSL/curtailment, zonal demand, weather, gas-hub series, PJM/MISO gen-by-fuel — reaches earlier
  than 2020 for any ISO.
- **2022 (holdout year):** genuinely bifurcated by rule-22 authorization status. ERCOT, PJM, and
  (as of 2026-07-08) CAISO/MISO have EIA-930 (fuel-mix bench + demand); CAMPD, LMP, gas-hub, and
  other gated datatypes remain ERCOT/PJM-only (and, as of 2026-07-07, NEISO for CAMPD only) — CAISO/
  MISO/NYISO do not have those (MISO/NYISO's apparent 2022 CAMPD coverage is a side effect of state
  overlap with PJM/ERCOT's own intake, not their own).
- **H1-2026:** ERCOT and PJM lead on CAMPD Q1, gas price partials, and gen-by-fuel; EIA-930 itself
  now reaches H1-2026 for ERCOT, PJM, CAISO, **and MISO** (landed 2026-07-08) — CAISO/MISO still
  have essentially nothing past 2025-12-31 for the other (CAMPD/gas/outage) datatypes in this repo.
- **Weather is the one universal gap:** capped to 2023-2025 for all six ISOs regardless of ISO
  holdout-authorization status.
