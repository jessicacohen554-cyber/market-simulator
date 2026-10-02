"""soco-100 record: monthly FERC-714 Sch. 6 lambda vs EIA-923 delivered gas and Henry Hub, per respondent (FINDING-soco-100 §3). Zero LP; reads committed data only."""

import pandas as pd, numpy as np

pd.set_option("display.width", 220)
UT = {
    "FPL": [6452],
    "FPC": [6455],
    "JEA": [9617],
    "TAL": [18445],
    "SOCO": [195, 7140, 12686],
}
g = pd.read_parquet("data/raw/eia-860/eia860_generator_operable.parquet")
g["uid"] = pd.to_numeric(g["Utility ID"], errors="coerce")
fc = pd.read_parquet("data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet")
fc = fc[fc.fuel_group == "Natural Gas"]
hh = pd.read_csv("data/raw/gas-prices/henry_hub_monthly.csv")
print(hh.columns.tolist())
GULF = {
    641,
    642,
    643,
    7242,
}  # Crist, Scholz, Lansing Smith, Pea Ridge: Gulf Power (SOCO BA pre-2022)
plants = {
    k: set(g.loc[g.uid.isin(v), "Plant Code"].astype(int))
    - (GULF if k == "FPL" else set())
    for k, v in UT.items()
}
lam = pd.read_csv(
    "data/raw/ferc-714/soco_neighbor_hourly_system_lambda_2019_2025.csv",
    parse_dates=["datetime_utc"],
)
so = pd.read_csv(
    "data/raw/ferc-714/soco_hourly_system_lambda_2019_2025.csv",
    parse_dates=["datetime_utc"],
)
so["ba_code"] = "SOCO"
lam = pd.concat([lam, so[lam.columns.intersection(so.columns)]])
vc = [c for c in lam.columns if "lambda" in c][0]
lam = lam[lam[vc] != 0]
lam["t"] = lam.datetime_utc - pd.Timedelta(hours=5)
lam["year"] = lam.t.dt.year
lam["month"] = lam.t.dt.month
lam = lam[lam.year.between(2019, 2025)]
mlam = lam.groupby(["ba_code", "year", "month"])[vc].mean().rename("lam").reset_index()
rows = []
for k, p in plants.items():
    f = fc[fc.plant_id.isin(p)]
    m = (
        f.groupby(["year", "month"])
        .apply(
            lambda x: np.average(x.price_per_mmbtu, weights=x.quantity),
            include_groups=False,
        )
        .rename("gas")
        .reset_index()
    )
    m["ba_code"] = k
    rows.append(m)
gas = pd.concat(rows)
d = mlam.merge(gas, on=["ba_code", "year", "month"]).merge(hh, on=["year", "month"])
d["hr_deliv"] = d.lam / d.gas
d["hr_hh"] = d.lam / d.price_usd_mmbtu
d["basis"] = d.gas - d.price_usd_mmbtu
a = (
    d.groupby(["ba_code", "year"])
    .agg(
        lam=("lam", "mean"),
        gas=("gas", "mean"),
        basis=("basis", "mean"),
        hr_deliv=("hr_deliv", "mean"),
        hr_hh=("hr_hh", "mean"),
    )
    .round(2)
)
print(a.unstack(0).swaplevel(axis=1).sort_index(axis=1).to_string())
d.to_csv("docs/records/soco/r-soco/soco100_lambda_vs_gas_monthly.csv", index=False)
