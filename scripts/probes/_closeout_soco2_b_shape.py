"""(b) hourly shape: model vs CAMPD (net-equivalent) by class, by load decile and hour of day."""

import pandas as pd
import numpy as np

OUT = "docs/records/soco/r-soco/closeout-soco-2/"
g = pd.read_parquet("data/raw/_processed-legacy/eia923_monthly_generation.parquet")
PM = {
    "CC_REGULAR": ["CA", "CT", "CS"],
    "COAL_BIT": ["ST"],
    "COAL_PRB": ["ST"],
    "ST_GAS": ["ST"],
    "CT_PEAKER": ["GT"],
}
out = []
for y in [2019, 2020, 2021, 2022, 2023, 2024]:
    u = pd.read_parquet(
        f"results/calibration/w0_soco_span/hourly/unit_marginal_{y}.parquet",
        columns=[
            "unit_id",
            "plant_code",
            "plant_group",
            "hour",
            "mw",
            "cap_mw",
            "mc",
            "marginal",
        ],
    )
    s = pd.read_parquet(f"results/calibration/w0_soco_span/hourly/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    dem = s.groupby("hour").demand.sum()
    price = s.groupby("hour").price.mean()
    frames = []
    for st in ["GA", "AL", "MS", "FL"]:
        try:
            c = pd.read_parquet(
                f"data/raw/campd-unit-level/{st}_{y}.parquet",
                columns=[
                    "facilityId",
                    "date",
                    "hour",
                    "grossLoad",
                    "unitType",
                    "primaryFuelInfo",
                ],
            )
        except Exception:
            continue
        c["plant_code"] = c.facilityId.astype(int)
        frames.append(c)
    C = pd.concat(frames)
    hrs = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
    C["h"] = (
        (pd.to_datetime(C.date) - pd.Timestamp(f"{y}-01-01")).dt.days * 24 + C.hour
    ).astype(int)
    C = C[C.h < 8760]
    for cls in ["CC_REGULAR", "COAL_BIT", "COAL_PRB"]:
        uu = u[u.plant_group == cls]
        plants = uu.plant_code.unique()
        m = uu.groupby("hour").mw.sum().reindex(range(8760), fill_value=0)
        cc = C[C.plant_code.isin(plants)]
        if cls == "CC_REGULAR":
            cc = cc[cc.unitType.str.contains("ombined", na=False)]
        else:
            cc = cc[cc.primaryFuelInfo.str.contains("Coal", na=False)]
        # per-plant k
        e = g[(g.year == y) & g.plant_id.isin(plants) & g.prime_mover.isin(PM[cls])]
        if cls != "CC_REGULAR":
            e = e[e.fuel_type.isin(["BIT", "SUB", "LIG", "RC", "WC"])]
        ek = e.groupby("plant_id").netgen_annual_mwh.sum()
        gk = cc.groupby("plant_code").grossLoad.sum()
        k = (ek / gk).replace([np.inf], np.nan).fillna(0).clip(0, 2)
        cc = cc.assign(net=cc.grossLoad * cc.plant_code.map(k).fillna(0))
        a = cc.groupby("h").net.sum().reindex(range(8760), fill_value=0)
        df = pd.DataFrame(
            {
                "model": m.values,
                "actual": a.values,
                "dem": dem.values,
                "price": price.values,
                "hod": hrs.hour,
                "mon": hrs.month,
            }
        )
        df["dec"] = pd.qcut(df.dem, 10, labels=False)
        df["cls"] = cls
        df["year"] = y
        out.append(df)
r = pd.concat(out)
r.groupby(["year", "cls", "dec"])[["model", "actual"]].mean().to_csv(
    OUT + "b_shape_deciles.csv"
)
for y in [2019, 2021, 2023]:
    for cls in ["CC_REGULAR", "COAL_BIT", "COAL_PRB"]:
        x = r[(r.year == y) & (r.cls == cls)]
        t = x.groupby("dec")[["model", "actual"]].mean().round(0)
        t["gap"] = t.model - t.actual
        print(
            y,
            cls,
            "TWh model %.2f actual(campd-net) %.2f"
            % (x.model.sum() / 1e6, x.actual.sum() / 1e6),
        )
        print(t.T.to_string())
