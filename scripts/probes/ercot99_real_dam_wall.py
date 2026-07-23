"""ERCOT-99 real DAM offer-stack measurement at the missed tail hours (charter
step 1, measured side).

Reconstructs, from the committed 2023 60-Day DAM Gen Resource disclosure (QSE
submitted energy offer curves), the ERCOT day-ahead supply stack at the missed
tail hours: how much thermal capability was OFFERED below $200, and what price
the marginal cleared/last-1-5-GW segment carried.  This is the measured wall the
model's cleared-share surface is derived from — quoting it at the missed hours
shows how much of reality's supply sat cheap vs how the offers ladder up to the
tail price.  DAM basis (the only 2023 energy-offer corpus on disk; the 60-Day
SCED disclosure is 2024/2025 sample-days only, so no 2023 RT ladder exists).

Clock: DAM Hour-Ending (CPT prevailing) → model CST hour-beginning via the
committed deriver's DST shift, so the per-hour stack aligns to the missed set.

Usage:
    python -m scripts.probes.ercot99_real_dam_wall [--year 2023] \\
        [--bundle results/calibration/ercot98_np6_hsl_fullspan]
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.data.derive_actual_lmp import (  # noqa: E402
    _MONTH_START_HOUR as _MSH,
    _PrevailingShift,
)

TAIL = 200.0
_MONTH_START_HOUR = np.asarray(_MSH, dtype=np.int64)
GAS = ("CCGT90", "CCLE90", "SCGT90", "SCLE90")
THERMAL = GAS + ("GSREH", "GSNONR", "GSSUP", "CLLIG")  # + steam + coal-lignite
_MW = [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]
_PR = [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]


def _load_dam(year: int, restypes: tuple[str, ...]) -> pd.DataFrame:
    cols = ["Delivery Date", "Hour Ending", "Resource Type", "HSL",
            "Awarded Quantity", "Resource Status"] + _MW + _PR
    frames = []
    for f in sorted(glob.glob(str(REPO / f"data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{year}_*.parquet"))):
        df = pd.read_parquet(f, columns=cols)
        frames.append(df[df["Resource Type"].isin(restypes)].copy())
    return pd.concat(frames, ignore_index=True)


def _hoy(df: pd.DataFrame, year: int) -> np.ndarray:
    dt = pd.to_datetime(df["Delivery Date"], format="%m/%d/%Y")
    mo, dy = dt.dt.month.to_numpy(), dt.dt.day.to_numpy()
    he = df["Hour Ending"].astype(int).to_numpy()
    hod = he - 1  # hour-beginning
    shift = _PrevailingShift(year, "America/Chicago")
    keep = ~((mo == 2) & (dy == 29)) & (dt.dt.year.to_numpy() == year)
    sh = np.array([shift(int(m), int(d), int(h), False)
                   for m, d, h in zip(mo[keep], dy[keep], hod[keep])])
    out = np.full(len(df), -1, dtype=np.int64)
    out[keep] = _MONTH_START_HOUR[mo[keep] - 1] + (dy[keep] - 1) * 24 + hod[keep] - sh
    return out


def _stack_segments(sub: pd.DataFrame):
    """Aggregate offer segments (mw, price) across all rows in a group."""
    MW = sub[_MW].to_numpy(float)
    PR = sub[_PR].to_numpy(float)
    seg_mw, seg_pr = [], []
    prev = np.zeros(len(sub))
    for k in range(10):
        q, p = MW[:, k], PR[:, k]
        ok = np.isfinite(q) & np.isfinite(p)
        step = np.where(ok, np.maximum(q - prev, 0.0), 0.0)
        seg_mw.append(step)
        seg_pr.append(np.where(ok, p, np.nan))
        prev = np.where(ok, np.maximum(prev, q), prev)
    return np.concatenate(seg_mw), np.concatenate(seg_pr)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ercot99_real_dam_wall")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--bundle", default="results/calibration/ercot98_np6_hsl_fullspan")
    args = ap.parse_args(argv)
    year = args.year

    # Missed-hour set from the keeper sidecar.
    s = pd.read_parquet(REPO / args.bundle / "hourly" / f"system_{year}.parquet")
    p1 = s[s["pass"] == "P1"]
    price = p1.pivot(index="hour", columns="zone", values="price")
    dem = p1.pivot(index="hour", columns="zone", values="demand")
    hub = ((price * dem).sum(axis=1) / dem.sum(axis=1)).reindex(range(8760)).to_numpy()
    lmp = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet")
    rt = lmp[lmp["year"] == year].set_index("hour")["rt"].reindex(range(8760)).to_numpy()
    missed = (rt > TAIL) & (hub <= TAIL)
    midx = set(np.where(missed)[0].tolist())

    df = _load_dam(year, THERMAL)
    df["hoy"] = _hoy(df, year)
    df = df[df["hoy"] >= 0]
    covered = sorted(h for h in midx if h in set(df["hoy"].unique()))
    print(f"[coverage] missed hours {len(midx)} | DAM-covered {len(covered)} "
          f"(disclosure spans Nov{year-1}-Oct{year})")

    # Per covered missed hour: offered-<$200 MW, awarded MW, marginal awarded price.
    rows = []
    gas_set = set(GAS)
    for h in covered:
        g = df[df["hoy"] == h]
        mw, pr = _stack_segments(g)
        ok = mw > 0
        mw, pr = mw[ok], pr[ok]
        order = np.argsort(pr)
        mw_s, pr_s = mw[order], pr[order]
        below = mw_s[pr_s < TAIL].sum()
        total_off = mw_s.sum()
        awarded = g["Awarded Quantity"].sum()
        # marginal offer at the cleared depth (awarded MW into the stack)
        cum = np.cumsum(mw_s)
        k = min(int(np.searchsorted(cum, awarded)), len(pr_s) - 1)
        marg_award = pr_s[k]
        # price the last 1 GW of the OFFERED stack carried (top of curve)
        below_top = pr_s[cum >= (total_off - 1000)]
        top1gw = below_top.min() if len(below_top) else np.nan
        rows.append((h, below, total_off, awarded, marg_award, top1gw, rt[h], hub[h]))

    arr = pd.DataFrame(rows, columns=["hoy", "off_below200", "off_total",
                                      "awarded", "marg_award_pr", "top1gw_pr",
                                      "rt", "hub"])
    print("\n[real DAM wall] over the covered missed hours (mean):")
    print(f"    thermal MW OFFERED < $200      : {arr['off_below200'].mean():8.0f}")
    print(f"    thermal MW OFFERED total        : {arr['off_total'].mean():8.0f}")
    print(f"    thermal MW AWARDED (DA cleared) : {arr['awarded'].mean():8.0f}")
    print(f"    marginal AWARDED offer price    : ${arr['marg_award_pr'].mean():7.1f} "
          f"(median ${arr['marg_award_pr'].median():.1f})")
    print(f"    price of the top ~1 GW offered  : ${arr['top1gw_pr'].mean():7.1f} "
          f"(median ${arr['top1gw_pr'].median():.1f})")
    print(f"    actual RT (ref)                 : ${arr['rt'].mean():7.0f}")
    print(f"    share of offered stack < $200   : "
          f"{(arr['off_below200'] / arr['off_total']).mean():.1%}")

    cal = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    print("\n[detail] August heat-wave missed hours (DAM offered<$200 / awarded / marg-award / RT):")
    for _, r in arr.iterrows():
        d = cal[int(r["hoy"])]
        if d.month == 8 and 14 <= d.hour <= 19 and d.day in (4, 7, 8, 10, 11):
            print(f"    {d.strftime('%m-%d')} HE{d.hour+1:02d}: off<200 {r['off_below200']:6.0f} "
                  f"| awarded {r['awarded']:6.0f} | marg-award ${r['marg_award_pr']:6.1f} "
                  f"| top1GW ${r['top1gw_pr']:7.1f} | RT ${r['rt']:6.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
