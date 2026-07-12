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

Run: ``python scripts/build_calibration_reference.py``
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
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
    "CAISO": (2023, 2024, 2025),
    # NYISO gained 2022 on 2026-07-12 under the owner-authorized rule-22 DATA
    # intake (calibration-complete.json intake_log; NO marker, NO solve — the
    # one-shot stays quarantined): 2022 is reference/bench data readiness
    # only, never a calibration year. The missing in-sample 2024 entry is a
    # separate, FLAGGED gap (the "gated on unit-level outages" rationale
    # above is stale — NY_2024 CEMS exists; NYISO-calibration-owner decision,
    # docs/holdout-data-equivalency-register-2026-07.md).
    "NYISO": (2022, 2023, 2025),
    # NEISO gained 2022 on 2026-07-07: the calibration-complete marker
    # (frontend/data/backcast/calibration-complete.json) authorizes the ONE-SHOT
    # 2022 holdout validation (CLAUDE.md rule 22) — 2022 is a validation year
    # for the frozen keeper, never a calibration year.
    "NEISO": (2022, 2023, 2024, 2025),
    # MISO is the Stage-F addition: the EIA-923/930 by-fuel and demand
    # extracts all cover 2023-2025 (the 2025 EIA-923 release is the partial
    # monthly survey, handled by the incomplete-vintage guard).
    "MISO": (2023, 2024, 2025),
}

# Measured Henry Hub natural-gas spot price, annual average ($/MMBtu).
# Source: EIA Henry Hub Natural Gas Spot Price, annual averages.
# URL: https://www.eia.gov/dnav/ng/hist/rngwhhdA.htm
HENRY_HUB_ACTUAL: dict[int, float] = {
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}

# eGRID benchmark workbook (EPA Emissions & Generation Resource Integrated
# Database, 2023 data release). The plant-level sheet PLNT23 carries a
# one-row banner above the header, hence skiprows=1.
EGRID_PATH: Path = FLEET_DIR / "egrid2023_data_rev2 2.xlsx"
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
_EIA923_EXTRA_FUELS_BY_ISO: dict[str, tuple[str, ...]] = {
    "NYISO": ("hydro", "oil"),
    "NEISO": ("hydro", "oil"),
    "MISO": ("hydro", "oil"),
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
    not carried in a fresh checkout. :mod:`scripts.process_f923_fuel_costs`
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

    Reads the per-BA hourly extract and sums each delivered fuel series. Empty
    when the ISO has no EIA-930 extract for the year. Grid-side telemetry, so
    the variable-renewable totals are not subject to the EIA-923 survey's
    under-count / BA mis-assignment.
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


def build_reference() -> Path:
    """Build the calibration reference JSON and per-year CSVs.

    Returns:
        The path of the written ``calibration_reference.json``.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    isos: dict[str, dict] = {}
    for iso in CALIBRATION_ISOS:
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

    payload = {
        "generated": dt.date.today().isoformat(),
        "description": (
            "Multi-year calibration reference: EIA-860 renewable capacity, "
            "measured Henry Hub prices, EIA-930 demand totals, EIA-923 "
            "by-fuel net generation (the per-year generation_twh benchmark, "
            "2023-2025), and the eGRID 2023 generation/emissions benchmark."
        ),
        "calibration_years": list(CALIBRATION_YEARS),
        "henry_hub_actual": {str(y): p for y, p in HENRY_HUB_ACTUAL.items()},
        "egrid_benchmark": {iso: _egrid_benchmark(iso) for iso in CALIBRATION_ISOS},
        "isos": isos,
    }

    out_path = OUTPUT_DIR / "calibration_reference.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    logger.info("wrote %s", out_path.relative_to(REPO))
    return out_path


if __name__ == "__main__":
    build_reference()
