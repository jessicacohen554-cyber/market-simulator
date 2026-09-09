"""Charter task 3 for NEISO: is the 2019-2022 retiree window inert in 2023-2025?

Builds the NEISO fleet twice off the committed keeper recipe
(``results/calibration/neiso106_offerlevel``) for one solve year, differing only
in which ``eia860_generator_retired_within_window.parquet`` vintage
``paths.active_eia860_dir`` serves: the committed 2019-window artifact versus a
copy filtered to ``planned_retirement_year >= 2023`` (byte-equivalent to the
pre-``7934e92c`` artifact). Nothing under ``data/raw`` is modified — the
alternate vintage is a temp directory of symlinks.

The gate (charter §5 task 3): **max |class-hour delta| = 0.000000 MW**. The
known risk is the redistribution defect
``docs/FINDING-pjm-retiree-window-redistribution-2026-09-09.md`` names, whose
NEISO exposure is Mystic Generating Station (521.5 MW).

Usage::

    python3 scripts/probes/_neiso_retiree_window_delta.py 2023
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from market_sim.config import paths  # noqa: E402

REAL = paths.active_eia860_dir()
NAME = "eia860_generator_retired_within_window.parquet"
tmp = Path(tempfile.mkdtemp(prefix="eia860_pre7934_"))
for _f in os.listdir(REAL):
    if _f != NAME:
        os.symlink(REAL / _f, tmp / _f)
_full = pd.read_parquet(REAL / NAME)
_full[_full.planned_retirement_year >= 2023].reset_index(drop=True).to_parquet(
    tmp / NAME, index=False
)

from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402

BUNDLE = ROOT / "results/calibration/neiso106_offerlevel"


def build(year: int) -> dict:
    """Return ``run_year``'s ``fleet_only`` payload for one solve year.

    Args:
        year: Solve year to build for.

    Returns:
        The ``fleet_only`` payload dict.
    """
    meta = json.loads((BUNDLE / "meta.json").read_text())
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


def _repoint() -> None:
    """Repoint every imported module's ``active_eia860_dir`` at the temp vintage."""
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


def ids(p: dict) -> list[str]:
    """Return one stable unit id per LP row, in row order.

    Args:
        p: A ``fleet_only`` payload.

    Returns:
        A list of unit-id strings, one per LP row.
    """
    fa = p["fleet_arrays"]
    for attr in ("unit_ids", "unit_id", "gen_ids", "ids", "names"):
        v = getattr(fa, attr, None)
        if v is not None and len(v) == fa.n_gen:
            return [str(x) for x in v]
    return [
        str(getattr(g, "unit_id", getattr(g, "name", i)))
        for i, g in enumerate(p["fleet"])
    ]


YEAR = int(sys.argv[1])
new = build(YEAR)
_repoint()
old = build(YEAR)

ni, oi = ids(new), ids(old)
fan, fao = new["fleet_arrays"], old["fleet_arrays"]
pn = np.asarray(fan.pmax, float)
po = np.asarray(fao.pmax, float)
an = np.asarray(fan.availability, float)
ao = np.asarray(fao.availability, float)
effn = pn[:, None] * an
effo = po[:, None] * ao

print(f"\n=== NEISO {YEAR}: 2019-window (HEAD) vs 2023-window (pre-7934e92c) ===")
extra = sorted(set(ni) - set(oi))
missing = sorted(set(oi) - set(ni))
print(f"  rows: {len(ni)} vs {len(oi)}   extra = {len(extra)}   missing = {len(missing)}")

idx = {u: i for i, u in enumerate(ni)}
if extra:
    ex = np.array([idx[u] for u in extra])
    print(f"  INJECTED rows nameplate pmax sum       = {pn[ex].sum():.4f} MW")
    print(f"  INJECTED rows EFFECTIVE MW-h           = {effn[ex].sum():.10f} MW-h")
    print(f"  INJECTED rows max availability         = {an[ex].max():.10f}")

common = [u for u in ni if u in set(oi)]
cn = np.array([idx[u] for u in common])
oidx = {u: i for i, u in enumerate(oi)}
co = np.array([oidx[u] for u in common])
dp = np.abs(pn[cn] - po[co])
da_full = np.abs(an[cn] - ao[co])
da = da_full.max(axis=1) if da_full.ndim == 2 else da_full
dm_full = np.abs(np.asarray(new["mc_base"])[cn] - np.asarray(old["mc_base"])[co])
dm = dm_full.max(axis=1) if dm_full.ndim == 2 else dm_full
de = effn[cn].sum() - effo[co].sum()
print(f"  SHARED rows ({len(common)}):")
print(f"    max|d pmax|         = {dp.max():.10f} MW")
print(f"    max|d availability| = {da.max():.10f}")
print(f"    max|d mc_base|      = {dm.max():.10f} $/MWh")
print(f"    d effective MW-h    = {de:+.4f}  ({de / max(effo[co].sum(), 1) * 100:+.6f} %)")

moved = np.where((dp > 1e-9) | (da > 1e-9) | (dm > 1e-9))[0]
print(f"    shared rows that MOVE: {len(moved)}")
if len(moved):
    by_plant: dict = defaultdict(lambda: [0, 0.0, 0.0])
    fleet = new["fleet"]
    for j in moved:
        g = fleet[cn[j]]
        key = (getattr(g, "plant_code", None), getattr(g, "zone", None), getattr(g, "fuel_type", None))
        by_plant[key][0] += 1
        by_plant[key][1] += float(pn[cn[j]] - po[co[j]])
        by_plant[key][2] = max(by_plant[key][2], float(dm[j]))
    print("    per-plant attribution (plant, zone, fuel) -> rows, d pmax MW, max d mc:")
    for k, v in sorted(by_plant.items(), key=lambda kv: -abs(kv[1][1])):
        print(f"      {k}  rows={v[0]}  d_pmax={v[1]:+.4f} MW  max_d_mc={v[2]:.4f}")

shutil.rmtree(tmp, ignore_errors=True)
