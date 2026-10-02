"""soco-100 record: CC incremental heat rate per Florida respondent from CAMPD hourly (dF/dP quadratic at median load) levelled to EIA-923 fuel/net (FINDING-soco-100 §4). Zero LP."""

import pandas as pd, numpy as np, sys

g = pd.read_parquet("data/raw/eia-860/eia860_generator_operable.parquet")
g["uid"] = pd.to_numeric(g["Utility ID"], errors="coerce")
UT = {"FPL": [6452], "FPC": [6455], "JEA": [9617], "TAL": [18445]}
GULF = {641, 642, 643, 7242}
plants = {
    k: set(g.loc[g.uid.isin(v), "Plant Code"].astype(int))
    - (GULF if k == "FPL" else set())
    for k, v in UT.items()
}
out = []
for y in [2019, 2020, 2022, 2023, 2024, 2025]:
    c = pd.read_parquet(f"data/raw/campd-unit-level/FL_{y}.parquet")
    c["facilityId"] = c.facilityId.astype(int)
    c = c[
        c.unitType.str.contains("Combined cycle", case=False, na=False)
        & c.primaryFuelInfo.str.contains("Natural Gas", na=False)
    ]
    for k, p in plants.items():
        x = c[c.facilityId.isin(p)]
        for fid, f in x.groupby("facilityId"):
            f = f.assign(on=(f.opTime >= 1) & (f.grossLoad > 0))
            h = f.groupby(["date", "hour"]).agg(
                n=("on", "sum"),
                nany=("opTime", lambda s: (s > 0).sum()),
                F=("heatInput", "sum"),
                P=("grossLoad", "sum"),
            )
            h = h[(h.n == h.nany) & (h.n > 0) & (h.P > 0)]
            for n, hh in h.groupby("n"):
                if len(hh) < 300:
                    continue
                a, b, cc = np.polyfit(hh.P, hh.F, 2)
                pm = hh.P.median()
                ihr = (2 * a * pm + b) / 1000
                ahr = hh.F.sum() / hh.P.sum() / 1000
                out.append(
                    dict(
                        ba=k,
                        year=y,
                        fid=fid,
                        fac=f.facilityName.iloc[0],
                        n=n,
                        hours=len(hh),
                        mwh=hh.P.sum(),
                        ihr=ihr,
                        ahr=ahr,
                    )
                )
o = pd.DataFrame(out)
e = pd.read_csv("data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv")
e = (
    e[e.prime_mover.isin(["CA", "CT", "CS"]) & (e.fuel_type == "NG")]
    .groupby(["year", "plant_id"])[["elec_fuel_mmbtu", "net_generation_mwh"]]
    .sum()
)
e["hr923"] = e.elec_fuel_mmbtu / e.net_generation_mwh
o = o.merge(
    e.hr923.reset_index(),
    left_on=["year", "fid"],
    right_on=["year", "plant_id"],
    how="left",
)
o["ratio"] = o.ihr / o.ahr
o["ihr"] = o.ratio * o.hr923
o["ahr"] = o.hr923
o = o[o.ihr.between(3, 14)]
o.to_csv("docs/records/soco/r-soco/soco100_cc_incremental_hr.csv", index=False)
w = o.groupby(["ba", "year"]).apply(
    lambda z: pd.Series(
        {
            "ihr_net": np.average(z.ihr, weights=z.mwh),
            "ahr_net": np.average(z.ahr, weights=z.mwh),
            "ratio": np.average(z.ratio, weights=z.mwh),
            "ihr_min": z.ihr.min(),
            "ihr_max": z.ihr.max(),
        }
    ),
    include_groups=False,
)
print(w.round(2).unstack(0).to_string())
print(o[o.ba == "TAL"].round(2).to_string())
