"""SPP-51c phase 0: (a) clock validation of the oversupply indicator, (b) is the
signal SYSTEM-wide or LOCATIONAL? Zero LP. The measured-negative set LABELS, never fits.
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
lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source" / f"actual_lmp_hourly_{ISO}.parquet")
print("actual LMP columns:", list(lmp.columns))
iso_cfg = get_iso_config(ISO)
zones = iso_cfg.zone_names
out = {}
for year in YEARS:
    gen = R.load_eia_hourly_renewable_gen(ISO, year)
    wind = np.asarray(gen["wind"], float)
    solar = np.asarray(gen.get("solar", np.zeros(HOURS_PER_YEAR)), float)
    zload = load_demand(ISO, year, iso_cfg)
    load = zload.sum(axis=0)
    nl = load - wind - solar
    sub = (lmp[lmp["year"] == year] if "year" in lmp.columns else lmp).sort_values("hour")
    rt = sub["rt"].to_numpy(float)[:HOURS_PER_YEAR]
    ok = np.isfinite(rt)
    neg = ok & (rt < 0.0); n = int(neg.sum())

    # (a) CLOCK: corr(NL, rt) and a +-4 h lag scan. A lag whose |corr| beats lag 0
    # would say the indicator and the price are on different clocks.
    lags = {}
    for L in range(-4, 5):
        s = np.roll(nl, L)
        m = ok.copy(); 
        lags[L] = float(np.corrcoef(s[m], rt[m])[0, 1])
    best = max(lags, key=lambda k: lags[k])

    row = {"n_neg": n, "corr_NL_rt_lag0": lags[0], "corr_by_lag": lags, "best_lag": best}

    # (b) LOCATIONAL: per-hub negative sets, and each zone's OWN oversupply axis.
    hubs = [c for c in sub.columns if "HUB" in c.upper()]
    shp = pd.read_parquet(SPP_WIND_SHAPE_DIR / f"spp_{year}_wind_zone_shape.parquet").sort_values("hour")
    monthly = R._eia860_monthly_capacity(ISO, "wind", zones, year)
    mi = R._hour_to_month_index(HOURS_PER_YEAR)
    for zi, z in enumerate(zones):
        if z not in shp.columns:
            continue
        zw = shp[z].to_numpy(float) * monthly[zi][mi]      # zone wind potential proxy (MW)
        znl = zload[zi] - zw                                # zone oversupply axis
        hub = [h for h in hubs if z.split("-")[-1].upper()[:5] in h.upper()]
        if not hub:
            continue
        p = sub[hub[0]].to_numpy(float)[:HOURS_PER_YEAR]
        okz = np.isfinite(p); negz = okz & (p < 0.0); nz = int(negz.sum())
        if nz == 0:
            continue
        rec_z = float((np.argsort(znl)[:nz][:, None] == np.flatnonzero(negz)[None, :]).any(axis=1).sum() / nz)
        rec_sys = float((np.argsort(nl)[:nz][:, None] == np.flatnonzero(negz)[None, :]).any(axis=1).sum() / nz)
        row[f"{z}_hub"] = hub[0]
        row[f"{z}_neg_hours"] = nz
        row[f"{z}_recall_own_zonal_NL"] = rec_z
        row[f"{z}_recall_system_NL"] = rec_sys

    if len(hubs) == 2:
        a = sub[hubs[0]].to_numpy(float)[:HOURS_PER_YEAR]
        b = sub[hubs[1]].to_numpy(float)[:HOURS_PER_YEAR]
        m = np.isfinite(a) & np.isfinite(b)
        na, nb = m & (a < 0), m & (b < 0)
        either = na | nb
        row["hubs"] = hubs
        row["either_hub_neg"] = int(either.sum())
        row["both_hubs_neg"] = int((na & nb).sum())
        row["only_one_hub_neg_pct"] = float((either & ~(na & nb)).sum() / either.sum() * 100.0)
        row["mean_abs_hub_spread"] = float(np.abs(a[m] - b[m]).mean())
    out[year] = row

print(json.dumps(out, indent=1))
Path("results/calibration/_spp51c_axis.json").write_text(json.dumps(out, indent=1))
