"""SPP-51c: the reported bands, computed from COMMITTED artifacts only.

The screen's post-solve report stage died before writing metrics.json (the LP
itself completed and wrote every hourly sidecar), so C3a/C3b/C3c are computed
here on the same basis the scorer uses and C1 is differenced against SPP-50's
committed registry payload. REPORTED AT FULL MAGNITUDE, NOT GATED ON.
"""
from __future__ import annotations
import base64, gzip, json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.eia930.demand import load_demand

ARM = Path("results/calibration/_spp51c_screen_ARM"); YEAR = 2025
cfg = get_iso_config("SPP")
sysd = pd.read_parquet(ARM / f"hourly/system_{YEAR}.parquet"); sysd = sysd[sysd["pass"] == "P1"]
P = sysd.pivot_table(index="hour", columns="zone", values="price").reindex(range(8760))
D = sysd.pivot_table(index="hour", columns="zone", values="demand").reindex(range(8760))
lw_h = (P * D).sum(axis=1) / D.sum(axis=1)
dtot = D.sum(axis=1)
model_lw = float((lw_h * dtot).sum() / dtot.sum())

lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_SPP.parquet")
sub = lmp[lmp["year"] == YEAR].sort_values("hour")
rt_raw = sub["rt"].to_numpy(float)[:8760]
d = load_demand("SPP", YEAR, cfg).sum(axis=0)
m = np.isfinite(rt_raw)
actual_mis = float((rt_raw[m] * d[m]).sum() / d[m].sum())
idx = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h", tz="America/Chicago")
off = np.where([bool(t.dst().total_seconds()) for t in idx], 5, 6)
src = np.arange(8760) + off; ok = src < 8760
rt_a = np.full(8760, np.nan); rt_a[ok] = rt_raw[src[ok]]
ma = np.isfinite(rt_a)
actual_aln = float((rt_a[ma] * d[ma]).sum() / d[ma].sum())

mon = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h").month.to_numpy()
lwv, dv = lw_h.to_numpy(float), dtot.to_numpy(float)
mm = np.array([float((lwv[mon == k] * dv[mon == k]).sum() / dv[mon == k].sum()) for k in range(1, 13)])
am = np.array([float(np.nansum(rt_raw[(mon == k) & m] * d[(mon == k) & m]) /
                     np.nansum(d[(mon == k) & m])) for k in range(1, 13)])
nrmse = float(np.sqrt(((mm - am) ** 2).mean()) / am.mean())

out = {
    "year": YEAR,
    "NOTE": "post-solve report stage died before metrics.json; LP completed, hourly sidecars intact",
    "C3a_model_LW": round(model_lw, 4),
    "C3a_actual_LW_as_committed": round(actual_mis, 4),
    "C3a_as_scored_pct": round((model_lw / actual_mis - 1) * 100, 2),
    "C3a_control_SPP50_pct": 14.2,
    "C3a_actual_LW_clock_corrected": round(actual_aln, 4),
    "C3a_on_corrected_actual_pct": round((model_lw / actual_aln - 1) * 100, 2),
    "C3b_monthly_NRMSE_as_scored": round(nrmse, 4),
    "C3b_control_SPP50": 0.253,
    "C3c_model_hours_gt_200": int((lwv > 200).sum()),
    "C3c_actual_hours_gt_200": int((rt_raw[m] > 200).sum()),
}
js = open("frontend/data/backcast/runs/2026-09-08-spp-50-rebaseline.js").read()
pay = json.loads(gzip.decompress(base64.b64decode(re.search(r'"(H4sIA[^"]+)"', js).group(1))))
ctl = pay["years"][str(YEAR)]["volErr"]
k = pd.read_parquet(ARM / f"hourly/class_hourly_{YEAR}.parquet"); k = k[k["pass"] == "P1"]
kp = k.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum").sum() / 1e6
rows = {}
for cls, v in ctl.items():
    sv = v.get("sys") or {}
    a, cm = sv.get("a"), sv.get("m")
    if not a:
        continue
    am_ = float(kp.get(cls, 0.0))
    rows[cls] = {"actual": a, "control_model": cm, "arm_model": round(am_, 3),
                 "control_err_pct": round((cm / a - 1) * 100, 2),
                 "arm_err_pct": round((am_ / a - 1) * 100, 2),
                 "delta_abs_err_TWh": round(abs(am_ - a) - abs(cm - a), 3)}
out["C1_vs_SPP50"] = rows
out["C1_sum_abs_err_control_TWh"] = round(sum(abs(r["control_model"] - r["actual"]) for r in rows.values()), 3)
out["C1_sum_abs_err_arm_TWh"] = round(sum(abs(r["arm_model"] - r["actual"]) for r in rows.values()), 3)
print(json.dumps(out, indent=1))
Path("results/calibration/_spp51c_bands.json").write_text(json.dumps(out, indent=1))
