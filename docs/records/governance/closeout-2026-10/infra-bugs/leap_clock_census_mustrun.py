import sys, numpy as np, pandas as pd
sys.path.insert(0, "scripts"); sys.path.insert(0, ".")
import run_calibration_full as rcf
from market_sim.utils.hour_calendar import model_clock
from market_sim.config.iso_configs import get_iso_config
OLD = lambda y, h: pd.date_range(f"{y}-01-01", periods=h, freq="h").month.to_numpy()
NEW = lambda y, h: model_clock(y, h).month.to_numpy()
gen = rcf.load_monthly_generation()
for iso in ["CAISO","ERCOT","MISO","PJM","NEISO","NYISO","SPP","SOCO","NWPP"]:
    for y in (2020, 2024):
        if iso == "NYISO" and y == 2020: continue
        try:
            e930 = rcf._eia930_frame(y, iso, get_iso_config(iso))
            dem = np.ones((1, 8760))
            res = {}
            for tag, f in (("old", OLD), ("new", NEW)):
                rcf._hour_months = f
                res[tag] = rcf._must_run_profiles(y, gen, iso, dem, e930=e930)
            for k in res["new"]:
                a = res["old"][k].sum(axis=0); b = res["new"][k].sum(axis=0)
                d = np.abs(a - b)
                print(f"{iso} {y} must-run {k}: annual {b.sum()/1e6:.3f} TWh (old {a.sum()/1e6:.3f}); sum|d| {d.sum():,.0f} MWh; max {d.max():.1f} MW; hours {int((d>1e-6).sum())}")
        except Exception as e:
            print(iso, y, "ERR", repr(e)[:200])
