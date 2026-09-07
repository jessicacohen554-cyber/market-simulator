"""nyiso-219 — is there an ADMISSIBLE daily driver for NYISO's within-month hydro allocation?

The successor instrument to ``nyiso218_hydro_shape_decomposition.py``. That probe
localized NYISO's hydro shape residual **completely**: month energy r ~ 1.000 and
hour-of-day r ~ 0.98 (both largely the armed mechanisms doing their jobs), while
**within-month day-to-day energy r is 0.207-0.392** -- the one dimension no armed
mechanism touches. It proposed no mechanism and handed over an open DATA question:

    does a forward-drivable, condition-responsive daily inflow/flow driver exist
    for NYISO's basins at usable quality?

This probe answers it with measurements, in three parts:

* **M1 -- fleet to water-source census.** Every NYISO conventional-hydro plant
  (prime mover ``HY``) is attributed to its EIA-860 ``Name of Water Source`` and
  weighted by nameplate MW. Published field, no geocoding guess.
* **M2 -- gauge availability census.** For every water source at >= 3 % of fleet
  MW, the USGS NWIS daily-values discharge record: coverage, approval status,
  licence, and the two day-to-day variability statistics that separate a
  *runoff* river from a *regulated / lake-buffered outflow*.
* **M3 -- does any candidate driver carry the missing signal?** Each candidate is
  scored by the **identical statistic** whose model-vs-actual value is 0.207-0.392
  (Pearson r of ``daily_total - that day's calendar-month mean``, 365 days), against
  the measured EIA-930 ``NG: WAT`` actual:

  - **D-A** leave-one-year-out day-of-year climatology (carries no information
    from the target year; forward-drivable by construction);
  - **D-B** year-specific measured basin discharge, MW-weighted over M1;
  - **D-C** the model's own drivers (daily mean load, daily mean price).

  **D-X, the forbidden outcome pin** (a shape pinned to the year's own measured
  ``NG: WAT`` daily totals) is r = 1.000 by construction. It is named only as the
  scale anchor and the tripwire -- *if an admissible driver returns ~0.95, check
  whether it has become this* -- and is never built.

**ZERO LP.** Model-side inputs are committed keeper artifacts; the hydrological
inputs are public-domain USGS records fetched read-only and cached beside this
probe's JSON record so every number reproduces without network.

**No held-out year is spent** (rule 22 ``[R-HOLDOUT]``): §M2/§M3 read *measured
data only* for years outside 2023-2025 -- no out-of-training model output is read,
no score is computed for one, nothing is solved or registered. What is held out is
the score, never the data.

Nothing here is gated on a price residual (rule 1 ``[R-STRUCT]``); it measures a
structural object that is not a rubric criterion at all.

PREREG: ``results/calibration/PREREG-nyiso219-hydro-daily-driver-data-question.md``.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

OUT_JSON = REPO / "results" / "calibration" / "_nyiso219_hydro_daily_driver_census.json"
CACHE_CSV = REPO / "results" / "calibration" / "_nyiso219_usgs_daily_discharge.csv.gz"

# The measured years available in the committed EIA-930 ``NYIS hourly`` extract
# (2015 and 2026 are partial and excluded). Ten full years, so the leave-one-out
# climatology always has nine donor years.
YEARS: tuple[int, ...] = (2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)

# Years the PREREG scores the variability and driver statistics over. 2016-2018
# are read for the D-A donor pool only (EIA-930's pre-2019 filings are the least
# comparable vintage), so every scored number sits on 2019-2025.
SCORED_YEARS: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024, 2025)

# USGS NWIS daily-values discharge gauges, one per material water source plus the
# pre-registered runoff comparator. Public domain (a work of the U.S. Geological
# Survey). Selected by position on the water source the M1 census attributes the
# plants to -- never by which one correlates best.
GAUGES: dict[str, dict[str, str]] = {
    "Niagara River": {
        "site": "04216000",
        "name": "NIAGARA RIVER AT BUFFALO NY",
        "role": "material-basin",
    },
    "St Lawrence River": {
        "site": "04264331",
        "name": "ST. LAWRENCE R AT CORNWALL ONT NR MASSENA NY",
        "role": "material-basin",
    },
    "Hudson River": {
        "site": "01327750",
        "name": "HUDSON RIVER AT FORT EDWARD NY",
        "role": "material-basin",
    },
    "Raquette River": {
        "site": "04267500",
        "name": "RAQUETTE RIVER AT SOUTH COLTON NY",
        "role": "material-basin",
    },
    # Cross-checks and the P2d runoff comparator -- not part of the D-B weight.
    "_check_Hudson_Hadley": {
        "site": "01318500",
        "name": "HUDSON RIVER AT HADLEY NY",
        "role": "cross-check",
    },
    "_check_Raquette_Raymondville": {
        "site": "04268000",
        "name": "RAQUETTE RIVER AT RAYMONDVILLE NY",
        "role": "cross-check",
    },
    "_comparator_Mohawk": {
        "site": "01357500",
        "name": "MOHAWK RIVER AT COHOES NY",
        "role": "runoff-comparator",
    },
    "Black River": {
        "site": "04260500",
        "name": "BLACK RIVER AT WATERTOWN NY",
        "role": "sub-threshold",
    },
}

USGS_DV = (
    "https://waterservices.usgs.gov/nwis/dv/?format=rdb&sites={site}"
    "&startDT=2016-01-01&endDT=2025-12-31&parameterCd=00060&statCd=00003"
)

# Calendar-month day counts on the loader's 365-day (no Feb 29) index, so the
# within-month deviation below is byte-comparable with the nyiso-218 statistic.
_MONTH_LENGTHS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _day_month_index() -> np.ndarray:
    """Return the 0-based calendar month of each of the year's 365 days."""
    return np.repeat(np.arange(12), _MONTH_LENGTHS)


def _within_month_dev(daily: np.ndarray) -> np.ndarray:
    """Subtract each day's own calendar-month mean (the nyiso-218 construction)."""
    dmonth = _day_month_index()
    means = np.array([daily[dmonth == k].mean() for k in range(12)])
    return daily - means[dmonth]


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r, NaN-safe on constant input."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.std() == 0.0 or b.std() == 0.0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _daily_totals(hourly: np.ndarray) -> np.ndarray:
    """Collapse an 8760-hour series to 365 daily totals (MWh if the input is MW)."""
    return hourly.reshape(365, 24).sum(axis=1)


# --------------------------------------------------------------------------- M1


def water_source_census() -> dict:
    """Attribute every NYISO hydro plant to its EIA-860 ``Name of Water Source``."""
    from market_sim.data.hydro import _load_hydro_nameplate

    nameplate = _load_hydro_nameplate("NYISO")
    plants = pd.read_parquet(REPO / "data/raw/eia-860/eia860_plant.parquet")
    plants["Plant Code"] = pd.to_numeric(plants["Plant Code"], errors="coerce")
    plants = plants.drop_duplicates("Plant Code").set_index("Plant Code")

    rows = []
    unmatched = 0
    for pid, mw in nameplate.items():
        if pid not in plants.index:
            unmatched += 1
            rows.append({"plant_id": pid, "mw": mw, "water_source": ""})
            continue
        rec = plants.loc[pid]
        source = str(rec["Name of Water Source"]).strip()
        if source.lower() == "nan":
            source = ""
        rows.append(
            {
                "plant_id": int(pid),
                "mw": float(mw),
                "water_source": source,
                "county": str(rec["County"]),
                "plant_name": str(rec["Plant Name"]),
            }
        )

    frame = pd.DataFrame(rows)
    total = float(frame.mw.sum())
    resolved = frame[frame.water_source != ""]
    grouped = (
        frame.groupby("water_source")
        .agg(mw=("mw", "sum"), n=("plant_id", "count"))
        .sort_values("mw", ascending=False)
    )
    grouped["pct"] = 100.0 * grouped.mw / total
    grouped["cum_pct"] = grouped.pct.cumsum()
    n_for_95 = int((grouped.cum_pct < 95.0).sum() + 1)

    great_lakes = ["Niagara River", "St Lawrence River"]
    gl_pct = float(grouped.loc[grouped.index.intersection(great_lakes), "pct"].sum())
    non_gl = grouped.drop(index=grouped.index.intersection(great_lakes))

    return {
        "n_plants": int(len(frame)),
        "unmatched_in_860_plant_file": unmatched,
        "fleet_mw": round(total, 1),
        "pct_plants_resolved": round(100.0 * len(resolved) / len(frame), 2),
        "pct_mw_resolved": round(100.0 * float(resolved.mw.sum()) / total, 2),
        "n_sources_for_95pct_mw": n_for_95,
        "great_lakes_outflow_pct_mw": round(gl_pct, 2),
        "largest_non_great_lakes": {
            "source": str(non_gl.index[0]),
            "pct_mw": round(float(non_gl.pct.iloc[0]), 2),
        },
        "sources": [
            {
                "source": str(idx),
                "mw": round(float(row.mw), 1),
                "n_plants": int(row.n),
                "pct_mw": round(float(row.pct), 3),
                "cum_pct_mw": round(float(row.cum_pct), 3),
            }
            for idx, row in grouped.iterrows()
        ],
        "material_sources_ge_3pct": [
            str(idx) for idx, row in grouped.iterrows() if row.pct >= 3.0
        ],
    }


# --------------------------------------------------------------------------- M2


def _fetch_usgs(site: str) -> pd.DataFrame:
    """Fetch one gauge's 2016-2025 daily mean discharge (cfs) from USGS NWIS."""
    url = USGS_DV.format(site=site)
    raw = subprocess.run(
        ["curl", "-sS", "--max-time", "180", url],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    frame = pd.read_csv(io.StringIO(raw), sep="\t", comment="#", dtype=str)
    frame = frame[frame.agency_cd == "USGS"]
    value_col = next(c for c in frame.columns if c.endswith("_00060_00003"))
    flag_col = f"{value_col}_cd"
    out = pd.DataFrame(
        {
            "site": site,
            "date": pd.to_datetime(frame["datetime"]),
            "cfs": pd.to_numeric(frame[value_col], errors="coerce"),
            "flag": frame[flag_col].astype(str).str.strip(),
        }
    )
    return out


def load_discharge(refresh: bool = False) -> pd.DataFrame:
    """Return the cached daily-discharge panel, fetching it once if absent."""
    if CACHE_CSV.exists() and not refresh:
        cached = pd.read_csv(CACHE_CSV, dtype={"site": str}, parse_dates=["date"])
        return cached
    frames = [_fetch_usgs(spec["site"]) for spec in GAUGES.values()]
    panel = pd.concat(frames, ignore_index=True)
    CACHE_CSV.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(CACHE_CSV, index=False)
    return panel


def gauge_census(panel: pd.DataFrame) -> dict:
    """Coverage, approval status and the two day-to-day variability statistics.

    The PREREG's P2b/P2c/P2d threshold is written as a "day-to-day coefficient of
    variation" without pinning the construction, so **both** readings are reported
    and each prediction is scored against both -- the gap is named, never closed
    after the numbers are seen:

    * ``cv_whole`` -- sd / mean over all scored days (carries the seasonal cycle);
    * ``cv_within_month`` -- the mean over months of (within-month daily sd / mean),
      which is the nyiso-218 statistic and the one the object is defined on.
    """
    out: dict[str, dict] = {}
    for source, spec in GAUGES.items():
        site = spec["site"]
        sub = panel[panel.site == site].copy()
        sub = sub[
            (sub.date >= "2019-01-01")
            & (sub.date <= "2025-12-31")
            & ~((sub.date.dt.month == 2) & (sub.date.dt.day == 29))
        ]
        expected = 365 * len(SCORED_YEARS)
        present = int(sub.cfs.notna().sum())
        flags = sub.flag.value_counts()
        approved = int(sum(v for k, v in flags.items() if k.startswith("A")))

        cvs_whole, cvs_within = [], []
        for year in SCORED_YEARS:
            year_rows = sub[sub.date.dt.year == year]
            values = year_rows.cfs.to_numpy(dtype=float)
            if len(values) != 365 or not np.isfinite(values).all() or values.mean() <= 0:
                continue
            cvs_whole.append(float(values.std() / values.mean()))
            dmonth = _day_month_index()
            monthly = [
                float(values[dmonth == k].std() / values[dmonth == k].mean())
                for k in range(12)
                if values[dmonth == k].mean() > 0
            ]
            cvs_within.append(float(np.mean(monthly)))

        out[source] = {
            "site": site,
            "station": spec["name"],
            "role": spec["role"],
            "coverage_pct_2019_2025": round(100.0 * present / expected, 2),
            "approved_pct_of_present": (
                round(100.0 * approved / present, 2) if present else None
            ),
            "flag_counts": {str(k): int(v) for k, v in flags.items()},
            "cv_whole_pct": round(100.0 * float(np.mean(cvs_whole)), 2) if cvs_whole else None,
            "cv_within_month_pct": (
                round(100.0 * float(np.mean(cvs_within)), 2) if cvs_within else None
            ),
            "years_scored": len(cvs_whole),
        }
    return out


# --------------------------------------------------------------------------- M3


def _actual_hydro_daily(year: int) -> np.ndarray | None:
    """Measured EIA-930 ``NG: WAT`` daily energy for NYISO (MWh/day)."""
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    bench = load_eia_hourly_benchmark("NYISO", year)
    if not bench or "hydro" not in bench:
        return None
    return _daily_totals(np.asarray(bench["hydro"], dtype=float))


def _actual_load_daily(year: int) -> np.ndarray | None:
    """Measured EIA-930 NYISO demand, daily mean (MW).

    Read from the **same** ``NYIS hourly`` extract and through the same year
    filter / gap-fill / pad the ``NG: WAT`` benchmark takes, so the load driver
    and the hydro target share one time index by construction.
    """
    from market_sim.data.eia930.actuals import _pad_to_year
    from market_sim.data.eia930.frames import _eia_hourly_path

    frame = pd.read_parquet(_eia_hourly_path("NYIS"))
    local = frame["Local date"]
    frame = frame[
        (local.dt.year == year) & ~((local.dt.month == 2) & (local.dt.day == 29))
    ].sort_values("UTC time")
    if frame.empty or "Demand" not in frame.columns:
        return None
    series = frame["Demand"].interpolate().bfill().ffill()
    if series.isna().any():
        return None
    return _daily_totals(_pad_to_year(series.to_numpy(dtype=float))) / 24.0


def driver_scores(discharge: pd.DataFrame, census: dict) -> dict:
    """Score every candidate daily driver on the nyiso-218 within-month statistic."""
    actual = {y: _actual_hydro_daily(y) for y in YEARS}
    actual = {y: v for y, v in actual.items() if v is not None}

    # D-A: leave-one-year-out day-of-year climatology. The target year contributes
    # nothing to its own driver, so this is what a forward year could actually use.
    loyo: dict[int, np.ndarray] = {}
    for year in actual:
        donors = [v for y, v in actual.items() if y != year]
        if donors:
            loyo[year] = np.mean(np.vstack(donors), axis=0)

    # D-B: MW-weighted measured basin discharge over the material (>= 3 % of fleet
    # MW) water sources that have a gauge. The weights are the M1 nameplate shares
    # -- fixed by the census, never chosen by which combination correlates best.
    weights = {
        row["source"]: row["pct_mw"]
        for row in census["sources"]
        if row["source"] in GAUGES and GAUGES[row["source"]]["role"] == "material-basin"
    }
    weight_sum = sum(weights.values())

    results: dict[str, dict] = {}
    for year in SCORED_YEARS:
        if year not in actual:
            continue
        target = _within_month_dev(actual[year])
        row: dict[str, float | None] = {}

        row["D-A_loyo_climatology_r"] = (
            round(_r(_within_month_dev(loyo[year]), target), 4) if year in loyo else None
        )

        per_basin: dict[str, float] = {}
        weighted = np.zeros(365)
        usable_weight = 0.0
        for source, pct in weights.items():
            site = GAUGES[source]["site"]
            sub = discharge[
                (discharge.site == site)
                & (discharge.date.dt.year == year)
                & ~((discharge.date.dt.month == 2) & (discharge.date.dt.day == 29))
            ].sort_values("date")
            values = sub.cfs.to_numpy(dtype=float)
            if len(values) != 365 or not np.isfinite(values).all():
                per_basin[source] = float("nan")
                continue
            per_basin[source] = round(_r(_within_month_dev(values), target), 4)
            # Weight each basin's flow by its share of fleet MW, normalizing the
            # basin to its own mean so a big river cannot dominate on units alone.
            weighted += (pct / weight_sum) * (values / values.mean())
            usable_weight += pct
        row["D-B_basin_discharge_r"] = (
            round(_r(_within_month_dev(weighted), target), 4) if usable_weight > 0 else None
        )
        row["D-B_per_basin_r"] = per_basin
        row["D-B_weight_covered_pct_fleet_mw"] = round(usable_weight, 2)

        # A single-gauge robustness check: the runoff comparator on its own.
        comp = discharge[
            (discharge.site == GAUGES["_comparator_Mohawk"]["site"])
            & (discharge.date.dt.year == year)
            & ~((discharge.date.dt.month == 2) & (discharge.date.dt.day == 29))
        ].sort_values("date")
        comp_values = comp.cfs.to_numpy(dtype=float)
        row["D-B_mohawk_only_r"] = (
            round(_r(_within_month_dev(comp_values), target), 4)
            if len(comp_values) == 365 and np.isfinite(comp_values).all()
            else None
        )

        load = _actual_load_daily(year)
        row["D-C_load_r"] = (
            round(_r(_within_month_dev(load), target), 4) if load is not None else None
        )

        # Actual vs its own next-day change: how persistent the real river is.
        row["actual_within_month_daily_cv_pct"] = round(
            100.0 * float(np.std(target) / actual[year].mean()), 3
        )
        results[str(year)] = row

    return {
        "d_b_weights_pct_fleet_mw": {k: round(v, 3) for k, v in weights.items()},
        "d_b_weight_total_pct_fleet_mw": round(weight_sum, 2),
        "per_year": results,
        "D-X_forbidden_pin_r": 1.0,
    }


def main() -> None:
    census = water_source_census()
    panel = load_discharge(refresh="--refresh" in sys.argv)
    gauges = gauge_census(panel)
    drivers = driver_scores(panel, census)

    record = {
        "session": "nyiso-219",
        "prereg": "results/calibration/PREREG-nyiso219-hydro-daily-driver-data-question.md",
        "keeper": "2026-09-07-nyiso-213-summer-seam",
        "keeper_cache_key": "95d4d8d167373eb7",
        "zero_lp": True,
        "M1_water_source_census": census,
        "M2_gauge_census": gauges,
        "M3_driver_scores": drivers,
        "inherited_model_within_month_r": {
            "2022": 0.358,
            "2023": 0.392,
            "2024": 0.248,
            "2025": 0.207,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
