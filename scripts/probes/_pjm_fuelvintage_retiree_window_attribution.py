"""G-6 part 3: WHICH shared rows move, and why."""

from __future__ import annotations
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/home/user/market-simulator")
sys.path.insert(0, str(ROOT))
from market_sim.config import paths

REAL = paths.active_eia860_dir()
NAME = "eia860_generator_retired_within_window.parquet"
tmp = Path(tempfile.mkdtemp(prefix="eia860_pre7934_"))
for f in os.listdir(REAL):
    if f != NAME:
        os.symlink(REAL / f, tmp / f)
full = pd.read_parquet(REAL / NAME)
full[full.planned_retirement_year >= 2023].reset_index(drop=True).to_parquet(
    tmp / NAME, index=False
)
from scripts import replay_keeper as rk
from scripts import run_calibration as rc

B = ROOT / "results/calibration/pjm_debugb_inputclock_A"


def build(year):
    """Return ``run_year``'s ``fleet_only`` payload for one solve year.

    Built through the same ``run_calibration.run_year`` entry a real solve uses,
    off the committed keeper's own ``meta.json``, so every recorded override
    lands exactly as it does in the LP.

    Args:
        year: Solve year to build for.

    Returns:
        The ``fleet_only`` payload dict (config, fleet, fleet_arrays, mc_base,
        fuel_prices, ...).
    """
    meta = json.loads((B / "meta.json").read_text())
    kw = rk.build_kwargs(meta)
    sig = set(rc.run_year.__code__.co_varnames[: rc.run_year.__code__.co_argcount])
    call = {k: v for k, v in kw.items() if k in sig}
    call.update(
        year=year,
        iso=meta["iso"],
        hours=8760,
        fleet_only=True,
        gas_price=meta["gas_prices"][str(year)],
        ttc_overrides={},
    )
    return rc.run_year(**call)


Y = int(sys.argv[1])
new = build(Y)
paths.active_eia860_dir = lambda *a, **k: tmp
for mod in list(sys.modules):
    m = sys.modules[mod]
    if not (mod.startswith("market_sim") or mod.startswith("scripts")):
        continue
    if getattr(m, "active_eia860_dir", None) is not None:
        try:
            m.active_eia860_dir = lambda *a, **k: tmp
        except Exception:
            pass
    for nm in dir(m):
        o = getattr(m, nm, None)
        if hasattr(o, "cache_clear"):
            try:
                o.cache_clear()
            except Exception:
                pass
old = build(Y)


def rows(p):
    """Return ``(unit_id, plant_code, fuel_type, zone)`` per LP row, in row order.

    Carries the plant code so a moved row can be attributed to its plant, which
    is what names W H Sammis.

    Args:
        p: A ``fleet_only`` payload.

    Returns:
        A list of per-row attribute tuples.
    """
    out = []
    for g in p["fleet"]:
        out.append(
            (
                str(getattr(g, "unit_id", getattr(g, "name", ""))),
                int(getattr(g, "plant_code", getattr(g, "plant_id", -1)) or -1),
                str(getattr(g, "fuel_type", "")),
                str(getattr(g, "zone", "")),
            )
        )
    return out


rn, ro = rows(new), rows(old)
pn = np.asarray(new["fleet_arrays"].pmax, float)
po = np.asarray(old["fleet_arrays"].pmax, float)
dn = {u: (i, pc, ft, z) for i, (u, pc, ft, z) in enumerate(rn)}
do_ = {u: (i, pc, ft, z) for i, (u, pc, ft, z) in enumerate(ro)}
shared = [u for u in dn if u in do_]
diffs = []
for u in shared:
    i, pc, ft, z = dn[u]
    j = do_[u][0]
    d = pn[i] - po[j]
    if abs(d) > 1e-9:
        diffs.append((abs(d), d, u, pc, ft, z, pn[i], po[j]))
diffs.sort(reverse=True)
print(
    f"\n=== PJM {Y}: shared rows whose pmax MOVED ({len(diffs)} of {len(shared)}) ==="
)
print(f"  net pmax change over shared rows = {sum(x[1] for x in diffs):+.4f} MW")
plants = {}
for _, d, u, pc, ft, z, a, b in diffs:
    plants.setdefault(pc, [0.0, ft, z, 0])
    plants[pc][0] += d
    plants[pc][3] += 1
print(f"  distinct plants affected = {len(plants)}")
print("  top plants by |net pmax delta|:")
for pc, (d, ft, z, n) in sorted(plants.items(), key=lambda kv: -abs(kv[1][0]))[:15]:
    print(f"    plant {pc:>6}  {ft:<14} {z:<18} {n:3d} rows  {d:+10.4f} MW")
retired_pre2023 = set(
    full.loc[full.planned_retirement_year < 2023, "plant_id"].astype(int)
)
hit = set(plants) & retired_pre2023
print(
    f"  of those plants, {len(hit)} of {len(plants)} ALSO appear in the 2019-2022 retiree rows"
)
print(
    "  (a plant with BOTH a pre-2023 retiree row and a surviving row is the predicted mechanism)"
)
shutil.rmtree(tmp, ignore_errors=True)
