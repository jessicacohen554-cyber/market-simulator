"""Localize the 2023-only deliverable-capacity delta the retiree A/B found.

``_caiso_retiree_window_inertness.py`` (process-isolated) measures a deliverable
delta of exactly 0.000000 MWh in 2024 and 2025 but **+3,367,624.32 MWh in 2023**,
while the 48 added rows themselves are fully COD-masked in every year. So the
2023 move is in rows that exist in BOTH arms: adding the retirees to the binning
input changed some incumbent unit's capacity or availability.

Dumps per-unit deliverable MWh for both arms and reports the rows that moved.
Each arm runs in its own interpreter — ``cod_ramp._load_cod_map`` is an
``lru_cache`` keyed on the eia860 directory, so an in-process swap is stale.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
ARTIFACT = REPO / "data/raw/eia-860/eia860_generator_retired_within_window.parquet"
BUNDLE = REPO / "results/calibration/caiso260_demand_vintage"

CHILD = r"""
import contextlib, io, json, sys
import numpy as np
sys.path[:0] = [".", "src", "scripts"]
from replay_keeper import derived_run_year_inputs, run_year_kwargs
from run_calibration import run_year
from scripts.lib.bundle_fleet import clear_fleet_caches
BUNDLE, year, dest = sys.argv[1], int(sys.argv[2]), sys.argv[3]
T = 8760
meta = json.load(open(BUNDLE + "/meta.json"))
kw = run_year_kwargs(meta); kw.update(derived_run_year_inputs(BUNDLE, year))
clear_fleet_caches()
with contextlib.redirect_stderr(io.StringIO()):
    st = run_year(year, meta["iso"], T, float(meta["gas_prices"][str(year)]), {},
                  fleet_only=True, **kw)
fa = st["fleet_arrays"]
pmax = np.asarray(fa.pmax, dtype=float)
av = np.asarray(fa.availability, dtype=float)
if av.ndim == 1:
    av = av[:, None] * np.ones(T)
np.savez(dest, ids=np.array(list(map(str, fa.unit_ids))),
         pmax=pmax, deliv=(pmax[:, None] * av).sum(axis=1),
         avail_mean=av.mean(axis=1))
print("OK")
"""


def _arm(year: int, dest: Path) -> None:
    p = subprocess.run(
        [sys.executable, "-c", CHILD, str(BUNDLE), str(year), str(dest)],
        cwd=REPO, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": f"{REPO}:{REPO/'src'}:{REPO/'scripts'}"},
    )
    if "OK" not in p.stdout:
        raise SystemExit(f"child failed\n{p.stdout[-1500:]}\n{p.stderr[-2500:]}")


def main() -> int:
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
    scratch = Path(__file__).resolve().parent / "_caiso_retiree_ab_tmp"
    shipped, parent = scratch / "shipped.parquet", scratch / "parent.parquet"
    a, c = scratch / f"arm{year}.npz", scratch / f"ctl{year}.npz"
    try:
        shutil.copy2(shipped, ARTIFACT); _arm(year, a)
        shutil.copy2(parent, ARTIFACT); _arm(year, c)
    finally:
        shutil.copy2(shipped, ARTIFACT)

    A, C = np.load(a, allow_pickle=True), np.load(c, allow_pickle=True)
    da = dict(zip(A["ids"].tolist(), zip(A["pmax"], A["deliv"], A["avail_mean"])))
    dc = dict(zip(C["ids"].tolist(), zip(C["pmax"], C["deliv"], C["avail_mean"])))
    shared = sorted(set(da) & set(dc))
    moved = [
        (u, dc[u][0], da[u][0], dc[u][1], da[u][1], dc[u][2], da[u][2])
        for u in shared
        if abs(da[u][1] - dc[u][1]) > 1e-6 or abs(da[u][0] - dc[u][0]) > 1e-9
    ]
    only_arm = sorted(set(da) - set(dc))
    print(f"year {year}: shared rows {len(shared)}, arm-only {len(only_arm)}")
    print(f"  arm-only deliverable MWh   = {sum(da[u][1] for u in only_arm):,.3f}")
    print(f"  shared rows that MOVED     = {len(moved)}")
    print(f"  shared deliverable delta   = "
          f"{sum(da[u][1]-dc[u][1] for u in shared):,.3f} MWh")
    print(f"  shared pmax delta          = "
          f"{sum(da[u][0]-dc[u][0] for u in shared):,.6f} MW")
    moved.sort(key=lambda r: -abs(r[4] - r[3]))
    print("\n  top movers (unit, pmax ctl->arm, deliverable ctl->arm, mean avail ctl->arm):")
    for u, p0, p1, d0, d1, v0, v1 in moved[:20]:
        print(f"    {u[:46]:48s} {p0:9.3f}->{p1:9.3f}  {d0:14,.1f}->{d1:14,.1f}  {v0:.4f}->{v1:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
