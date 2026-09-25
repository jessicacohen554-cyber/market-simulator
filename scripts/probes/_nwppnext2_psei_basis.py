"""NWPP-NEXT-2 item 4 probe (zero LP): PSEI EIA-930 basis vs FERC 714, the Colstrip
double booking, and the non-balance demand flag. Record:
docs/handoffs/FINDING-nwppnext2-psei-basis-2026-09-25.md. Run from repo root.
"""

# ruff: noqa
# --- part 1: annual basis + Aug-2021 window
import pandas as pd, numpy as np

e = pd.read_parquet("data/raw/eia-930-hourly/PSEI hourly.parquet")
e["utc"] = pd.to_datetime(e["UTC time"])
e = e.set_index("utc")
f = pd.read_csv("data/raw/ferc-714/psei_hourly_planning_area_demand_2018_2024.csv")
f["utc"] = pd.to_datetime(f["datetime_utc"]).dt.tz_localize(None)
f = f.set_index("utc")["demand_reported_mwh"]
e["ferc"] = f.reindex(e.index)
e["ferc_m1"] = f.reindex(e.index - pd.Timedelta(hours=1)).values
e["bal"] = e["Net generation"] - e["Total interchange"]
e["bal_adj"] = e["Net generation (Adjusted)"] - e["Total interchange (Adjusted)"]
e["yr"] = e.index.year
g = e.groupby("yr")
out = pd.DataFrame(
    {
        "D_TWh": g["Demand"].sum() / 1e6,
        "Dadj_TWh": g["Demand (Adjusted)"].sum() / 1e6,
        "Dfc_TWh": g["Demand forecast"].sum() / 1e6,
        "FERC_TWh": g["ferc"].sum() / 1e6,
        "NG": g["Net generation"].sum() / 1e6,
        "TI": g["Total interchange"].sum() / 1e6,
        "nanD": g["Demand"].apply(lambda s: s.isna().sum()),
        "nanDadj": g["Demand (Adjusted)"].apply(lambda s: s.isna().sum()),
        "D_neq_Dadj_h": g.apply(
            lambda d: ((d["Demand"] - d["Demand (Adjusted)"]).abs() > 1).sum()
        ),
        "bal_resid_med": g.apply(
            lambda d: (d["Demand (Adjusted)"] - d["bal_adj"]).median()
        ),
        "ratio_D_FERC_med": g.apply(
            lambda d: (d["Demand (Adjusted)"] / d["ferc"]).median()
        ),
        "ratio_Dfc_FERC_med": g.apply(
            lambda d: (d["Demand forecast"] / d["ferc"]).median()
        ),
    }
)
pd.set_option("display.width", 250)
print(out.round(3))
# monthly ratio 2020-2021
m = e["2020-01":"2021-03"]
print((m["Demand (Adjusted)"] / m["ferc"]).resample("MS").median().round(3))
print(m["Demand (Adjusted)"].resample("MS").count())
w = e["2021-07-25":"2021-08-22"]
d = w.assign(diff=w["Demand (Adjusted)"] - w["ferc"])
print(d["diff"].resample("D").mean().round(0))
print(
    d[
        [
            "Demand",
            "Demand (Adjusted)",
            "ferc",
            "Demand forecast",
            "bal",
            "bal_adj",
            "Net generation",
            "Total interchange",
        ]
    ]
    .resample("D")
    .mean()
    .round(0)
)
print(
    out[
        [
            "NG",
            "TI",
            "nanD",
            "nanDadj",
            "D_neq_Dadj_h",
            "bal_resid_med",
            "FERC_TWh",
            "Dfc_TWh",
        ]
    ].round(3)
)
# hours where TI missing but D present, per year
e["ti_nan_d_ok"] = (
    e["Total interchange (Adjusted)"].isna() & e["Demand (Adjusted)"].notna()
)
print(e.groupby("yr")["ti_nan_d_ok"].sum())
x = e[e.ti_nan_d_ok]
print(
    x.groupby("yr").apply(
        lambda d: pd.Series(
            {
                "h": len(d),
                "D_minus_NG_max": (
                    d["Demand (Adjusted)"] - d["Net generation (Adjusted)"]
                )
                .abs()
                .max(),
                "D_minus_FERC_TWh": (d["Demand (Adjusted)"] - d["ferc"]).sum() / 1e6,
            }
        )
    )
)
# 2019 balance check
for y in (2019, 2021, 2023):
    d = e[e.yr == y]
    print(
        y,
        "median |D-(NG-TI)|",
        (d["Demand (Adjusted)"] - d["bal_adj"]).abs().median(),
        "D/FERC(lag-1) med",
        (d["Demand (Adjusted)"] / d["ferc_m1"]).median(),
    )

# --- part 2: Colstrip regression


def load(m):
    x = pd.read_parquet(f"data/raw/eia-930-hourly/{m} hourly.parquet")
    x["utc"] = pd.to_datetime(x["UTC time"])
    return x.set_index("utc")


p = load("PSEI")
n = load("NWMT")
f = pd.read_csv("data/raw/ferc-714/psei_hourly_planning_area_demand_2018_2024.csv")
f["utc"] = pd.to_datetime(f["datetime_utc"]).dt.tz_localize(None)
f = f.set_index("utc")["demand_reported_mwh"]
p["ferc"] = f.reindex(p.index - pd.Timedelta(hours=1)).values  # lag -1 in 2019
y = p.loc["2019"]
ok = y["Demand (Adjusted)"].notna() & y["ferc"].notna() & y["NG: COL"].notna()
ex = (y["Demand (Adjusted)"] - y["ferc"])[ok]
col = y["NG: COL"][ok]
print(
    "2019 excess TWh",
    ex.sum() / 1e6,
    "COL TWh",
    col.sum() / 1e6,
    "r",
    np.corrcoef(ex, col)[0, 1],
)
b = np.polyfit(col, ex, 1)
print("slope,intercept", b)
# residual after removing COL
r = ex - col
print("resid mean MW", r.mean(), "sd", r.std(), "excess sd", ex.std())
# NWMT COL
for yr in (2019, 2020, 2021, 2022):
    print(
        yr,
        "NWMT NG:COL TWh",
        n.loc[str(yr)]["NG: COL"].sum() / 1e6,
        "PSEI NG:COL",
        p.loc[str(yr)]["NG: COL"].sum() / 1e6,
    )
# monthly Colstrip from CAMPD? skip
# 2021 check: D vs FERC lag0 residual vs COL (zero)

# --- part 3: non-balance flag over all members

from market_sim.data.eia930.frames import _POOL_HOURLY_MEMBERS

rows = []
for m in _POOL_HOURLY_MEMBERS["NWPP"]:
    e = pd.read_parquet(f"data/raw/eia-930-hourly/{m} hourly.parquet")
    e["yr"] = pd.to_datetime(e["UTC time"]).dt.year
    D = e["Demand (Adjusted)"]
    NG = e["Net generation (Adjusted)"]
    TI = e["Total interchange (Adjusted)"]
    flag = TI.isna() & D.notna() & (D == NG)
    tin = TI.isna() & D.notna()
    for y, g in e.assign(flag=flag, tin=tin).groupby("yr"):
        if y < 2019 or y > 2025:
            continue
        if g.flag.sum() or g.tin.sum():
            rows.append(
                (
                    m,
                    y,
                    int(g.tin.sum()),
                    int(g.flag.sum()),
                    round(g.loc[g.flag, "Demand (Adjusted)"].sum() / 1e6, 3),
                )
            )
print(
    pd.DataFrame(
        rows, columns=["ba", "yr", "TInan_Dpresent", "D_eq_NG_TInan", "D_TWh_in_flag"]
    ).to_string()
)
