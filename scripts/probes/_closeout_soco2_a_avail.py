"""(a) availability vs demonstrated: per CC_REGULAR plant-month, model avail/MWh vs EIA-923 vs CAMPD p99.9."""

import pandas as pd

OUT = "docs/records/soco/r-soco/closeout-soco-2/"
g = pd.read_parquet("data/raw/_processed-legacy/eia923_monthly_generation.parquet")
MON = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]
res = []
for y in range(2019, 2026):
    u = pd.read_parquet(
        f"results/calibration/w0_soco_span/hourly/unit_marginal_{y}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "hour", "mw", "cap_mw", "mc"],
    )
    u = u[u.plant_group == "CC_REGULAR"]
    hrs = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
    u["m"] = hrs.month.values[u.hour.values]
    pm = (
        u.groupby(["plant_code", "m"], observed=True)
        .agg(avail=("cap_mw", "sum"), mwh=("mw", "sum"))
        .reset_index()
    )
    # plant-hour model cap for p99.9 compare
    plants = pm.plant_code.unique()
    # 923 CC prime movers
    e = g[
        (g.year == y)
        & (g.plant_id.isin(plants))
        & (g.prime_mover.isin(["CA", "CT", "CS"]))
    ]
    e = e.groupby("plant_id")[[f"netgen_{m}_mwh" for m in MON]].sum()
    e.columns = range(1, 13)
    e = (
        e.stack()
        .rename("e923")
        .reset_index()
        .rename(columns={"plant_id": "plant_code", "level_1": "m"})
    )
    # CAMPD
    frames = []
    for st in ["GA", "AL", "MS", "FL"]:
        try:
            c = pd.read_parquet(
                f"data/raw/campd-unit-level/{st}_{y}.parquet",
                columns=[
                    "facilityId",
                    "unitId",
                    "date",
                    "hour",
                    "grossLoad",
                    "unitType",
                ],
            )
        except Exception:
            continue
        c["plant_code"] = c.facilityId.astype(int)
        c = c[c.plant_code.isin(plants)]
        frames.append(c)
    c = pd.concat(frames)
    c = c[c.unitType.str.contains("ombined", na=False)]
    ph = c.groupby(["plant_code", "date", "hour"]).grossLoad.sum().reset_index()
    ph["m"] = pd.to_datetime(ph.date).dt.month
    camp = (
        ph.groupby(["plant_code", "m"])
        .grossLoad.agg(p999=lambda s: s.quantile(0.999), gsum="sum")
        .reset_index()
    )
    ann = ph.groupby("plant_code").grossLoad.sum().rename("g_ann")
    d = pm.merge(e, on=["plant_code", "m"], how="left").merge(
        camp, on=["plant_code", "m"], how="left"
    )
    e_ann = d.groupby("plant_code").e923.sum().rename("e_ann")
    d = d.join(ann, on="plant_code").join(e_ann, on="plant_code")
    d["k"] = d.e_ann / d.g_ann
    d["hours"] = d.m.map(lambda m: (hrs.month == m).sum())
    d["demo"] = d.k * d.p999 * d.hours  # demonstrated net-equivalent capability MWh
    d["year"] = y
    res.append(d)
r = pd.concat(res)
r.to_csv(OUT + "a_plant_month.csv", index=False)
a = (
    r.groupby(["year", "plant_code"])
    .agg(
        avail=("avail", "sum"),
        mwh=("mwh", "sum"),
        e923=("e923", "sum"),
        demo=("demo", "sum"),
        k=("k", "first"),
    )
    .reset_index()
)
a["over_avail_demo"] = a.avail - a.demo
a["over_mwh_e923"] = a.mwh - a.e923
a["util"] = a.mwh / a.avail
a["excess_above_demo_month"] = (
    r.assign(x=(r.avail - r.demo).clip(lower=0))
    .groupby(["year", "plant_code"])
    .x.sum()
    .values
)
pd.set_option("display.width", 250)
for y in [2019, 2020, 2021, 2023, 2024]:
    t = a[a.year == y].sort_values("over_mwh_e923", ascending=False)
    print(
        y,
        "CLASS: avail %.2f mwh %.2f e923 %.2f demo %.2f  sum(avail-demo)+ %.2f TWh"
        % (
            t.avail.sum() / 1e6,
            t.mwh.sum() / 1e6,
            t.e923.sum() / 1e6,
            t.demo.sum() / 1e6,
            t.excess_above_demo_month.sum() / 1e6,
        ),
    )
    print(
        (
            t.set_index("plant_code")[
                [
                    "avail",
                    "mwh",
                    "e923",
                    "demo",
                    "excess_above_demo_month",
                    "over_mwh_e923",
                    "util",
                    "k",
                ]
            ]
            .assign(
                **{
                    c: lambda x, c=c: x[c] / 1e3
                    for c in [
                        "avail",
                        "mwh",
                        "e923",
                        "demo",
                        "excess_above_demo_month",
                        "over_mwh_e923",
                    ]
                }
            )
            .round(3)
        )
        .head(14)
        .to_string()
    )
