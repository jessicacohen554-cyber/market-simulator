"""SPP-51c: WHY the LP absorbed 98 % of the concentrated headroom instead of
spilling it. Measures the thermal turn-down the model still had available in the
allocated hours where wind did NOT go interior. Zero LP -- reads the arm's own
committed hourly sidecars.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data import renewables as R
from market_sim.data.eia930.demand import load_demand

ARM = Path("results/calibration/_spp51c_screen_ARM"); YEAR = 2025
cfg = get_iso_config("SPP"); z = cfg.zone_names
rate = R._reference_curtailment_rate("SPP", "wind")[0]
gen = R.load_eia_hourly_renewable_gen("SPP", YEAR)
w = np.asarray(gen["wind"], float); s = np.asarray(gen.get("solar", np.zeros(8760)), float)
m = R._eia860_monthly_capacity("SPP", "wind", z, YEAR)
cap = m.sum(axis=0)[R._hour_to_month_index(HOURS_PER_YEAR)]
load = load_demand("SPP", YEAR, cfg).sum(axis=0)
flat = w / (1 - rate)
curt, lam = R._oversupply_curtailment_allocation(load - w - s, np.maximum(cap - w, 0.0),
                                                 float(flat.sum() - w.sum()))
bound = w + curt; alloc = curt > 1e-9

k = pd.read_parquet(ARM / f"hourly/class_hourly_{YEAR}.parquet"); k = k[k["pass"] == "P1"]
kp = k.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum").reindex(range(8760)).fillna(0.0)
wind_arm = kp["wind"].to_numpy(float)
NONTHERMAL = {"wind", "solar", "nuclear", "hydro"}
thermal = kp[[c for c in kp.columns if c not in NONTHERMAL]].sum(axis=1).to_numpy(float)
interior = wind_arm < bound - 1.0
tmin = float(thermal.min())

def blk(mask, name):
    return {
        "hours": int(mask.sum()),
        "thermal_mean_MW": round(float(thermal[mask].mean()), 1) if mask.any() else None,
        "thermal_min_MW": round(float(thermal[mask].min()), 1) if mask.any() else None,
        "turn_down_still_available_mean_MW": round(float((thermal[mask] - tmin).mean()), 1) if mask.any() else None,
        "wind_bound_mean_MW": round(float(bound[mask].mean()), 1) if mask.any() else None,
        "wind_spilled_mean_MW": round(float((bound - wind_arm)[mask].mean()), 1) if mask.any() else None,
    }

out = {
    "year": YEAR,
    "thermal_annual_min_MW": round(tmin, 1),
    "thermal_annual_mean_MW": round(float(thermal.mean()), 1),
    "headroom_offered_TWh": round(float(curt.sum()) / 1e6, 4),
    "headroom_actually_spilled_TWh": round(float((bound - wind_arm).sum()) / 1e6, 4),
    "absorbed_by_thermal_displacement_pct": round(
        float(1 - (bound - wind_arm).sum() / curt.sum()) * 100, 2),
    "allocated_and_interior": blk(alloc & interior, "spilled"),
    "allocated_NOT_interior": blk(alloc & ~interior, "absorbed"),
    "not_allocated": blk(~alloc, "untouched"),
}
# how much MORE turn-down would have been needed to spill in the absorbed hours
absorbed = alloc & ~interior
out["deficit_to_spill_in_absorbed_hours_mean_MW"] = round(
    float((thermal[absorbed] - tmin).mean()), 1)
out["hours_absorbed_with_turndown_over_2GW"] = int(
    ((thermal - tmin) > 2000)[absorbed].sum())
print(json.dumps(out, indent=1))
Path("results/calibration/_spp51c_absorption.json").write_text(json.dumps(out, indent=1))
