"""UC-DA-BASIS zero-LP effect table: commitment increment before -> after (R16, R17).

Audit-style stats (FINDING-ucmilp-df-audit-2026-10-16 section 4): mean over
QA-valid hours, share below 0, median over the top-100 metered-load hours,
p5. Reads the live per-ISO basis (data/commitment_demand.py). Writes
effect.csv next to this file. Run from the repo root with PYTHONPATH=.
"""
from pathlib import Path
import numpy as np, pandas as pd
from market_sim.data import eia930
import market_sim.data.commitment_demand as cd
def st(fc, act, ref):
    err, valid = cd.qa_forecast_error(fc, act)
    e = err[valid]; top = np.argsort(ref)[::-1][:100]
    return dict(qa=int((~valid).sum()), mean=round(e.mean(),1), below0=round((e<0).mean(),3), top100=round(float(np.median(err[top])),1), p5=round(float(np.quantile(e,0.05)),1))
rows=[]
for y in range(2019,2026):
    f = eia930._eia_hourly_frame_filled("SWPP", y)
    act = f["Demand"].to_numpy(float)
    rows.append(dict(iso="SPP",year=y,basis="before (EIA DF)",**st(f["Demand forecast"].to_numpy(float),act,act)))
    fc,a = cd.forecast_and_actual_mw("SPP",y)
    rows.append(dict(iso="SPP",year=y,basis="after (MTLF DA-RUC)",**st(fc,a,act)))
    fc,a = cd.forecast_and_actual_mw("SPP",y,"intraday")
    rows.append(dict(iso="SPP",year=y,basis="RUC (MTLF ID-RUC 4h)",**st(fc,a,act)))
for y in range(2019,2026):
    f = eia930._eia_hourly_frame_filled("CISO", y)
    act = f["Demand"].to_numpy(float)
    rows.append(dict(iso="CAISO",year=y,basis="before",**st(f["Demand forecast"].to_numpy(float),act,act)))
    fc,a = cd.forecast_and_actual_mw("CAISO",y)
    rows.append(dict(iso="CAISO",year=y,basis="after (net charging)",**st(fc,a,act)))
df=pd.DataFrame(rows); print(df.to_string()); df.to_csv("Path(__file__).parent / "effect.csv"",index=False)
