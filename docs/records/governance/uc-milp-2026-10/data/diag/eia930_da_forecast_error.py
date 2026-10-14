# UC-DIAG zero-LP reading (FINDING-ucmilp-diag-undercommit-2026-10-14).
# EIA-930 BA day-ahead demand forecast (DF) minus actual demand, at the year's top-100 / top-10 % load hours.
# Rows with |DF - actual| > 30 % of actual are dropped as data errors (count reported).
import pandas as pd

print(
    "BA year | n_drop | top-100 actual-load h: median(DF-actual) MW | mean | top-10% load h: median(DF-actual) | all h median | all h MAPE"
)
for ba, yrs in [
    ("SWPP", [2019, 2020, 2021, 2022, 2023, 2024]),
    ("CISO", [2020, 2021, 2022, 2023, 2024]),
    ("NYIS", [2022, 2023]),
    ("ISNE", [2022, 2023]),
    ("ERCO", [2019, 2020]),
    ("MISO", [2023, 2024]),
]:
    d = pd.read_parquet(f"data/raw/eia-930-hourly/{ba} hourly.parquet")
    d["y"] = pd.to_datetime(d["Local time"]).dt.year
    for y in yrs:
        x = d[(d.y == y)].dropna(subset=["Demand forecast", "Demand"])
        x = x[(x.Demand > 0)]
        bad = (x["Demand forecast"] - x.Demand).abs() > 0.3 * x.Demand
        x = x[~bad]
        e = x["Demand forecast"] - x["Demand"]
        t100 = x.Demand.nlargest(100).index
        t10 = x.Demand.nlargest(int(len(x) * 0.1)).index
        print(
            f"{ba} {y} | {bad.sum()} | {e[t100].median():6.0f} | {e[t100].mean():6.0f} | {e[t10].median():6.0f} | {e.median():5.0f} | {(e.abs() / x.Demand).mean() * 100:.1f}%"
        )
