"""SPP-109 robustness (reported, not gating): Z1 without the MMU offer-side bands; Z2 de-seasonalised.

Usage: ``python scripts/probes/_spp109_robustness.py <cache> <out.json>`` (shares the main probe's cache).
"""

import sys
import json

sys.path.insert(0, ".")
from pathlib import Path
import numpy as np
import pandas as pd
import scripts.probes._spp109_subfiveday_gas_phase0 as P
from scripts.probes._spp84_published_outage_rebasis import spp_outage_on_model_clock
from market_sim.config.paths import RAW_DATA_DIR

P.ARMS["Kn"] = {"spp_mmu_offer_unavailability": False, "spp_mmu_offer_repair": False}
P.ARMS["Gpn"] = {
    **P.ARMS["Gp"],
    "spp_mmu_offer_unavailability": False,
    "spp_mmu_offer_repair": False,
}
cache = Path(sys.argv[1])
spp = pd.read_csv(RAW_DATA_DIR / "spp-gen-outage/spp_capacity_gen_outage_hourly.csv")
spp.columns = [c.strip() for c in spp.columns]
spp["t"] = pd.to_datetime(
    spp["Market Hour"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
)
spp = spp.dropna(subset=["t"]).drop_duplicates("t", keep="last")
out = {}
allr = []
for y in range(2019, 2026):
    fl = {a: P.rebuild(y, cache, a) for a in ("K", "G", "Kn", "Gpn")}
    rows = fl["K"]["rows"]
    ft = np.array([r["fuel_type"] for r in rows])
    cls = P.class_of(rows)
    pm = fl["K"]["pmax"].astype(float)
    av = {a: pm[:, None] * fl[a]["availability"].astype(float) for a in ("K", "G")}
    live = ~np.array([P.edge_mask(x) for x in av["K"]])
    un = {a: np.where(live, pm[:, None] - av[a], 0.0) for a in ("K", "G")}
    gas = np.isin(ft, P.GAS_FUELS)
    four = np.isin(cls, P.SHORT_GROUPS)
    sp = spp_outage_on_model_clock(spp, y)["Natural Gas MW"].to_numpy()
    ok = np.isfinite(sp)
    r = {}
    for a in ("Kn", "Gpn"):
        ra = fl[a]["rows"]
        fta = np.array([q["fuel_type"] for q in ra])
        pa = fl[a]["pmax"].astype(float)
        ava = pa[:, None] * fl[a]["availability"].astype(float)
        lv = ~np.array([P.edge_mask(q) for q in ava])
        x = np.where(lv, pa[:, None] - ava, 0.0)[np.isin(fta, P.GAS_FUELS)].sum(0)
        r[a] = {
            "minus_spp_gw": round(float(np.mean(x[ok] - sp[ok])) / 1e3, 3),
            "mean_abs_gap_gw": round(float(np.mean(np.abs(x[ok] - sp[ok]))) / 1e3, 3),
        }
    s = (un["G"][four] - un["K"][four]).sum(0)
    mon = (
        pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), unit="h")
    ).month
    d = (
        pd.DataFrame({"s": s, "p": sp, "day": np.arange(8760) // 24, "mon": mon})
        .dropna()
        .groupby("day")
        .agg(s=("s", "mean"), p=("p", "mean"), mon=("mon", "first"))
    )
    dm = d.groupby("mon")[["s", "p"]].transform("mean")
    dd = d[["s", "p"]] - dm
    r["corr_within_month"] = round(float(dd.s.corr(dd.p)), 3)
    r["S_monthly_gw"] = [round(float(v) / 1e3, 2) for v in d.groupby("mon").s.mean()]
    r["SPP_monthly_gw"] = [round(float(v) / 1e3, 2) for v in d.groupby("mon").p.mean()]
    dd["y"] = y
    allr.append(dd)
    out[y] = r
A = pd.concat(allr)
out["pooled_corr_within_month"] = round(float(A.s.corr(A.p)), 3)
out["pooled_mean_abs_gap_gw"] = {
    a: round(
        float(np.mean([out[y][a]["mean_abs_gap_gw"] for y in range(2019, 2026)])), 3
    )
    for a in ("Kn", "Gpn")
}
json.dump(out, open(sys.argv[2], "w"), indent=1)
print(json.dumps(out, indent=0)[:4000])
