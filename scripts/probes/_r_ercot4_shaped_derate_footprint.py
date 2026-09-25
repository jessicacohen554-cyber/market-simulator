"""R-ERCOT-4 zero-LP probe: shaped partial-outage days capped below the plant's own measured peak.

For each ERCOT plateau in ``data/raw/campd-partial-outages-shaped.csv`` (rebuilt with
the deriver's own frozen detector, ``scripts.lib.outage_detect.detect_shaped``),
counts the days whose shaped derate sits more than 0.05 below the plant's OWN
same-day measured daily-max CF / ref, and the MW gap on those days.

Usage::

    PYTHONPATH=.:src:scripts:scripts/data python3 \
        scripts/probes/_r_ercot4_shaped_derate_footprint.py <out.json>

Record: ``docs/handoffs/FINDING-r-ercot-4-validation-years-2026-09-25.md``.
"""
import json, sys, numpy as np, pandas as pd
sys.path[:0] = ["scripts/data", "scripts", "src", "."]
from scripts.lib.outage_detect import _plateau_state, _plateau_spans, detect_shaped
import derive_partial_outages as D
from market_sim.data import campd
bins = D.load_campd_bins("data/raw/reference/custom-bin-assignments.csv")
cap = dict(zip(bins["Plant_Code"].astype(int), bins["capacity_mw"])); grp = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Group"]))
nm = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Name"]))
shp = pd.read_csv("data/raw/campd-partial-outages-shaped.csv")
out = {}
for yr in range(2019, 2026):
    df = campd.load_campd_hourly(campd.states_for_iso("ERCOT"), [yr])
    end = min(pd.Timestamp(f"{yr}-12-31 23:00"), df["date"].max() + pd.Timedelta(hours=23))
    full = pd.date_range(f"{yr}-01-01", end, freq="h")
    codes = sorted(set(shp[shp.year == yr].oris_code.astype(int)))
    tot = {"COAL": [0, 0, 0.0, 0.0], "CC_REGULAR": [0, 0, 0.0, 0.0]}; worst = []
    for code in codes:
        g = campd.plant_hourly_grid(df, code, yr)
        if g.empty or cap.get(code, 0) <= 0: continue
        cf = (g["gross_mw"].reindex(full).fillna(0.0) / cap[code]).to_numpy(float)
        st = _plateau_state(cf)
        if st is None: continue
        dmax, ref, sm, partial = st
        for i, j, prof in detect_shaped(cf):
            own = np.minimum(1.0, dmax[i:j] / ref)
            gap = np.maximum(0.0, own - prof)
            viol = gap > 0.05
            k = "COAL" if str(grp.get(code, "")).upper().startswith("COAL") else "CC_REGULAR"
            t = tot.setdefault(k, [0, 0, 0.0, 0.0])
            t[0] += j - i; t[1] += int(viol.sum()); t[2] += float((gap[viol] * cap[code]).sum()); t[3] += float(gap[viol].max() * cap[code]) if viol.any() else 0
            for d in np.where(viol)[0]:
                worst.append((round(float(gap[d] * cap[code])), str((pd.Timestamp(f"{yr}-01-01") + pd.Timedelta(days=int(i + d))).date()), nm.get(code, code), round(float(prof[d]), 3), round(float(own[d]), 3)))
    worst.sort(reverse=True)
    out[yr] = {k: {"plateau_days": v[0], "days_capped_below_own_peak": v[1], "sum_daily_MW_gap": round(v[2]), } for k, v in tot.items()}
    out[yr]["top"] = worst[:8]
    print(yr, json.dumps({k: out[yr][k] for k in tot}), flush=True)
    for w in worst[:6]: print("   ", w, flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
