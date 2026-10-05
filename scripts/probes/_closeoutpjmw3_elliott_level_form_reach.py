"""closeout-PJM-w3 phase 0 — reach of the LEVEL-form Elliott overlay, alone and with measured interchange. ZERO LP.

Per event hour, fleet thermal unavailable MW is set to the measured total (GADS Figure-30 forced+derate plus
eDART planned+maintenance); the change against the keeper's own unavailable MW is withdrawn (or restored) from
in-LP headroom and priced with the w2 merit-walk / ORDC / VOLL estimator. The second reading also withdraws the
measured extra export (PJM Data Miner ``act_sch_interchange`` actual tie flows, EPT, minus the model's export).
Record: ``docs/records/pjm/closeout-pjm-w3/FINDING-closeout-pjm-w3-elliott-identity-2026-10-04.md`` §5-§6.
"""

import numpy as np
import pandas as pd

K = "results/calibration/closeout_pjm_nuc_full_span/hourly/"
H = np.arange(8544, 8616)
u = pd.read_parquet(
    K + "unit_marginal_2022.parquet",
    columns=["unit_id", "fuel", "zone", "hour", "mw", "cap_mw", "mc", "plant_group"],
)
u = u[
    u.fuel.astype(str).isin(["coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear"])
    & (u.zone.astype(str) != "PJM_external")
    & ~u.plant_group.astype(str).str.startswith("VIRTUAL")
]
inst = u.groupby("unit_id", observed=True).cap_mw.max()
w = u[u.hour.isin(H)].copy()
w["un"] = w.unit_id.map(inst).astype(float) - w.cap_mw
w["hr"] = w.cap_mw - w.mw
g = w.groupby("hour").agg(un=("un", "sum"), head=("hr", "sum"))
fig = pd.read_csv(
    "data/raw/pjm-elliott-forced-outages/figure30_digitised.csv"
).drop_duplicates("hour_beginning_ept")
fr = (
    (pd.to_datetime(fig.hour_beginning_ept) - pd.Timestamp("2022-01-01"))
    / pd.Timedelta("1h")
).astype(int)
gads = (
    pd.Series(fig.bar_total_mw.values, index=fr.values).reindex(H).interpolate().ffill()
)
e = pd.read_csv("data/raw/pjm-outages/by-year/gen_outages_by_type_2022.csv")
e = e[(e.region == "PJM RTO") & (e.lead_days == 0)]
e["d"] = pd.to_datetime(e.forecast_date)
pm = e.set_index("d").planned_outages_mw + e.set_index("d").maintenance_outages_mw
day = (pd.Timestamp("2022-01-01") + pd.to_timedelta(H, unit="h")).normalize()
meas = gads.values + np.array([pm.get(d) for d in day])
inc = meas - g.un.values  # +: withdraw more, -: restore
resid = g["head"].values - inc
s = pd.read_parquet(K + "system_2022.parquet")
s = s[(s["pass"] == "P1") & (s.zone.astype(str) != "PJM_external")]
p = (
    (
        s.assign(x=s.price * s.demand).groupby("hour").x.sum()
        / s.groupby("hour").demand.sum()
    )
    .reindex(H)
    .values
)
r = pd.read_parquet(K + "reserve_family_2022.parquet")
req = (
    r[(r["pass"] == "P1") & (r.family == "pjm_primary")]
    .groupby("hour")
    .requirement_mw.sum()
    .reindex(H)
    .values
)
walk = []
for i, h in enumerate(H):
    d = w[(w.hour == h) & (w.hr > 0)].sort_values("mc")
    if inc[i] <= 0:
        walk.append(p[i])
        continue
    a = d[d.mc >= p[i] - 1e-6]
    c = np.cumsum(a.hr.values)
    k = int(np.searchsorted(c, inc[i]))
    walk.append(float(a.mc.values[min(k, len(a) - 1)]) if len(a) else p[i])
walk = np.array(walk)
est = np.where(
    resid < 0,
    2000,
    np.where(resid < req, walk + 850, np.where(resid < req + 190, walk + 300, walk)),
)
ix = slice(0, 48)
print(
    "inc min/mean/max GW",
    round(inc.min() / 1e3, 1),
    round(inc.mean() / 1e3, 1),
    round(inc.max() / 1e3, 1),
)
print(
    "hours resid<0",
    int((resid < 0).sum()),
    " <req",
    int((resid < req).sum()),
    " min resid GW",
    round(resid.min() / 1e3, 1),
)
print(
    "Dec23-24 mean est (simple) $",
    round(est[ix].mean(), 1),
    " keeper $",
    round(p[ix].mean(), 1),
)
# --- add measured interchange (PJM Data Miner act_sch_interchange, export-positive)
a = pd.read_csv(
    "data/raw/pjm-elliott-interchange/act_sch_interchange_2022-12-20_28.csv",
    encoding="utf-8-sig",
)
a["t"] = pd.to_datetime(a.datetime_beginning_ept, format="%m/%d/%Y %I:%M:%S %p")
pj = -a.groupby("t").actual_flow.sum()
pj.index = ((pj.index - pd.Timestamp("2022-01-01")) / pd.Timedelta("1h")).astype(int)
nb = "results/calibration/closeout_pjm_elliott_2022/hourly/network_2022.parquet"
n = pd.read_parquet(nb)
n = n[(n["pass"] == "P1") & (n.kind == "link")]
n["name"] = n.name.astype(str)
mexp = (
    -n[n.name.str.startswith("PJM_external>")].groupby("hour").mw.sum()
)  # model export-positive (probe leg; keeper interchange assumed same outside window)
extra = pj.reindex(H).values - mexp.reindex(H).values
resid2 = resid - np.clip(extra, 0, None)
print(
    "extra export needed GW min/mean/max",
    round(np.nanmin(extra) / 1e3, 1),
    round(np.nanmean(extra) / 1e3, 1),
    round(np.nanmax(extra) / 1e3, 1),
)
print(
    "LEVEL+EXPORTS: hours resid<0",
    int((resid2 < 0).sum()),
    " <req",
    int((resid2 < req).sum()),
    " min resid GW",
    round(np.nanmin(resid2) / 1e3, 1),
)
