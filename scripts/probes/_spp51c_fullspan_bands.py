"""SPP-51c: full-span bands for the oversupply keeper candidate, on the REPAIRED clock."""
from __future__ import annotations
import base64, gzip, json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data import renewables as R
from market_sim.data.eia930.demand import load_demand

ARM = Path("results/calibration/spp51c_oversupply")
cfg = get_iso_config("SPP")
lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source" / "actual_lmp_hourly_SPP.parquet")
js = open("frontend/data/backcast/runs/2026-09-08-spp-50-rebaseline.js").read()
pay = json.loads(gzip.decompress(base64.b64decode(re.search(r'"(H4sIA[^"]+)"', js).group(1))))
rate = R._reference_curtailment_rate("SPP", "wind")[0]
out = {}
for year in (2023, 2024, 2025):
    s = pd.read_parquet(ARM / f"hourly/system_{year}.parquet"); s = s[s["pass"] == "P1"]
    P = s.pivot_table(index="hour", columns="zone", values="price").reindex(range(8760))
    D = s.pivot_table(index="hour", columns="zone", values="demand").reindex(range(8760))
    lw_h = (P * D).sum(axis=1) / D.sum(axis=1); dt = D.sum(axis=1)
    model_lw = float((lw_h * dt).sum() / dt.sum())
    sub = lmp[lmp["year"] == year].sort_values("hour")
    rt = sub["rt"].to_numpy(float)[:8760]
    d = load_demand("SPP", year, cfg).sum(axis=0)
    m = np.isfinite(rt)
    actual_lw = float((rt[m] * d[m]).sum() / d[m].sum())
    mon = pd.date_range(f"{year}-01-01", periods=8760, freq="h").month.to_numpy()
    lwv, dv = lw_h.to_numpy(float), dt.to_numpy(float)
    mm = np.array([float((lwv[mon == k] * dv[mon == k]).sum() / dv[mon == k].sum()) for k in range(1, 13)])
    am = np.array([float(np.nansum(rt[(mon == k) & m] * d[(mon == k) & m]) / np.nansum(d[(mon == k) & m])) for k in range(1, 13)])
    k = pd.read_parquet(ARM / f"hourly/class_hourly_{year}.parquet"); k = k[k["pass"] == "P1"]
    kp = k.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    gen = R.load_eia_hourly_renewable_gen("SPP", year)
    wind_delivered = float(np.asarray(gen["wind"], float).sum())
    model_wind = float(kp["wind"].sum())
    row = {
        "C3a_model_LW": round(model_lw, 4), "C3a_actual_LW_repaired": round(actual_lw, 4),
        "C3a_pct": round((model_lw / actual_lw - 1) * 100, 2),
        "C3b_NRMSE": round(float(np.sqrt(((mm - am) ** 2).mean()) / am.mean()), 4),
        "C3c_model_h": int((lwv > 200).sum()), "C3c_actual_h": int((rt[m] > 200).sum()),
        "neg_lw_hours": int((lwv < 0).sum()),
        "wind_identity": round(model_wind / wind_delivered, 5),
        "recurtail_pct": round((1 - model_wind / (wind_delivered / (1 - rate))) * 100, 4),
        "min_zonal_price": round(float(np.nanmin(P.to_numpy(float))), 2),
        "slack_MWh": round(float(s["slack"].sum()), 1), "dump_MWh": round(float(s["dump"].sum()), 1),
    }
    ctl = pay["years"][str(year)]["volErr"]
    c1 = {}
    for cls, v in ctl.items():
        sv = v.get("sys") or {}
        a, cm = sv.get("a"), sv.get("m")
        if not a: continue
        am_ = float(kp[cls].sum()) / 1e6 if cls in kp.columns else 0.0
        c1[cls] = {"actual": a, "ctl": cm, "arm": round(am_, 3),
                   "ctl_pct": round((cm/a-1)*100, 2), "arm_pct": round((am_/a-1)*100, 2)}
    row["C1"] = c1
    row["C1_sumabs_ctl"] = round(sum(abs(r["ctl"]-r["actual"]) for r in c1.values()), 3)
    row["C1_sumabs_arm"] = round(sum(abs(r["arm"]-r["actual"]) for r in c1.values()), 3)
    out[year] = row
print(json.dumps(out, indent=1))
Path("results/calibration/_spp51c_fullspan_bands.json").write_text(json.dumps(out, indent=1))
