"""closeout-NWPP wave 1 (zero LP): lever C census — Bridger 8066 2023, keeper #20 vs CEMS, level vs decommitment.

Reads keeper #20's 2023 leg ``unit_hourly_2023`` (extract: ``git fetch --depth=1 origin
a54c7b97a9c588564bab90746f2dbbc44fd56838 && git archive a54c7b97a9c588564bab90746f2dbbc44fd56838
results/calibration/nwppnext16c_2023 | tar -x -C LEG_ROOT``) and CAMPD unit-level CEMS. Prints FINDING-nwpp-closeout-w1-censuses §2.

Usage: python scripts/probes/_nwpp_closeout_w1_leverc_bridger_shape.py [LEG_ROOT]
"""

import sys
import numpy as np
import pandas as pd
from itertools import groupby

B = (
    sys.argv[1] if len(sys.argv) > 1 else "."
) + "/results/calibration/nwppnext16c_2023/hourly/unit_hourly_2023.parquet"
u = pd.read_parquet(B)
b = u[u.plant_code == 8066].copy()
b["unit_id"] = b.unit_id.astype(str)
b["tr"] = b.unit_id.str.rsplit("_", n=1).str[1]
P = b.pivot_table(index="hour", columns="tr", values="mw", aggfunc="sum").fillna(0)
C = b.pivot_table(index="hour", columns="tr", values="cap_mw", aggfunc="sum").fillna(0)
ts = pd.Timestamp("2023-01-01") + pd.to_timedelta(P.index, unit="h")
mon = ts.month
plant = P.sum(1)
cap = C.sum(1)
econ = P[["econlo", "econhi", "peak", "committed"]].sum(1)
NAME = 2119.0
d = pd.read_parquet("data/raw/campd-unit-level/WY_2023.parquet")
d = d[d.facilityId.astype(str) == "8066"].copy()
d["gl"] = 0
d["ts"] = pd.to_datetime(d.date) + pd.to_timedelta(d.hour, unit="h")
d["gl"] = pd.to_numeric(d.grossLoad).fillna(0)
d["op"] = pd.to_numeric(d.opTime).fillna(0)
units = sorted(d.unitId.unique())
print("CEMS units", units, d.primaryFuelInfo.unique())
G = (
    d.pivot_table(index="ts", columns="unitId", values="gl", aggfunc="sum")
    .reindex(pd.date_range("2023-01-01", periods=8760, freq="h"))
    .fillna(0)
)
O = (
    d.pivot_table(index="ts", columns="unitId", values="op", aggfunc="sum")
    .reindex(G.index)
    .fillna(0)
)
cm = G.index.month
umax = G.quantile(0.995)
print("unit p99.5 gross MW", umax.round(0).to_dict())
rows = []
for m in range(1, 13):
    mm = mon == m
    cmm = cm == m
    n = mm.sum()
    pl = plant[mm]
    ec = econ[mm]
    Gm = G[cmm]
    Om = O[cmm]
    on = Om > 0
    load_on = (Gm.where(on) / umax).stack().median()
    rows.append(
        dict(
            m=m,
            mod_GWh=pl.sum() / 1e3,
            mod_mean=pl.mean(),
            mod_mustrun_only_h=int((ec < 1).sum()),
            mod_lt5pct_h=int((pl < 0.05 * NAME).sum()),
            mod_lt25pct_h=int((pl < 0.25 * NAME).sum()),
            cems_GWh=Gm.sum().sum() / 1e3,
            cems_unit_hrs_online=float(Om.sum().sum()),
            cems_mean_units_on=float(on.sum(1).mean()),
            cems_h_zero_units=int((on.sum(1) == 0).sum()),
            cems_h_le1_unit=int((on.sum(1) <= 1).sum()),
            cems_plant_lt25pct_h=int((Gm.sum(1) < 0.25 * NAME).sum()),
            cems_load_when_on=float(load_on),
            hours=int(n),
        )
    )
R = pd.DataFrame(rows).set_index("m").round(2)
print(R.to_string())
# per-unit CEMS online hours by month
print((O.groupby(cm).sum()).round(0).to_string())
# CEMS per-unit offline spells >=24h in Aug-Oct
for uid in units:
    s = (O[uid] > 0).values
    spells = []
    i = 0
    for k, gp in groupby(s):
        L = len(list(gp))
    pos = 0
    for k, gp in groupby(s):
        L = len(list(gp))
        if not k and L >= 24:
            spells.append((str(G.index[pos].date()), L))
        pos += L
    print(
        "CEMS",
        uid,
        "off-spells>=24h:",
        [x for x in spells if x[0] >= "2023-07-15" and x[0] <= "2023-11-01"],
    )
# model econ-tranche gaps in Aug-Oct
s = (econ > 0.05 * econ.max()).values
pos = 0
gaps = []
for k, gp in groupby(s):
    L = len(list(gp))
    if not k:
        gaps.append((str(ts[pos].date()), L))
    pos += L
ao = [g for g in gaps if "2023-07-25" <= g[0] <= "2023-10-31"]
print("model econ-off gaps Aug-Oct (start,len h):", ao)
L = np.array([g[1] for g in ao])
print(
    "gap len hist <16h",
    (L < 16).sum(),
    "16-24",
    ((L >= 16) & (L < 24)).sum(),
    "24-168",
    ((L >= 24) & (L < 168)).sum(),
    ">=168",
    (L >= 168).sum(),
    "hours in gaps<16h",
    L[L < 16].sum(),
    "in gaps<24h",
    L[L < 24].sum(),
)
# committed tranche runs (detector input)
cs = (P["committed"] > 0.05 * C["committed"].max()).values
print(
    "committed tranche on-hours by month",
    pd.Series(cs, index=mon).groupby(level=0).sum().to_dict(),
)
# bound: Aug-Oct, CEMS online count x min-load ( p05 of load-when-on) vs model
lsl = (G.where(O > 0) / umax).quantile(0.05)
print("unit LSL frac p05 of load-when-on", lsl.round(3).to_dict())
for m in (8, 9, 10):
    mm = mon == m
    cmm = cm == m
    hold = (
        (O[cmm] > 0).astype(float).mul(lsl * umax, axis=1).sum(1).values
    )  # MW floor if CEMS-online units held at LSL
    model = plant[mm].values
    gap_vs_lsl = np.clip(hold - model, 0, None).sum() / 1e3
    gap_vs_cems = (G[cmm].sum(1).values - model).sum() / 1e3
    print(
        m,
        "GWh: floor-at-LSL shortfall",
        round(gap_vs_lsl, 1),
        "model-CEMS gap",
        round(-gap_vs_cems, 1),
    )
print(
    "--- alt LSL bounds (GWh shortfall if CEMS-online units held at frac x unit p99.5), Aug/Sep/Oct"
)
full = O >= 1
for q in (0.05, 0.10, 0.25):
    print(
        "p%02d load|opTime=1" % int(q * 100),
        (G.where(full) / umax).quantile(q).round(3).to_dict(),
    )
for lab, fr in [
    ("meas_p10", (G.where(full) / umax).quantile(0.10)),
    ("0.30", pd.Series(0.30, index=umax.index)),
    ("0.40", pd.Series(0.40, index=umax.index)),
]:
    out = []
    for m in (8, 9, 10):
        mm = mon == m
        cmm = cm == m
        hold = (O[cmm] > 0).astype(float).mul(fr * umax, axis=1).sum(axis=1).values
        out.append(round(np.clip(hold - plant[mm].values, 0, None).sum() / 1e3, 1))
    print(
        lab,
        "MW floor 4 units",
        round(float((fr * umax).sum()), 0),
        "shortfall GWh Aug/Sep/Oct",
        out,
        "sum",
        round(sum(out), 1),
    )
print("model must-run MW by month", C["mustrun"].groupby(mon).mean().round(1).to_dict())
