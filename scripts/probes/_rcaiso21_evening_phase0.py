"""R-CAISO-21 phase 0 (ZERO LP): the evening (h17-22) under-price on keeper 2026-09-30-caiso-r20-overnight.

Part A: model P1 zonal price vs measured OASIS DAM / RTM hub LMP, by hour-of-day window x month,
on the model's fixed-PST hour-of-year clock (the clock `_rcaiso10_object2_price_setter.py` uses).
Zones -> hubs: NP15->TH_NP15, ZP26->TH_ZP26, SP15_rest->TH_SP15, LA_BASIN->DLAP_SCE, SDGE->DLAP_SDGE.

Inputs: the keeper's committed hourly sidecars (results/calibration/rcaiso20_A_span/hourly/).
Writes results/calibration/_rcaiso21/partA_price.json.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso21_evening_phase0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BUNDLE = Path("results/calibration/rcaiso20_A_span/hourly")
LMP = "data/raw/lmp-data/CAISO/CAISO_{m}_hourly_{y}.csv"
OUT = Path("results/calibration/_rcaiso21/partA_price.json")
T = 8760
HOD = np.arange(T) % 24
HUB = {
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
    "SP15_rest": "TH_SP15_GEN-APND",
    "LA_BASIN": "DLAP_SCE-APND",
    "SDGE": "DLAP_SDGE-APND",
}
WINDOWS = {
    "h0_5": (0, 5),
    "h6_9": (6, 9),
    "h10_16": (10, 16),
    "h17_22": (17, 22),
    "h23": (23, 23),
}


def measured(y: int, market: str) -> dict[str, np.ndarray]:
    """Measured hub LMP per model zone on the fixed-PST hour-of-year clock."""
    d = pd.read_csv(LMP.format(m=market, y=y))
    t = pd.to_datetime(d.interval_start_gmt).dt.tz_convert("Etc/GMT+8")
    h = (
        (t - pd.Timestamp(f"{y}-01-01", tz="Etc/GMT+8")).dt.total_seconds() // 3600
    ).astype(int)
    d = d.assign(h=h)
    d = d[(d.h >= 0) & (d.h < T)]
    out = {}
    for z, node in HUB.items():
        s = d[d.node == node].groupby("h").LMP.mean()
        a = np.full(T, np.nan)
        a[s.index.to_numpy()] = s.to_numpy()
        out[z] = a
    return out


def month_of_hour(y: int) -> np.ndarray:
    """Calendar month (1-12) of each fixed-PST hour of year."""
    return (
        pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), "h")
    ).month.to_numpy()


def main() -> None:
    """Tabulate model-minus-measured price by window, month and zone."""
    res = {}
    for y in (2022, 2023, 2024, 2025):
        s = pd.read_parquet(BUNDLE / f"system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        mo = month_of_hour(y)
        yr = {}
        for mkt in ("dam", "rtm"):
            meas = measured(y, mkt)
            zr = {}
            for z in HUB:
                p = s[s.zone == z].sort_values("hour").price.to_numpy()[:T]
                a = meas[z]
                ok = ~np.isnan(a)
                w = {}
                for wn, (lo, hi) in WINDOWS.items():
                    k = ok & (HOD >= lo) & (HOD <= hi)
                    w[wn] = {
                        "model": round(float(p[k].mean()), 2),
                        "actual": round(float(a[k].mean()), 2),
                    }
                    if wn == "h17_22":
                        w[wn]["by_month_diff"] = [
                            round(
                                float(
                                    p[k & (mo == m)].mean() - a[k & (mo == m)].mean()
                                ),
                                1,
                            )
                            for m in range(1, 13)
                        ]
                w["all"] = {
                    "model": round(float(p[ok].mean()), 2),
                    "actual": round(float(a[ok].mean()), 2),
                }
                w["hod_diff"] = [
                    round(
                        float(p[ok & (HOD == h)].mean() - a[ok & (HOD == h)].mean()), 1
                    )
                    for h in range(24)
                ]
                zr[z] = w
            yr[mkt] = zr
        res[y] = yr
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    for y, yr in res.items():
        for mkt in ("dam", "rtm"):
            z = yr[mkt]["SP15_rest"]
            print(
                y,
                mkt,
                "SP15",
                {
                    k: (v["model"], v["actual"])
                    for k, v in z.items()
                    if k.startswith("h") and k != "hod_diff"
                },
            )
            print("   h17-22 diff by month", z["h17_22"]["by_month_diff"])
        print("   dam hod diff SP15", yr["dam"]["SP15_rest"]["hod_diff"])
        print("   dam hod diff NP15", yr["dam"]["NP15"]["hod_diff"])


if __name__ == "__main__":
    main()


def part_b() -> dict:
    """Part B: split the SP15 RT h17-22 residual into the measured-tail hours vs the body.

    Tail = hours whose measured RT hub price is at or above that year's evening p95.
    Also reports the DA-RT spread (measured) in the same hours.
    """
    out = {}
    for y in (2022, 2023, 2024, 2025):
        s = pd.read_parquet(BUNDLE / f"system_{y}.parquet")
        s = s[(s["pass"] == "P1") & (s.zone == "SP15_rest")].sort_values("hour")
        p = s.price.to_numpy()[:T]
        rt = measured(y, "rtm")["SP15_rest"]
        da = measured(y, "dam")["SP15_rest"]
        ev = (HOD >= 17) & (HOD <= 22) & ~np.isnan(rt) & ~np.isnan(da)
        q = np.nanpercentile(rt[ev], 95)
        tail = ev & (rt >= q)
        body = ev & ~tail
        n = ev.sum()
        out[y] = {
            "evening_resid_rt": round(float((p[ev] - rt[ev]).mean()), 2),
            "tail_contrib": round(float((p[tail] - rt[tail]).sum() / n), 2),
            "body_contrib": round(float((p[body] - rt[body]).sum() / n), 2),
            "tail_p95_rt": round(float(q), 1),
            "dart_evening": round(float((da[ev] - rt[ev]).mean()), 2),
            "dart_midday": round(
                float(np.nanmean((da - rt)[(HOD >= 10) & (HOD <= 16)])), 2
            ),
            "dart_overnight": round(float(np.nanmean((da - rt)[HOD <= 5])), 2),
        }
    return out


if __name__ == "__main__":
    b = part_b()
    Path("results/calibration/_rcaiso21/partB_tail.json").write_text(
        json.dumps(b, indent=1)
    )
    for y, v in b.items():
        print(y, v)
