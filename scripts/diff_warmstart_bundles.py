"""Diff two calibration dispatch bundles (cold vs warm-start) per plant.

Reads ``dispatch/<year>_P1.parquet`` from two run bundles and reports, for
every plant_code, how much the hourly and annual MW moved between the cold
(two independent solves) and warm-start (build-once, re-cost) paths. Prints a
focused view of named plants of interest plus a fleet-wide summary.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

COLD, WARM, YEAR = sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2023

NAMED = {60122: "Colorado Bend II", 59812: "Wolf Hollow II", 3491: "Handley"}


def load(bundle):
    df = pd.read_parquet(Path(bundle) / "dispatch" / f"{YEAR}_P1.parquet")
    # Sum every unit's MW into its plant for each hour (a plant can hold
    # several units / efficiency-bin rows).
    return df.groupby(["plant_code", "hour"], as_index=False)["mw"].sum()


def plant_series(df, code):
    s = df[df.plant_code == code].sort_values("hour")
    return s["mw"].to_numpy(dtype=float)


c = load(COLD)
w = load(WARM)
codes_c = set(c.plant_code.unique())
codes_w = set(w.plant_code.unique())
assert codes_c == codes_w, f"plant sets differ: {codes_c ^ codes_w}"

# Wide (plant x hour) for fleet-wide stats.
cw = c.pivot(index="plant_code", columns="hour", values="mw").fillna(0.0)
ww = w.pivot(index="plant_code", columns="hour", values="mw").reindex(cw.index).fillna(0.0)
diff = (cw - ww)
annual_c = cw.sum(axis=1) / 1e3  # MWh -> GWh
annual_w = ww.sum(axis=1) / 1e3
annual_d = (annual_c - annual_w)

print(f"=== cold {COLD}  vs  warm {WARM}   year {YEAR}   P1 ===")
print(f"plants: {len(cw)}   hours: {cw.shape[1]}\n")

print("Named plants of interest:")
print(f"{'plant':18s} {'code':>6s} {'cold GWh':>10s} {'warm GWh':>10s} "
      f"{'ΔGWh':>10s} {'Δ%':>7s} {'max|Δ|MW':>9s} {'mean|Δ|MW':>10s} "
      f"{'hrs|Δ|>1':>9s} {'corr':>7s}")
for code, name in NAMED.items():
    if code not in cw.index:
        print(f"{name:18s} {code:6d}  NOT IN FLEET")
        continue
    cs, wsv = plant_series(c, code), plant_series(w, code)
    d = cs - wsv
    ac, aw = cs.sum() / 1e3, wsv.sum() / 1e3
    pct = 100 * (ac - aw) / ac if ac else 0.0
    corr = np.corrcoef(cs, wsv)[0, 1] if cs.std() > 0 and wsv.std() > 0 else 1.0
    print(f"{name:18s} {code:6d} {ac:10.2f} {aw:10.2f} {ac-aw:10.4f} "
          f"{pct:6.2f}% {np.abs(d).max():9.1f} {np.abs(d).mean():10.3f} "
          f"{int((np.abs(d)>1).sum()):9d} {corr:7.4f}")

print("\nFleet-wide:")
print(f"  total annual gen  cold {annual_c.sum():.1f} GWh  "
      f"warm {annual_w.sum():.1f} GWh  Δ {annual_c.sum()-annual_w.sum():+.4f} GWh")
print(f"  max  | annual Δ |  over all plants: {annual_d.abs().max():.4f} GWh "
      f"(plant {annual_d.abs().idxmax()})")
print(f"  mean | annual Δ |  over all plants: {annual_d.abs().mean():.4f} GWh")
print(f"  plants with |annual Δ| > 1 GWh : {(annual_d.abs() > 1).sum()}")
print(f"  plants with |annual Δ| > 0.1 GWh: {(annual_d.abs() > 0.1).sum()}")
print(f"  max hourly |Δ| anywhere: {diff.abs().to_numpy().max():.1f} MW")
# Sum of absolute hourly swaps as a share of total generation (the churn).
churn = diff.abs().to_numpy().sum()
print(f"  Σ|hourly Δ| (gross reshuffle): {churn/1e3:.1f} GWh "
      f"= {100*churn/cw.to_numpy().sum():.3f}% of total gen")

# Top movers by annual delta.
top = annual_d.abs().sort_values(ascending=False).head(8)
print("\n  Top 8 plants by |annual Δ|:")
for code, val in top.items():
    nm = NAMED.get(int(code), "")
    print(f"    {int(code):6d} {nm:18s} {val:8.4f} GWh "
          f"(cold {annual_c[code]:.2f} -> warm {annual_w[code]:.2f})")
