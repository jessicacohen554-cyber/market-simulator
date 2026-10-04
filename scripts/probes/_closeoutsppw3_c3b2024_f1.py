"""Zero-LP (closeout-SPP-w3 desk item 2): C3b 2024 with the excess Sep-Oct S-N RT MCC (above 2023 Sep-Oct 5.68) removed from the actual, keeper and arm."""

import pandas as pd
import numpy as np
import math

c = pd.read_parquet(
    "data/raw/_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet"
)
c = c[(c.year == 2024) & (c.market.astype(str).str.upper().str.startswith("RT"))]
print(c.market.unique()[:5], c.zone.unique())
p = c.pivot_table(index="hour", columns="zone", values="mcc")
spread = p["SPPSOUTH_HUB"] - p["SPPNORTH_HUB"]
mon = (pd.Timestamp("2024-01-01") + pd.to_timedelta(spread.index, unit="h")).month
excess = np.where(np.isin(mon, [9, 10]), np.clip(spread - 5.68, 0, None), 0)
z = pd.read_parquet("data/raw/_validation-source/actual_lmp_hourly_SPP.parquet")
a = z[z.year == 2024].set_index("hour").rt.reindex(range(8760))
# system hub = simple mean of N and S hubs -> removing excess from S lowers system by excess/2
adj = a - pd.Series(excess / 2, index=spread.index).reindex(range(8760)).fillna(0)
s = pd.read_parquet(
    "results/calibration/closeout_spp_nuc_span/hourly/system_2024.parquet"
)
s = s[s["pass"] == "P1"]
d = s.groupby("hour").demand.sum().reindex(range(8760))
m = (pd.Timestamp("2024-01-01") + pd.to_timedelta(np.arange(8760), unit="h")).month


def lwm(x):
    df = pd.DataFrame({"x": x.values, "d": d.values, "m": m}).dropna()
    return df.groupby("m").apply(lambda b: (b.x * b.d).sum() / b.d.sum()).values


for tag, run in (("keeper", "closeout_spp_nuc_span"), ("arm", "closeout_spp_w3_span")):
    ss = pd.read_parquet(f"results/calibration/{run}/hourly/system_2024.parquet")
    ss = ss[ss["pass"] == "P1"]
    mm = (
        ss.assign(
            m=(pd.Timestamp("2024-01-01") + pd.to_timedelta(ss.hour, unit="h")).dt.month
        )
        .groupby("m")
        .apply(lambda b: (b.price * b.demand).sum() / b.demand.sum())
        .values
    )
    for lab, act in (
        ("actual", lwm(a)),
        ("actual minus excess Sep-Oct S-N MCC", lwm(adj)),
    ):
        print(tag, lab, "C3b %.3f" % (math.sqrt(((mm - act) ** 2).mean()) / act.mean()))
