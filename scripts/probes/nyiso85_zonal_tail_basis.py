"""nyiso-85 Task 1b — the C3c basis asymmetry, measured on NYISO's real zonal prices.

``calibration_verdict.score_price_tail`` compares two things that are NOT the
same statistic:

* **model side** — the count of hours the LP's **max zonal dual** exceeds the
  threshold, and
* **actual side** — the count of hours the committed hub series exceeds it,
  where NYISO's hub is the simple mean of the ELEVEN INTERNAL ZONES
  (``derive_actual_lmp.py``: "the system price is the simple mean of the eleven
  internal zones").

max-over-zones vs mean-over-zones. This probe measures the size of that wedge
from the raw 5-minute zonal RTD LBMP files by rebuilding, on the model's own
chronological 8760 clock, three actual hourly series per year:

* ``hub``      — the 11-zone mean (reproduces the committed parquet; asserted),
* ``max_zone`` — the max over the 11 internal zones (the model-side statistic),
* per-model-zone means under ``derive_actual_lmp.NYISO_ZONE_MAP``.

It reports the >threshold hour count on each basis, and for the hub-tail hours
the zonal dispersion (how BROAD the high prices were) — the quantity that says
whether NYISO's scored tail is a system-wide shortage or one load pocket pulling
an 11-zone average up.

Rule 22 [R-HOLDOUT]: 2023-2025 only. Scoring-side characterisation of committed
actuals — no LP, no model input touched.

Usage:
    PYTHONPATH=$PWD:$PWD/src .venv/bin/python \
        scripts/probes/nyiso85_zonal_tail_basis.py --fetch-cache <dir> [--json-out o.json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from nyiso85_tail_anatomy import (  # noqa: E402
    NYISO_INTERNAL,
    NYISO_ZONE_MAP,
    YEARS,
    _hub_hourly,
    _is_leap,
    _load_5min_month,
    _LEAP_SKIP_INDEX,
)


def _chrono_index(ts_local: pd.Series, year: int) -> np.ndarray:
    """Map published PREVAILING-clock timestamps to the model's 8760 row index.

    Inverse of ``nyiso85_tail_anatomy._utc_of_hour``: convert prevailing -> UTC
    using the US DST rule, take whole hours since Jan 1 05:00Z, then subtract the
    24-hour local-standard Feb 29 that the model calendar drops in a leap year.
    Rows outside [0, 8760) (i.e. Feb 29 itself) come back as -1.
    """
    y = year
    mar = dt.datetime(y, 3, 1)
    second_sun = mar + dt.timedelta(days=(6 - mar.weekday()) % 7 + 7)
    nov = dt.datetime(y, 11, 1)
    first_sun = nov + dt.timedelta(days=(6 - nov.weekday()) % 7)
    dst_start = pd.Timestamp(second_sun.replace(hour=2))  # prevailing-clock
    dst_end = pd.Timestamp(first_sun.replace(hour=2))
    is_edt = (ts_local >= dst_start) & (ts_local < dst_end)
    off = np.where(is_edt, 4, 5)
    utc = ts_local + pd.to_timedelta(off, unit="h")
    k = ((utc - pd.Timestamp(year, 1, 1, 5)) // pd.Timedelta("1h")).astype("int64")
    if _is_leap(year):
        k = np.where(k >= _LEAP_SKIP_INDEX + 24, k - 24, k)
        k = np.where(
            (k >= _LEAP_SKIP_INDEX) & (k < _LEAP_SKIP_INDEX + 24), -1, k
        )  # Feb 29 itself
    k = np.where((k < 0) | (k >= 8760), -1, k)
    return np.asarray(k)


def _zonal_hourly(year: int, cache: Path | None) -> pd.DataFrame | None:
    """Per-internal-zone hourly actual RT LBMP on the model's 8760 clock."""
    frames = []
    for month in range(1, 13):
        m5 = _load_5min_month(year, month, cache=cache)
        if m5 is None:
            print(f"  [warn] {year}-{month:02d} 5-minute source missing", file=sys.stderr)
            continue
        m5 = m5.copy()
        m5["k"] = _chrono_index(m5["ts"], year)
        m5 = m5[m5["k"] >= 0]
        frames.append(m5.groupby(["k", "Name"], observed=True)["lbmp"].mean())
    if not frames:
        return None
    s = pd.concat(frames)
    wide = s.groupby(level=[0, 1]).mean().unstack("Name")
    return wide.reindex(range(8760)).reindex(columns=list(NYISO_INTERNAL))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--threshold", type=float, default=300.0)
    ap.add_argument("--fetch-cache", type=Path, default=None)
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args(argv)
    thr = float(args.threshold)

    out: dict = {"threshold": thr, "years": {}}
    for year in YEARS:
        wide = _zonal_hourly(year, args.fetch_cache)
        if wide is None:
            continue
        hub = wide.mean(axis=1)
        mx = wide.max(axis=1)

        # Provenance: the rebuilt hub must reproduce the committed scoring series.
        committed = _hub_hourly(year).set_index("hour")["rt"].reindex(range(8760))
        both = committed.notna() & hub.notna()
        mae = float(np.abs(committed[both] - hub[both]).mean())

        mzone = {
            mz: wide[[z for z in members if z in wide.columns]].mean(axis=1)
            for mz, members in NYISO_ZONE_MAP.items()
        }

        tail_mask = hub > thr
        disp = []
        for k in np.flatnonzero(tail_mask.to_numpy()):
            row = wide.iloc[k].dropna()
            if row.empty:
                continue
            disp.append(
                {
                    "hour": int(k),
                    "hub": round(float(hub.iloc[k]), 1),
                    "zmin": round(float(row.min()), 1),
                    "zmed": round(float(row.median()), 1),
                    "zmax": round(float(row.max()), 1),
                    "n_zones_gt": int((row > thr).sum()),
                    "top_share_of_hub": round(float(row.max() / row.sum()), 3),
                }
            )
        rec = {
            "hub_rebuild_mae_vs_committed": round(mae, 4),
            "count_hub_gt": int(tail_mask.sum()),
            "count_maxzone_gt": int((mx > thr).sum()),
            "count_by_model_zone_gt": {
                mz: int((s > thr).sum()) for mz, s in mzone.items()
            },
            "median_zones_gt_in_hub_tail": (
                float(np.median([d["n_zones_gt"] for d in disp])) if disp else None
            ),
            "median_top_share_in_hub_tail": (
                float(np.median([d["top_share_of_hub"] for d in disp])) if disp else None
            ),
            "hub_tail_dispersion": disp,
        }
        out["years"][str(year)] = rec

        print(f"\n=== {year} (threshold ${thr:.0f}) ===")
        print(f"  hub rebuild MAE vs committed scoring series: {mae:.4f} $/MWh")
        print(f"  actual hours hub (11-zone MEAN)  > thr : {rec['count_hub_gt']:>4}   <- C3c actual side")
        print(f"  actual hours MAX-ZONE            > thr : {rec['count_maxzone_gt']:>4}   <- basis the MODEL side uses")
        print("  actual hours per MODEL zone > thr:")
        for mz, n in sorted(rec["count_by_model_zone_gt"].items(), key=lambda x: -x[1]):
            print(f"      {mz:<16} {n:>4}")
        if disp:
            print(
                f"  within the {len(disp)} hub-tail hours: median zones>thr = "
                f"{rec['median_zones_gt_in_hub_tail']:.0f}/11, "
                f"median top-zone share of the 11-zone sum = "
                f"{rec['median_top_share_in_hub_tail']:.1%} (1/11 = 9.1% would be flat)"
            )

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(out, indent=1))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
