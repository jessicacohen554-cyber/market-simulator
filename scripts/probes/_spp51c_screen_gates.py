"""SPP-51c: grade the 2025 screen against the PRECOMMIT's STRUCTURAL stop gate.

G-1a interior-wind hours, G-1b system-LW negative hours, G-2 footprint confinement,
G-3 the wind identity, G-4 C1 non-regression vs SPP-50, G-5 protective bands.
C3a/C3b/C3c are reported at full magnitude and are NOT gated on, in either direction.
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

ARM = Path("results/calibration/_spp51c_screen_ARM")
YEAR = 2025
cfg = get_iso_config("SPP"); zones = cfg.zone_names
rate = R._reference_curtailment_rate("SPP", "wind")[0]

# --- the instrument, rebuilt exactly as the loader builds it -------------------
gen = R.load_eia_hourly_renewable_gen("SPP", YEAR)
wind = np.asarray(gen["wind"], float); solar = np.asarray(gen.get("solar", np.zeros(8760)), float)
monthly = R._eia860_monthly_capacity("SPP", "wind", zones, YEAR)
cap = monthly.sum(axis=0)[R._hour_to_month_index(HOURS_PER_YEAR)]
load = load_demand("SPP", YEAR, cfg).sum(axis=0)
flat = wind / (1 - rate); C = float(flat.sum() - wind.sum())
nl = load - wind - solar; H = np.maximum(cap - wind, 0.0)
curt, lam = R._oversupply_curtailment_allocation(nl, H, C)
bound_arm = wind + curt          # the arm's hourly system wind bound (MW)
bound_ctl = flat                 # the control's: SPP-50 rides it to 0.0003 %
alloc = curt > 1e-9

# --- the arm's own hourly output ----------------------------------------------
sysd = pd.read_parquet(ARM / f"hourly/system_{YEAR}.parquet")
sysd = sysd[sysd["pass"] == "P1"]
piv_p = sysd.pivot_table(index="hour", columns="zone", values="price").reindex(range(8760))
piv_d = sysd.pivot_table(index="hour", columns="zone", values="demand").reindex(range(8760))
lw = (piv_p * piv_d).sum(axis=1) / piv_d.sum(axis=1)
kl = pd.read_parquet(ARM / f"hourly/class_hourly_{YEAR}.parquet")
kl = kl[kl["pass"] == "P1"]
kp = kl.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum").reindex(range(8760)).fillna(0.0)
wind_arm = kp["wind"].to_numpy(float)

interior = wind_arm < bound_arm - 1.0            # MW tolerance
neg_lw = (lw.to_numpy(float) < 0.0)
dwind = np.abs(wind_arm - bound_ctl)             # control wind == its bound

out = {
 "year": YEAR, "lambda_MW": round(lam, 1),
 "G1a_interior_hours": int(interior.sum()), "G1a_predicted": 871, "G1a_band": [348, 2178],
 "G1b_neg_lw_hours": int(neg_lw.sum()), "G1b_predicted": 592, "G1b_band": [237, 1480],
 "G1_any_zone_neg_hours": int((piv_p.min(axis=1).to_numpy(float) < 0).sum()),
 "G2_wind_change_in_alloc_hours_pct": round(float(dwind[alloc].sum() / max(dwind.sum(), 1e-9) * 100), 2),
 "G3_model_wind_TWh": round(float(wind_arm.sum()) / 1e6, 4),
 "G3_delivered_TWh": round(float(wind.sum()) / 1e6, 4),
 "G3_identity": round(float(wind_arm.sum() / wind.sum()), 5),
 "G3_control_identity": 1.10681,
 "recurtailment_pct": round(float((bound_arm.sum() - wind_arm.sum()) / bound_arm.sum() * 100), 4),
 "min_zonal_price": round(float(np.nanmin(piv_p.to_numpy(float))), 3),
 "lw_mean_price": round(float(np.nansum(lw * piv_d.sum(axis=1)) / np.nansum(piv_d.sum(axis=1))), 4),
 "slack_MWh": round(float(sysd["slack"].sum()), 2),
 "dump_MWh": round(float(sysd["dump"].sum()), 2),
}
for c in ("nuclear", "hydro", "solar"):
    if c in kp.columns:
        out[f"nonthermal_{c}_TWh"] = round(float(kp[c].sum()) / 1e6, 4)
out["class_TWh"] = {c: round(float(kp[c].sum()) / 1e6, 4) for c in sorted(kp.columns)}
if (ARM / "metrics.json").exists():
    out["metrics_keys"] = sorted(json.load(open(ARM / "metrics.json")).keys())[:40]
print(json.dumps(out, indent=1))
Path("results/calibration/_spp51c_screen_gates.json").write_text(json.dumps(out, indent=1))
