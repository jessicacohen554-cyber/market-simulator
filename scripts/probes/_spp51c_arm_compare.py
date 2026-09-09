"""SPP-51c phase 0: the three allocation rules, measured LIKE FOR LIKE on the
CORRECTED clock. SPP-51b's availability-arm numbers were measured against the
UTC-indexed sidecar, so they are not comparable to anything on the model clock;
this re-measures that arm here so the comparison is fair. Zero LP.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import RAW_DATA_DIR, SPP_WIND_SHAPE_DIR
from market_sim.data import renewables as R
from market_sim.data.eia930.demand import load_demand

ISO, YEARS = "SPP", (2023, 2024, 2025)
lmp = pd.read_parquet(RAW_DATA_DIR/"_validation-source"/f"actual_lmp_hourly_{ISO}.parquet")
cfg = get_iso_config(ISO); zones = cfg.zone_names
rate = R._reference_curtailment_rate(ISO, "wind")[0]

def aligned_rt(year, raw):
    idx = pd.date_range(f"{year}-01-01", periods=HOURS_PER_YEAR, freq="h", tz="America/Chicago")
    off = np.where([bool(t.dst().total_seconds()) for t in idx], 5, 6)
    src = np.arange(HOURS_PER_YEAR) + off
    out = np.full(HOURS_PER_YEAR, np.nan); ok = src < HOURS_PER_YEAR
    out[ok] = raw[src[ok]]
    return out

res = {}
for year in YEARS:
    gen = R.load_eia_hourly_renewable_gen(ISO, year)
    wind = np.asarray(gen["wind"], float); solar = np.asarray(gen.get("solar", np.zeros(HOURS_PER_YEAR)), float)
    monthly = R._eia860_monthly_capacity(ISO, "wind", zones, year)
    mi = R._hour_to_month_index(HOURS_PER_YEAR)
    cap_online = monthly.sum(axis=0)[mi]
    load = load_demand(ISO, year, cfg).sum(axis=0)
    flat = wind/(1.0-rate); C = float(flat.sum()-wind.sum())
    sub = (lmp[lmp["year"]==year]).sort_values("hour")
    rt = aligned_rt(year, sub["rt"].to_numpy(float)[:HOURS_PER_YEAR])
    neg = np.isfinite(rt) & (rt < 0.0)

    # ARM A -- availability (SPP-51b section 3): potential = max(delivered, Ahat * fleet shape)
    shp = pd.read_parquet(SPP_WIND_SHAPE_DIR/f"spp_{year}_wind_zone_shape.parquet").sort_values("hour")
    shape_sys = sum(shp[z].to_numpy(float)*monthly[zi][mi] for zi, z in enumerate(zones) if z in shp.columns)
    lo, hi = 0.0, 20.0
    for _ in range(200):
        a = 0.5*(lo+hi)
        if np.maximum(wind, a*shape_sys).sum() < flat.sum(): lo = a
        else: hi = a
    potA = np.maximum(wind, 0.5*(lo+hi)*shape_sys)

    # ARM B -- oversupply water-fill (this lane)
    nl = load - wind - solar; H = np.maximum(cap_online - wind, 0.0)
    lo2, hi2 = float(nl.min())-1, float(nl.max())+1
    for _ in range(200):
        m = 0.5*(lo2+hi2)
        if np.minimum(np.maximum(m-nl,0.0), H).sum() < C: lo2 = m
        else: hi2 = m
    potB = wind + np.minimum(np.maximum(0.5*(lo2+hi2)-nl,0.0), H)

    row = {"neg_hours": int(neg.sum())}
    for nm, pot in (("flat", flat), ("A_availability", potA), ("B_oversupply", potB)):
        curt = pot - wind
        row[nm] = {
            "share_of_C_in_neg_hours_pct": round(float(curt[neg].sum()/max(curt.sum(),1e-9)*100), 2),
            "mean_bound_in_neg_MW": round(float(pot[neg].mean()), 1),
            "lift_over_flat_in_neg_MW": round(float((pot-flat)[neg].mean()), 1),
            "alloc_hours": int((curt > 1e-9).sum()),
            "neg_hours_covered_pct": round(float(((curt>1e-9)&neg).sum()/max(neg.sum(),1)*100), 1),
            "annual_TWh": round(float(pot.sum())/1e6, 4),
        }
    res[year] = row
print(json.dumps(res, indent=1))
Path("results/calibration/_spp51c_arm_compare.json").write_text(json.dumps(res, indent=1))
