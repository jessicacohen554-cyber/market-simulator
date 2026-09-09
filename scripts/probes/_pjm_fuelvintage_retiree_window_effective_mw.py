"""G-6 part 2: the 382 extra PJM 2023 rows — do they carry ANY capacity?"""

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


YEAR = int(sys.argv[1])
new = build(YEAR)
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
old = build(YEAR)


def ids(p):
    """Return one stable unit id per LP row, in row order.

    Prefers whatever id array the ``FleetArrays`` carries and falls back to the
    ``Generator`` objects, so the two vintages' rows can be matched by identity
    rather than by position (their row counts differ, which is the finding).

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


ni, oi = ids(new), ids(old)
print(f"\n=== PJM {YEAR}: 2019-window vs 2023-window fleet ===")
print(
    f"  rows: {len(ni)} vs {len(oi)}   extra = {len(set(ni) - set(oi))}   missing = {len(set(oi) - set(ni))}"
)
extra = sorted(set(ni) - set(oi))
idx = {u: i for i, u in enumerate(ni)}
ex = np.array([idx[u] for u in extra])
fa = new["fleet_arrays"]
pmax = np.asarray(fa.pmax, float)
av = np.asarray(fa.availability, float)
eff = pmax[:, None] * av
print(f"  extra rows nameplate pmax sum        = {pmax[ex].sum():.4f} MW")
print(f"  extra rows EFFECTIVE MW-h (pmax x av) = {eff[ex].sum():.10f} MW-h")
print(f"  extra rows max effective MW in any h  = {eff[ex].max():.10f} MW")
print(f"  extra rows max availability           = {av[ex].max():.10f}")
mcn = new["mc_base"]
mco = old["mc_base"]
common = [u for u in ni if u in set(oi)]
ci_n = np.array([idx[u] for u in common])
oidx = {u: i for i, u in enumerate(oi)}
ci_o = np.array([oidx[u] for u in common])
print(f"  SHARED rows ({len(common)}):")
print(
    f"    max|d pmax|    = {np.abs(pmax[ci_n] - np.asarray(old['fleet_arrays'].pmax, float)[ci_o]).max():.10f}"
)
avo = np.asarray(old["fleet_arrays"].availability, float)
print(f"    max|d avail|   = {np.abs(av[ci_n] - avo[ci_o]).max():.10f}")
print(f"    max|d mc_base| = {np.abs(mcn[ci_n] - mco[ci_o]).max():.10f}")
print(
    f"    total effective MW-h: new {eff[ci_n].sum():.6f}  old {(np.asarray(old['fleet_arrays'].pmax, float)[:, None] * avo)[ci_o].sum():.6f}"
)
shutil.rmtree(tmp, ignore_errors=True)
