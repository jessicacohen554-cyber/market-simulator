"""MISO baseline dispatch-profile diagnostic (reads a solved bundle).

Extracts from results/calibration/miso_diag_2024_baseline/dispatch/2024_P1.parquet:
  - system load-weighted mean LMP vs actual RT ($30.8, MISO 2024)  [C3a]
  - LMP distribution + scarcity-tail hour counts                    [C3c]
  - per-class annual TWh, model vs CAMPD/e930 bench                 [C1]
  - marginal-class attribution by LMP band (joins fleet SRMC)

Throwaway diagnostic (rule 15), not dashboard-registered.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import gzip
import json

sys.path.insert(0, "scripts")
sys.path.insert(0, "src")

YEAR = 2024
GAS = 2.19
BUNDLE = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path("results/calibration/miso_diag_2024_baseline")
)

disp = pd.read_parquet(BUNDLE / "dispatch" / f"{YEAR}_P1.parquet")
print(f"# rows {len(disp):,}  cols {list(disp.columns)}")

# ---- system load-weighted mean LMP (C3a) ----
# per zone-hour LMP is carried on each gen row; take per (zone,hour) unique, weight by zonal load
zl = disp.groupby(["zone", "hour"], observed=True)["lmp"].first()
# zonal demand proxy = total dispatched mw per zone-hour (gen ~ load + net export; good enough weight)
zd = disp.groupby(["zone", "hour"], observed=True)["mw"].sum()
sysmean = np.average(zl.values, weights=zd.values)
print(
    f"\n## C3a system load-weighted mean LMP: model ${sysmean:.2f}  actual $30.80  "
    f"({100 * (sysmean - 30.8) / 30.8:+.1f}%)"
)

lmp_h = (
    disp.groupby("hour", observed=True)["lmp"].mean().to_numpy()
)  # simple hourly mean LMP
print("## LMP distribution (simple hourly mean across zones):")
for p in (5, 25, 50, 75, 90, 95, 99):
    print(f"   p{p:02d} ${np.percentile(lmp_h, p):.1f}")
for thr in (75, 100, 150, 200, 500):
    print(f"   hours > ${thr}: {(lmp_h > thr).sum()}")

# ---- per-class annual TWh model vs bench (C1) ----
model_twh = disp.groupby("klass", observed=True)["mw"].sum() / 1e6
print("\n## C1 per-class annual TWh (model):")
for k, v in model_twh.sort_values(ascending=False).items():
    print(f"   {k:16s} {v:7.2f}")

# bench actual class TWh (e930 / classFull)
try:
    bench = json.load(gzip.open(f"frontend/data/backcast/bench/MISO/{YEAR}.json.gz"))[
        "bench"
    ]
    cf = bench.get("classFull") or {}
    print("\n## C1 bench (CAMPD classFull) annual TWh + model delta:")
    for grp, node in sorted(cf.items()):
        # node may carry annual GWh under a key; probe common shapes
        val = None
        if isinstance(node, dict):
            for key in ("twh", "gwh", "annual", "ann", "total"):
                if key in node:
                    val = node[key]
                    break
            if val is None and "mon" in node and isinstance(node["mon"], list):
                val = sum(x for x in node["mon"] if x)
        if val is not None:
            atwh = val / (1e3 if val > 1e3 else 1)  # gwh->twh heuristic
            print(f"   {grp:16s} actual~{atwh:7.2f}")
except Exception as e:
    print("bench class parse skipped:", e)

# ---- marginal-class attribution: join fleet SRMC, find max-SRMC dispatching tranche/hour ----
from run_calibration import run_year  # noqa: E402

out = run_year(
    YEAR,
    "MISO",
    8760,
    GAS,
    ttc_overrides={},
    coal_prb_passthrough=1.0,
    outage_source="historic",
    coal_prb_passthrough_sigmoid=True,
    coal_mustrun_per_plant=True,
    coal_drop_pof=True,
    coal_prb_passthrough_tiered=True,
    coal_bit_sigmoid=True,
    cc_intermediate_split=True,
    ct_intermediate_split=True,
    st_gas_intermediate=True,
    fleet_only=True,
)
fa = out["fleet_arrays"]
srmc = np.asarray(fa.heat_rate, float) * GAS + np.asarray(fa.vom, float)
srmc_by_uid = dict(zip(fa.unit_ids, srmc))
pg_by_uid = {
    u: (
        str(fa.plant_group[i])
        if fa.plant_group is not None and fa.plant_group[i]
        else "?"
    )
    for i, u in enumerate(fa.unit_ids)
}

d2 = disp[disp["mw"] > 1.0].copy()
d2["srmc"] = d2["unit_id"].map(srmc_by_uid)
d2["mcls"] = d2["unit_id"].map(pg_by_uid)
d2 = d2.dropna(subset=["srmc"])
# per hour: the dispatching tranche with the highest SRMC = marginal-ish class
idx = d2.groupby("hour", observed=True)["srmc"].idxmax()
marg = d2.loc[idx, ["hour", "mcls", "srmc", "lmp"]]
print("\n## marginal-class attribution (highest-SRMC dispatching tranche / hour):")
print(marg["mcls"].value_counts().to_string())
print("\n## marginal class within LMP bands:")
for lo, hi in [(0, 25), (25, 30), (30, 40), (40, 60), (60, 1e9)]:
    sub = marg[(marg["lmp"] >= lo) & (marg["lmp"] < hi)]
    if len(sub):
        top = sub["mcls"].value_counts().head(3)
        print(
            f"   LMP[{lo},{hi}) n={len(sub):5d}: "
            + ", ".join(f"{k} {v}" for k, v in top.items())
        )
