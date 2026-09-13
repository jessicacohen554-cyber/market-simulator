"""nyiso-232 (ZERO LP): does NYISO's C3a year-to-year tilt survive removing the tail?

The decomposition test behind
``docs/FINDING-nyiso232-c3a-is-two-objects-2026-09-13.md``. Progressively removes
each year's highest-ACTUAL-price hours from the designated keeper's committed
``hourly/system_<year>.parquet`` and re-measures both the load-weighted C3a
residual and its correlation with the solve year's own gas anchor.

The excluded set is chosen on the ACTUAL series, never the model's, so the
model's own behaviour cannot select which hours are dropped.

MEASURED: the year-to-year SPREAD is invariant (10.23 -> 10.09 pp while 5 % of
hours are removed) and the gas correlation holds (r -0.92 to -0.99), while the
LEVEL lifts ~13 pp in every year and flips sign. Two objects, separated.
"""

import numpy as np
import pandas as pd
from pathlib import Path

BUN = Path("results/calibration/nyiso231_anchor_span/hourly")
act = pd.read_parquet("data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet")
ANCH = {2022: 8.4431, 2023: 3.3566, 2024: 2.7969, 2025: 5.5602}
out = []
for y in (2022, 2023, 2024, 2025):
    s = pd.read_parquet(BUN / f"system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    n = s.assign(pw=s.price * s.demand).groupby("hour")[["pw", "demand"]].sum()
    g = pd.DataFrame(
        {
            "hour": n.index,
            "model": (n.pw / n.demand).to_numpy(),
            "demand": n.demand.to_numpy(),
        }
    )
    a = act[act.year == y][["hour", "rt"]].rename(columns={"rt": "actual"})
    m = g.merge(a, on="hour").dropna()
    m["year"] = y
    out.append(m)
d = pd.concat(out, ignore_index=True)


def resid(x):
    return (
        100
        * (
            np.average(x.model, weights=x.demand)
            - np.average(x.actual, weights=x.demand)
        )
        / np.average(x.actual, weights=x.demand)
    )


print(
    f"{'excluded':>28s} | "
    + " ".join(f"{y:>8d}" for y in (2022, 2023, 2024, 2025))
    + " |   spread |      r |     r2"
)
for label, k in (
    ("nothing (all 8760 h)", 0),
    ("worst 25 ACTUAL-price h", 25),
    ("worst 50 ACTUAL-price h", 50),
    ("worst 100 ACTUAL-price h", 100),
    ("worst 200 ACTUAL-price h", 200),
    ("worst 438 h (top 5%)", 438),
):
    rs = []
    for y in (2022, 2023, 2024, 2025):
        x = d[d.year == y]
        if k:
            x = x[~x.hour.isin(x.nlargest(k, "actual").hour)]
        rs.append(resid(x))
    sp = max(rs) - min(rs)
    r = np.corrcoef([ANCH[y] for y in (2022, 2023, 2024, 2025)], rs)[0, 1]
    print(
        f"{label:>28s} | "
        + " ".join(f"{v:+8.2f}" for v in rs)
        + f" | {sp:8.2f} | {r:+6.3f} | {r**2:6.3f}"
    )

print(
    "\n  share of ISO-hours removed at each cut: 25 h = 0.29%, 100 h = 1.14%, 438 h = 5.00%"
)
print("\n=== and the same cut on C3c's own object (model hours > $300) ===")
for y in (2022, 2023, 2024, 2025):
    x = d[d.year == y]
    print(
        f"  {y}: actual h>$300 = {int((x.actual > 300).sum()):4d}   model h>$300 = {int((x.model > 300).sum()):3d}"
        f"   actual h>$200 = {int((x.actual > 200).sum()):4d}   model h>$200 = {int((x.model > 200).sum()):3d}"
    )
