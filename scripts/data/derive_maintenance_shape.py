"""Derive a forecast-mode monthly planned-maintenance shape from CAMPD outages.

The forecast availability model concentrates planned outages (POF) into the
spring/autumn shoulder months. Historically this was a *flat* block smeared
across ``{3,4,5,10,11}`` (``_CC_SHOULDER_MONTHS``) — every shoulder hour carried
the same POF, every other hour carried none. This script replaces that flat
heuristic with a **historically-derived monthly maintenance shape**: a 12-month
weight per plant group, learned from the measured timing/magnitude of
spring/autumn maintenance in the committed CAMPD unit-outage extracts.

Source: ``data/raw/campd-unit-outages*.csv`` (the per-unit, capacity-weighted,
dated outage windows for all six ISOs, written by
``scripts/data/derive_campd_unit_outages.py``). These have already passed the
revealed-availability filter (economic idling dropped), so what remains is the
real outage footprint — forced + planned. The *seasonal concentration* over the
flat forced-outage floor is the planned-maintenance signal.

Method (per plant group, pooled across all ISOs and years for a forecast-mode
shape that is **not** pinned to any one backcast year):

1. Spread each outage window's ``unit_capacity_mw`` across the calendar months it
   spans (weighted by the days it overlaps each month), giving outage-MW-days per
   (group, month).
2. Divide by the group's total capacity-days in each month to get a capacity-
   weighted monthly outage *rate* ``r[m]`` (fraction of fleet out).
3. Isolate the planned-maintenance component as the excess over the annual
   minimum month (the forced-outage floor): ``e[m] = max(0, r[m] - min_k r[k])``.
   The minimum month is typically a summer/winter peak, where (by design) almost
   no planned maintenance is scheduled.
4. Normalize to a month-length-weighted mean of 1: ``w[m] = e[m] · H / Σ(e[k]·h[k])``
   with ``h[m]`` the hours in month ``m`` of a 365-day year and ``H = 8760``.

``w[m]`` is the bakeable constant (:data:`MAINTENANCE_MONTHLY_SHAPE` in
``config/constants.py``). At apply time (``data.fleet.generators_to_fleet_arrays``,
forecast mode only) the per-hour planned-maintenance derate is
``B_group · w[group][month]`` where ``B_group = POF[group] · shoulder_hours / H``
is the group's *existing* annual POF budget. Because ``w`` has a month-weighted
mean of 1, ``Σ maint[m]·h[m] = B·H = POF·shoulder_hours`` exactly — the annual
planned-outage budget (GADS-anchored) is **conserved**; only its seasonal
*distribution* is sharpened from the rigid 5-month block to the measured shape.

This is a forecast-mode structural default. It does NOT touch the backcast
historic overlay (``data/outages.py``), which remains the calibration path.

Run: ``python scripts/data/derive_maintenance_shape.py`` (prints the constant block).
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent

# Hours per calendar month in a 365-day (non-leap) reference year; the weighting
# basis for both the capacity-days denominator and the mean-1 normalization.
_MONTH_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], dtype=float)
_MONTH_HOURS = _MONTH_DAYS * 24.0
_H = float(_MONTH_HOURS.sum())  # 8760

# Plant groups carried in THERMAL_AVAILABILITY whose forecast POF this shape
# replaces. Groups with too few outage observations fall back to the pooled
# all-thermal shape (so a sparse class still gets a sensible seasonal curve).
_TARGET_GROUPS = (
    "COAL",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
)
# Minimum distinct (facility, year) outage observations for a group to use its
# own shape rather than the pooled fallback.
_MIN_OBS = 12


def _month_overlap_days(start: pd.Timestamp, end: pd.Timestamp) -> np.ndarray:
    """Days of an outage window ``[start, end)`` falling in each calendar month.

    Returns a length-12 array (Jan..Dec), pooling across whatever years the
    window spans onto a single 12-month axis (a forecast shape has no year).
    """
    out = np.zeros(12, dtype=float)
    if end <= start:
        return out
    cur = start
    while cur < end:
        # End of the current month.
        if cur.month == 12:
            nxt = pd.Timestamp(year=cur.year + 1, month=1, day=1)
        else:
            nxt = pd.Timestamp(year=cur.year, month=cur.month + 1, day=1)
        seg_end = min(end, nxt)
        out[cur.month - 1] += (seg_end - cur).total_seconds() / 86400.0
        cur = seg_end
    return out


def load_unit_outages() -> pd.DataFrame:
    """Concatenate every committed ``campd-unit-outages*.csv`` (all ISOs)."""
    paths = sorted(glob.glob(str(REPO / "data" / "raw" / "campd-unit-outages*.csv")))
    frames = []
    for p in paths:
        df = pd.read_csv(p)
        df["_iso_file"] = Path(p).stem
        frames.append(df)
    if not frames:
        raise FileNotFoundError("no campd-unit-outages*.csv under data/raw/")
    return pd.concat(frames, ignore_index=True)


def monthly_outage_mwdays(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Outage-MW-days per (plant_group, month), pooled across ISOs and years."""
    acc: dict[str, np.ndarray] = {}
    obs: dict[str, int] = {}
    for _, row in df.iterrows():
        grp = str(row["plant_group"])
        cap = float(row["unit_capacity_mw"])
        if cap <= 0:
            continue
        start = pd.Timestamp(row["outage_start"])
        end = pd.Timestamp(row["outage_end"])
        days = _month_overlap_days(start, end)
        if days.sum() <= 0:
            continue
        acc.setdefault(grp, np.zeros(12))
        acc[grp] += cap * days
        obs[grp] = obs.get(grp, 0) + 1
    acc["_obs"] = obs  # type: ignore[assignment]
    return acc


def group_capacity_mw(df: pd.DataFrame) -> dict[str, float]:
    """Total distinct-unit nameplate per group (the capacity-rate denominator).

    A unit appears once per outage window; dedupe on (file, facility, unit) so a
    unit with several outages is counted once toward its group's fleet capacity.
    """
    key = ["_iso_file", "facility_id", "unit_id"]
    uniq = df.drop_duplicates(subset=key)
    return uniq.groupby("plant_group")["unit_capacity_mw"].sum().to_dict()


def shape_from_rate(rate: np.ndarray) -> np.ndarray:
    """Excess-over-minimum-month, normalized to month-length-weighted mean 1."""
    excess = np.maximum(0.0, rate - rate.min())
    denom = float((excess * _MONTH_HOURS).sum())
    if denom <= 0:
        return np.ones(12)  # degenerate: flat (no seasonal signal)
    return excess * _H / denom


def derive() -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, int]]:
    """Return ``(per_group_shape, pooled_thermal_shape, obs_counts)``."""
    df = load_unit_outages()
    mwdays = monthly_outage_mwdays(df)
    obs: dict[str, int] = mwdays.pop("_obs")  # type: ignore[assignment]
    cap = group_capacity_mw(df)

    # Pooled all-thermal rate (capacity-weighted) for the fallback shape.
    pooled_mwdays = np.zeros(12)
    pooled_cap = 0.0
    for grp, md in mwdays.items():
        pooled_mwdays += md
        pooled_cap += cap.get(grp, 0.0)
    pooled_rate = (
        pooled_mwdays / (pooled_cap * _MONTH_DAYS) if pooled_cap else pooled_mwdays
    )
    pooled_shape = shape_from_rate(pooled_rate)

    shapes: dict[str, np.ndarray] = {}
    for grp in _TARGET_GROUPS:
        if grp not in mwdays or obs.get(grp, 0) < _MIN_OBS or cap.get(grp, 0.0) <= 0:
            shapes[grp] = pooled_shape
            continue
        rate = mwdays[grp] / (cap[grp] * _MONTH_DAYS)
        shapes[grp] = shape_from_rate(rate)
    return shapes, pooled_shape, obs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--emit",
        choices=["report", "constant"],
        default="report",
        help="report = human summary; constant = paste-ready Python dict.",
    )
    args = ap.parse_args()

    shapes, pooled, obs = derive()
    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    if args.emit == "constant":
        print("MAINTENANCE_MONTHLY_SHAPE: dict[str, tuple[float, ...]] = {")
        for grp in _TARGET_GROUPS:
            vals = ", ".join(f"{v:.3f}" for v in shapes[grp])
            print(f'    "{grp}": ({vals}),')
        pv = ", ".join(f"{v:.3f}" for v in pooled)
        print(f'    "_POOLED": ({pv}),')
        print("}")
        return

    print(f"{'group':<12} {'obs':>5}  " + " ".join(f"{m:>5}" for m in months))
    for grp in _TARGET_GROUPS:
        n = obs.get(grp, 0)
        flag = "" if n >= _MIN_OBS else "  (pooled fallback)"
        vals = " ".join(f"{v:5.2f}" for v in shapes[grp])
        print(f"{grp:<12} {n:>5}  {vals}{flag}")
    print(f"{'_POOLED':<12} {'':>5}  " + " ".join(f"{v:5.2f}" for v in pooled))
    print(
        "\nWeights are month-length-weighted to mean 1 (Σ w·hours = 8760). "
        "Apply as B_group·w[month], B_group = POF·shoulder_hours/8760."
    )


if __name__ == "__main__":
    main()
