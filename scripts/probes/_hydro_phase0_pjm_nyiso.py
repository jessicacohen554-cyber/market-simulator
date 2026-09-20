"""Phase-0 hydro-physics census for PJM and NYISO (zero LP).

Measures the designated keepers' own committed class-hourly sidecars against
each ISO's **own published** hourly hydro series — PJM's Data Miner
``gen_by_fuel`` ``Hydro`` category and NYISO's real-time fuel-mix ``Hydro``
category — never EIA-930 ``NG: WAT``, which folds pumped-storage discharge for
both BAs (PJM is in ``EIA930_PS_FOLDED_INTO_WAT``; NYISO's WAT is the BA
aggregate). The question this answers is rule-17 ``[R-FLOOR-WINDOW]`` shaped:
*which hours does the model's hydro sit in, against the hours the real fleet
sits in*, and how much of the month's water does the model concentrate.

Emits one JSON blob per (ISO, year) with the statistics the PRECOMMIT needs:

* zero/near-zero hour counts (the "0 hydro hours" claim, measured)
* p5 / p50 / p95 of the hourly fleet output, model vs actual
* top-100 net-load hour capacity factor, model vs actual (the "dispatches
  like a peaker" claim)
* within-month day-to-day energy correlation and amplitude ratio
* hour-of-day shape correlation
* summer (Jun-Aug) peak-window mean, model vs actual

Run: ``uv run --no-sync python3 scripts/probes/_hydro_phase0_pjm_nyiso.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from market_sim.data.fleet import _hour_to_month_index  # noqa: E402

KEEPERS = {
    "PJM": ("results/calibration/pjm_h13_meritalloc_span", [2023, 2024, 2025]),
    "NYISO": ("results/calibration/nyiso247_fuelinv_span", [2022, 2023, 2024, 2025]),
}


def model_hydro(bundle: str, year: int) -> np.ndarray:
    """Return the keeper's P1 hourly conventional-hydro MW, shape ``(8760,)``."""
    df = pd.read_parquet(ROOT / bundle / "hourly" / f"class_hourly_{year}.parquet")
    sub = df[(df["klass"] == "hydro") & (df["pass"] == "P1")].sort_values("hour")
    out = np.zeros(8760, dtype=float)
    out[sub["hour"].to_numpy(dtype=int)] = sub["mw"].to_numpy(dtype=float)
    return out


def model_demand(bundle: str, year: int) -> np.ndarray:
    """Return the keeper's P1 ISO-total hourly demand, shape ``(8760,)``.

    ``system_<year>.parquet`` is per ZONE, so the ISO total is the per-hour sum
    over zones — the load the top-load-hour ranking below must be taken on.
    """
    df = pd.read_parquet(ROOT / bundle / "hourly" / f"system_{year}.parquet")
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    tot = df.groupby("hour")["demand"].sum().sort_index()
    out = np.zeros(8760, dtype=float)
    out[tot.index.to_numpy(dtype=int)] = tot.to_numpy(dtype=float)
    return out


def actual_pjm(year: int) -> np.ndarray | None:
    """PJM Data Miner ``gen_by_fuel`` Hydro on the model's fixed-EST 8760 clock."""
    path = ROOT / "data/raw/ISO-specific-gen-data" / f"PJM_{year}_gen_by_fuel.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["datetime_beginning_utc", "fuel_type", "mw"])
    df = df[df["fuel_type"] == "Hydro"]
    est = (
        pd.to_datetime(df["datetime_beginning_utc"], format="mixed", errors="coerce")
        .dt.tz_localize("UTC")
        .dt.tz_convert("Etc/GMT+5")
        .dt.tz_localize(None)
    )
    return _to_8760(est, df["mw"].to_numpy(dtype=float), year)


def actual_nyiso(year: int) -> np.ndarray | None:
    """NYISO real-time fuel-mix Hydro on the model's fixed-EST 8760 clock."""
    path = ROOT / "data/raw/NYISO/fuel-mix" / f"NYISO_fuelmix_hourly_{year}.csv.gz"
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["interval_start_utc", "fuel_category", "gen_mw"])
    df = df[df["fuel_category"] == "Hydro"]
    est = (
        pd.to_datetime(df["interval_start_utc"], format="mixed", utc=True)
        .dt.tz_convert("Etc/GMT+5")
        .dt.tz_localize(None)
    )
    return _to_8760(est, df["gen_mw"].to_numpy(dtype=float), year)


def _to_8760(est: pd.Series, vals: np.ndarray, year: int) -> np.ndarray:
    """Place a tz-naive EST stamp series onto the model's fixed non-leap 8760."""
    from market_sim.data.eia930.frames import _MONTH_START_HOUR

    month = est.dt.month.to_numpy()
    day = est.dt.day.to_numpy()
    hour = est.dt.hour.to_numpy()
    yr = est.dt.year.to_numpy()
    ok = est.notna().to_numpy() & (yr == year) & ~((month == 2) & (day == 29))
    hoy = (
        np.array(_MONTH_START_HOUR)[month[ok].astype(int) - 1]
        + (day[ok].astype(int) - 1) * 24
        + hour[ok].astype(int)
    )
    out = np.full(8760, np.nan)
    out[hoy] = vals[ok]
    # Bridge short holes (DST spring-forward etc.) so the stats are on 8760.
    s = pd.Series(out).interpolate(limit=6, limit_direction="both")
    return s.to_numpy()


def day_index(hours: int = 8760) -> np.ndarray:
    return np.arange(hours) // 24


def census(model: np.ndarray, actual: np.ndarray, demand: np.ndarray) -> dict:
    """Return the model-vs-actual hydro statistics the PRECOMMIT quotes."""
    ok = np.isfinite(actual)
    m, a, d = model[ok], actual[ok], demand[ok]
    cap = float(np.nanmax(a))  # measured fleet high-water mark, a scale reference

    def q(x, p):
        return float(np.percentile(x, p))

    # Top-100 gross-load hours: does the class behave like a peaker?
    top = np.argsort(d)[-100:]
    # Diurnal shape
    hod = np.arange(len(m)) % 24
    m_hod = np.array([m[hod == h].mean() for h in range(24)])
    a_hod = np.array([a[hod == h].mean() for h in range(24)])
    # Within-month day-to-day energy (the nyiso-218 dimension)
    di = day_index(8760)[ok]
    mi = _hour_to_month_index(8760)[ok]
    md = pd.Series(m).groupby(di).sum()
    ad = pd.Series(a).groupby(di).sum()
    dm = pd.Series(mi).groupby(di).first()
    rs, amps = [], []
    for mo in range(12):
        sel = dm == mo
        if sel.sum() < 5:
            continue
        x, y = md[sel.to_numpy()], ad[sel.to_numpy()]
        if x.std() > 0 and y.std() > 0:
            rs.append(float(np.corrcoef(x, y)[0, 1]))
            amps.append(float(x.std() / y.std()))
    # Summer peak window (Jun-Aug, HE 14-19 EST)
    summer = np.isin(mi, [5, 6, 7]) & np.isin(hod, [14, 15, 16, 17, 18, 19])
    return {
        "measured_max_mw": round(cap, 1),
        "annual_twh_model": round(float(m.sum()) / 1e6, 4),
        "annual_twh_actual": round(float(a.sum()) / 1e6, 4),
        "hours_below_1pct_of_max_model": int((m < 0.01 * cap).sum()),
        "hours_below_1pct_of_max_actual": int((a < 0.01 * cap).sum()),
        "hours_below_25pct_of_max_model": int((m < 0.25 * cap).sum()),
        "hours_below_25pct_of_max_actual": int((a < 0.25 * cap).sum()),
        "p5_model": round(q(m, 5), 1),
        "p5_actual": round(q(a, 5), 1),
        "p50_model": round(q(m, 50), 1),
        "p50_actual": round(q(a, 50), 1),
        "p95_model": round(q(m, 95), 1),
        "p95_actual": round(q(a, 95), 1),
        "top100_load_hours_mean_model": round(float(m[top].mean()), 1),
        "top100_load_hours_mean_actual": round(float(a[top].mean()), 1),
        "summer_peak_window_mean_model": round(float(m[summer].mean()), 1),
        "summer_peak_window_mean_actual": round(float(a[summer].mean()), 1),
        "hod_shape_r": round(float(np.corrcoef(m_hod, a_hod)[0, 1]), 3),
        "within_month_daily_r_mean": round(float(np.mean(rs)), 3) if rs else None,
        "within_month_daily_amp_ratio": (
            round(float(np.mean(amps)), 3) if amps else None
        ),
        "hourly_cv_model": round(float(m.std() / max(m.mean(), 1e-9)), 3),
        "hourly_cv_actual": round(float(a.std() / max(a.mean(), 1e-9)), 3),
    }


def main() -> None:
    out: dict = {}
    for iso, (bundle, years) in KEEPERS.items():
        out[iso] = {}
        for y in years:
            try:
                m = model_hydro(bundle, y)
            except FileNotFoundError:
                out[iso][y] = {"error": "no class_hourly sidecar"}
                continue
            a = actual_pjm(y) if iso == "PJM" else actual_nyiso(y)
            if a is None:
                out[iso][y] = {"error": "no published hourly hydro for this year"}
                continue
            out[iso][y] = census(m, a, model_demand(bundle, y))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
