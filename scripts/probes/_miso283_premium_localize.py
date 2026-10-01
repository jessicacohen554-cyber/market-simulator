#!/usr/bin/env python3
"""miso-283 phase 0 (ZERO LP): localize the keeper's MISO zone-price premium over measured hubs.

Joins the designated keeper's committed P1 zone prices
(``results/calibration/miso280_span/hourly/system_<Y>.parquet``) to the measured
MISO named-hub LMPs (RT final and DA ex-post, ``data/raw/lmp-data/MISO``) on the
model's 8760 index (hour 0 = HE01, market time, Dec 31 dropped in a leap year —
the convention the miso-282 probes use). Hub -> zone mapping is
``scripts/data/derive_miso_hub_lmp.py`` scope §7; MISO-South is compared against
each South hub and their simple mean. Only hub-covered hours are compared.

Output: ``results/phase0/miso/_miso283_premium_localize.json`` with, per year,
zone x market annual mean model-hub, hour-of-day and month profiles for South,
and the South premium split by model-price quantile.

Rule 13: nothing here feeds a solve; it localizes a residual.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/miso280_span"
YEARS = range(2019, 2026)
ZONE_HUB = {
    "MISO-West": ["MINN.HUB"],
    "MISO-Illinois": ["ILLINOIS.HUB"],
    "MISO-Indiana": ["INDIANA.HUB"],
    "MISO-East": ["MICHIGAN.HUB"],
    "MISO-South": ["LOUISIANA.HUB", "MS.HUB", "ARKANSAS.HUB", "TEXAS.HUB"],
}


def hub(year: int, mkt: str) -> pd.DataFrame:
    """Hourly hub LMP on the model's 8760 index; NaN where unpublished."""
    fs = sorted(
        glob.glob(str(REPO / f"data/raw/lmp-data/MISO/miso_hub_lmp_{year}_{mkt}*"))
    )
    d = pd.concat([pd.read_csv(x) for x in fs])
    d = d[(d.type == "Hub") & (d.value == "LMP")]
    hs = [f"he{i:02d}" for i in range(1, 25)]
    m = d.melt(id_vars=["date", "node"], value_vars=hs, var_name="he", value_name="lmp")
    m["hour"] = m.he.str[2:].astype(int) - 1
    m["date"] = pd.to_datetime(m.date).dt.strftime("%Y-%m-%d")
    m = m.pivot_table(
        index=["date", "hour"], columns="node", values="lmp"
    ).reset_index()
    ts = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    idx = pd.DataFrame({"date": ts.strftime("%Y-%m-%d"), "hour": ts.hour})
    return idx.merge(m, on=["date", "hour"], how="left")


def main() -> int:
    """CLI entry point."""
    out = {}
    for y in YEARS:
        s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
        s = (
            s[s["pass"] == "P1"]
            .pivot(index="hour", columns="zone", values="price")
            .sort_index()
        )
        ts = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
        hod, mon = ts.hour.to_numpy(), ts.month.to_numpy()
        yo = {"zone_mean_model": {z: round(float(s[z].mean()), 2) for z in s.columns}}
        for mkt in ("rt", "da"):
            h = hub(y, mkt)
            zs = {}
            for z, hubs in ZONE_HUB.items():
                for hb in hubs + (["SOUTH_MEAN"] if z == "MISO-South" else []):
                    hv = (
                        h[hubs].mean(axis=1).to_numpy()
                        if hb == "SOUTH_MEAN"
                        else h[hb].to_numpy()
                    )
                    ok = ~np.isnan(hv)
                    pm = s[z].to_numpy()
                    d = pm - hv
                    zs[f"{z}|{hb}"] = {
                        "n": int(ok.sum()),
                        "model": round(float(pm[ok].mean()), 2),
                        "hub": round(float(hv[ok].mean()), 2),
                        "diff": round(float(d[ok].mean()), 2),
                        "diff_median": round(float(np.median(d[ok])), 2),
                    }
            yo[mkt] = zs
            # South profiles vs LA hub and South mean
            hv = h[ZONE_HUB["MISO-South"]].mean(axis=1).to_numpy()
            pm = s["MISO-South"].to_numpy()
            ok = ~np.isnan(hv)
            df = pd.DataFrame({"hod": hod, "mon": mon, "pm": pm, "hub": hv})[ok]
            df["d"] = df.pm - df.hub
            yo[f"south_{mkt}_hod"] = (
                df.groupby("hod")[["pm", "hub", "d"]].mean().round(2).to_dict("list")
            )
            yo[f"south_{mkt}_mon"] = (
                df.groupby("mon")[["pm", "hub", "d"]].mean().round(2).to_dict("list")
            )
            # South minus North(ILLINOIS) spread: model vs measured
            pn = s["MISO-Illinois"].to_numpy()
            hn = h["ILLINOIS.HUB"].to_numpy()
            ok2 = ok & ~np.isnan(hn)
            dd = pd.DataFrame(
                {"hod": hod[ok2], "ms": (pm - pn)[ok2], "hs": (hv - hn)[ok2]}
            )
            yo[f"south_minus_il_{mkt}"] = {
                "model": round(float(dd.ms.mean()), 2),
                "hub": round(float(dd.hs.mean()), 2),
                "hod_model": dd.groupby("hod").ms.mean().round(2).tolist(),
                "hod_hub": dd.groupby("hod").hs.mean().round(2).tolist(),
            }
        out[y] = yo
        rt = out[y]["rt"]
        print(
            y,
            {
                k.split("|")[0][5:] + "|" + k.split("|")[1][:4]: v["diff"]
                for k, v in rt.items()
            },
        )
    p = REPO / "results/phase0/miso/_miso283_premium_localize.json"
    p.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
