"""closeout-NWPP wave 1 (zero LP): owner ruling R-3 applied to Jim Bridger (plant 8066), 2023.

The EIA-923 take-ceiling envelope (receipts + month-end stock above a declared ``stock_min``) in its
per-month and cumulative forms, against the Page-2 stocks, the Page-5 receipts and keeper #20's Bridger
energy. Prints the tables of FINDING-nwpp-closeout-w1-censuses §3. Run from the repo root. No LP.
"""

import pandas as pd
import numpy as np

R = "data/raw/"
st = {}
for y in range(2018, 2025):
    d = pd.read_csv(R + f"coal-stocks/coal_stocks_{y}.csv")
    d = d[d["Plant Id"] == 8066]
    cols = [c for c in d.columns if c.startswith("Quantity ")]
    st[y] = d[cols].sum().to_numpy(float)
rc = {}
hc = {}
for y in (2022, 2023):
    d = pd.read_csv(R + f"coal-receipts/coal_receipts_{y}.csv")
    d = d[d["Plant Id"] == 8066]
    d["mm"] = d.QUANTITY * d["Average Heat Content"]
    g = (
        d.groupby("MONTH")
        .agg(t=("QUANTITY", "sum"), mm=("mm", "sum"))
        .reindex(range(1, 13), fill_value=0)
    )
    rc[y] = g.t.to_numpy(float)
    hc[y] = (g.mm / g.t).to_numpy()
    print(
        y,
        "receipts kt",
        np.round(rc[y] / 1e3, 0),
        "annual Mt",
        rc[y].sum() / 1e6,
        "hc",
        np.round(hc[y], 2),
    )
gf = pd.read_csv(R + "eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv")
b = (
    gf[(gf.plant_id == 8066) & (gf.year.isin([2022, 2023]))]
    .groupby("year")[["total_fuel_mmbtu", "net_generation_mwh"]]
    .sum()
)
b["hr"] = b.total_fuel_mmbtu / b.net_generation_mwh
print(b)
allst = np.concatenate([st[y] for y in range(2018, 2025)])
print(
    "min stock 2018-24",
    allst.min(),
    "min 2018-22",
    np.concatenate([st[y] for y in range(2018, 2023)]).min(),
)
prev = np.r_[st[2022][-1], st[2023][:-1]]
burn_t = prev + rc[2023] - st[2023]
hr = b.loc[2023, "hr"]
h = hc[2023]


def twh(t):
    return t * h / hr / 1e6


cems = np.array([906, 416, 294, 164, 345, 661, 1155, 1170, 892, 1267, 879, 960]) / 1e3
k20 = np.array([1.37, 1.32, 0.94, 0.61, 0.19, 0.25, 0.36, 1.37, 0.31, 0.21, 0.80, 0.78])
mn = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
print("stock 2023 kt", np.round(st[2023] / 1e3))
print(
    "implied burn kt",
    np.round(burn_t / 1e3),
    "TWh",
    np.round(twh(burn_t), 3),
    "sum",
    twh(burn_t).sum(),
)
for smin_name, smin in [
    ("0", 0),
    ("min18-24 (Oct23)", allst.min()),
    ("min18-22 (Dec22)", 797782),
]:
    ceil_t = rc[2023] + prev - smin
    c = twh(ceil_t)
    print("\nS_min", smin_name, "ceiling TWh", np.round(c, 3))
    cut = np.maximum(k20 - c, 0)
    print(
        " cut by month",
        np.round(cut, 3),
        "FebMay cut",
        cut[1:5].sum(),
        "annual",
        cut.sum(),
    )
# cumulative (pile-carry) form: S_dec + cumR - smin vs model cumulative
for smin in (0, allst.min()):
    cumc = twh(np.cumsum(rc[2023]) + st[2022][-1] - smin)  # approx using monthly hc
    print(
        "cum ceiling smin",
        smin,
        np.round(cumc, 2),
        " model cum",
        np.round(np.cumsum(k20), 2),
    )
print(
    "FebMay: k20",
    k20[1:5].sum(),
    "cems gross",
    cems[1:5].sum(),
    "cems*0.92",
    0.92 * cems[1:5].sum(),
    "implied burn",
    twh(burn_t)[1:5].sum(),
)
d = pd.read_csv(R + "coal-receipts/coal_receipts_2021.csv")
d = d[d["Plant Id"] == 8066]
r21 = d.QUANTITY.sum()
rate = (r21 + rc[2022].sum()) / 2
print("2021 Mt", r21 / 1e6, "prior rate Mt", rate / 1e6)
inc = st[2022][-1] + np.arange(1, 13) / 12 * rate
print("incumbent ratable cum ceiling TWh", np.round(inc * 18.5 / hr / 1e6, 2))
smax = max(np.concatenate([st[y] for y in range(2018, 2023)]))
print("S_max 2018-22", smax)
