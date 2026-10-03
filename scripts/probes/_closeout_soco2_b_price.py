"""(b) merit order: model offers vs F923-delivered (and spot-receipt) fuel at measured HR, CC vs coal BIT, per month."""

import pandas as pd
import numpy as np

OUT = "docs/records/soco/r-soco/closeout-soco-2/"
fc = pd.read_parquet("data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet")
g = pd.read_parquet("data/raw/_processed-legacy/eia923_monthly_generation.parquet")
rows = []
for y in range(2019, 2026):
    u = pd.read_parquet(
        f"results/calibration/w0_soco_span/hourly/unit_marginal_{y}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "hour", "mw", "cap_mw", "mc"],
    )
    hrs = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
    u["m"] = hrs.month.values[u.hour.values]
    u = u[u.plant_group.isin(["CC_REGULAR", "COAL_BIT", "COAL_PRB"])]
    u["tr"] = u.unit_id.astype(str).str.extract(
        r"_(committed|econlo|econhi|peak|mustrun)$"
    )[0]
    ue = u[u.tr.isin(["econlo", "econhi"])]
    # capacity-weighted econ mc per plant-month
    mm = (
        ue.assign(w=ue.cap_mw * ue.mc)
        .groupby(["plant_group", "plant_code", "m"], observed=True)[["w", "cap_mw"]]
        .sum()
    )
    mm = (mm.w / mm.cap_mw).rename("model_mc").reset_index()
    rcp = pd.read_csv(f"data/raw/coal-receipts/coal_receipts_{y}.csv", low_memory=False)
    rcp = rcp[rcp["Plant Id"].isin(mm.plant_code.unique())]
    for _c in ["QUANTITY", "Average Heat Content", "FUEL_COST"]:
        rcp[_c] = pd.to_numeric(rcp[_c], errors="coerce")
    rcp["mmbtu"] = rcp.QUANTITY * rcp["Average Heat Content"]
    rcp["cost"] = rcp.mmbtu * rcp.FUEL_COST / 100
    sp = (
        rcp[rcp["Purchase Type"] == "S"]
        .groupby(["Plant Id", "MONTH"])[["cost", "mmbtu"]]
        .sum()
    )
    sp = (sp.cost / sp.mmbtu).rename("spot")
    al = rcp.groupby(["Plant Id", "MONTH"])[["cost", "mmbtu"]].sum()
    al = (al.cost / al.mmbtu).rename("rcpt_all")
    f = fc[(fc.year == y)].copy()
    gas = (
        f[f.fuel_group == "Natural Gas"]
        .set_index(["plant_id", "month"])
        .price_per_mmbtu.rename("f923_gas")
    )
    coal = (
        f[f.fuel_group == "Coal"]
        .set_index(["plant_id", "month"])
        .price_per_mmbtu.rename("f923_coal")
    )
    mm = (
        mm.join(gas, on=["plant_code", "m"])
        .join(coal, on=["plant_code", "m"])
        .join(sp, on=["plant_code", "m"])
        .join(al, on=["plant_code", "m"])
    )
    mm["year"] = y
    rows.append(mm)
r = pd.concat(rows)
# measured HR per plant-year: CAMPD heat input / EIA-923 net
hrr = []
for y in range(2019, 2026):
    fr = []
    for st in ["GA", "AL", "MS", "FL"]:
        try:
            c = pd.read_parquet(
                f"data/raw/campd-unit-level/{st}_{y}.parquet",
                columns=["facilityId", "heatInput", "unitType", "primaryFuelInfo"],
            )
        except Exception:
            continue
        c["plant_code"] = c.facilityId.astype(int)
        fr.append(c)
    C = pd.concat(fr)
    cc = (
        C[C.unitType.str.contains("ombined", na=False)]
        .groupby("plant_code")
        .heatInput.sum()
    )
    co = (
        C[C.primaryFuelInfo.str.contains("Coal", na=False)]
        .groupby("plant_code")
        .heatInput.sum()
    )
    e = g[g.year == y]
    ecc = (
        e[e.prime_mover.isin(["CA", "CT", "CS"])]
        .groupby("plant_id")
        .netgen_annual_mwh.sum()
    )
    eco = (
        e[e.fuel_type.isin(["BIT", "SUB", "LIG", "RC"])]
        .groupby("plant_id")
        .netgen_annual_mwh.sum()
    )
    h = pd.concat([(cc / ecc).rename("hr_cc"), (co / eco).rename("hr_coal")], axis=1)
    h["year"] = y
    hrr.append(h.reset_index().rename(columns={"index": "plant_code"}))
H = pd.concat(hrr).rename(columns={"plant_id": "plant_code"})
r = r.merge(H, on=["plant_code", "year"], how="left")
r["hr"] = np.where(r.plant_group == "CC_REGULAR", r.hr_cc, r.hr_coal)
r["f923_fuel"] = np.where(r.plant_group == "CC_REGULAR", r.f923_gas, r.f923_coal)
r["mc_f923"] = r.hr * r.f923_fuel
r["mc_spot"] = np.where(r.plant_group == "CC_REGULAR", np.nan, r.hr * r.spot)
r["implied_fuel"] = r.model_mc / r.hr
r.to_csv(OUT + "b_price.csv", index=False)
pd.set_option("display.width", 250)
a = (
    r.groupby(["year", "plant_group"])
    .agg(
        model_mc=("model_mc", "median"),
        mc_f923=("mc_f923", "median"),
        mc_spot=("mc_spot", "median"),
        f923=("f923_fuel", "median"),
        spot=("spot", "median"),
        impl=("implied_fuel", "median"),
        hr=("hr", "median"),
    )
    .round(2)
)
print(a.to_string())
for y in [2019, 2021]:
    print(y)
    print(
        r[r.year == y]
        .groupby(["plant_group", "plant_code"])
        .agg(
            model_mc=("model_mc", "mean"),
            mc_f923=("mc_f923", "mean"),
            mc_spot=("mc_spot", "mean"),
            f923=("f923_fuel", "mean"),
            spot=("spot", "mean"),
            rcpt=("rcpt_all", "mean"),
            impl=("implied_fuel", "mean"),
            hr=("hr", "first"),
        )
        .round(2)
        .to_string()
    )
