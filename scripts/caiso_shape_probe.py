"""CAISO dispatch shape diagnostic — model diurnal vs CAMPD/EIA-930 per class.

Permanent acceptance gate for CAISO shape-calibration work (Steps A–E of the
2026-06 overhaul plan).  Replaces the lost scratch ``shape_probe.py`` from the
container that produced the audit in ``docs/caiso-lever-audit-2026-06.md``.

Measures per-class mean MW by hour-of-day (``diurnal profile``) from the model
dispatch against three measured sources:

* **CAMPD CEMS** – per-unit ``grossLoad`` from ``data/raw/campd-unit-level/
  CA_<yr>.parquet``.  Each unit is routed to the dispatch class it belongs to
  via INTERSECT of its ORIS plant-code (after applying
  :data:`market_sim.data.campd.CAMPD_UNIT_PLANT_REMAP` for AES Alamitos / HB
  split units) and the plant's :code:`klass` column in the dispatch parquet.
  Co-located mixed units at one ``facilityId`` (e.g. AES Alamitos – old steam
  boilers + new CCGT filing under the same ORIS) split correctly because the
  remap re-keys the CCGT units to their own EIA code before the class lookup.
* **EIA-930** – ``data/raw/eia-930-hourly/CISO hourly.parquet`` (``NG: NG``
  for gas total, ``NG: SUN`` for solar).
* **CAISO curtailment** – ``data/raw/caiso-curtailment/
  productionandcurtailmentsdata_<yr>.xlsx`` (``Curtailments`` sheet, 5-minute
  solar curtailment in MW, averaged to hourly).

Clock convention
----------------
All sources are aligned to the model's naive local-standard clock (hour 0 =
Jan 1 00:00 CAISO local standard, no DST, 8760 hours/year with Feb 29
dropped in leap years):

* **Model dispatch** – direct index (row i = hour i of the year).
* **CEMS** – ``date + hour`` (0-23) in local standard time; Feb 29 mapped to
  -1 and dropped.
* **EIA-930** – ``Local time`` column already in CAISO local standard time.
  Leap-year Feb 29 rows dropped to keep 8760 hours.
* **Curtailment** – ``Date + hour`` (1-24, hour-ending); converted to 0-based
  and averaged from 5-minute to hourly.

Metrics
-------
Computed over the full 8760-hour aligned vectors (not over the 24-point
diurnal average):

* ``r`` – hourly Pearson *r* (scipy).
* ``NRMSE`` – RMSE / mean(measured).
* ``mdl band`` / ``meas band`` – mean MW over h13–23 (thermal) or h10–15
  (solar), matching the audit table convention.
* ``mdl TWh`` / ``meas TWh`` – annual total.

Modes
-----
Default
    Print the shape-metrics table for all specified years, replicating the
    audit table in ``docs/caiso-lever-audit-2026-06.md``.
``--compare bundle2 [bundle3 ...]``
    Overlay per-class diurnal MW profiles side by side for the baseline bundle
    (positional ``bundle``) and each additional run.  Useful for lever-on vs
    lever-off comparison.
``--floor-attribution``
    Decompose each class's dispatch into floor-forced vs economic.  Recomputes
    the gas commitment floor target from
    :func:`market_sim.data.eia_loader.measured_gas_floor_profile` and the
    CT reliability floor target from
    :func:`market_sim.data.eia_loader.caiso_load_weighted_tmax`, distributes
    the fleet-level target to classes cheapest-first (CC absorbs before CT for the gas
    floor), and reports binding hours, floor-forced TWh, and economic TWh.

Usage
-----
::

    # Default shape table
    .venv/bin/python scripts/caiso_shape_probe.py BUNDLE_DIR \\
        [--year 2023 2024 2025] [--pass P1]

    # Compare baseline vs lever-off run
    .venv/bin/python scripts/caiso_shape_probe.py BUNDLE_DIR \\
        --compare BUNDLE_OFF_DIR [BUNDLE_OFF_DIR2 ...] [--year 2024]

    # Floor attribution
    .venv/bin/python scripts/caiso_shape_probe.py BUNDLE_DIR \\
        --floor-attribution [--year 2023 2024 2025] \\
        [--gas-floor-frac 0.8] [--ct-floor-base 0.049]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import RAW_DIR
from market_sim.data.campd import CAMPD_UNIT_PLANT_REMAP

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_CAMPD_DIR: Path = RAW_DIR / "campd-unit-level"
_CISO_HOURLY: Path = RAW_DIR / "eia-930-hourly" / "CISO hourly.parquet"
_CURT_DIR: Path = RAW_DIR / "caiso-curtailment"
_TMAX_FILE: Path = RAW_DIR / "caiso-weather" / "caiso_load_weighted_tmax_daily.csv"

# ---------------------------------------------------------------------------
# Class groupings
# ---------------------------------------------------------------------------

# Dispatch classes tracked in CAMPD
_GAS_CLASSES: tuple[str, ...] = (
    "CC_REGULAR",
    "CT_PEAKER",
    "CT_CHP",
    "CC_CHP",
    "ST_GAS",
)

# CEMS unitType → technology bucket for class disambiguation on mixed facilities
_UNITTYPE_BUCKET: dict[str, str] = {
    "Combined cycle": "cc",
    "Combustion turbine": "ct",
    "Tangentially-fired": "st",
    "Dry bottom wall-fired boiler": "st",
    "Stoker": "st",
    "Other boiler": "st",
    "Integrated gasification combined cycle": "cc",
    "Boiler": "st",
    "Cell burner boiler": "st",
}

# Technology bucket → compatible dispatch classes (used when plant appears
# under multiple klasses in the dispatch, e.g. a cogeneration + merchant split)
_BUCKET_CLASSES: dict[str, frozenset[str]] = {
    "cc": frozenset({"CC_REGULAR", "CC_CHP"}),
    "ct": frozenset({"CT_PEAKER", "CT_CHP"}),
    "st": frozenset({"ST_GAS", "ST_CHP"}),
}

# Diurnal-band hour ranges (inclusive), per class category
_BAND_HOURS: dict[str, tuple[int, int]] = {
    "solar": (10, 15),
    "default": (13, 23),
}

# ---------------------------------------------------------------------------
# Floor-attribution constants (matching transmission.py + scenarios.py)
# ---------------------------------------------------------------------------

_GAS_FLOOR_H_START: int = 9  # midday window start (inclusive)
_GAS_FLOOR_H_END: int = 16  # midday window end (exclusive)
_CT_FLOOR_H_START: int = 15  # evening window start (inclusive)
_CT_FLOOR_H_END: int = 22  # evening window end (inclusive)

# Default ScenarioConfig values for the CT floor curve
_CT_DEFAULT_SLOPE: float = 0.047
_CT_DEFAULT_T0: float = 25.0
_CT_DEFAULT_CAP: float = 0.46

# ---------------------------------------------------------------------------
# Hour-of-year utilities
# ---------------------------------------------------------------------------

# Cumulative hours at the start of each month (non-leap year)
_MONTH_START_HOUR: list[int] = [
    0,
    744,
    1416,
    2160,
    2880,
    3624,
    4344,
    5088,
    5832,
    6552,
    7296,
    8016,
]


def _hoy_from_date_hour(
    date: "pd.Series[pd.Timestamp]", hour: "pd.Series[int]"
) -> np.ndarray:
    """Convert (date, 0-based hour) to non-leap hour-of-year index (0–8759).

    Feb 29 in a leap year returns -1 so callers can filter it out; all other
    dates map to a valid index in [0, 8760).
    """
    m = date.dt.month.to_numpy(dtype=int)
    d = date.dt.day.to_numpy(dtype=int)
    h = np.asarray(hour, dtype=int)
    base = np.array(_MONTH_START_HOUR)[m - 1]
    idx = base + (d - 1) * 24 + h
    return np.where((m == 2) & (d == 29), -1, idx)


def _eia930_to_8760(df_hourly: pd.DataFrame, year: int) -> pd.DataFrame:
    """Filter CISO hourly frame to one year, drop Feb 29, return 8760 rows.

    Aligns the EIA-930 ``Local time`` column to the model's naive local-standard
    clock; returns the filtered frame sorted by local time, with a new ``hoy``
    column (hour-of-year, 0–8759).  The returned frame has ≤ 8760 rows (missing
    hours for the rare partially-uploaded year) but the ``hoy`` index is correct
    for the rows present.
    """
    local = pd.to_datetime(df_hourly["Local time"])
    mask = local.dt.year == year
    df = df_hourly[mask].copy()
    local = pd.to_datetime(df["Local time"])
    # Drop Feb 29
    feb29 = (local.dt.month == 2) & (local.dt.day == 29)
    df = df[~feb29].copy()
    # Compute hour-of-year
    t0 = pd.Timestamp(f"{year}-01-01")
    hoy = ((pd.to_datetime(df["Local time"]) - t0) / pd.Timedelta("1h")).round()
    df["hoy"] = hoy.astype(int)
    return df.sort_values("hoy").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------


def load_dispatch(bundle_dir: Path, year: int, pass_label: str = "P1") -> pd.DataFrame:
    """Load the per-generator-hour dispatch frame for one year.

    Args:
        bundle_dir: Path to the calibration bundle directory.
        year: Calendar year.
        pass_label: LP pass label (``"P1"`` or ``"P2"``).  

    Returns:
        DataFrame with columns ``year``, ``plant_code``, ``klass``, ``hour``,
        ``mw`` (and more from the bundle writer).  Returns empty DataFrame if
        the file is absent.
    """
    path = bundle_dir / "dispatch" / f"{year}_{pass_label}.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def build_plant_klass_map(disp: pd.DataFrame) -> dict[int, set[str]]:
    """Build plant_code → set-of-klasses from a dispatch frame.

    Only thermal rows (``plant_code > 0``) are included; wind/solar/pseudo
    units use ``plant_code == 0``.

    Args:
        disp: Dispatch DataFrame from :func:`load_dispatch`.

    Returns:
        Dict mapping each EIA plant code to the set of dispatch classes
        (``klass`` values) it appears under.  Most plants map to a single
        class; the rare multi-class plant requires unitType disambiguation.
    """
    thermal = disp[disp["plant_code"] > 0]
    result: dict[int, set[str]] = {}
    for pc, grp in thermal.groupby("plant_code"):
        result[int(pc)] = set(grp["klass"].unique())
    return result


def _route_unit_to_klass(
    fac_id: int,
    unit_id: str,
    unit_type: str,
    plant_klass_map: dict[int, set[str]],
) -> str | None:
    """Return the dispatch class for one CAMPD unit row.

    Applies :data:`market_sim.data.campd.CAMPD_UNIT_PLANT_REMAP` for the
    known AES split-plant cases, then looks up the plant code in
    ``plant_klass_map``.  If the plant maps to multiple klasses (unusual),
    ``unit_type`` disambiguates via the technology-bucket mapping.

    Args:
        fac_id: CAMPD ``facilityId`` cast to int.
        unit_id: CAMPD ``unitId`` string.
        unit_type: CAMPD ``unitType`` string.
        plant_klass_map: From :func:`build_plant_klass_map`.

    Returns:
        The dispatch class string, or ``None`` if the plant is absent from the
        dispatch (too small, out-of-state, storage, etc.).
    """
    # Apply split-plant remap: AES Alamitos CT1/CT2 → 62115, etc.
    effective_pc = CAMPD_UNIT_PLANT_REMAP.get((fac_id, unit_id), fac_id)
    klasses = plant_klass_map.get(effective_pc)
    if not klasses:
        return None
    if len(klasses) == 1:
        return next(iter(klasses))
    # Multiple klasses: use unitType bucket to pick the right one
    bucket = _UNITTYPE_BUCKET.get(unit_type, "")
    compat = _BUCKET_CLASSES.get(bucket, frozenset())
    matches = klasses & compat
    if len(matches) == 1:
        return next(iter(matches))
    # Still ambiguous (e.g. a CC unit at a plant with both CC_REGULAR and CC_CHP):
    # prefer the first alphabetically for determinism.
    return sorted(matches or klasses)[0]


def load_campd_measured(
    year: int, plant_klass_map: dict[int, set[str]]
) -> pd.DataFrame:
    """Load CA CAMPD CEMS data and route each unit to its dispatch class.

    Reads ``data/raw/campd-unit-level/CA_<year>.parquet``, applies the
    AES split-plant remap, looks up each plant's dispatch class, and returns
    an hourly (8760-row) DataFrame of ``{klass: mw}`` columns with row index =
    hour-of-year (0–8759).

    Args:
        year: Calendar year.
        plant_klass_map: From :func:`build_plant_klass_map` on the matching
            dispatch parquet; used to route each CAMPD unit to the right class.

    Returns:
        DataFrame indexed by hour-of-year (0–8759) with one column per class
        found in the CAMPD data (summed ``grossLoad`` in MW).  Missing hours
        have NaN.
    """
    path = _CAMPD_DIR / f"CA_{year}.parquet"
    if not path.exists():
        return pd.DataFrame()

    raw = pd.read_parquet(
        path, columns=["facilityId", "unitId", "date", "hour", "grossLoad", "unitType"]
    )
    raw = raw.dropna(subset=["grossLoad"])
    raw["fac_id"] = pd.to_numeric(raw["facilityId"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["fac_id"])

    date = pd.to_datetime(raw["date"])
    hoy = _hoy_from_date_hour(date, raw["hour"].astype(int))
    valid = (hoy >= 0) & (hoy < 8760)
    raw = raw[valid].copy()
    raw["hoy"] = hoy[valid]

    # Route each row to its dispatch class
    klasses = [
        _route_unit_to_klass(
            int(fac),
            str(uid),
            str(ut),
            plant_klass_map,
        )
        for fac, uid, ut in zip(raw["fac_id"], raw["unitId"], raw["unitType"])
    ]
    raw["klass"] = klasses
    raw = raw[raw["klass"].notna()].copy()

    # Aggregate to (hoy, klass) → sum MW
    agg = raw.groupby(["hoy", "klass"])["grossLoad"].sum().unstack(fill_value=0.0)
    # Reindex to full 8760
    agg = agg.reindex(range(8760), fill_value=0.0)
    return agg


def _load_ciso_hourly(year: int) -> pd.DataFrame | None:
    """Load CISO EIA-930 hourly parquet aligned to the model's 8760-hour clock.

    Returns an 8760-row DataFrame (or fewer if the year is incomplete in the
    raw file) with columns ``hoy``, ``gas_mw`` (``NG: NG``), ``solar_mw``
    (``NG: SUN``).  Returns ``None`` if the file is absent or the year has no
    rows.
    """
    if not _CISO_HOURLY.exists():
        return None
    df = pd.read_parquet(_CISO_HOURLY)
    df_yr = _eia930_to_8760(df, year)
    if df_yr.empty:
        return None
    out = pd.DataFrame({"hoy": df_yr["hoy"]})
    out["gas_mw"] = pd.to_numeric(df_yr.get("NG: NG", np.nan), errors="coerce").values
    out["solar_mw"] = pd.to_numeric(
        df_yr.get("NG: SUN", np.nan), errors="coerce"
    ).values
    return out.set_index("hoy")


def load_solar_curtailment(year: int) -> np.ndarray | None:
    """Load CAISO 5-minute solar curtailment and average to hourly MW.

    Reads the ``Curtailments`` sheet from
    ``data/raw/caiso-curtailment/productionandcurtailmentsdata_<year>.xlsx``.
    Each 5-minute-interval row carries the instantaneous MW curtailed.  We
    divide the per-hour sum by 12 (the number of 5-minute slots per hour) to
    get the mean hourly-equivalent MW, then map to the model's 8760-hour clock.

    Args:
        year: Calendar year.

    Returns:
        ``(8760,)`` float array of hourly mean curtailment MW, zeros where no
        curtailment occurred.  Returns ``None`` if the file is absent.
    """
    path = _CURT_DIR / f"productionandcurtailmentsdata_{year}.xlsx"
    if not path.exists():
        return None

    # The Curtailments sheet has a description row at index 0; use header=None
    # and assign column names manually.  Values are 5-minute MW (instantaneous).
    raw = pd.read_excel(path, sheet_name="Curtailments", header=None, skiprows=1)
    raw.columns = [
        "date",
        "hour",
        "interval",
        "wind_curt_mw",
        "solar_curt_mw",
        "reason",
    ]
    raw = raw.dropna(subset=["solar_curt_mw"])
    raw["solar_curt_mw"] = pd.to_numeric(raw["solar_curt_mw"], errors="coerce").fillna(
        0.0
    )

    # hour is 1-24 (hour-ending); convert to 0-based for hoy mapping
    raw["hour0"] = raw["hour"].astype(int) - 1
    date = pd.to_datetime(raw["date"])
    hoy = _hoy_from_date_hour(date, raw["hour0"])
    valid = (hoy >= 0) & (hoy < 8760)
    raw = raw[valid].copy()
    raw["hoy"] = hoy[valid]

    # Sum 5-min values per hour, divide by 12 for mean MW
    hourly = raw.groupby("hoy")["solar_curt_mw"].sum() / 12.0
    result = np.zeros(8760, dtype=float)
    for h, v in hourly.items():
        if 0 <= h < 8760:
            result[h] = v
    return result


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def shape_metrics(model: np.ndarray, measured: np.ndarray) -> dict[str, float]:
    """Compute hourly Pearson r, NRMSE, diurnal band, and TWh.

    Both arrays are aligned 8760-hour vectors (MW).  NaN positions in either
    are excluded from the correlation and NRMSE.

    Args:
        model: Model dispatch MW, shape (8760,).
        measured: Measured generation MW, shape (8760,).

    Returns:
        Dict with keys ``r``, ``nrmse``, ``mdl_twh``, ``meas_twh``.
    """
    model = np.asarray(model, dtype=float)
    measured = np.asarray(measured, dtype=float)
    valid = np.isfinite(model) & np.isfinite(measured)
    if valid.sum() < 2:
        return {
            "r": float("nan"),
            "nrmse": float("nan"),
            "mdl_twh": float("nan"),
            "meas_twh": float("nan"),
        }

    m, a = model[valid], measured[valid]
    r, _ = pearsonr(m, a)
    rmse = float(np.sqrt(np.mean((m - a) ** 2)))
    mean_meas = float(np.mean(a))
    nrmse = rmse / mean_meas if mean_meas > 0 else float("nan")
    mdl_twh = float(np.nansum(model)) / 1e6
    meas_twh = float(np.nansum(measured)) / 1e6
    return {"r": r, "nrmse": nrmse, "mdl_twh": mdl_twh, "meas_twh": meas_twh}


def diurnal_mean(hourly_mw: np.ndarray) -> np.ndarray:
    """Return mean MW by hour-of-day (24-element array) from 8760 hourly MW.

    Args:
        hourly_mw: 1-D array of length 8760.

    Returns:
        24-element float array; index = hour-of-day (0 = midnight).
    """
    arr = np.asarray(hourly_mw, dtype=float)
    out = np.full(24, np.nan)
    for h in range(24):
        vals = arr[h::24]
        finite = vals[np.isfinite(vals)]
        if finite.size:
            out[h] = float(np.mean(finite))
    return out


def _band(hod_mw: np.ndarray, h_start: int, h_end: int) -> float:
    """Mean MW over hour-of-day range [h_start, h_end] (inclusive)."""
    vals = hod_mw[h_start : h_end + 1]
    finite = vals[np.isfinite(vals)]
    return float(np.mean(finite)) if finite.size else float("nan")


# ---------------------------------------------------------------------------
# Default mode: shape metrics table
# ---------------------------------------------------------------------------


def _model_class_8760(disp: pd.DataFrame, klass: str) -> np.ndarray:
    """Extract hourly model MW for one class from a dispatch frame.

    Sums across all units of the class within each hour, mapping hour column
    (0-based within the year) to a (8760,) array.

    Args:
        disp: Dispatch DataFrame from :func:`load_dispatch`.
        klass: Class label (e.g. ``"CC_REGULAR"``).

    Returns:
        Float array of shape (8760,), zeros where no units of that class exist.
    """
    rows = disp[disp["klass"] == klass]
    if rows.empty:
        return np.zeros(8760, dtype=float)
    hourly = rows.groupby("hour")["mw"].sum()
    out = np.zeros(8760, dtype=float)
    for h, v in hourly.items():
        if 0 <= h < 8760:
            out[h] = float(v)
    return out


def run_shape_table(
    bundle_dir: Path,
    years: Sequence[int],
    pass_label: str = "P1",
) -> None:
    """Print the per-class shape-metrics table, replicating the audit report.

    For each year, prints model vs CAMPD and model vs EIA-930 metrics (Pearson
    r, NRMSE, diurnal band, TWh).  CAMPD coverage is confirmed per class; EIA-
    930 covers the gas total (CC_REGULAR + CC_CHP + CT_PEAKER + CT_CHP +
    ST_GAS) and solar.

    Args:
        bundle_dir: Calibration bundle directory (must contain ``dispatch/``).
        years: Year(s) to analyse.
        pass_label: LP pass label (``"P1"`` or ``"P2"``).  
    """
    for year in years:
        disp = load_dispatch(bundle_dir, year, pass_label)
        if disp.empty:
            print(
                f"[WARN] no {pass_label} dispatch at {bundle_dir}/dispatch/{year}_{pass_label}.parquet"
            )
            continue

        pkmap = build_plant_klass_map(disp)
        campd = load_campd_measured(year, pkmap)
        e930 = _load_ciso_hourly(year)
        curt = load_solar_curtailment(year)

        _print_year_table(year, disp, campd, e930, curt, pass_label)


def _print_year_table(
    year: int,
    disp: pd.DataFrame,
    campd: pd.DataFrame,
    e930: "pd.DataFrame | None",
    curt: "np.ndarray | None",
    pass_label: str,
) -> None:
    """Print the metrics table for one year."""
    hdr = f"\n{year}  ({pass_label})  mdl TWh  meas TWh      r   NRMSE  mdl band  meas band  band×  source"
    print(hdr)
    print("-" * len(hdr.lstrip()))

    def _row(
        label: str, model_mw: np.ndarray, meas_mw: np.ndarray, source: str
    ) -> None:
        mets = shape_metrics(model_mw, meas_mw)
        hod_mdl = diurnal_mean(model_mw)
        hod_meas = diurnal_mean(meas_mw)
        bh = _BAND_HOURS.get("solar" if label == "solar" else "default")
        mdl_band = _band(hod_mdl, *bh)
        meas_band = _band(hod_meas, *bh)
        band_x = mdl_band / meas_band if meas_band > 0 else float("nan")
        print(
            f"  {label:<14}"
            f"  {mets['mdl_twh']:>7.2f}"
            f"  {mets['meas_twh']:>7.2f}"
            f"  {mets['r']:>6.2f}"
            f"  {mets['nrmse']:>7.2f}"
            f"  {mdl_band:>8.0f}"
            f"  {meas_band:>8.0f}"
            f"  {band_x:>6.2f}"
            f"  {source}"
        )

    # Gas classes from CAMPD
    for klass in _GAS_CLASSES:
        model_mw = _model_class_8760(disp, klass)
        if klass in campd.columns:
            meas_mw = campd[klass].to_numpy(dtype=float)
        else:
            meas_mw = np.zeros(8760, dtype=float)
        _row(klass, model_mw, meas_mw, "CAMPD")

    # Gas TOTAL vs EIA-930
    gas_model = sum(_model_class_8760(disp, k) for k in _GAS_CLASSES)
    if e930 is not None:
        gas_meas = np.zeros(8760, dtype=float)
        # Insert EIA-930 gas at the matching hour-of-year indices
        for hoy, v in e930["gas_mw"].items():
            if 0 <= hoy < 8760 and np.isfinite(v):
                gas_meas[hoy] = v
        _row("GAS TOTAL", gas_model, gas_meas, "EIA-930")

    # Solar from EIA-930 + curtailment
    solar_model = _model_class_8760(disp, "solar")
    if e930 is not None:
        solar_meas = np.zeros(8760, dtype=float)
        for hoy, v in e930["solar_mw"].items():
            if 0 <= hoy < 8760 and np.isfinite(v):
                solar_meas[hoy] = v
        _row("solar (EIA930)", solar_model, solar_meas, "EIA-930")
        if curt is not None:
            solar_pot = solar_meas + curt
            _row("solar+curt pot", solar_model, solar_pot, "EIA-930+curt")
            # Curtailment summary
            print(
                f"  {'solar curtailment':<22}  model≈{solar_model.sum() / 1e6:.2f}  "
                f"measured+curt≈{solar_meas.sum() / 1e6:.2f}+{curt.sum() / 1e6:.2f}="
                f"{solar_pot.sum() / 1e6:.2f} TWh"
            )


# ---------------------------------------------------------------------------
# Compare mode: overlay runs per class
# ---------------------------------------------------------------------------


def run_compare(
    baseline_dir: Path,
    other_dirs: Sequence[Path],
    years: Sequence[int],
    pass_label: str = "P1",
) -> None:
    """Print per-class diurnal MW profiles across multiple bundles.

    Prints mean MW by hour-of-day for each class, one column per bundle.
    Useful for lever-on vs lever-off comparison (e.g. baseline vs gas-floor-off).

    Args:
        baseline_dir: The reference (keeper / lever-on) bundle.
        other_dirs: Additional bundles to overlay.
        years: Year(s) to analyse.
        pass_label: LP pass label.
    """
    all_dirs = [baseline_dir] + list(other_dirs)
    labels = [d.name for d in all_dirs]

    for year in years:
        disps = [load_dispatch(d, year, pass_label) for d in all_dirs]
        if all(d.empty for d in disps):
            print(f"[WARN] no dispatch found for year {year} in any bundle")
            continue

        # Build plant_klass_map from baseline for CAMPD routing
        pkmap = build_plant_klass_map(disps[0]) if not disps[0].empty else {}
        campd = load_campd_measured(year, pkmap)
        e930 = _load_ciso_hourly(year)

        classes_to_show = list(_GAS_CLASSES) + ["solar"]
        print(f"\n=== Compare {year} ({pass_label}): diurnal mean MW by class ===")

        for klass in classes_to_show:
            print(f"\n  {klass}")
            hod_cols: list[tuple[str, np.ndarray]] = []
            for i, (d, label) in enumerate(zip(disps, labels)):
                if d.empty:
                    continue
                mw = _model_class_8760(d, klass)
                hod_cols.append((label, diurnal_mean(mw)))

            # Measured reference
            if klass in campd.columns:
                hod_cols.append(("CAMPD", diurnal_mean(campd[klass].to_numpy())))
            elif klass == "solar" and e930 is not None:
                sol = np.zeros(8760)
                for hoy, v in e930["solar_mw"].items():
                    if 0 <= hoy < 8760 and np.isfinite(v):
                        sol[hoy] = v
                hod_cols.append(("EIA-930", diurnal_mean(sol)))

            if not hod_cols:
                print("    (no data)")
                continue

            # Header
            header = f"    {'h':>3}  " + "  ".join(f"{lb:>12}" for lb, _ in hod_cols)
            print(header)
            for h in range(24):
                vals = "  ".join(f"{col[h]:>12.0f}" for _, col in hod_cols)
                print(f"    {h:>3}  {vals}")


# ---------------------------------------------------------------------------
# Floor attribution mode
# ---------------------------------------------------------------------------


def run_floor_attribution(
    bundle_dir: Path,
    years: Sequence[int],
    pass_label: str = "P1",
    gas_floor_frac: float = 0.8,
    ct_floor_base: float = 0.049,
    ct_floor_slope: float = _CT_DEFAULT_SLOPE,
    ct_floor_t0: float = _CT_DEFAULT_T0,
    ct_floor_cap: float = _CT_DEFAULT_CAP,
) -> None:
    """Decompose per-class dispatch into floor-forced and economic components.

    Recomputes the gas commitment floor target and CT reliability floor target
    from their source functions (not from the LP's min_gen arrays, which are
    not persisted), distributes the gas fleet-level target to classes
    cheapest-first (CC absorbs before CT), and reports:

    * Per-class: floor target mean MW (midday / evening window), binding hours,
      floor-forced TWh, economic TWh.
    * Gas total: floor target vs total dispatch.

    The floor targets are computed from the same source functions used in
    production (:func:`market_sim.data.eia_loader.measured_gas_floor_profile`
    and :func:`~market_sim.data.eia_loader.caiso_load_weighted_tmax`), so the
    attribution is reproducible without a re-solve.

    Args:
        bundle_dir: Calibration bundle directory.
        years: Year(s) to analyse.
        pass_label: LP pass label.
        gas_floor_frac: ``caiso_gas_floor_frac`` used in the run (default 0.8,
            matching the keeper flag ``--caiso-gas-floor-frac 0.8``).
        ct_floor_base: ``caiso_ct_floor_base`` used in the run (default 0.049).
        ct_floor_slope: CT floor curve slope (deg C⁻\xb9).
        ct_floor_t0: CT floor zero-crossing temperature (deg C).
        ct_floor_cap: CT floor maximum capacity fraction.
    """
    from market_sim.data.eia_loader import (
        caiso_load_weighted_tmax,
        measured_gas_floor_profile,
    )

    for year in years:
        disp = load_dispatch(bundle_dir, year, pass_label)
        if disp.empty:
            print(f"[WARN] no {pass_label} dispatch for {year}")
            continue

        hours = 8760
        clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
        hod = clock.hour.to_numpy()

        # Gas commitment floor target (fleet-wide MW, over midday window only)
        raw_profile = measured_gas_floor_profile("CAISO", year, hours)
        gas_floor = np.zeros(hours, dtype=float)
        if raw_profile is not None:
            midday = (hod >= _GAS_FLOOR_H_START) & (hod < _GAS_FLOOR_H_END)
            gas_floor[midday] = gas_floor_frac * np.asarray(raw_profile)[midday]

        # CT reliability floor target (fraction of available CT capacity)
        ct_floor_frac_arr = np.zeros(hours, dtype=float)
        tmax = caiso_load_weighted_tmax(year, hours)
        if tmax is not None:
            frac = np.clip(
                ct_floor_base
                + ct_floor_slope * (np.asarray(tmax, dtype=float) - ct_floor_t0),
                ct_floor_base,
                ct_floor_cap,
            )
            evening = (hod >= _CT_FLOOR_H_START) & (hod <= _CT_FLOOR_H_END)
            ct_floor_frac_arr[evening] = frac[evening]

        # Per-class dispatch arrays
        class_mw: dict[str, np.ndarray] = {
            k: _model_class_8760(disp, k) for k in _GAS_CLASSES
        }
        cc_mw = class_mw["CC_REGULAR"] + class_mw["CC_CHP"]
        ct_mw = class_mw["CT_PEAKER"] + class_mw["CT_CHP"]

        # Distribute gas floor to CC first, residual to CT
        floor_cc = np.minimum(cc_mw, gas_floor)
        floor_ct_from_gas = np.maximum(0.0, gas_floor - cc_mw)

        # CT reliability floor (use fraction × CT dispatch as proxy for target;
        # available capacity ≈ dispatch / (1 - outage rate), but we don't have
        # availability here.  Use the CT dispatch as a lower-bound proxy: when
        # the floor binds, dispatch ≈ avail_cap × frac so avail_cap ≈ dispatch
        # / frac).  This slightly underestimates the target on lightly-loaded
        # hours but is conservative and avoids needing the fleet arrays.
        with np.errstate(divide="ignore", invalid="ignore"):
            ct_avail_proxy = np.where(
                ct_floor_frac_arr > 0,
                ct_mw / np.maximum(ct_floor_frac_arr, 0.01),
                0.0,
            )
        floor_ct_reliability = ct_floor_frac_arr * ct_avail_proxy

        print(
            f"\n=== Floor Attribution {year} ({pass_label}) gas_floor_frac={gas_floor_frac}, ct_base={ct_floor_base} ==="
        )

        def _attr_row(
            label: str,
            class_mw_h: np.ndarray,
            floor_target_h: np.ndarray,
            window: np.ndarray,
            floor_name: str,
        ) -> None:
            """Print one attribution row."""
            floor_twh = float(np.sum(floor_target_h)) / 1e6
            class_twh = float(np.sum(class_mw_h)) / 1e6
            # Binding hours: class dispatch ≤ floor target + tolerance
            tol = 200.0  # MW
            binding = (
                window & (class_mw_h <= floor_target_h + tol) & (floor_target_h > 0)
            )
            n_binding = int(np.sum(binding))
            forced_twh = (
                float(np.sum(np.minimum(class_mw_h, floor_target_h)[binding])) / 1e6
            )
            econ_twh = class_twh - forced_twh
            floor_mean_mw = (
                float(np.mean(floor_target_h[floor_target_h > 0]))
                if np.any(floor_target_h > 0)
                else 0.0
            )
            print(
                f"  {label:<14}  floor={floor_name:<20}  "
                f"target_TWh={floor_twh:.2f}  class_TWh={class_twh:.2f}  "
                f"binding_h={n_binding:>4}  forced_TWh={forced_twh:.2f}  "
                f"econ_TWh={econ_twh:.2f}  floor_mean_MW={floor_mean_mw:.0f}"
            )

        midday_mask = (hod >= _GAS_FLOOR_H_START) & (hod < _GAS_FLOOR_H_END)
        evening_mask = (hod >= _CT_FLOOR_H_START) & (hod <= _CT_FLOOR_H_END)

        _attr_row(
            "CC_REGULAR+CHP", cc_mw, floor_cc, midday_mask, "gas_floor (CC share)"
        )
        _attr_row(
            "CT gas-floor",
            ct_mw,
            floor_ct_from_gas,
            midday_mask,
            "gas_floor (CT resid)",
        )
        _attr_row(
            "CT reliability",
            ct_mw,
            floor_ct_reliability,
            evening_mask,
            "ct_reliability_floor",
        )

        # Hourly diurnal breakdown (midday window)
        print(
            f"\n  Gas floor target vs CC+CT dispatch — diurnal (mean MW, h{_GAS_FLOOR_H_START}–{_GAS_FLOOR_H_END - 1})"
        )
        print(
            f"  {'h':>3}  {'gas_floor_tgt':>14}  {'CC_mw':>10}  {'CT_mw':>10}  {'floor_to_CC':>12}  {'floor_to_CT':>12}"
        )
        for h in range(_GAS_FLOOR_H_START, _GAS_FLOOR_H_END):
            sel = hod == h
            gf = float(np.mean(gas_floor[sel]))
            cc_h = float(np.mean(cc_mw[sel]))
            ct_h = float(np.mean(ct_mw[sel]))
            fcc = float(np.mean(floor_cc[sel]))
            fct = float(np.mean(floor_ct_from_gas[sel]))
            print(
                f"  {h:>3}  {gf:>14.0f}  {cc_h:>10.0f}  {ct_h:>10.0f}  {fcc:>12.0f}  {fct:>12.0f}"
            )

        print(
            f"\n  CT reliability floor vs CT dispatch — diurnal (mean MW, h{_CT_FLOOR_H_START}–{_CT_FLOOR_H_END})"
        )
        print(f"  {'h':>3}  {'ct_rel_tgt':>12}  {'CT_mw':>10}  {'frac':>8}")
        for h in range(_CT_FLOOR_H_START, _CT_FLOOR_H_END + 1):
            sel = hod == h
            tgt_h = float(np.mean(floor_ct_reliability[sel]))
            ct_h = float(np.mean(ct_mw[sel]))
            frac_h = float(np.mean(ct_floor_frac_arr[sel]))
            print(f"  {h:>3}  {tgt_h:>12.0f}  {ct_h:>10.0f}  {frac_h:>8.3f}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the probe script."""
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("bundle", type=Path, help="Baseline calibration bundle directory")
    ap.add_argument(
        "--year",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="Year(s) to analyse (default: 2023 2024 2025)",
    )
    ap.add_argument(
        "--pass",
        dest="pass_label",
        default="P1",
        choices=["P1", "P2"],
        help="LP pass label (default: P1)",
    )
    ap.add_argument(
        "--compare",
        nargs="+",
        type=Path,
        default=None,
        metavar="BUNDLE_DIR",
        help="Additional bundle(s) to overlay in compare mode",
    )
    ap.add_argument(
        "--floor-attribution",
        action="store_true",
        help="Run floor-attribution decomposition",
    )
    ap.add_argument(
        "--gas-floor-frac",
        type=float,
        default=0.8,
        help="caiso_gas_floor_frac used in the run (default: 0.8)",
    )
    ap.add_argument(
        "--ct-floor-base",
        type=float,
        default=0.049,
        help="caiso_ct_floor_base used in the run (default: 0.049)",
    )
    ap.add_argument(
        "--ct-floor-slope",
        type=float,
        default=_CT_DEFAULT_SLOPE,
        help=f"CT floor curve slope per deg C (default: {_CT_DEFAULT_SLOPE})",
    )
    ap.add_argument(
        "--ct-floor-t0",
        type=float,
        default=_CT_DEFAULT_T0,
        help=f"CT floor zero-crossing temperature deg C (default: {_CT_DEFAULT_T0})",
    )
    ap.add_argument(
        "--ct-floor-cap",
        type=float,
        default=_CT_DEFAULT_CAP,
        help=f"CT floor max capacity fraction (default: {_CT_DEFAULT_CAP})",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CAISO shape probe."""
    args = _parse_args(argv)
    years = args.year

    if args.floor_attribution:
        run_floor_attribution(
            args.bundle,
            years,
            pass_label=args.pass_label,
            gas_floor_frac=args.gas_floor_frac,
            ct_floor_base=args.ct_floor_base,
            ct_floor_slope=args.ct_floor_slope,
            ct_floor_t0=args.ct_floor_t0,
            ct_floor_cap=args.ct_floor_cap,
        )
    elif args.compare is not None:
        run_compare(args.bundle, args.compare, years, pass_label=args.pass_label)
    else:
        run_shape_table(args.bundle, years, pass_label=args.pass_label)


if __name__ == "__main__":
    main()
