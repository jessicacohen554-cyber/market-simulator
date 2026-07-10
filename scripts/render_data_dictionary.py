#!/usr/bin/env python
"""Render ``data/dictionary/data-dictionary.md`` deterministically.

The data dictionary is a generated artifact, not a hand-maintained document.
Two sources feed it, and only these:

* **Per-column tables** come from the canonical schema YAMLs under
  ``data/dictionary/schema/`` (the source of truth — name, dtype, unit,
  nullability, description). Change a column there and re-render; never edit the
  table here.
* **The ISO x year coverage matrix** comes from the ``market_sim.*`` provenance
  metadata embedded in each ``data/clean`` Parquet file (``iso`` / ``year`` /
  ``datatype``), read through :func:`scripts.lib.clean_io.read_clean_metadata`.
  Regenerate the clean tree first with ``python scripts/regenerate_clean.py``;
  the matrix then reflects exactly what landed on disk.

The narrative scaffold around those two — each datatype's one-line purpose and
its "Reconciles" note — lives in :data:`NARRATIVE` below, so the whole document
is reproducible from this script plus the schemas plus the clean tree.

Usage
-----
    python scripts/render_data_dictionary.py            # write the doc
    python scripts/render_data_dictionary.py --check    # exit 1 if out of date
    python scripts/render_data_dictionary.py --stdout    # print, don't write

A companion test (``tests/test_data_dictionary_sync.py``) asserts the committed
doc equals a fresh render.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from collections import defaultdict
from pathlib import Path

# Allow running as a plain script (``python scripts/render_data_dictionary.py``)
# as well as a module — clean_io lives in the ``scripts`` package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.lib import clean_io  # noqa: E402
from market_sim.config import paths  # noqa: E402

DOC_PATH: Path = paths.DICTIONARY_DIR / "data-dictionary.md"

# ISO columns of the coverage matrix, in the project's canonical order.
ISO_ORDER: tuple[str, ...] = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

# Datatype sections, in render order. Mostly mirrors scripts/regenerate_clean.DATATYPES,
# plus `energy-offers`, which ships a schema but is curated by a dedicated pipeline
# (scripts/fetch_pjm_energy_offers.py → scripts/curate_energy_offers.py) rather than
# the generic regenerate path. This tuple must cover every data/dictionary/schema/*.yaml
# (enforced by tests/test_data_dictionary_sync.py).
DATATYPE_ORDER: tuple[str, ...] = (
    "lmp",
    "load",
    "demand-profile",
    "ancillary-services",
    "energy-offers",
    "generation",
    "renewables",
    "emissions",
    "emissions-unit-annual",
    "outages",
    "validation",
    "fleet",
    "fuel-prices",
    "fuel-hub-monthly",
    "fuel-basis",
    "fuel-zonal-hub",
    "fuel-ercot-ep-gas",
    "fuel-takeorpay",
    "reference",
    "border-lmp",
    "zonal-shares",
    "weather",
    "egrid",
    "unit-outage-events",
    "partial-outages",
    "capacity-deliverability",
    "confirmed-retirements",
    "gtc-limits",
    "ramp-capability",
    "winter-fuel-inventory",
    "rggi-co2-budgets",
    "carb-cap-schedule",
    "chp-btm-share",
    "nyiso-downstate-gas",
    "ercot-wtx-congestion",
    "nyiso-renewable-curtailment",
    "nyiso-renewable-curtailment-monthly",
    "coal-basin-price",
    "coal-mining-ppi",
    "nyiso-reserve-requirements",
    "nyiso-operating-events",
    "nyiso-interface-flows",
    "nyiso-som-hub-fuel-annual",
)

# Per-datatype narrative scaffold. ``summary`` is the one-line purpose under the
# heading; ``reconciles`` is the "what raw layouts fold into this" note. ``keys``
# overrides the schema key list only where the prose says more than the schema
# (reference). Everything else — the per-column table, the key list — is derived.
NARRATIVE: dict[str, dict[str, str]] = {
    "lmp": {
        "summary": "Locational marginal prices and components.",
        "reconciles": (
            "CAISO `LMP/MCC/MCE/MCL/MGHG`, PJM `DA_LMP/RT_LMP`, NYISO LBMP "
            "components, ERCOT settlement-point price, NEISO SMD hub LMP — into "
            "one total `lmp_usd_per_mwh` plus energy/congestion/loss/ghg "
            "components, with DA vs RT carried in the `market` key."
        ),
    },
    "load": {
        "summary": "Hourly demand and forecast by zone.",
        "reconciles": (
            "CAISO TAC-area `mw`, NYISO `Load`, EIA-930 `Demand` / "
            "`Demand forecast` — into `load_mw`, `load_forecast_mw`, optional "
            "`net_load_mw`."
        ),
    },
    "demand-profile": {
        "summary": (
            "Repaired legacy EIA-930 per-ISO system-total hourly demand "
            "(hour-of-year clock, no zone breakdown)."
        ),
        "reconciles": (
            "The raw `eia_demand_profiles.parquet` extract's `raw_mw` / "
            "`normalized`, repaired via a physical-bounds screen (value <= 0, "
            "or > 5x the (iso, year) series median) plus linear interpolation "
            "-- the sole demand source `eia_loader.load_demand` falls back to "
            "for any (iso, year) with no dedicated per-BA hourly extract "
            "(every PJM year; CAISO/MISO 2021-2022). `repaired` flags the "
            "corrected hours."
        ),
    },
    "ancillary-services": {
        "summary": "AS clearing prices and cleared quantities.",
        "reconciles": (
            "NYISO `spin_10/nonsync_10/op_30/reg_cap`, PJM long "
            "`ancillary_service/value`, ERCOT `REGUP/REGDN/RRS/ECRS/NSPIN`, "
            "CAISO `RU/RD/SR/NR` — onto a common product taxonomy (reg up/down, "
            "spin, nonspin, 30-min supplemental), prices in `$/MW`."
        ),
    },
    "gtc-limits": {
        "summary": (
            "Measured ERCOT Generic Transmission Constraint hourly limits "
            "(stability-limited export interfaces)."
        ),
        "reconciles": (
            "ERCOT NP6-86-CD SCED shadow-price / binding-constraint CSVs "
            "(~5-min) — filtered to GTC rows (empty `FromStation`) and "
            "aggregated to the fixed non-leap 8760-hour ERCOT-local clock as "
            "per-(gtc, hour) mean/min enforced limit, active/binding interval "
            "counts, and mean positive shadow price. Sparse: a row exists only "
            "for hours the constraint was in SCED's active set. ERCOT-only "
            "(published physical transfer limits, rule #13/#14 admissible)."
        ),
    },
    "ercot-wtx-congestion": {
        "summary": (
            "Measured ERCOT West Texas Export corridor transmission-congestion "
            "pressure (hourly) — the VRE curtailment-share driver's shape source."
        ),
        "reconciles": (
            "ERCOT NP6-86-CD SCED binding constraints geo-attributed to the West "
            "Texas Export wind corridor via ERCOT's authoritative Settlement "
            "Points List / electrical-bus load-zone mapping (NP4-160): a binding "
            "row counts when either station is in the LZ_WEST settlement zone or "
            "the constraint is the WESTEX/PNHNDL export GTC. Aggregated to the "
            "fixed non-leap 8760-hour ERCOT-local clock as per-hour SCED-execution "
            "and West-binding counts, congestion fraction, interface-only "
            "fraction, and mean positive West shadow price (dense). ERCOT-only "
            "(measured congestion incidence, rule #13/#14 admissible — never the "
            "reported curtailment volume)."
        ),
    },
    "winter-fuel-inventory": {
        "summary": (
            "Forward-derivable oil-burn budget drivers for the winter "
            "fuel-constrained fleet (Nov–Mar seasonal scarcity)."
        ),
        "reconciles": (
            "EIA-860 per-plant `Net Winter Capacity with Oil (MW)` (multifuel) "
            "and `Firing Rate Using Petroleum` (boiler design) — derived "
            "programmatically — unioned with hand-curated ISO-NE study/program "
            "figures (OFSA 2018 tank autonomy / fill rate / LNG caps; Winter "
            "Reliability Program oil-inventory targets; Mystic retention) onto "
            "one tidy `(entity, entity_type, season, metric, value, unit)` "
            "frame. Physical/logistics INPUTS only — never measured burn/"
            "delivery outcomes (F923 receipts are excluded by design)."
        ),
    },
    "rggi-co2-budgets": {
        "summary": (
            "RGGI regional/per-state CO2 allowance budgets and the "
            "price-control-band trigger-price schedule."
        ),
        "reconciles": (
            "RGGI, Inc. Allowance Distribution tables (regional + per-member-"
            "state annual budgets, short tons) and the 2017 Model Rule Cost "
            "Containment Reserve / Emissions Containment Reserve / minimum-"
            "reserve trigger prices onto one tidy `(state, budget_year, metric, "
            "value, unit)` frame. The budget feeds the optional power-sector "
            "mass-cap row (a scenario, no-bank instrument — NOT the RGGI market "
            "price); the trigger prices feed the projected forecast "
            "allowance-price band. Never intake 2022/H1-2026 (rule 22)."
        ),
    },
    "carb-cap-schedule": {
        "summary": (
            "CARB cap-and-trade annual allowance budget and Auction Reserve "
            "floor-price schedule."
        ),
        "reconciles": (
            "CARB Cap-and-Trade Regulation §95841 annual allowance budgets (MMT "
            "CO2e) and the §95911(c) Auction Reserve (floor) price with its 5% + "
            "CPI escalation onto one tidy `(budget_year, metric, value, unit)` "
            "frame. The budget feeds the optional power-sector mass-cap row (a "
            "scenario, no-bank instrument — NOT the CARB market price); the "
            "floor escalator feeds the projected forecast allowance price for "
            "CAISO. Never intake 2022/H1-2026 (rule 22)."
        ),
    },
    "chp-btm-share": {
        "summary": (
            "Measured per-plant CHP behind-the-meter host self-supply share "
            "(replaces the sector-keyed chp_btm_pct default for forecast years)."
        ),
        "reconciles": (
            "The committed `plant_emission_rates_v2` (CAMPD CEMS grid-net "
            "generation, steam-reporting units only) and "
            "`eia923_monthly_generation` (EIA-923 Page-1 net class generation) "
            "processed-legacy artifacts — into one "
            "`btm_share = (eia923_net_mwh - campd_net_mwh) / eia923_net_mwh` per "
            "(iso, plant, CHP class), pooled across every available "
            "non-quarantined year. Consumed by "
            "`market_sim.data.chp.measured_btm_share_by_plant` for forecast-year "
            "CHP must-run sizing only; the backcast `_btm_frame` path is "
            "untouched. Never intake 2022/H1-2026 (rule 22)."
        ),
    },
    "nyiso-downstate-gas": {
        "summary": (
            "Daily downstate NYISO delivered-gas index, per zone, for the "
            "non-firm LM6000 CT-peaker fleet (NYC zone J + Long Island zone K)."
        ),
        "reconciles": (
            "The measured Transco Zone 6 NY pipeline-hub daily spot "
            "(`transco_z6_ny_daily.csv`, the peaker's own commodity), Henry Hub "
            "daily (`henry_hub_daily.csv`, provenance), and the measured monthly "
            "per-LDC non-firm transportation delivery rate "
            "(`nyiso_downstate_ldc_transport_monthly.csv`: KEDNY SC-22 for NYC, "
            "KEDLI SC-19 for Long Island) — into one daily series per zone "
            "`delivered_gas = transco_z6_ny_daily + ldc_transport_adder_month`, "
            "interpolated to every calendar day. Each component is a measured, "
            "forward-native market/tariff input (rule-13); nothing fitted to a "
            "residual. This v2 per-zone transport construction supersedes the v1 "
            "statewide EIA-citygate premium (the interruptible peakers are "
            "transport customers). Consumed by "
            "`market_sim.data.fuel.apply_nyiso_downstate_ct_gas_daily` to "
            "re-ground the downstate CT-peaker offer level."
        ),
    },
    "nyiso-renewable-curtailment": {
        "summary": (
            "NYISO's coarse annual NYCA-wide + 4-zone wind/FTM-solar "
            "curtailment aggregate — a labeled diagnostic, not an hourly HSL "
            "series (NYISO publishes no per-plant uncurtailed-potential data)."
        ),
        "reconciles": (
            "Hand-transcribed from NYISO's annual NYCA Renewables presentation "
            "series (ICAPWG/MIWG decks, nyiso.com/reports-information): "
            "NYCA-wide annual curtailed GWh + percent-of-production for wind "
            "(2017-2025) and FTM solar (2022-2025), plus zonal (West/Central/"
            "North/Mohawk Valley) annual wind curtailed GWh for the years each "
            "deck reports its own current year (2020-2023, 2025 — no "
            "standalone 2024 deck was found). See "
            "`data/raw/nyiso-renewable-curtailment/README.md` for exact source "
            "URLs and documented gaps. Read by "
            "`market_sim.data.nyiso_renewable_curtailment`; not consumed by "
            "dispatch."
        ),
    },
    "nyiso-renewable-curtailment-monthly": {
        "summary": (
            "Monthly companion to `nyiso-renewable-curtailment`: NYCA-wide "
            "percent-of-production (wind) and zonal curtailed GWh, by month."
        ),
        "reconciles": (
            "Same source decks as `nyiso-renewable-curtailment`: NYCA-wide "
            "monthly wind curtailment percent (2017-2025, cross-checked across "
            "overlapping decks) and zonal monthly curtailed GWh for the years "
            "with a published zonal breakdown (2020-2023, 2025). Read by "
            "`market_sim.data.nyiso_renewable_curtailment`; not consumed by "
            "dispatch."
        ),
    },
    "ramp-capability": {
        "summary": (
            "Measured per-plant 10-minute ramp / fast-start capability inputs "
            "for the per-generator reserve co-optimization."
        ),
        "reconciles": (
            "EIA-860 Schedule 3.1 `Time from Cold Shutdown to Full Load` "
            "(the `10M` fast-start category → `fast_start_mw` over the plant's "
            "thermal nameplate `thermal_nameplate_mw`) and EPA CAMPD CEMS "
            "hourly unit gross load (the maximum observed 1-hour plant-level "
            "up-ramp → `ramp_up_1h_mw`, plus `observed_pmax_mw` and "
            "`hours_observed`) — reconciled per plant (EIA plant code = CAMPD "
            "facilityId) onto one tidy frame, pooled 2023-2025 (holdouts "
            "excluded, rule 22). Per-ISO scoping is the balancing-authority "
            "spec in `scripts/lib/ramp_capability/<iso>.py` (PJM, MISO, CAISO). "
            "Consumed as the measured ceiling on the class-rate estimate feeding "
            "`FleetArrays.ramp10`, the 10-minute reserve-deliverability bound."
        ),
    },
    "energy-offers": {
        "summary": "PJM Real-Time effective energy offer curves (long step form).",
        "reconciles": (
            "PJM DataMiner2 `energy_market_offers` wide `mw1..mw20`/`bid1..bid20` "
            "breakpoints (plus daily `avg_ecomin`/`avg_ecomax`, no-load and "
            "hot/cold/inter start costs) — pivoted to one row per "
            "(`unit_code` × operating-hour × `step_idx`) with `step_mw` / "
            "`step_price_usd_per_mwh`. PJM-only; unit identity is anonymised and "
            "rotated annually (not joinable across calendar years)."
        ),
    },
    "generation": {
        "summary": "Generation by fuel (long form).",
        "reconciles": (
            "EIA-930 wide `NG: *` fuel columns (unpivoted), PJM "
            "`fuel_type/mw/is_renewable`, CAISO technology buckets."
        ),
    },
    "renewables": {
        "summary": "Renewable output, availability (HSL) and curtailment.",
        "reconciles": (
            "CAISO/ERCOT HSL `wind_gen_mw/wind_hsl_mw/solar_*` (unpivoted), "
            "CAISO curtailment — into `generation_mw`, `hsl_mw`, "
            "`curtailment_mw`."
        ),
    },
    "emissions": {
        "summary": "Hourly CEMS/CAMPD emissions by plant/unit.",
        "reconciles": (
            "CAMPD facility- and unit-level "
            "`co2Mass/noxMass/so2Mass/heatInput/grossLoad` — masses "
            "standardized to `*_kg`, heat input to MMBtu."
        ),
    },
    "emissions-unit-annual": {
        "summary": (
            "Annual unit-level CAMPD roll-up (one row per plant/unit/year) — "
            "the forward per-plant CO2-rate estimator's input."
        ),
        "reconciles": (
            "The hourly unit-level CAMPD extracts (`data/raw/campd-unit-level`) "
            "rolled up to annual `gross_mwh`, `heat_mmbtu`, `co2/nox/so2_kg` "
            "(kg), `op_hours`, `starts`, plus `co2_source` / `mw_source` "
            "provenance flags. Curated by `curate_emissions_unit_annual.py`; the "
            "quarantined 2022/H1-2026 years are hard-skipped (rule 22)."
        ),
    },
    "outages": {
        "summary": "Generator outages / available capacity.",
        "reconciles": (
            "CAMPD-derived downtime, ERCOT curated unit-outage lists — into "
            "`outage_mw` / `available_mw`."
        ),
    },
    "validation": {
        "summary": "Calibration/validation reference targets (tidy long form).",
        "reconciles": (
            "heterogeneous `_validation-source` benchmark files (renewable "
            "capacity, generation, emissions, price) into `(dimensions → "
            "metric, value, unit)`."
        ),
    },
    "fleet": {
        "summary": "Generator fleet registry.",
        "reconciles": (
            "EIA-860 (`Plant Code`, `Generator ID`, `Nameplate Capacity "
            "(MW)`, …), master plant registry, eGRID — into snake_case + "
            "unit-suffixed columns."
        ),
    },
    "fuel-prices": {
        "summary": "Delivered fuel price benchmarks.",
        "reconciles": (
            "Henry Hub daily `price_usd_mmbtu`, citygate/basis benchmarks — "
            "into `price_usd_per_mmbtu` by `fuel`/`hub`."
        ),
    },
    "fuel-hub-monthly": {
        "summary": "Monthly Henry Hub spot averages (EIA RNGWHHDm).",
        "reconciles": (
            "`henry_hub_monthly.csv` `price_usd_mmbtu` — into "
            "`price_usd_per_mmbtu` keyed by `fuel`/`hub`/`year`/`month`."
        ),
    },
    "fuel-basis": {
        "summary": "Per-ISO monthly gas basis vs Henry Hub (winter hub overlay).",
        "reconciles": (
            "`gas_basis_by_iso_month.csv` `basis_usd_mmbtu` (Algonquin for "
            "NEISO, Transco Z6/Iroquois for NYISO when filled) — `source` "
            "column stripped; keyed by `iso`/`year`/`month`/`hub`."
        ),
    },
    "fuel-zonal-hub": {
        "summary": "Per-ISO zonal gas-hub annual prices/basis.",
        "reconciles": (
            "ERCOT/PJM/MISO `basis_vs_hh_usd_mmbtu`; NYISO absolute "
            "`hub_usd_mmbtu`; ERCOT West `neg_day_freq` — keyed by "
            "`iso`/`zone`/`year`/`hub`, ISO-partitioned by directory."
        ),
    },
    "fuel-ercot-ep-gas": {
        "summary": "Monthly EIA N3045TX3 TX delivered-to-electric-power gas price ($/Mcf).",
        "reconciles": (
            "`ercot_electric_power_gas_price.csv` `price_usd_mcf` — `source` "
            "column stripped; keyed by `year`/`month`."
        ),
    },
    "fuel-takeorpay": {
        "summary": "ERCOT per-plant EIA-923 gas spot vs contract share.",
        "reconciles": (
            "`gas_takeorpay_ERCOT.csv` — retains `plant_code`, `spot_share`, "
            "`total_mmbtu`; strips `contract_share`, `n_receipts`, `source`, "
            "`breakdown`."
        ),
    },
    "reference": {
        "summary": "Crosswalk / lookup tables (heterogeneous).",
        "reconciles": (
            "master plant registry, bin assignments, zone/node crosswalks — "
            "conventions enforced, table-specific columns permitted."
        ),
        "keys": "`key` (+ `plant_id`/`iso`/`zone`/`node` when applicable)",
    },
    "border-lmp": {
        "summary": "Measured neighbor-border hourly Day-Ahead LMP.",
        "reconciles": (
            "CAISO OASIS WECC intertie LMP (MALIN, PALOVRDE), PJM hub LMP "
            "(CHICAGO GEN / AEP GEN / ATSI GEN equal-weight mean for MISO "
            "PJM_WEST) — on the model's fixed non-leap 8760-hour local-year "
            "calendar, dense `price` (NaN for gaps)."
        ),
    },
    "zonal-shares": {
        "summary": "Hourly zonal load share fractions (per ISO, per year).",
        "reconciles": (
            "PJM metered-load CSV (20 real zones → 8 model zones), ERCOT "
            "native-load XLSX (8 weather zones → 6 model zones), CAISO "
            "TAC-area CSV (4 areas → 3 trading-hub zones), MISO EIA-930 "
            "sub-BA CSV (6 sub-BAs → 3 model zones), NYISO pal CSV "
            "(11 settlement zones → 5 model zones), NEISO SMD wide CSV "
            "(8 load zones → 4 model zones) — into `share` fractions "
            "summing to ≈1.0 per hour, long format `(hour, zone, share)`. "
            "Files are ISO-partitioned by directory path "
            "(`data/clean/zonal-shares/<ISO>/`)."
        ),
    },
    "weather": {
        "summary": "Daily maximum and minimum temperature by model zone.",
        "reconciles": (
            "Per-ISO NOAA GHCN-Daily TMAX/TMIN CSVs (zone-level files plus "
            "load-weighted ISO aggregates for CAISO and NEISO, NYC-metro "
            "aggregate for NYISO) — into one `(date, zone, tmax_c, tmin_c)` "
            "row per zone per calendar day. Sentinel zones: `_load_weighted` "
            "(CAISO, NEISO ISO-level aggregate), `_downstate` (NYISO "
            "NYC-metro). Files are ISO-partitioned by directory path "
            "(`data/clean/weather/<ISO>/`)."
        ),
    },
    "egrid": {
        "summary": "eGRID plant-level extract (location, BA, fuel/CO2 columns).",
        "reconciles": (
            "EPA eGRID workbook plant sheet (`PLNT<YY>`) `ORISPL/LAT/LON/"
            "FIPSST/FIPSCNTY/BACODE/PLFUELCT/PLNGENAN/PLCO2AN` — the union of "
            "what `zone_assignment.py` (geography) and `egrid.py` (fossil CO2 "
            "rate) each need, unfiltered, one file per eGRID vintage year."
        ),
    },
    "unit-outage-events": {
        "summary": ("Per-unit CAMPD outage events (one row per detected window)."),
        "reconciles": (
            "`campd-unit-outages.csv` (ERCOT) / `campd-unit-outages-<ISO>.csv` "
            "(CAISO/MISO/NEISO/NYISO/PJM) — event grain (not hourly-expanded), "
            "`iso` stamped at curation."
        ),
    },
    "partial-outages": {
        "summary": "Per-plant CAMPD CF-ceiling partial-outage derate windows.",
        "reconciles": (
            "`campd-partial-outages.csv` (ERCOT) — a multiplicative "
            "availability `derate_factor` per detected window, `iso` stamped "
            "at curation."
        ),
    },
    "capacity-deliverability": {
        "summary": (
            "Per-capacity-area locational capacity requirements and "
            "import/export transfer limits by delivery period."
        ),
        "reconciles": (
            "PJM CETO/CETL, MISO LRR/LCR/CIL/CEL/ZIA/PRMR, NYISO ICAP-req/"
            "LCR%/Bulk-Power-Transmission-Limit/IRM, ISO-NE LSR/MCL/interface "
            "import limit/ICR, CAISO LCR `Capacity Needed`/Maximum Import "
            "Capability/PRM — onto one canonical metric vocabulary "
            "(`requirement`, `import_limit`, `export_limit`, "
            "`local_clearing_requirement`, `import_ability`, "
            "`system_requirement`), long form keyed by "
            "`(iso, area, delivery_year, season, metric)`. ERCOT is excluded "
            "(energy-only, no capacity market). See "
            "[`docs/capacity-deliverability-wiring.md`](../../docs/capacity-deliverability-wiring.md) "
            "for how the model consumes it (area→zone crosswalk, gated "
            "`capacity_deliverability_limits`)."
        ),
    },
    "confirmed-retirements": {
        "summary": (
            "Binding-instrument retirement registry: units whose exit is bound "
            "by an enforceable public instrument, with the instrument's date "
            "and full provenance."
        ),
        "reconciles": (
            "PJM deactivation acceptances, MISO Attachment Y approvals, NYISO "
            "deactivation notices, ISO-NE cleared de-list bids, CAISO SWRCB/CPUC "
            "orders, ERCOT NSO acceptances, and cross-ISO federal consent decrees "
            "/ state statutes — onto one long frame keyed by "
            "`(iso, plant_id, generator_id, instrument_id)` with a closed "
            "`confirmation_class` vocabulary (`rto_deactivation`, "
            "`consent_decree`, `statute`, `regulatory_order`, `rmr_end`). "
            "ANNOUNCED-only retirements (EIA-860 planned dates, IRP/press "
            "announcements) do NOT belong here — they stay with the "
            "economic-retirement screen. Superseded rows (a counter-instrument "
            "suspends the exit) are kept for audit and ignored by the loader. "
            "Consumed forecast-forward only by "
            "`data.confirmed_retirements.load_confirmed_exits` → "
            "`model.capacity.apply_confirmed_exits` (GATED "
            "`confirmed_exits_enabled`, default off)."
        ),
    },
    "coal-basin-price": {
        "summary": (
            "EIA Annual Coal Report region/rank f.o.b.-mine coal price "
            "(annual, national)."
        ),
        "reconciles": (
            "EIA `coal/market-sales-price` (region x market-type, all ranks) "
            "and `coal/price-by-rank` (region x coal rank) tidied onto one "
            "`metric`-keyed frame, with an `ALL` sentinel on whichever "
            "dimension the other route doesn't carry. The free public-domain "
            "substitute for the S&P/Argus/McCloskey-paywalled daily basin "
            "spot indices — collected to give the coal-vs-gas passthrough "
            "sigmoids (issue #1347) a real coal commodity price to check "
            "their `floor`/`ceil`/`gas_mid` asymptotes against. Region -> "
            "ISO-plant crosswalk: `reference` datatype, "
            "`market=coal-region-crosswalk`."
        ),
    },
    "coal-mining-ppi": {
        "summary": "BLS Producer Price Index for coal (national, monthly).",
        "reconciles": (
            "BLS `WPU051` (PPI commodity Coal) and `PCU2121--2121--` (PPI "
            "industry Coal Mining, NAICS 2121) — a monthly elasticity/slope "
            "cross-check on the annual `coal-basin-price` region prices. No "
            "regional breakout exists in BLS PPI for coal (confirmed by "
            "probing candidate series ids)."
        ),
    },
    "nyiso-reserve-requirements": {
        "summary": (
            "NYISO's published locational operating-reserve requirements by "
            "product x region for each dated version of the Locational "
            "Reserve Requirements posting, including the SENY 30-minute "
            "hourly step shape and Thunderstorm-Alert zeroing flags "
            "(issue #1344 / Ask B3)."
        ),
        "reconciles": (
            "Hand-transcription of the dated LRR PDFs (Wayback-bounded "
            "versions v2020/v2021/v2026) under "
            "`data/raw/NYISO-AS/requirements/`; see that README for the "
            "effective-date caveats. Feeds the gated hourly "
            "`ReserveFamily.requirement` channel; not yet consumed by any "
            "keeper."
        ),
    },
    "nyiso-operating-events": {
        "summary": (
            "Typed NYISO operating events (Thunderstorm Alert windows, "
            "system state, reserve pick-ups, OOM reliability commitments, "
            "emergency transactions) parsed from the public MIS message "
            "logs, 2018 through H1-2026 (Ask B2)."
        ),
        "reconciles": (
            "NYISO MIS P-35 Real-Time Events and P-25 Operational "
            "Announcements monthly archives, re-serialized per-year under "
            "`data/raw/NYISO-AS/requirements/` and parsed against a "
            "controlled template vocabulary (parse-only; unmatched messages "
            "stay in raw). Out-of-training years intaken under the "
            "2026-07-10 owner authorization "
            "(`docs/out-of-sample-results-2026-07.md` §1.2)."
        ),
    },
    "nyiso-interface-flows": {
        "summary": (
            "Hourly per-interface gross flows and posted limits for NYISO "
            "internal interfaces and external ties, aggregated from the "
            "public 5-minute MIS posting (Ask D1)."
        ),
        "reconciles": (
            "NYISO MIS P-32 ExternalLimitsFlows monthly archives, "
            "5-min -> hourly (mean flow, most-binding limits; +/-9999 MW "
            "unbounded sentinels nulled), one partition per year 2018 "
            "through H1-2026 from `data/raw/NYISO/interface-flows/`."
        ),
    },
    "nyiso-som-hub-fuel-annual": {
        "summary": (
            "Annual average fuel index prices by hub serving New York "
            "(incl. Iroquois Zone 2) transcribed from the NYISO State of "
            "the Market reports (Ask C1 annual floor)."
        ),
        "reconciles": (
            "SOM Figure A-6 annual tables across the 2020/2022/2023/2024/"
            "2025 reports (overlapping years cross-check identically), "
            "2018-2025, from `data/raw/gas-prices/"
            "nyiso_som_hub_fuel_annual.csv`. The daily/monthly Z2 series "
            "remains Platts-licensed (open licence ask)."
        ),
    },
}

# Short scope note for the national (non-ISO-partitioned) datatypes' table.
NATIONAL_SCOPE: dict[str, str] = {
    "emissions": "CAMPD/CEMS, by plant and unit",
    "outages": "derived (CAMPD downtime + curated ERCOT lists)",
    "fleet": "EIA-860 / eGRID / master registry",
    "fuel-prices": "national hubs (Henry Hub)",
    "fuel-hub-monthly": "national (Henry Hub monthly)",
    "fuel-basis": "per-ISO rows in one file (iso column key)",
    "fuel-ercot-ep-gas": "ERCOT / TX electric-power consumers",
    "fuel-takeorpay": "ERCOT plants (EIA-923 Schedule-5)",
    "reference": "crosswalks / lookups (ISO-agnostic)",
    "border-lmp": "neighbor-border hubs (WECC intertie, PJM_WEST)",
    "zonal-shares": "per-ISO via directory partitioning",
    "weather": "per-ISO via directory partitioning",
    "egrid": "national (EPA eGRID, by vintage year)",
    "coal-basin-price": "national/regional (EIA Annual Coal Report, by producing region)",
    "coal-mining-ppi": "national (BLS PPI, coal)",
}

NA = "n/a"
NONE_CELL = "—"

PREAMBLE = """\
# Data dictionary

The canonical contract for the curated `data/clean` tree. Every clean datatype
has exactly one schema under [`schema/`](schema/) (`<datatype>.schema.yaml`)
declaring its canonical columns — name, dtype, unit, nullability — and its key
columns. All curation sessions write through the shared
[`scripts/lib/clean_io.py`](../../scripts/lib/clean_io.py) `write_clean(...)`
seam, which validates against these schemas before writing Parquet and embeds
the schema version + source provenance in each file.

**Conventions (enforced by `clean_io`):**

- Columns are `lower_snake_case`.
- Time is tz-aware **UTC** in `interval_start_utc`; an optional tz-naive
  wall-clock `interval_start_local` may accompany it (UTC is authoritative).
- Standard keys: `iso`, `zone`, `node`, `plant_id`, `unit_id`, `year`,
  `month`, `hour`.
- Units are explicit in column names: `*_mw`, `*_mwh`, `price_*_usd_per_mwh`,
  `*_usd_per_mw` (AS capacity), `*_usd_per_mmbtu` (fuel), `*_kg` (emissions).

> **This file is generated — do not hand-edit.** Per-column tables are rendered
> from the schema YAMLs and the coverage matrix from the provenance metadata
> embedded in `data/clean`. To change a column, edit its schema YAML (or
> recurate the data) and run `python scripts/render_data_dictionary.py`. The
> test `tests/test_data_dictionary_sync.py` guards that the committed file
> matches a fresh render.

## Regenerate from raw

The clean tree is derived and disposable; it is rebuilt from `data/raw` by the
per-datatype curation scripts (`scripts/curate_*.py`, added per session), each
calling `clean_io.write_clean(df, datatype, ...)`. To regenerate everything run
`python scripts/regenerate_clean.py`; to verify an existing file round-trips
against its embedded schema, call `clean_io.validate_clean(path)`. Raw inputs
are described in [`../README.md`](../README.md) and are never modified in place."""


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------
def _para(text: str) -> str:
    """Wrap a paragraph at 79 cols without splitting links or hyphenated tokens."""
    return textwrap.fill(text, width=79, break_long_words=False, break_on_hyphens=False)


def _bullet(label: str, text: str) -> str:
    """Render a ``- **Label:** text`` bullet, wrapped with a hanging indent."""
    return textwrap.fill(
        f"- **{label}:** {text}",
        width=79,
        subsequent_indent="  ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def _fmt_years(years: set[int]) -> str:
    """Compact a set of years into contiguous ranges (e.g. ``2021, 2023–2025``)."""
    ys = sorted(years)
    if not ys:
        return NONE_CELL
    runs: list[tuple[int, int]] = []
    start = prev = ys[0]
    for y in ys[1:]:
        if y == prev + 1:
            prev = y
            continue
        runs.append((start, prev))
        start = prev = y
    runs.append((start, prev))
    return ", ".join(f"{a}" if a == b else f"{a}–{b}" for a, b in runs)


# ---------------------------------------------------------------------------
# Schema-driven per-column tables
# ---------------------------------------------------------------------------
def column_table(datatype: str) -> str:
    """Render a datatype's per-column table straight from its schema YAML."""
    schema = clean_io.load_schema(datatype)
    lines = [
        "| column | dtype | unit | nullable | description |",
        "|---|---|---|---|---|",
    ]
    for col in schema.columns:
        desc = " ".join(col.description.split()).replace("|", r"\|")
        nullable = "yes" if col.nullable else "no"
        lines.append(
            f"| `{col.name}` | `{col.dtype}` | `{col.unit}` | {nullable} | {desc} |"
        )
    return "\n".join(lines)


def _keys(datatype: str) -> str:
    """Key columns for a datatype — narrative override, else the schema list."""
    override = NARRATIVE[datatype].get("keys")
    if override:
        return override
    schema = clean_io.load_schema(datatype)
    return ", ".join(f"`{k}`" for k in schema.key_columns)


# ---------------------------------------------------------------------------
# Clean-tree-driven coverage
# ---------------------------------------------------------------------------
def enumerate_coverage() -> tuple[
    dict[str, dict[str, set[int]]], dict[str, set[int]], set[str]
]:
    """Read ``data/clean`` provenance into coverage maps.

    Returns ``(iso_years, national_years, iso_datatypes)``:

    * ``iso_years[datatype][iso]`` -> set of years (datatypes with an ``iso``
      partition),
    * ``national_years[datatype]`` -> set of years (datatypes with no ``iso``),
    * ``iso_datatypes`` -> the set of datatypes that carry any ``iso``.
    """
    iso_years: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    national_years: dict[str, set[int]] = defaultdict(set)
    iso_datatypes: set[str] = set()

    for path in sorted(paths.CLEAN_DIR.rglob("*.parquet")):
        meta = clean_io.read_clean_metadata(path)
        datatype = meta.get("datatype")
        if not datatype:
            continue
        iso = meta.get("iso")
        raw_year = meta.get("year")
        year = int(raw_year) if raw_year not in (None, "") else None
        if iso:
            iso_datatypes.add(datatype)
            if year is not None:
                iso_years[datatype][iso].add(year)
        elif year is not None:
            national_years[datatype].add(year)
    return iso_years, national_years, iso_datatypes


def _iso_partitioned(datatype: str) -> bool:
    """Whether a datatype is ISO-partitioned, per its schema.

    Classification is schema-driven (``iso`` is a key column) rather than
    derived from whichever files happen to exist in ``data/clean``. This keeps
    :func:`coverage_section` deterministic and crash-free when the (gitignored)
    clean tree is absent, while reproducing the data-driven partition for the
    actually-curated datatypes.
    """
    return "iso" in clean_io.load_schema(datatype).key_columns


def coverage_section() -> str:
    """Render the ISO x year matrix and the national-datatype table."""
    iso_years, national_years, _ = enumerate_coverage()
    iso_datatypes = {d for d in DATATYPE_ORDER if _iso_partitioned(d)}

    out: list[str] = ["## ISO coverage matrix", ""]
    out.append(
        _para(
            "Built from the `market_sim.*` provenance metadata embedded in "
            "`data/clean` (regenerate the tree with `python "
            "scripts/regenerate_clean.py`). Each cell is the span of calendar "
            "years curated for that datatype and ISO; `—` means none is "
            "curated. Markets (DAM/RTM) are aggregated here — see each "
            "datatype's section for the market split."
        )
    )
    out.append("")
    out.append("| datatype | " + " | ".join(ISO_ORDER) + " |")
    out.append("|---|" + "---|" * len(ISO_ORDER))
    for datatype in DATATYPE_ORDER:
        if datatype not in iso_datatypes:
            continue
        cells = [_fmt_years(iso_years[datatype].get(iso, set())) for iso in ISO_ORDER]
        out.append(f"| {datatype} | " + " | ".join(cells) + " |")

    out.append("")
    out.append("### National / ISO-agnostic datatypes")
    out.append("")
    out.append(
        _para(
            "Not partitioned by ISO (no `iso` in their `data/clean` "
            "provenance); coverage is national. `n/a` marks datatypes with no "
            "year partition (a single current snapshot)."
        )
    )
    out.append("")
    out.append("| datatype | scope | years |")
    out.append("|---|---|---|")
    for datatype in DATATYPE_ORDER:
        if datatype in iso_datatypes:
            continue
        years = national_years.get(datatype, set())
        years_cell = _fmt_years(years) if years else NA
        out.append(
            f"| {datatype} | {NATIONAL_SCOPE.get(datatype, NONE_CELL)} | {years_cell} |"
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def _datatype_section(datatype: str) -> str:
    narrative = NARRATIVE[datatype]
    summary = (
        f"{narrative['summary']} Schema: "
        f"[`schema/{datatype}.schema.yaml`](schema/{datatype}.schema.yaml)."
    )
    return "\n".join(
        [
            f"## {datatype}",
            "",
            _para(summary),
            "",
            _bullet("Keys", _keys(datatype)),
            _bullet("Reconciles", narrative["reconciles"]),
            "",
            column_table(datatype),
        ]
    )


def render_document() -> str:
    """Render the full data-dictionary markdown (ends with a trailing newline)."""
    parts = [PREAMBLE, coverage_section(), "---"]
    parts.extend(_datatype_section(dt) for dt in DATATYPE_ORDER)
    return "\n\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the committed doc differs from a fresh render",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="write the rendered doc to stdout instead of the file",
    )
    args = parser.parse_args(argv)

    doc = render_document()

    if args.stdout:
        sys.stdout.write(doc)
        return 0

    if args.check:
        current = DOC_PATH.read_text() if DOC_PATH.is_file() else ""
        if current != doc:
            print(
                f"{DOC_PATH} is out of date — run "
                f"`python scripts/render_data_dictionary.py`",
                file=sys.stderr,
            )
            return 1
        print(f"{DOC_PATH} is up to date")
        return 0

    DOC_PATH.write_text(doc)
    print(f"wrote {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
