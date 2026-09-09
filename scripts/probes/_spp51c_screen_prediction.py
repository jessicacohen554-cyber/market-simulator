"""SPP-51c: the EX ANTE screen prediction for G-1, computed BEFORE the arm solves.

Estimates how many hours the oversupply-allocated bound lift exceeds the LP's
available thermal turn-down, using keeper-3's committed 2025 hourly sidecars.
Limitation stated in the addendum: keeper-3 is the PRE-SPP-48/49 input surface,
so this is an estimator, not a control.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data import renewables as R
from market_sim.data.eia930.demand import load_demand

YEAR = 2025
cfg = get_iso_config("SPP"); zones = cfg.zone_names
rate = R._reference_curtailment_rate("SPP", "wind")[0]
gen = R.load_eia_hourly_renewable_gen("SPP", YEAR)
wind = np.asarray(gen["wind"], float); solar = np.asarray(gen.get("solar", np.zeros(8760)), float)
monthly = R._eia860_monthly_capacity("SPP", "wind", zones, YEAR)
mi = R._hour_to_month_index(HOURS_PER_YEAR)
cap = monthly.sum(axis=0)[mi]
load = load_demand("SPP", YEAR, cfg).sum(axis=0)
flat = wind/(1-rate); C = float(flat.sum()-wind.sum())
nl = load - wind - solar; H = np.maximum(cap-wind, 0.0)
lo, hi = float(nl.min())-1, float(nl.max())+1
for _ in range(200):
    m = .5*(lo+hi)
    if np.minimum(np.maximum(m-nl,0), H).sum() < C: lo = m
    else: hi = m
lift = np.minimum(np.maximum(.5*(lo+hi)-nl,0), H) - (flat-wind)   # new bound minus old bound

k = pd.read_parquet(f"results/calibration/spp43_screened_B/hourly/class_hourly_{YEAR}.parquet")
k = k[k["pass"]=="P1"]
piv = k.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum").reindex(range(8760)).fillna(0.0)
NONTHERMAL = {"wind","solar","nuclear","hydro","NUCLEAR","HYDRO","WIND","SOLAR","storage","STORAGE"}
thermal_cols = [c for c in piv.columns if c not in NONTHERMAL]
thermal = piv[thermal_cols].sum(axis=1).to_numpy(float)
tmin = float(np.percentile(thermal, 0.5))     # the LP's realised deep floor
headroom_down = np.maximum(thermal - tmin, 0.0)

pred = int(((lift > 0) & (lift > headroom_down)).sum())
out = {
  "year": YEAR,
  "keeper_thermal_classes": sorted(thermal_cols),
  "thermal_mean_MW": round(float(thermal.mean()),1),
  "thermal_p0.5_floor_MW": round(tmin,1),
  "thermal_annual_min_MW": round(float(thermal.min()),1),
  "lift_mean_MW": round(float(lift.mean()),1),
  "lift_max_MW": round(float(lift.max()),1),
  "hours_lift_positive": int((lift>0).sum()),
  "G1_predicted_interior_wind_hours": pred,
  "G1_band_0.4x": int(round(pred*0.4)), "G1_band_2.5x": int(round(pred*2.5)),
}
print(json.dumps(out, indent=1))
Path("results/calibration/_spp51c_screen_prediction.json").write_text(json.dumps(out, indent=1))
