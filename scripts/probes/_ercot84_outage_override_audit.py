"""Classify ALL 2024-overlapping ERCOT gas-class outage windows by keeping gate.

Writes override_only_2024.csv (the drop list for the throwaway probe).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
from lib import outage_detect as od

win = pd.read_csv(REPO / "data/raw/campd-unit-outages.csv")
win["outage_start"] = pd.to_datetime(win["outage_start"])
win["outage_end"] = pd.to_datetime(win["outage_end"])
s0, e0 = pd.Timestamp("2024-01-01"), pd.Timestamp("2025-01-01")
w = win[(win.outage_start < e0) & (win.outage_end > s0)
        & win.plant_group.isin(("CC_REGULAR", "CC_CHP", "ST_GAS"))].copy()
print(f"2024-overlapping gas windows: {len(w)}, {w.unit_capacity_mw.sum()/1e3:.1f} GW")

mask = od.high_load_mask("ERCOT", 2024, 8784)
cems = pd.read_parquet(REPO / "data/raw/campd-unit-level/TX_2024.parquet",
                       columns=["facilityId", "unitId", "date", "hour", "grossLoad"])
cems["ts"] = pd.to_datetime(cems["date"]) + pd.to_timedelta(cems["hour"], unit="h")
y0 = pd.Timestamp("2024-01-01")
cems["idx"] = ((cems["ts"] - y0).dt.total_seconds() // 3600).astype(int)
T = len(mask)

rows = []
for (fid, uid), grp in w.groupby(["facility_id", "unit_id"]):
    cu = cems[(cems["facilityId"].astype(str) == str(fid)) & (cems["unitId"].astype(str) == str(uid))]
    cap = float(grp.unit_capacity_mw.iloc[0])
    cf = np.zeros(T)
    if len(cu) and cap > 0:
        gl = cu.groupby("idx")["grossLoad"].sum()
        ii = gl.index.to_numpy()
        ok = (ii >= 0) & (ii < T)
        cf[ii[ok]] = gl.to_numpy()[ok] / cap
    for ridx, r in grp.iterrows():
        s = int(max((r.outage_start - y0).total_seconds() // 3600, 0))
        e = int(min((r.outage_end - y0).total_seconds() // 3600, T))
        if e <= s:
            continue
        high = mask[s:e]; cf_span = cf[s:e]
        ran_high = int((high & (cf_span >= od.REAL_RUN_CF)).sum())
        down_high = int((high & (cf_span < od.REAL_RUN_CF)).sum())
        dur = (e - s) / 24.0
        span_cf = float(cf_span.mean())
        revealed = ran_high < od.MIN_INMERIT_HOURS and down_high >= od.MIN_INMERIT_HOURS
        override = (ran_high < od.MIN_INMERIT_HOURS and dur >= od.FULL_STOP_OVERRIDE_DAYS
                    and span_cf < od.FULL_STOP_OVERRIDE_CF)
        gate = "revealed" if revealed else ("override_only" if override else "neither")
        rows.append((ridx, r.facility_id, r.unit_id, r.plant_group, cap,
                     str(r.outage_start), str(r.outage_end), r.duration_days, gate))

df = pd.DataFrame(rows, columns=["row", "fid", "uid", "grp", "mw", "start", "end", "days", "gate"])
print(df.groupby("gate").agg(n=("mw", "size"), gw=("mw", lambda x: round(x.sum()/1e3, 2))).to_string())
oo = df[df.gate == "override_only"]
oo.to_csv("override_only_2024.csv", index=False)
mo = pd.to_datetime(oo.start).dt.month
print("\noverride-only windows by start month (n):", mo.value_counts().sort_index().to_dict())
print(f"wrote override_only_2024.csv ({len(oo)} windows, {oo.mw.sum()/1e3:.2f} GW)")
