"""closeout-PJM-w3 phase 0 — Elliott supply identity: probe outage vs measured outage, and interchange. ZERO LP.

Reads the Elliott probe's 2022 leg (``results/calibration/closeout_pjm_elliott_2022``, extracted from
``claude/closeout-pjm-elliott-2022`` @ d4ea021f) and the keeper's committed 2022 sidecars, the digitised
GADS Figure-30 series, the eDART planned/maintenance daily snapshot and EIA-930 PJM interchange. Prints,
per event hour, the model's thermal unavailable MW against the measured total (GADS forced + eDART
planned/maintenance) and PJM's measured net export. Record:
``docs/records/pjm/closeout-pjm-w3/FINDING-closeout-pjm-w3-elliott-identity-2026-10-04.md``.
"""

import numpy as np
import pandas as pd

B = "results/calibration/closeout_pjm_elliott_2022/hourly/"
K = "results/calibration/closeout_pjm_nuc_full_span/hourly/"
H = list(range(8544, 8616))


def sysg(b):
    s = pd.read_parquet(b + "system_2022.parquet")
    s = s[(s["pass"] == "P1") & (s.zone.astype(str) != "PJM_external")]
    return s.groupby("hour")[["demand", "slack"]].sum().reindex(H)


def unav(b):
    u = pd.read_parquet(
        b + "unit_marginal_2022.parquet",
        columns=["unit_id", "fuel", "zone", "hour", "cap_mw", "plant_group"],
    )
    u = u[
        u.fuel.astype(str).isin(
            ["coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear"]
        )
        & (u.zone.astype(str) != "PJM_external")
        & ~u.plant_group.astype(str).str.startswith("VIRTUAL")
    ]
    inst = u.groupby("unit_id", observed=True).cap_mw.max()
    w = u[u.hour.isin(H)].copy()
    w["un"] = w.unit_id.map(inst).astype(float) - w.cap_mw
    return w.groupby("hour").un.sum().reindex(H), float(inst.sum())


se = sysg(B)
ue, inst = unav(B)
uk, _ = unav(K)
d = pd.read_parquet("data/raw/eia-930-interchange/PJM interchange hourly.parquet")
d["local_time"] = pd.to_datetime(d.local_time)
x = d.groupby("local_time").mw.sum()
# EIA local_time is hour-ending -> hour-beginning row
xr = pd.Series(
    x.values,
    index=(
        (x.index - pd.Timedelta("1h") - pd.Timestamp("2022-01-01")) / pd.Timedelta("1h")
    ).astype(int),
)
fig = pd.read_csv(
    "data/raw/pjm-elliott-forced-outages/figure30_digitised.csv"
).drop_duplicates("hour_beginning_ept")
ft = pd.to_datetime(fig.hour_beginning_ept)
fr = ((ft - pd.Timestamp("2022-01-01")) / pd.Timedelta("1h")).astype(int)
gads = (
    pd.Series(fig.bar_total_mw.values, index=fr.values).reindex(H).interpolate().ffill()
)
e = pd.read_csv("data/raw/pjm-outages/by-year/gen_outages_by_type_2022.csv")
e = e[(e.region == "PJM RTO") & (e.lead_days == 0)]
e["d"] = pd.to_datetime(e.forecast_date)
pm = e.set_index("d").planned_outages_mw + e.set_index("d").maintenance_outages_mw
day = (pd.Timestamp("2022-01-01") + pd.to_timedelta(H, unit="h")).normalize()
pmh = pd.Series([pm.get(dd, np.nan) for dd in day], index=H)
out = pd.DataFrame(
    {
        "slack": se.slack,
        "model_unav_keeper": uk,
        "model_unav_probe": ue,
        "gads_forced": gads,
        "edart_plan_maint": pmh,
        "real_net_export": xr.reindex(H),
    }
)
out["measured_total"] = out.gads_forced + out.edart_plan_maint
out["probe_minus_measured"] = out.model_unav_probe - out.measured_total
sh = out[out.slack > 0]
print("installed thermal proxy GW", round(inst / 1e3, 1))
print(out.iloc[::3].round(0).to_string())
print("shed hours mean:", sh.mean().round(0).to_dict())
