"""pjm-119 readout: C3c any-zone tail + monthly LMP for a solved bundle.

Scores a bundle's ``hourly/system_<year>.parquet`` on the SAME definitions the
dashboard payload and the C3c scorer use, so a diagnostic probe's numbers are
directly comparable to a registered run's without regenerating the payload:

* **C3c tail** — ``render_calibration_html._tail_hours``: hours whose MAX zonal
  LMP exceeds the ISO threshold ($200 for PJM), model and actual on the identical
  rule (the actual hub series enters as a single "zone").
* **Monthly LMP** — demand-weighted system price per month vs the actual RT hub
  series, the basis the pjm-118 lane's Jun −19.9 $/MWh table was built on.

Usage:
    python scripts/probes/pjm119_eastcut_readout.py results/probes/pjm119_eastcut \
        --years 2025 [--iso PJM]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import render_calibration_html as rch  # noqa: E402


def readout(bundle: Path, iso: str, year: int) -> dict:
    """Return the tail counts and monthly price table for one solved year."""
    sy = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    hours = int(sy["hour"].max()) + 1
    price_by_zone: dict[str, np.ndarray] = {}
    dem_by_zone: dict[str, np.ndarray] = {}
    for zone, zg in sy.groupby("zone", observed=True):
        p = np.full(hours, np.nan)
        d = np.zeros(hours)
        hr = zg["hour"].to_numpy()
        p[hr] = zg["price"].to_numpy(float)
        d[hr] = zg["demand"].to_numpy(float)
        price_by_zone[str(zone)] = p
        dem_by_zone[str(zone)] = d

    thr = rch.TAIL_THRESHOLD.get(iso, 200.0)
    actual = rch._actual_lmp_hourly(iso, year)
    model_tail = rch._tail_hours(price_by_zone, thr)
    actual_tail = rch._tail_hours({"hub": actual}, thr) if actual is not None else None

    # Demand-weighted system hourly price (the payload's mp_iso construction).
    pz = np.vstack([price_by_zone[z] for z in price_by_zone])
    dz = np.vstack([dem_by_zone[z] for z in dem_by_zone])
    wsum = np.where(np.isfinite(pz), dz, 0.0).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mp = np.nansum(np.where(np.isfinite(pz), pz * dz, 0.0), axis=0) / wsum
    mp[wsum <= 0] = np.nan

    rt = rch._actual_rt_padded(iso, year, hours)
    idx = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    tbl = pd.DataFrame({"model": mp}, index=idx)
    if rt is not None:
        tbl["actual"] = rt
    # Demand-weighted monthly means (weights = the same total demand).
    w = pd.Series(np.where(wsum > 0, wsum, np.nan), index=idx)
    out_rows = []
    for m, g in tbl.groupby(tbl.index.month):
        ww = w.loc[g.index]
        mm = float(np.nansum(g["model"] * ww) / np.nansum(ww))
        aa = (
            float(np.nansum(g["actual"] * ww) / np.nansum(ww))
            if "actual" in g
            else float("nan")
        )
        out_rows.append((m, mm, aa, mm - aa))
    ann_m = float(np.nansum(tbl["model"] * w) / np.nansum(w))
    ann_a = (
        float(np.nansum(tbl["actual"] * w) / np.nansum(w))
        if "actual" in tbl
        else float("nan")
    )
    return {
        "year": year,
        "threshold": thr,
        "model_tail": model_tail,
        "actual_tail": actual_tail,
        "monthly": out_rows,
        "annual": (ann_m, ann_a, 100.0 * (ann_m - ann_a) / ann_a if ann_a else None),
        "p99": float(np.nanpercentile(mp, 99)),
        "max": float(np.nanmax(mp)),
        "gt100": int(np.nansum(mp > 100)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    ap.add_argument("--iso", default="PJM")
    ap.add_argument("--years", nargs="+", type=int, default=[2025])
    args = ap.parse_args()

    for year in args.years:
        r = readout(Path(args.bundle), args.iso, year)
        print(f"\n=== {args.iso} {year}  (bundle {args.bundle})")
        print(
            f"C3c any-zone tail > ${r['threshold']:.0f}: "
            f"model {r['model_tail']} h  |  actual {r['actual_tail']} h"
        )
        am, aa, pct = r["annual"]
        print(
            f"C3a load-weighted mean LMP: model {am:.2f} vs actual {aa:.2f} "
            f"({pct:+.1f}%)"
        )
        print(
            f"system LMP p99 {r['p99']:.1f}  max {r['max']:.1f}  "
            f"hours > $100: {r['gt100']}"
        )
        print("month  model  actual   delta")
        for m, mm, aa_, dd in r["monthly"]:
            print(f"  {m:>2}   {mm:6.2f} {aa_:7.2f} {dd:+7.2f}")


if __name__ == "__main__":
    main()
