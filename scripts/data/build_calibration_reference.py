"""Build the multi-year calibration reference dataset.

Calibration backcasts the dispatch model against historical years for which
EIA actuals exist (2021-2024). Each year needs year-specific renewable
capacity from EIA-860 (not the forward-projection ``RENEWABLE_INSTALLED_MW``
constants), the measured Henry Hub gas price, and a generation/emissions
benchmark to compare against.

This script extracts that reference data once and writes it under
``data/raw/_validation-source/`` so :mod:`scripts.run_calibration` (and any other
consumer) can read pre-computed values rather than re-deriving them:

* ``calibration_reference.json`` — the full reference: per ISO and year, the
  EIA-860 renewable capacity (December year-end totals, zone shares, monthly
  ramp factors, per-zone monthly capacity), the measured Henry Hub price, and
  the EIA-930 demand totals; plus the per-ISO eGRID 2023 generation/emissions
  benchmark shared across consumers.
* ``{ISO}_{year}_renewable_capacity.csv`` — one tidy CSV per ISO-year with
  the per-zone, per-month EIA-860 operable wind and solar capacity (MW).

Every number here is a MEASURED OUTCOME used only as the SCORE (rule 13
``[R-MEASURED]``): nothing in this file is an input to a solve. The EIA-930
``NG:`` fuel series arrive already screened for unit-slip hours — the repair
lives at the loader seam (``eia930.actuals._screen_fuel_spike_columns``, lane
SPP-41), where every consumer inherits it, so this builder applies no screen
of its own (rule 19 ``[R-ONE-MECH]``; the builder-local ``_screen_fuel_spikes``
SPP-31 landed here was deleted, rule 26 ``[R-DELETE]``).

Run: ``python scripts/data/build_calibration_reference.py``
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
# Repo root FIRST: ``eia930.frames._read_clean_seam`` imports ``scripts.lib.
# clean_io`` lazily, and on a DIRECT run (``python scripts/data/build_calibration
# _reference.py``) sys.path[0] is this script's own directory, so that import
# fails, the seam resolves to ``None``, and every ``load_demand_meta`` call below
# silently falls back to the CORRUPTED legacy ``eia_demand_profiles`` summary —
# the demand block would then carry PJM 2021's 2.1e9 MW spike and SPP 2023's
# 3,621,097 MW unit slip as ``peak_mw``, and PJM 2019 (which the legacy summary
# has no row for at all) would hard-fail. The committed reference was built with
# the seam live, so this line reproduces it rather than changing it; the MISO
# builder carries the same insert for the same reason. Added 2026-09-07, lane
# SPP-31.
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import CALIBRATION_DIR, FLEET_DIR  # noqa: E402
from market_sim.data.eia923 import (  # noqa: E402
    EIA923_MONTHLY_GENERATION_PATH,
)
from market_sim.data.eia_loader import (  # noqa: E402
    load_demand_meta,
    load_eia_hourly_benchmark,
)
from market_sim.data.renewables import (  # noqa: E402
    _RENEWABLE_FUELS,
    _eia860_monthly_capacity,
)

# An incomplete current-year EIA-923 release (e.g. the 2025 early monthly
# survey, ~70% of plants reporting) silently under-counts every fuel — most
# severely the variable renewables, which have no CEMS backfill. When the
# EIA-923 BA solar+wind total falls below this fraction of the EIA-930
# grid-side (wind+solar) telemetry, the vintage is treated as incomplete and
# wind/solar are sourced from EIA-930 instead (the authority the volume gate
# already uses for these classes, see results.calibration.actuals_source).
_EIA923_RENEWABLE_COMPLETENESS_FRACTION: float = 0.80

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("build_calibration_reference")

# Calibration years are the historical years with EIA-930 hourly profiles.
# 2021-2024 each have their own EIA-860 fleet snapshot; 2025 reuses the
# latest available EIA-860 vintage (2024), which carries no 2025 builds, so
# its renewable capacity equals the 2024 year-end totals held flat. ERCOT was
# the first ISO calibrated; PJM the second; CAISO the third; NYISO and NEISO
# are the Stage-E additions. The per-ISO-year derivation is fully generic on
# the ISO's zone topology (zone_names) and balancing-authority code, so adding
# an ISO is a CALIBRATION_ISOS + BA-code-map change only.
CALIBRATION_YEARS: tuple[int, ...] = (2021, 2022, 2023, 2024, 2025)
CALIBRATION_ISOS: tuple[str, ...] = (
    "ERCOT",
    "PJM",
    "CAISO",
    "NYISO",
    "NEISO",
    "MISO",
    "SPP",
)

# Per-ISO calibration-year overrides. CAISO's backcast targets 2023-2025
# (doc 06: 2023 = wet hydro + Diablo at full output; 2024/2025 = the
# big-battery era) — the years with CAMPD unit-level CA extracts and EIA-923
# by-fuel benchmarks. NYISO targets 2023 (cleanest year, full CEMS) and 2025;
# 2024 is added once the NY_2024 CEMS extract lands (doc 07 §2 U1) — the
# reference data for 2024 already exists, but the backcast year is gated on
# its unit-level outages. NEISO targets 2023-2025 (it has the most complete
# CEMS coverage of the new ISOs). ISOs not listed use the full
# CALIBRATION_YEARS span.
CALIBRATION_YEARS_BY_ISO: dict[str, tuple[int, ...]] = {
    # PJM gained 2019 on 2026-08-06 (session pjm-160), the first pre-2021 year
    # any ISO carries. What unblocked it is the F3 closure in
    # scripts/data/curate_demand_profile.py::curate_pre_window: the pre-2021
    # gap was never the hourly demand DRIVER (load_demand('PJM', 2019) has
    # worked since PJM gained its per-BA extract adapter — the extract covers
    # 2018-2026), only load_demand_meta, which fell through to the legacy
    # eia_demand_meta.parquet summary and raised. The curator now writes a
    # pre-window `demand-profile` clean partition from the SAME per-BA series
    # load_demand serves, so _demand_totals resolves for 2019.
    # This is DATA READINESS ONLY (rule 22): 2019 is LOCKED-TEST tier, PJM
    # holds no `final` marker, and the holdout spend freeze is ACTIVE — so no
    # 2019 solve, score or registration is authorized by this entry. Its whole
    # purpose is that when a `final` grant is eventually issued, the inputs are
    # already prepared and frozen, with nothing left to assemble mid-spend
    # (rule 22's "already configured precisely like the frontier keeper").
    # 2020 is deliberately NOT added: PJM's 2020 per-BA demand series carries
    # two residual metering-artifact hours (192,229 and 176,085 MW against a
    # 145 GW third-highest and an 85 GW median) that the loader's 2.5x-median
    # spike screen leaves in place, so its peak_mw would be wrong by ~47 GW.
    # That is a root-cause fix in eia930.demand._screen_demand_spikes, not
    # something to bury in a reference block (rule 14 [R-ACCURATE]); see
    # FINDING-pjm160-f3-demand-profile-closure-2026-08-06.md.
    "PJM": (2019, 2021, 2022, 2023, 2024, 2025),
    # CAISO gained 2021-2022 on 2026-07-31 under the owner-authorized rule-22
    # Option-2 DATA intake (calibration-complete.json intake_log; CAISO holds
    # NO marker, so no solve/score/registration of either year — reference and
    # bench readiness only, never calibration years). 2018-2020 are NOT added:
    # eia_demand_profiles.parquet has no CAISO rows before 2021, so
    # _demand_totals hard-fails — the same F3/F4-class cross-ISO blocker
    # already recorded for NEISO below
    # (docs/holdout-data-equivalency-register-2026-07.md sec. CAISO).
    "CAISO": (2021, 2022, 2023, 2024, 2025),
    # NYISO gained 2022 on 2026-07-12 under the owner-authorized rule-22 DATA
    # intake (calibration-complete.json intake_log; NO marker, NO solve — the
    # one-shot stays quarantined): 2022 is reference/bench data readiness
    # only, never a calibration year.
    # 2024 added 2026-07-31, closing the in-sample gap the register had carried
    # since 2026-07-12: the "gated on NY_2024 unit-level outages" rationale in
    # the comment above was stale on both counts — campd-unit-level/NY_2024
    # (and NJ_2024) are on disk, and the 2026-07-24 all-ISO re-derivation gives
    # campd-unit-outages-NYISO.csv uniform-detector windows for 2018-2026. 2024
    # is an ordinary IN-SAMPLE training year (rule 22 train tier), so this is a
    # parity repair, not a holdout action: NYISO was the only multi-year ISO
    # missing a reference block for a year it is actually calibrated on.
    # 2018-2021 remain absent — build_reference()._demand_totals hard-requires
    # eia_demand_profiles.parquet rows, and that artifact starts at 2021 for
    # every ISO (the cross-ISO F3 blocker); extending it is not a NYISO task.
    "NYISO": (2022, 2023, 2024, 2025),
    # NEISO gained 2022 on 2026-07-07: the calibration-complete marker
    # (frontend/data/backcast/calibration-complete.json) authorizes the ONE-SHOT
    # 2022 holdout validation (CLAUDE.md rule 22) — 2022 is a validation year
    # for the frozen keeper, never a calibration year. 2021 added 2026-07-13
    # under the same marker's rule-22 Option-2 DATA-INTAKE channel (owner
    # authorization, calibration-complete.json intake_log) — a pre-window
    # holdout year, never a calibration year either.
    # 2019 and 2020 added 2026-08-07 (session neiso-89), on the SAME F3 closure
    # that unblocked PJM 2019 above: the blocker was never the hourly demand
    # DRIVER (load_demand('NEISO', 2019) has resolved 8,760 h off the per-BA
    # `ISNE hourly` extract all along — neiso-88 §2.3 corrects neiso-87 §3.1 on
    # this) but load_demand_meta, which fell through to the legacy
    # eia_demand_meta.parquet summary and raised. curate_demand_profile's
    # pre-window partition closes it at the curation seam for all six ISOs.
    # Unlike PJM, NEISO's 2020 per-BA series is CLEAN — 0 hours flagged by the
    # physical-bounds screen, max/median 1.93 against the 5.0 ceiling and the
    # 2.1 empirical bound — so the metering-artifact exclusion that keeps PJM
    # 2020 out does not apply here (measured this session; PJM 2020 peaks at
    # 192,229 MW, NEISO 2020 at 24,697 MW against a 12,790 MW median).
    # This is DATA READINESS ONLY (rule 22 as rewritten 2026-08-06: "what is
    # held out is the SCORE, never the DATA"). 2019 is LOCKED-TEST tier and
    # NEISO holds no `final` marker; 2020 is validation tier and the holdout
    # spend freeze is ACTIVE — so this entry authorizes no solve, no scoring
    # and no registration of either year. Its whole purpose is rule 22's
    # "already configured precisely like the frontier keeper, with nothing left
    # to prepare": the inputs are applied consistently across ALL years now, so
    # that if a grant is ever issued nothing is assembled mid-spend.
    "NEISO": (2019, 2020, 2021, 2022, 2023, 2024, 2025),
    # MISO is the Stage-F addition: the EIA-923/930 by-fuel and demand
    # extracts all cover 2023-2025 (the 2025 EIA-923 release is the partial
    # monthly survey, handled by the incomplete-vintage guard). 2021-2022
    # added 2026-07-31 under the owner-authorized rule-22 Option-2 DATA-INTAKE
    # channel (calibration-complete.json intake_log; MISO holds NO marker, so
    # the solve/score/register quarantine stands) — holdout reference/bench
    # readiness only, never calibration years. 2018-2020 and 2026 are NOT
    # added: eia_demand_profiles.parquet carries MISO rows for 2021-2025 only,
    # so _demand_totals hard-fails ("No EIA-930 data for ISO 'MISO' in year
    # 2018") — the same F3-class cross-ISO blocker recorded for NEISO above,
    # fix = extend eia_demand_profiles{,_meta}.parquet first.
    "MISO": (2021, 2022, 2023, 2024, 2025),
    # SPP is the Stage-G addition (registered 2026-09-06 by lane SPP-20; this
    # block landed 2026-09-07 by lane SPP-31). TRAINING TIER ONLY: 2023-2025,
    # the three years rule 22 [R-HOLDOUT] lets any ISO be built and scored on.
    # 2021-2022 are DELIBERATELY ABSENT even though every input for them now
    # resolves (eia_demand_profiles.parquet carries SPP 2021-2025 and the clean
    # demand-profile partitions cover 2019-2025): they are validation tier, SPP
    # holds NO marker in calibration-complete.json, and the ISOs that do carry
    # pre-2023 blocks got them through the owner-authorized rule-22 Option-2
    # DATA-INTAKE channel recorded in that file's intake_log. SPP has no such
    # authorization, so adding them here is not this lane's to do. Data
    # readiness is unaffected either way (rule 22, 2026-08-06: "what is held out
    # is the SCORE, never the DATA") — the inputs are prepared and consistent
    # across every year already, and only the reference block waits on a grant.
    "SPP": (2023, 2024, 2025),
}

# Measured Henry Hub natural-gas spot price, annual average ($/MMBtu).
# Source: EIA Henry Hub Natural Gas Spot Price, annual averages.
# URL: https://www.eia.gov/dnav/ng/hist/rngwhhdA.htm
HENRY_HUB_ACTUAL: dict[int, float] = {
    2018: 3.15,
    2019: 2.57,
    2020: 2.03,
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}

# eGRID benchmark workbook (EPA Emissions & Generation Resource Integrated
# Database, 2023 data release). The plant-level sheet PLNT23 carries a
# one-row banner above the header, hence skiprows=1.
EGRID_PATH: Path = FLEET_DIR / "egrid2023_data_rev2.xlsx"
EGRID_SHEET: str = "PLNT23"
EGRID_SKIPROWS: int = 1
EGRID_YEAR: int = 2023

# Heat-rate threshold (Btu/kWh) splitting eGRID gas plants into combined
# cycle (efficient, below the cut) and combustion turbine (above, or with
# no reported heat rate). 8500 sits between modern CC (~6500-7500) and
# frame CT (~10000+) heat rates.
GAS_CC_HEAT_RATE_CUTOFF: float = 8500.0

# eGRID PLFUELCT plant fuel category -> model fuel label. GAS is resolved
# separately into gas_cc / gas_ct by plant heat rate.
EGRID_FUEL_MAP: dict[str, str] = {
    "COAL": "coal",
    "NUCLEAR": "nuclear",
    "WIND": "wind",
    "SOLAR": "solar",
    "HYDRO": "hydro",
    "BIOMASS": "biomass",
    "OIL": "oil",
    "OTHF": "other",
    "OFSL": "other",
}

# eGRID reports annual CO2 mass in US short tons; the dispatch model and its
# CO2_RATES are in metric tonnes. 1 short ton = 0.90718474 metric tonnes.
SHORT_TON_TO_METRIC_TONNE: float = 0.90718474

_MWH_PER_TWH: float = 1.0e6
_MONTHS: tuple[int, ...] = tuple(range(1, 13))

# Output goes to the single validation-source root the loaders read from
# (data/raw/_validation-source). The pre-W1 ``inputs/calibration`` path was
# collapsed into data/raw/ — see config/paths.py CALIBRATION_DIR.
OUTPUT_DIR: Path = CALIBRATION_DIR


def _eia860_renewables(iso: str, year: int) -> dict:
    """Return the EIA-860 renewable-capacity reference for one ISO-year.

    For each renewable fuel the EIA-860 operable plants are placed in model
    zones and accumulated month by month from their commercial-operation
    dates (see :func:`_eia860_monthly_capacity`). The result captures the
    December year-end total, the year-end zone shares, the ISO-wide monthly
    ramp factors, and the full per-zone monthly capacity grid.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calibration year.

    Returns:
        ``{fuel: {december_total_mw, zone_shares, monthly_ramp,
        monthly_capacity_mw}}`` for each renewable fuel with EIA-860 data.
    """
    zone_names = get_iso_config(iso).zone_names
    out: dict[str, dict] = {}
    for fuel in _RENEWABLE_FUELS:
        monthly = _eia860_monthly_capacity(iso, fuel, zone_names, year)
        if monthly is None:
            logger.warning("no EIA-860 %s data for %s %d", fuel, iso, year)
            continue
        december = monthly[:, -1]
        december_total = float(december.sum())
        iso_monthly = monthly.sum(axis=0)
        out[fuel] = {
            "december_total_mw": round(december_total, 2),
            "zone_shares": {
                zone_names[z]: round(float(december[z] / december_total), 6)
                for z in range(len(zone_names))
            },
            "monthly_ramp": [
                round(float(iso_monthly[m] / iso_monthly[-1]), 6) for m in range(12)
            ],
            "monthly_capacity_mw": {
                zone_names[z]: [round(float(monthly[z, m]), 2) for m in range(12)]
                for z in range(len(zone_names))
            },
        }
    return out


def _demand_totals(iso: str, year: int) -> dict:
    """Return the EIA-930 annual demand totals for one ISO-year."""
    meta = load_demand_meta(iso, year)
    return {
        "total_twh": round(float(meta["total_annual_mwh"]) / _MWH_PER_TWH, 4),
        "total_mwh": float(meta["total_annual_mwh"]),
        "peak_mw": float(meta["peak_mw"]),
        "min_mw": float(meta["min_mw"]),
        "avg_mw": round(float(meta["avg_mw"]), 2),
    }


def _classify_gas(heat_rate: float) -> str:
    """Return ``gas_cc`` or ``gas_ct`` for an eGRID gas plant by heat rate.

    A plant with no reported heat rate cannot be confirmed as an efficient
    combined-cycle unit, so it is conservatively counted as a combustion
    turbine.
    """
    if heat_rate != heat_rate:  # NaN — no reported heat rate
        return "gas_ct"
    return "gas_cc" if heat_rate < GAS_CC_HEAT_RATE_CUTOFF else "gas_ct"


def _egrid_benchmark(iso: str) -> dict:
    """Return the eGRID 2023 generation/emissions benchmark for one ISO.

    Reads the plant-level PLNT23 sheet, filters to the ISO's balancing
    authority, and aggregates annual net generation (TWh) and CO2 emissions
    (metric Mt) by model fuel. Gas plants are split into combined cycle and
    combustion turbine by plant heat rate (:data:`GAS_CC_HEAT_RATE_CUTOFF`).

    Args:
        iso: ISO identifier; mapped to its eGRID balancing-authority code.

    Returns:
        A benchmark dict with ``generation_twh`` and ``co2_mt`` mappings.
    """
    # eGRID balancing-authority code for the ISO footprint. eGRID's BACODE
    # uses the same EIA-930 codes as :data:`_ISO_BA_CODE` (ERCO, PJM, ...).
    ba_code = {
        "ERCOT": "ERCO",
        "PJM": "PJM",
        "CAISO": "CISO",
        "NYISO": "NYIS",
        "NEISO": "ISNE",
        # eGRID 2023 PLNT23 BACODE for MISO is the bare "MISO" (verified
        # against the workbook), unlike the EIA-930 abbreviations elsewhere.
        "MISO": "MISO",
        # SPP's eGRID BACODE is the EIA-930 abbreviation "SWPP" (verified
        # against the workbook: 661 PLNT23 rows, no "SPP" code exists).
        "SPP": "SWPP",
    }[iso]
    df = pd.read_excel(EGRID_PATH, sheet_name=EGRID_SHEET, skiprows=EGRID_SKIPROWS)
    plants = df[df["BACODE"] == ba_code].copy()

    fuel_cat = plants["PLFUELCT"].astype(str).str.strip().str.upper()
    gen_mwh = pd.to_numeric(plants["PLNGENAN"], errors="coerce").fillna(0.0)
    co2_ton = pd.to_numeric(plants["PLCO2AN"], errors="coerce").fillna(0.0)
    heat_rate = pd.to_numeric(plants["PLHTRT"], errors="coerce")

    generation_twh: dict[str, float] = {}
    co2_mt: dict[str, float] = {}
    for cat, gen, co2, hr in zip(fuel_cat, gen_mwh, co2_ton, heat_rate):
        if cat == "GAS":
            fuel = _classify_gas(hr)
        else:
            fuel = EGRID_FUEL_MAP.get(cat, "other")
        generation_twh[fuel] = generation_twh.get(fuel, 0.0) + float(gen) / _MWH_PER_TWH
        co2_mt[fuel] = (
            co2_mt.get(fuel, 0.0)
            + float(co2) * SHORT_TON_TO_METRIC_TONNE / _MWH_PER_TWH
        )

    return {
        "iso": iso,
        "benchmark_year": EGRID_YEAR,
        "source": "EPA eGRID 2023 (PLNT23), filtered BACODE=%s" % ba_code,
        "co2_unit": "metric Mt (eGRID short tons converted)",
        "generation_twh": {k: round(v, 4) for k, v in sorted(generation_twh.items())},
        "co2_mt": {k: round(v, 4) for k, v in sorted(co2_mt.items())},
    }


def _write_year_csv(iso: str, year: int, renewables: dict) -> Path:
    """Write the per-zone, per-month renewable capacity CSV for one ISO-year.

    Args:
        iso: ISO identifier.
        year: Calibration year.
        renewables: The ISO-year renewable block from :func:`_eia860_renewables`.

    Returns:
        The path of the written CSV.
    """
    rows: list[dict] = []
    for fuel, block in renewables.items():
        for zone, monthly in block["monthly_capacity_mw"].items():
            for month, capacity in zip(_MONTHS, monthly):
                rows.append(
                    {
                        "iso": iso,
                        "year": year,
                        "fuel": fuel,
                        "zone": zone,
                        "month": month,
                        "capacity_mw": capacity,
                    }
                )
    path = OUTPUT_DIR / f"{iso}_{year}_renewable_capacity.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


# A whole EIA-923 vintage is treated as a partial release (every fuel, incl.
# the gas split, under-counted) when the balancing authority's total EIA-923
# net generation falls below this fraction of the EIA-930 grid net generation
# for the year. The 2025 early monthly survey runs ~74%; complete years ~100%.
_EIA923_VINTAGE_COMPLETENESS_FRACTION: float = 0.90

# EIA-923 reported fuel-type codes that count as coal.
_EIA923_COAL_FUELS: frozenset[str] = frozenset({"BIT", "SUB", "LIG", "WC", "RC"})
# EIA-923 reported fuel-type codes that count as oil (distillate, residual,
# kerosene, jet, waste oil, petroleum coke) — the dual-fuel winter switch fuel
# in NYISO/NEISO. Any prime mover counts; the fuel code alone classifies oil.
_EIA923_OIL_FUELS: frozenset[str] = frozenset({"DFO", "RFO", "JF", "KER", "WO", "PC"})
# ISO identifier -> EIA balancing-authority code.
_ISO_BA_CODE: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "PJM": "PJM",
    "NYISO": "NYIS",
    "NEISO": "ISNE",
    "MISO": "MISO",
    "SPP": "SWPP",
}

# Extra EIA-923 by-fuel benchmarks emitted only for the ISOs where they are
# first-order. NYISO and NEISO additionally benchmark conventional hydro
# (NYISO's Niagara/St-Lawrence carry ~25-30 TWh/yr) and the winter dual-fuel
# oil burn. The already-calibrated ERCOT/PJM/CAISO blocks are not listed, so
# their generation_twh stays byte-identical (hydro/oil are negligible or not
# benchmarked there). Pumped storage (WAT/PS) is storage, not energy, and is
# excluded from the hydro total.
# MISO carries material upper-Midwest conventional hydro (~9 TWh/yr, on par
# with NEISO's benchmarked hydro) and a non-trivial dual-fuel oil burn
# (~2-3 TWh/yr, larger than the NYISO/NEISO oil totals already benchmarked),
# so both are first-order energy classes for its by-fuel benchmark.
# SPP carries material conventional hydro on the Missouri/Arkansas river
# projects (EIA-923 WAT/HY: 8.4002 TWh in 2023, 8.7018 in 2024 — on par with
# MISO's benchmarked ~9 TWh and above NEISO's), so hydro is first-order for its
# by-fuel benchmark. OIL IS DELIBERATELY OMITTED: SPP's EIA-923 oil burn is
# 0.2590 / 0.3237 / 0.2230 TWh over 2023-2025 (~0.09 % of a ~280 TWh system) —
# an order of magnitude below the smallest oil total already benchmarked, and
# EIA-930 agrees (0.2159 / 0.1007 / 0.0219 TWh). It is a fleet of 2.4 GW of
# petroleum-liquids nameplate that essentially never runs, not a winter
# dual-fuel switch, so it is not a first-order energy class here.
_EIA923_EXTRA_FUELS_BY_ISO: dict[str, tuple[str, ...]] = {
    "NYISO": ("hydro", "oil"),
    "NEISO": ("hydro", "oil"),
    "MISO": ("hydro", "oil"),
    "SPP": ("hydro",),
}


def _eia923_generation(iso: str, year: int) -> dict[str, float]:
    """EIA-923 net generation by model fuel (TWh), with the incomplete-vintage
    guard applied (wind/solar deferred to EIA-930 when the 923 release is a
    partial current-year survey). See :func:`_eia923_generation_raw` for the
    raw extraction and :func:`_guard_incomplete_eia923` for the guard.
    """
    return _guard_incomplete_eia923(iso, year, _eia923_generation_raw(iso, year))


@lru_cache(maxsize=1)
def _eia923_generation_table() -> pd.DataFrame:
    """Return the committed EIA-923 Page-1 net-generation table.

    The raw ``f923_{year}*.zip`` releases are large source downloads that are
    not carried in a fresh checkout. :mod:`scripts.data.process_f923_fuel_costs`
    distils them once into ``eia923_monthly_generation.parquet`` under
    ``data/raw/_processed-legacy`` — keeping the original Page-1 row grain (one
    row per plant / prime mover / fuel code), the EIA-930 ``ba_code`` and the
    annual net generation — so a balancing-authority by-fuel total summed from
    this parquet is byte-identical to the same total summed from the raw zip.
    That parquet is the resolved source here.
    """
    return pd.read_parquet(EIA923_MONTHLY_GENERATION_PATH)


@lru_cache(maxsize=None)
def _eia923_ba_frame(iso: str, year: int) -> pd.DataFrame | None:
    """Return the EIA-923 Page-1 rows for an ISO's balancing authority.

    Filters the committed EIA-923 net-generation parquet
    (:func:`_eia923_generation_table`) to the ISO's balancing authority and
    year, returning a frame with ``net_gen`` (MWh), ``pm`` (prime mover) and
    ``fc`` (fuel code). ``None`` when the parquet has no rows for the year
    (2021/2022, which predate the committed vintage) or the ISO has no
    balancing-authority mapping. Cached so the by-fuel split and the
    completeness check share a single read.
    """
    ba = _ISO_BA_CODE.get(iso)
    if ba is None:
        return None
    table = _eia923_generation_table()
    df = table[
        (table["year"] == year) & (table["ba_code"].astype(str).str.strip() == ba)
    ]
    if df.empty:
        return None
    return pd.DataFrame(
        {
            "net_gen": pd.to_numeric(df["netgen_annual_mwh"], errors="coerce")
            .fillna(0.0)
            .to_numpy(),
            "pm": df["prime_mover"].astype(str).str.strip().to_numpy(),
            "fc": df["fuel_type"].astype(str).str.strip().to_numpy(),
        }
    )


def _eia923_generation_raw(iso: str, year: int) -> dict[str, float]:
    """Return EIA-923 net generation by model fuel (TWh) for an ISO-year.

    Classifies each balancing-authority row (:func:`_eia923_ba_frame`) by
    reported fuel code and prime mover. Gas is split into combined cycle (prime
    movers CA/CT/CC/CS), combustion turbine (GT) and gas steam (ST). For ISOs in
    :data:`_EIA923_EXTRA_FUELS_BY_ISO` (NYISO/NEISO) conventional hydro
    (WAT/HY) and oil (:data:`_EIA923_OIL_FUELS`) are emitted too. Unlike the
    eGRID plant snapshot, these totals sum to the balancing authority's actual
    net generation, so they are a self-consistent calibration benchmark.

    Returns an empty dict when no EIA-923 zip exists for the year (2021 and
    2022 have none) or the ISO has no balancing-authority mapping.
    """
    df = _eia923_ba_frame(iso, year)
    if df is None:
        return {}
    net_gen, pm, fc = df["net_gen"], df["pm"], df["fc"]
    is_gas = fc == "NG"
    masks = {
        "coal": fc.isin(_EIA923_COAL_FUELS),
        "gas_cc": is_gas & pm.isin(["CA", "CT", "CC", "CS"]),
        "gas_ct": is_gas & pm.isin(["GT"]),
        "gas_st": is_gas & pm.isin(["ST"]),
        "nuclear": fc == "NUC",
        "wind": fc == "WND",
        "solar": fc == "SUN",
    }
    for fuel in _EIA923_EXTRA_FUELS_BY_ISO.get(iso, ()):
        if fuel == "hydro":
            # Conventional hydro only; pumped storage (WAT/PS) is storage.
            masks["hydro"] = (fc == "WAT") & (pm == "HY")
        elif fuel == "oil":
            masks["oil"] = fc.isin(_EIA923_OIL_FUELS)
    return {
        fuel: round(float(net_gen[mask].sum()) / _MWH_PER_TWH, 4)
        for fuel, mask in masks.items()
    }


def _eia930_annual_by_fuel(iso: str, year: int) -> dict[str, float]:
    """Return EIA-930 grid-side net generation by fuel (TWh) for an ISO-year.

    Reads the per-BA hourly extract through the calibration bench loader and
    sums each series. The ``NG:`` fuel series arrive with EIA-930 unit-slip
    hours already repaired at the loader seam
    (``eia930.actuals._screen_fuel_spike_columns``, SPP-41) — this function
    applies no screen of its own, so the loader is the ONLY place the repair
    happens (rule 19 ``[R-ONE-MECH]``). Empty when the ISO has no EIA-930
    extract for the year. Grid-side telemetry, so the variable-renewable totals
    are not subject to the EIA-923 survey's under-count / BA mis-assignment.
    """
    bench = load_eia_hourly_benchmark(iso, year)
    if not bench:
        return {}
    return {
        fuel: round(float(np.nansum(np.asarray(arr, dtype=float))) / _MWH_PER_TWH, 4)
        for fuel, arr in bench.items()
    }


def _incomplete_renewable_fuels(
    iso: str, year: int, raw: dict[str, float]
) -> list[str]:
    """Return the variable-renewable fuels EIA-923 under-counts for an ISO-year.

    A fuel (wind or solar) is under-counted when its raw EIA-923 BA total is
    below :data:`_EIA923_RENEWABLE_COMPLETENESS_FRACTION` of the EIA-930
    grid-side telemetry for that fuel. Evaluated PER FUEL (not on the combined
    renewable total) so a partial wind release is caught even when solar
    reports fully. Empty for complete vintages (the two sources then agree to
    within a few percent), so the guard is a no-op there. Also empty when there
    is no EIA-923 vintage at all (``raw`` empty, e.g. 2021/2022): a missing
    benchmark is left missing, not fabricated from EIA-930.
    """
    if not raw:
        return []
    e930 = _eia930_annual_by_fuel(iso, year)
    out: list[str] = []
    for fuel in ("wind", "solar"):
        ref = e930.get(fuel, 0.0)
        if ref <= 0.0:
            continue
        if raw.get(fuel, 0.0) < _EIA923_RENEWABLE_COMPLETENESS_FRACTION * ref:
            out.append(fuel)
    return out


def _guard_incomplete_eia923(
    iso: str, year: int, gen: dict[str, float]
) -> dict[str, float]:
    """Source wind/solar from EIA-930 when the EIA-923 vintage under-counts them.

    The incomplete current-year EIA-923 release under-counts the variable
    renewables (no CEMS backfill reaches them). Any wind/solar fuel below the
    completeness fraction (:func:`_incomplete_renewable_fuels`) is replaced with
    the EIA-930 grid total — byte-identical for complete vintages, where the two
    agree. Other classes are left on EIA-923 (thermal is backfilled from CAMPD
    downstream); callers flag the year via :func:`_eia923_is_incomplete`.
    """
    e930 = _eia930_annual_by_fuel(iso, year)
    patched = dict(gen)
    for fuel in _incomplete_renewable_fuels(iso, year, gen):
        logger.info(
            "%s %s: EIA-923 %s %.2f TWh is incomplete; using EIA-930 %.2f TWh",
            iso,
            year,
            fuel,
            patched.get(fuel, 0.0),
            e930[fuel],
        )
        patched[fuel] = e930[fuel]
    return patched


def _eia923_is_incomplete(iso: str, year: int) -> bool:
    """True when the WHOLE ISO-year EIA-923 vintage is a partial release.

    Distinct from the per-fuel renewable guard (which also fires on a
    single-fuel BA mis-assignment, e.g. CAISO wind, in an otherwise complete
    year): this stamps the reference year block only when the balancing
    authority's *total* EIA-923 net generation is far below the EIA-930 grid
    total (the 2025 early survey, ~74%), so downstream scorecards know the
    remaining EIA-923 by-fuel totals — notably the gas split, which has no
    clean EIA-930 equivalent — are incomplete and should defer to EIA-930.
    Complete vintages return False, so the flag never appears in their block.
    """
    df = _eia923_ba_frame(iso, year)
    if df is None:
        return False
    e930 = _eia930_annual_by_fuel(iso, year)
    e930_total = e930.get("net_gen", 0.0)
    if e930_total <= 0.0:
        return False
    e923_total = float(df["net_gen"].sum()) / _MWH_PER_TWH
    return e923_total < _EIA923_VINTAGE_COMPLETENESS_FRACTION * e930_total


def build_reference(isos_filter: tuple[str, ...] | None = None) -> Path:
    """Build the calibration reference JSON and per-year CSVs.

    Args:
        isos_filter: Optional subset of :data:`CALIBRATION_ISOS` to rebuild.
            ``None`` (the default) rebuilds every ISO, exactly as before.

    MERGE, NEVER REPLACE (added 2026-09-07, lane SPP-31 — plan §7 gate **G9**,
    "shared regenerated files alter other ISOs' rows"). The committed reference
    is loaded first and only the ISOs actually built this run are updated, so an
    ISO left out keeps its committed block byte-for-byte. This is the same
    discipline ``derive_actual_lmp.main`` and ``build_miso_lmp_reference.main``
    already apply to ``actual_lmp.json``, and it matters for the same reason: a
    whole-file rebuild silently folds in every upstream input that has landed
    since the file was last written. Concretely, on 2026-09-07 a no-op rebuild of
    the committed 2026-08-07 reference moved CAISO's ENTIRE renewables block —
    ``zone_shares`` and ``monthly_capacity_mw`` reallocated across
    NP15 / ZP26 / SP15_rest — because merge ``5a910016`` (2026-09-05) landed the
    EIA-860 ``vintage_2024`` parquets and CAISO's measured plant-hub /
    FSNO-subzone membership crosswalks a month after the reference was built.
    That is a real and probably wanted CAISO re-derivation, but it is a CAISO
    input change and it belongs to the CAISO lane, not to whichever lane happens
    to add an ISO next.

    Returns:
        The path of the written ``calibration_reference.json``.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_isos = tuple(
        iso for iso in CALIBRATION_ISOS if isos_filter is None or iso in isos_filter
    )
    unknown = sorted(set(isos_filter or ()) - set(CALIBRATION_ISOS))
    if unknown:
        raise SystemExit(f"not calibration ISOs: {unknown}")

    isos: dict[str, dict] = {}
    for iso in build_isos:
        years: dict[str, dict] = {}
        for year in CALIBRATION_YEARS_BY_ISO.get(iso, CALIBRATION_YEARS):
            renewables = _eia860_renewables(iso, year)
            block = {
                "henry_hub_actual": HENRY_HUB_ACTUAL[year],
                "demand": _demand_totals(iso, year),
                "renewables": renewables,
                "generation_twh": _eia923_generation(iso, year),
            }
            if _eia923_is_incomplete(iso, year):
                # Partial current-year EIA-923 release: wind/solar already
                # swapped to EIA-930 above; flag so scorecards know the
                # remaining EIA-923 by-fuel totals (notably the gas split) are
                # incomplete and should defer to EIA-930 grid totals.
                block["eia923_incomplete"] = True
            years[str(year)] = block
            csv_path = _write_year_csv(iso, year, renewables)
            logger.info("wrote %s", csv_path.relative_to(REPO))
        isos[iso] = years

    out_path = OUTPUT_DIR / "calibration_reference.json"
    payload: dict = json.loads(out_path.read_text()) if out_path.exists() else {}
    payload["generated"] = dt.date.today().isoformat()
    payload["description"] = (
        "Multi-year calibration reference: EIA-860 renewable capacity, "
        "measured Henry Hub prices, EIA-930 demand totals, EIA-923 "
        "by-fuel net generation (the per-year generation_twh benchmark, "
        "2023-2025), and the eGRID 2023 generation/emissions benchmark."
    )
    payload["calibration_years"] = list(CALIBRATION_YEARS)
    payload["henry_hub_actual"] = {str(y): p for y, p in HENRY_HUB_ACTUAL.items()}
    payload.setdefault("egrid_benchmark", {}).update(
        {iso: _egrid_benchmark(iso) for iso in build_isos}
    )
    payload.setdefault("isos", {}).update(isos)

    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    logger.info(
        "wrote %s (built: %s)", out_path.relative_to(REPO), ", ".join(build_isos)
    )
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--isos",
        nargs="+",
        default=None,
        help="Subset of CALIBRATION_ISOS to rebuild; default all. Only the "
        "built ISOs are updated -- every other ISO keeps its committed block "
        "and per-year CSVs byte-for-byte (plan gate G9).",
    )
    args = ap.parse_args()
    build_reference(tuple(args.isos) if args.isos else None)


if __name__ == "__main__":
    main()
